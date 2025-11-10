# YappySA/services/pipeline.py
from __future__ import annotations
import pandas as pd
from sqlalchemy.exc import IntegrityError
from YappySA.utils.data_utils import load_excel_normalized, validate_df, classify_row
from YappySA.infra.db.session import SessionLocal
from YappySA.infra.db.repository import upsert_client_and_contacts
from YappySA.infra.reporting.exporter import export_failed_rows

def run_import_pipeline(path: str) -> dict:
    df = load_excel_normalized(path)

    errors = validate_df(df)
    if errors:
        raise ValueError("Errores de validación:\n" + "\n".join(errors))

    df["__class"] = df.apply(classify_row, axis=1)

    failed: list[dict] = []

    p_mask = df["__class"].eq("PERSONAL")
    nid = df["national_id"].fillna("").astype(str).str.strip()
    p_valid = p_mask & nid.ne("")
    p_dup_mask = nid[p_valid].duplicated(keep="first")
    for idx in nid[p_valid][p_dup_mask].index:
        row = df.loc[idx]
        failed.append({
            "row_number_excel": int(idx) + 2,
            "reason": "Duplicado en archivo (cédula)",
            "client_type": "PERSONAL",
            "name": row.get("name",""),
            "national_id": row.get("national_id",""),
            "ruc": "",
            "company_name": row.get("company_name",""),
            "email": row.get("email",""),
            "phone": row.get("phone",""),
            "alias": row.get("alias",""),
        })

    c_mask = df["__class"].eq("COMMERCIAL")
    ruc = df["ruc"].fillna("").astype(str).str.strip() if "ruc" in df.columns else pd.Series([""]*len(df))
    c_no_ruc = c_mask & ruc.eq("")
    for idx in ruc[c_no_ruc].index:
        row = df.loc[idx]
        failed.append({
            "row_number_excel": int(idx) + 2,
            "reason": "RUC obligatorio en clientes comerciales",
            "client_type": "COMMERCIAL",
            "name": row.get("name",""),
            "national_id": row.get("national_id",""),
            "ruc": "",
            "company_name": row.get("company_name",""),
            "email": row.get("email",""),
            "phone": row.get("phone",""),
            "alias": row.get("alias",""),
        })

    c_with_ruc = c_mask & ruc.ne("")
    c_dup_mask = ruc[c_with_ruc].duplicated(keep="first")
    for idx in ruc[c_with_ruc][c_dup_mask].index:
        row = df.loc[idx]
        failed.append({
            "row_number_excel": int(idx) + 2,
            "reason": "Duplicado en archivo (RUC)",
            "client_type": "COMMERCIAL",
            "name": row.get("name",""),
            "national_id": row.get("national_id",""),
            "ruc": row.get("ruc",""),
            "company_name": row.get("company_name",""),
            "email": row.get("email",""),
            "phone": row.get("phone",""),
            "alias": row.get("alias",""),
        })

    # Índices a omitir por validaciones "suaves"
    to_skip = set(nid[p_valid][p_dup_mask].index) | set(ruc[c_no_ruc].index) | set(ruc[c_with_ruc][c_dup_mask].index)
    df = df.drop(index=list(to_skip))

    # 4) importar lo restante (aún pueden fallar por duplicados en BD)
    total = len(df) + len(to_skip)
    personal = int((df["__class"] == "PERSONAL").sum())
    commercial = int((df["__class"] == "COMMERCIAL").sum())
    inserted = 0

    with SessionLocal() as session:
        for i, row in df.iterrows():
            kind = row["__class"]

            class DTO: pass
            dto = DTO()
            dto.name = str(row.get("name", "") or "").strip()
            dto.national_id = str(row.get("national_id", "") or "").strip()
            dto.company_name = str(row.get("company_name", "") or "").strip()
            dto.email = str(row.get("email", "") or "").strip()
            dto.phone = str(row.get("phone", "") or "").strip()
            dto.alias = str(row.get("alias", "") or "").strip()
            dto.ruc = str(row.get("ruc", "") or "").strip()


            try:
                with session.begin():
                    upsert_client_and_contacts(session, dto, kind)
                inserted += 1
            except Exception as e:
                failed.append({
                    "row_number_excel": int(i) + 2,
                    "reason": str(e).splitlines()[0],  # ej: "❌ Cédula duplicada: ..."
                    "client_type": kind,
                    "name": dto.name,
                    "national_id": dto.national_id,
                    "ruc": dto.ruc,
                    "company_name": dto.company_name,
                    "email": dto.email,
                    "phone": dto.phone,
                    "alias": dto.alias,
                })
                session.rollback()

    failed_path = export_failed_rows(failed)

    return {
        "total": total,
        "personal": personal,
        "commercial": commercial,
        "inserted": inserted,
        "skipped": len(failed),
        "failed_csv": failed_path
    }
