from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Union

import pandas as pd
from sqlalchemy import text

from YappySA.infra.db.session import engine


# -------------------------------------------------
# Helper para normalizar filtros (1 ó varios valores)
# -------------------------------------------------
def _normalize_list(value: Optional[Union[str, Sequence[str]]]) -> Optional[List[str]]:
    """
    Acepta:
      - None
      - str
      - lista / tupla / set de str

    Devuelve:
      - None si no hay nada útil
      - list[str] si hay uno o más valores no vacíos
    """
    if value is None:
        return None

    # Si ya es una colección
    if isinstance(value, (list, tuple, set)):
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or None

    # Cadena única
    s = str(value).strip()
    if not s:
        return None
    return [s]


# -------------------------------------------------
# SELECT base (vista consolidada a partir de tablas)
# -------------------------------------------------
_BASE_SELECT = """
SELECT
    c.client_id,
    c.client_type,
    CASE
        WHEN c.client_type = 'PERSONAL'   THEN p.full_name
        WHEN c.client_type = 'COMMERCIAL' THEN m.company_name
        ELSE COALESCE(p.full_name, m.company_name)
    END AS display_name,
    p.national_id,
    m.ruc,
    ci.email,
    ci.phone,
    ci.alias,
    c.created_at
FROM client c
LEFT JOIN personal_client   p  ON p.client_id = c.client_id
LEFT JOIN commercial_client m  ON m.client_id = c.client_id
LEFT JOIN contact_info      ci ON ci.client_id = c.client_id
"""


# -------------------------------------------------
# Últimos N clientes (pantalla "Ver últimas 100")
# -------------------------------------------------
def fetch_recent_clients(limit: int = 100) -> pd.DataFrame:
    """
    Devuelve los últimos N clientes usando el SELECT consolidado.
    """
    limit = max(1, int(limit or 100))

    sql = _BASE_SELECT + """
WHERE 1 = 1
ORDER BY c.created_at DESC
OFFSET 0 ROWS FETCH NEXT :n ROWS ONLY;
"""
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params={"n": limit})


# -------------------------------------------------
# Consulta filtrada (pantalla "Consultar / Exportar")
# -------------------------------------------------
def query_clients_filtered(
    *,
    kinds: Iterable[str],
    since_date: Optional[datetime] = None,
    uuid: Optional[Union[str, Sequence[str]]] = None,
    national_id: Optional[Union[str, Sequence[str]]] = None,
    ruc: Optional[Union[str, Sequence[str]]] = None,
    limit: Optional[int] = 200,
) -> pd.DataFrame:
    """
    Consulta filtrada para la pantalla 'Consultar / Exportar'.

    Soporta:
      - tipos de cliente (PERSONAL / COMMERCIAL)
      - fecha desde
      - uno o varios UUID
      - una o varias cédulas (national_id)
      - uno o varios RUC
    """

    # Normalizar tipos de cliente
    kinds = [k for k in (kinds or []) if k]
    if not kinds:
        # La UI ya protege esto, pero por seguridad
        return pd.DataFrame()

    # Normalizar filtros a listas
    uuid_list = _normalize_list(uuid)
    nid_list = _normalize_list(national_id)
    ruc_list = _normalize_list(ruc)

    where: List[str] = ["1=1"]
    params: dict = {}

    # Tipos de cliente (IN)
    if kinds:
        holders = []
        for i, k in enumerate(kinds):
            key = f"k{i}"
            holders.append(f":{key}")
            params[key] = k
        where.append(f"c.client_type IN ({', '.join(holders)})")

    # Fecha desde
    if since_date is not None:
        where.append("c.created_at >= :since")
        params["since"] = since_date

    # UUID(s)
    if uuid_list:
        holders = []
        for i, u in enumerate(uuid_list):
            key = f"uuid_{i}"
            holders.append(f":{key}")
            params[key] = u
        where.append(f"c.client_id IN ({', '.join(holders)})")

    # Cédula(s)
    if nid_list:
        holders = []
        for i, n in enumerate(nid_list):
            key = f"nid_{i}"
            holders.append(f":{key}")
            params[key] = n
        where.append(f"p.national_id IN ({', '.join(holders)})")

    # RUC(s)
    if ruc_list:
        holders = []
        for i, r_ in enumerate(ruc_list):
            key = f"ruc_{i}"
            holders.append(f":{key}")
            params[key] = r_
        where.append(f"m.ruc IN ({', '.join(holders)})")

    # Construir SQL final
    sql = _BASE_SELECT + f"\nWHERE {' AND '.join(where)}\nORDER BY c.created_at DESC\n"
    if limit:
        sql += "OFFSET 0 ROWS FETCH NEXT :n ROWS ONLY;"
        params["n"] = int(limit)

    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)
