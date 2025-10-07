# YappySA/infra/db/repository.py
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from YappySA.infra.db.session import SessionLocal  # ← de session.py

def upsert_client_and_contacts(session, dto, kind: str):
    try:
        res = session.execute(text("""
            INSERT INTO client (client_id, client_type)
            OUTPUT inserted.client_id
            VALUES (NEWID(), :kind)
        """), {"kind": kind})
        client_id = res.scalar_one()

        if kind == "PERSONAL":
            session.execute(text("""
                INSERT INTO personal_client (client_id, full_name, national_id)
                VALUES (:cid, :name, NULLIF(:nid,''))
            """), {"cid": client_id, "name": dto.name or "", "nid": dto.national_id or ""})
        else:  # COMMERCIAL
            session.execute(text("""
                INSERT INTO commercial_client (client_id, company_name, representative, ruc)
                VALUES (:cid, NULLIF(:company,''), NULLIF(:repr,''), :ruc)
            """), {"cid": client_id, "company": dto.company_name or "",
                   "repr": dto.name or "", "ruc": (dto.ruc or "").strip()})

        if (dto.email or dto.phone or dto.alias):
            session.execute(text("""
                INSERT INTO contact_info (client_id, email, phone, alias)
                VALUES (:cid, NULLIF(:email,''), NULLIF(:phone,''), NULLIF(:alias,''))
            """), {"cid": client_id, "email": dto.email or "",
                   "phone": dto.phone or "", "alias": dto.alias or ""})

        return client_id

    except IntegrityError as e:
        msg = "❌ Registro duplicado en la base de datos."
        if getattr(dto, "national_id", ""):
            msg = f"❌ Cédula duplicada: {dto.national_id}"
        if getattr(dto, "ruc", ""):
            msg = f"❌ RUC duplicado: {dto.ruc}"
        raise ValueError(msg) from e
