# repo.py
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

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")  # simple y eficaz
_PHONE_RE = re.compile(r"^[\d\s+\-()]{5,30}$")         # dígitos y separadores comunes

def _validate_uuid(value: str) -> str:
    try:
        UUID(value)  # solo valida formato
        return value
    except Exception as e:
        raise ValidationError(f"client_uuid inválido: {e}")

def _validate_nonempty(value: str, field: str, maxlen: int = 255) -> str:
    if value is None:
        raise ValidationError(f"{field} es requerido")
    v = value.strip()
    if not v:
        raise ValidationError(f"{field} no puede estar vacío")
    if len(v) > maxlen:
        raise ValidationError(f"{field} excede {maxlen} caracteres")
    return v

def _validate_email(email: str) -> str:
    email = _validate_nonempty(email, "email", maxlen=255)
    if not _EMAIL_RE.match(email):
        raise ValidationError("email no tiene un formato válido")
    return email

def _validate_phone(phone: str) -> str:
    phone = _validate_nonempty(phone, "phone_number", maxlen=50)
    if not _PHONE_RE.match(phone):
        raise ValidationError("phone_number contiene caracteres no permitidos")
    return phone

def _coerce_datetime(value: Union[str, datetime]) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # soporta "YYYY-MM-DD HH:MM:SS" o ISO "YYYY-MM-DDTHH:MM:SS"
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
    raise ValidationError("registration_date debe ser datetime o string con formato YYYY-MM-DD[ HH:MM:SS]")

# ───────────────────────────
# CRUD para personal_client
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
    # Validaciones
    client_uuid = _validate_uuid(client_uuid)
    personal_identification = _validate_nonempty(personal_identification, "personal_identification", maxlen=100)
    first_name  = _validate_nonempty(first_name, "first_name", maxlen=100)
    last_name   = _validate_nonempty(last_name, "last_name", maxlen=100)
    email       = _validate_email(email)
    phone_number = _validate_phone(phone_number)
    registration_date = _coerce_datetime(registration_date)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO personal_client (
                client_uuid, personal_identification, first_name, last_name,
                email, phone_number, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            client_uuid, personal_identification, first_name, last_name,
            email, phone_number, registration_date
        ))

def obtener_todos_personal_client(limit: int = 10) -> List[Tuple]:
    # TOP no acepta parámetro: validamos y formateamos
    limit = int(limit)
    if limit <= 0 or limit > 1000:
        raise ValidationError("limit debe estar entre 1 y 1000")
    sql = f"""
        SELECT TOP {limit}
            client_uuid, personal_identification, first_name, last_name,
            email, phone_number, registration_date
        FROM personal_client
        ORDER BY registration_date DESC
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

def buscar_personal_client_por_uuid(client_uuid: str) -> Optional[Tuple]:
    client_uuid = _validate_uuid(client_uuid)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                client_uuid, personal_identification, first_name, last_name,
                email, phone_number, registration_date
            FROM personal_client
            WHERE client_uuid = ?
        """, (client_uuid,))
        return cur.fetchone()

def actualizar_email(client_uuid: str, nuevo_email: str) -> int:
    client_uuid = _validate_uuid(client_uuid)
    nuevo_email = _validate_email(nuevo_email)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE personal_client
            SET email = ?
            WHERE client_uuid = ?
        """, (nuevo_email, client_uuid))
        return cur.rowcount

def actualizar_telefono(client_uuid: str, nuevo_phone: str) -> int:
    client_uuid = _validate_uuid(client_uuid)
    nuevo_phone = _validate_phone(nuevo_phone)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE personal_client
            SET phone_number = ?
            WHERE client_uuid = ?
        """, (nuevo_phone, client_uuid))
        return cur.rowcount

def borrar_personal_client(client_uuid: str) -> int:
    client_uuid = _validate_uuid(client_uuid)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM personal_client WHERE client_uuid = ?", (client_uuid,))
        return cur.rowcount
