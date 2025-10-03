# YappySA/infra/db/repository.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from YappySA.core.settings import settings

engine = create_engine(settings.sqlalchemy_url, fast_executemany=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def upsert_client_and_contacts(session, dto, kind: str):
    """
    Inserta en client + tabla hija + contact_info y retorna client_id (UNIQUEIDENTIFIER).
    Usa OUTPUT para obtener el id en una sola sentencia (evita múltiples statements).
    """
    # 1) client → OUTPUT inserted.client_id
    res = session.execute(text("""
        INSERT INTO client (client_id, client_type)
        OUTPUT inserted.client_id
        VALUES (NEWID(), :kind)
    """), {"kind": kind})
    client_id = res.scalar_one()

    # 2) tabla hija según tipo
    if kind == "PERSONAL":
        session.execute(text("""
            INSERT INTO personal_client (client_id, full_name, national_id)
            VALUES (:cid, :name, NULLIF(:nid, ''))
        """), {"cid": client_id, "name": dto.name or "", "nid": (dto.national_id or "")})
    else:
        session.execute(text("""
            INSERT INTO commercial_client (client_id, company_name, representative, tax_id)
            VALUES (:cid, NULLIF(:company,''), NULLIF(:repr,''), NULLIF(:tax,''))
        """), {
            "cid": client_id,
            "company": dto.company_name or "",
            "repr": dto.name or "",
            "tax": None
        })

    # 3) contacto si hay al menos un dato
    if (dto.email or dto.phone or dto.alias):
        session.execute(text("""
            INSERT INTO contact_info (client_id, email, phone, alias)
            VALUES (:cid, NULLIF(:email,''), NULLIF(:phone,''), NULLIF(:alias,''))
        """), {
            "cid": client_id,
            "email": dto.email or "",
            "phone": dto.phone or "",
            "alias": dto.alias or ""
        })

    return client_id
