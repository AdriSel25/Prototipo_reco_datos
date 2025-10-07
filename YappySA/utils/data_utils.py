from __future__ import annotations
import pandas as pd

# Aliases para columnas comunes
ALIASES = {
    "name": "name",
    "full_name": "name",
    "display_name": "name",

    "national_id": "national_id",
    "cedula": "national_id",
    "dni": "national_id",

    "company_name": "company_name",
    "razon_social": "company_name",

    "email": "email",
    "correo": "email",

    "phone": "phone",
    "telefono": "phone",

    "alias": "alias",

    "client_type": "client_type",
    "tipo": "client_type",

    "ruc": "ruc",
    "ruc_empresa": "ruc",
    "tax_id": "ruc",
    "rif": "ruc"
}


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {}
    for col in df.columns:
        key = col.strip().lower()
        mapping[col] = ALIASES.get(key, col.strip())
    return df.rename(columns=mapping)


def load_excel_normalized(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = normalize_headers(df)
    return df

# YappySA/utils/data_utils.py
def validate_df(df: pd.DataFrame) -> list[str]:
    # aquí deja SOLO errores que realmente impidan continuar
    return []



def classify_row(row: pd.Series) -> str:
    ctype = str(row.get("client_type", "")).strip().upper()
    if "COMMERCIAL" in ctype or "COMERCIAL" in ctype:
        return "COMMERCIAL"
    return "PERSONAL"
