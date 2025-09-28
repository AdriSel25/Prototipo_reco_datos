from __future__ import annotations
import os
import unicodedata
from pathlib import Path
from typing import List
import pandas as pd

# ----- Config básica -----
REQUIRED_COLS = ["name","email","national_id","client_type","company_name","alias","phone"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs"

# Mapeo de alias comunes → nombre canónico
ALIASES = {
    # email
    "e-mail": "email", "correo": "email", "mail": "email",
    # national_id
    "cedula": "national_id", "cédula": "national_id", "id": "national_id",
    "identificacion": "national_id", "identificación": "national_id",
    # client_type
    "tipo_cliente": "client_type", "tipo": "client_type", "tipo-de-cliente": "client_type",
    # company_name
    "empresa": "company_name", "razon_social": "company_name", "razón_social": "company_name",
    "compania": "company_name", "compañia": "company_name",
    # alias
    "alias_yappy": "alias", "yappy_alias": "alias", "apodo": "alias",
    # phone
    "telefono": "phone", "teléfono": "phone", "celular": "phone", "movil": "phone", "móvil": "phone",
    # name
    "nombre": "name", "nombre_completo": "name", "razon_social_contacto": "name"
}

# ----- Utilidades de columnas -----
def _slug_col(col: str) -> str:
    s = (col or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.replace("\u00A0", " ").replace("  ", " ").strip()  # non-breaking space
    s = s.replace(" ", "_")
    return s

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_slug_col(c) for c in df.columns]
    df.columns = [ALIASES.get(c, c) for c in df.columns]
    return df

# ----- Carga, validación y clasificación -----
def load_excel_normalized(path: str | os.PathLike) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    return normalize_columns(df).fillna("")

def validate_df(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []

    # columnas requeridas
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        errors.append(f"Columnas faltantes (tras normalizar): {missing}")

    # email (si existe)
    emails = df.get("email", pd.Series([""] * len(df)))
    bad_emails = emails.astype(str).str.strip()
    bad_emails = bad_emails[(bad_emails != "") & (~bad_emails.str.contains("@"))]
    if len(bad_emails) > 0:
        errors.append(f"Correos con formato inválido: {len(bad_emails)} fila(s)")

    # national_id duplicado (si existe)
    nids = df.get("national_id", pd.Series([""] * len(df))).astype(str).str.strip()
    dup_mask = (nids != "") & nids.duplicated(keep=False)
    if dup_mask.any():
        errors.append("Se detectaron national_id duplicados.")

    # client_type válido (si existe)
    if "client_type" in df.columns:
        ct = df["client_type"].astype(str).str.strip().str.upper()
        bad_ct = ~ct.isin(["PERSONAL", "COMMERCIAL", ""])
        if bad_ct.any():
            errors.append("Valores no válidos en client_type (use PERSONAL/COMMERCIAL).")

    return errors

def classify_row(row: pd.Series) -> str:
    ctype = str(row.get("client_type", "") or "").strip().upper()
    company = str(row.get("company_name", "") or "").strip()
    if ctype in ("COMMERCIAL", "COMERCIAL") or company:
        return "COMMERCIAL"
    return "PERSONAL"

# ----- Exportación -----
def export_outputs(personal: pd.DataFrame, commercial: pd.DataFrame) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p_path = OUT_DIR / "personal.csv"
    c_path = OUT_DIR / "commercial.csv"
    all_path = OUT_DIR / "all.xlsx"

    personal.to_csv(p_path, index=False, encoding="utf-8")
    commercial.to_csv(c_path, index=False, encoding="utf-8")
    with pd.ExcelWriter(all_path, engine="openpyxl") as xlw:
        personal.to_excel(xlw, sheet_name="personal", index=False)
        commercial.to_excel(xlw, sheet_name="commercial", index=False)

    return OUT_DIR
