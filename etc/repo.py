from typing import List, Tuple, Optional, Union
from datetime import datetime
from uuid import UUID
import re

from db_windows_auth import get_connection

# ───────────────────────────
# Validaciones
# ───────────────────────────

class ValidationError(ValueError):
    pass

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[\d\s+\-()]{5,30}$")

def _validate_uuid(value: str) -> str:
    """Valida que el string sea un UUID correcto."""
    UUID(value)  # lanza excepción si no es válido
    return value

def _validate_nonempty(value: str, field: str, maxlen: int = 255) -> str:
    """Valida que un campo no esté vacío y no exceda el tamaño máximo."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{field} no puede estar vacío")
    v = str(value).strip()
    if len(v) > maxlen:
        raise ValidationError(f"{field} excede {maxlen} caracteres")
    return v

def _validate_phone(phone: str) -> str:
    phone = _validate_nonempty(phone, "phone_number", maxlen=50)
    if not _PHONE_RE.match(phone):
        raise ValidationError("phone_number inválido")
    return phone

def _coerce_datetime(value: Union[str, datetime]) -> datetime:
    """Convierte un string/datetime a datetime válido."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
    raise ValidationError("registration_date debe ser datetime o string con formato válido")

# ───────────────────────────
# personal_client
# ───────────────────────────

def crear_personal_client(
    client_uuid: str,
    personal_identification: str,
    first_name: str,
    last_name: str,
    email: str,
    phone_number: str,
    registration_date: Union[str, datetime]
) -> None:
    """Inserta un cliente personal en la tabla personal_client."""
    client_uuid = _validate_uuid(client_uuid)
    personal_identification = _validate_nonempty(personal_identification, "personal_identification", 100)
    first_name  = _validate_nonempty(first_name, "first_name", 100)
    last_name   = _validate_nonempty(last_name, "last_name", 100)
    email       = _validate_email(email)
    phone_number = _validate_phone(phone_number)
    registration_date = _coerce_datetime(registration_date)

    with get_connection() as conn:
        conn.cursor().execute("""
            INSERT INTO dbo.personal_client (
                client_uuid, personal_identification, first_name, last_name,
                email, phone_number, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_uuid, personal_identification, first_name, last_name,
            email, phone_number, registration_date
        ))

def obtener_personal_clients(limit: int = 10) -> List[Tuple]:
    """Devuelve hasta N clientes personales más recientes."""
    limit = int(limit)
    sql = f"""
        SELECT TOP {limit}
            client_uuid, personal_identification, first_name, last_name,
            email, phone_number, registration_date
        FROM dbo.personal_client
        ORDER BY registration_date DESC
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

def buscar_personal_client_por_uuid(client_uuid: str) -> Optional[Tuple]:
    """Busca un cliente personal por UUID."""
    client_uuid = _validate_uuid(client_uuid)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                client_uuid, personal_identification, first_name, last_name,
                email, phone_number, registration_date
            FROM dbo.personal_client
            WHERE client_uuid = ?
        """, (client_uuid,))
        return cur.fetchone()

# ───────────────────────────
# commercial_client
# ───────────────────────────

def crear_commercial_client(
    client_uuid: str,
    commerce_name: str,
    ruc: str,
    admin_id: str,
    email: str,
    registration_date: Union[str, datetime]
) -> None:
    """Inserta un cliente comercial/emprendedor en la tabla commercial_client."""
    client_uuid   = _validate_uuid(client_uuid)
    commerce_name = _validate_nonempty(commerce_name, "commerce_name", 150)
    ruc           = _validate_nonempty(ruc, "ruc", 50)
    admin_id      = _validate_nonempty(admin_id, "admin_id", 100)
    email         = _validate_email(email)
    registration_date = _coerce_datetime(registration_date)

    with get_connection() as conn:
        conn.cursor().execute("""
            INSERT INTO dbo.commercial_client (
                client_uuid, commerce_name, ruc, admin_id, email, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            client_uuid, commerce_name, ruc, admin_id, email, registration_date
        ))

def obtener_commercial_clients(limit: int = 10) -> List[Tuple]:
    """Devuelve hasta N clientes comerciales más recientes."""
    limit = int(limit)
    sql = f"""
        SELECT TOP {limit}
            client_uuid, commerce_name, ruc, admin_id, email, registration_date
        FROM dbo.commercial_client
        ORDER BY registration_date DESC
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

def buscar_commercial_client_por_uuid(client_uuid: str) -> Optional[Tuple]:
    """Busca un cliente comercial por UUID."""
    client_uuid = _validate_uuid(client_uuid)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                client_uuid, commerce_name, ruc, admin_id, email, registration_date
            FROM dbo.commercial_client
            WHERE client_uuid = ?
        """, (client_uuid,))
        return cur.fetchone()
