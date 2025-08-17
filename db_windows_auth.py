# db_windows_auth.py
import pyodbc
from contextlib import contextmanager

# Configuración según tu captura
SERVER   = r"DESKTOP-UEMBHIE\SQLEXPRESS"  # Cambia XXXXX por lo que tienes
DATABASE = "protoyapp"                    # Pon el nombre real de tu BD

def _conn_str() -> str:
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};DATABASE={DATABASE};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;"
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
