# YappySA/infra/db/repository.py
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from YappySA.infra.db.session import SessionLocal  # ← de session.py
import math


def _clean_field(val):
    """
    Normaliza un campo que puede venir como None, '', NaN, etc.
    Devuelve:
      - str con contenido si hay algo útil
      - None si está vacío o es NaN
    """
    if val is None:
        return None

    # Si viene como float NaN (típico de pandas)
    if isinstance(val, float):
        try:
            if math.isnan(val):
                return None
        except TypeError:
            pass

    s = str(val).strip()
    return s or None


def upsert_client_and_contacts(session, dto, kind: str):
    try:
        # Inserta en client y obtiene el UUID generado
        res = session.execute(text("""
            INSERT INTO client (client_id, client_type)
            OUTPUT inserted.client_id
            VALUES (NEWID(), :kind)
        """), {"kind": kind})
        client_id = res.scalar_one()

        # Datos personales vs comerciales (sin cambios en la lógica original)
        if kind == "PERSONAL":
            session.execute(text("""
                INSERT INTO personal_client (client_id, full_name, national_id)
                VALUES (:cid, :name, NULLIF(:nid,''))
            """), {
                "cid": client_id,
                "name": dto.name or "",
                "nid": dto.national_id or "",
            })
        else:  # COMMERCIAL
            session.execute(text("""
                INSERT INTO commercial_client (client_id, company_name, representative, ruc)
                VALUES (:cid, NULLIF(:company,''), NULLIF(:repr,''), :ruc)
            """), {
                "cid": client_id,
                "company": dto.company_name or "",
                "repr": dto.name or "",
                "ruc": (dto.ruc or "").strip(),
            })

        # Contacto opcional (igual que antes)
        if (dto.email or dto.phone or dto.alias):
            session.execute(text("""
                INSERT INTO contact_info (client_id, email, phone, alias)
                VALUES (:cid, NULLIF(:email,''), NULLIF(:phone,''), NULLIF(:alias,''))
            """), {
                "cid": client_id,
                "email": dto.email or "",
                "phone": dto.phone or "",
                "alias": dto.alias or "",
            })

        return client_id

    except IntegrityError as e:
        # --- NUEVA lógica de mensaje, sin tocar las inserciones ---
        nid = _clean_field(getattr(dto, "national_id", None))
        ruc = _clean_field(getattr(dto, "ruc", None))
        kind_norm = (kind or "").upper()

        msg = "❌ Registro duplicado en la base de datos."

        # Preferimos el campo que corresponde al tipo de cliente
        if kind_norm == "PERSONAL" and nid:
            msg = f"❌ Cédula duplicada: {nid}"
        elif kind_norm == "COMMERCIAL" and ruc:
            msg = f"❌ RUC duplicado: {ruc}"
        else:
            # Fallback: usamos lo que realmente tiene valor
            if ruc:
                msg = f"❌ RUC duplicado: {ruc}"
            elif nid:
                msg = f"❌ Cédula duplicada: {nid}"

        raise ValueError(msg) from e
