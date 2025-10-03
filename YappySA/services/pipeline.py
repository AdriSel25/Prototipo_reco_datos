# YappySA/services/pipeline.py
from YappySA.infra.db.repository import SessionLocal, upsert_client_and_contacts
from YappySA.infra.excel.loader import load_excel_normalized
from YappySA.utils.data_utils import validate_df, classify_row

def run_import_pipeline(path: str) -> dict:
    df = load_excel_normalized(path)
    errors = validate_df(df)
    if errors:
        raise ValueError("Errores de validación:\n" + "\n".join(errors))

    df["__class"] = df.apply(classify_row, axis=1)

    total = len(df); personal = 0; commercial = 0

    with SessionLocal() as session:
        with session.begin():  # transacción
            for _, row in df.iterrows():
                kind = row["__class"]
                personal += (kind == "PERSONAL")
                commercial += (kind == "COMMERCIAL")

                class DTO: pass
                dto = DTO()
                dto.name = row.get("name", "")
                dto.national_id = row.get("national_id", "")
                dto.company_name = row.get("company_name", "")
                dto.email = row.get("email", "")
                dto.phone = row.get("phone", "")
                dto.alias = row.get("alias", "")

                upsert_client_and_contacts(session, dto, kind)

    return {"total": total, "personal": personal, "commercial": commercial}
