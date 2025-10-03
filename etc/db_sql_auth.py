# db_sql_auth.py
import pyodbc
from contextlib import contextmanager
import os

# Configuración (puedes usar variables de entorno para mayor seguridad)
SERVER   = os.getenv("DB_SERVER", "localhost")
DATABASE = os.getenv("DB_NAME", "TuBaseDeDatos")
UID      = os.getenv("DB_USER", "sa")
PWD      = os.getenv("DB_PASS", "tu_password")

def _conn_str() -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={UID};PWD={PWD};"
        "TrustServerCertificate=yes;"
    )

def connect():
    return pyodbc.connect(_conn_str(), autocommit=False)

@contextmanager
def get_connection():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
