# YappySA/infra/db/queries.py
from __future__ import annotations
from typing import Sequence, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from YappySA.infra.db.session import engine   # ← aquí

_BASE_SELECT = """
SELECT
  c.client_id,
  c.client_type,
  COALESCE(p.full_name, m.company_name) AS display_name,
  p.national_id,
  m.ruc,
  ci.email,
  ci.phone,
  ci.alias,
  c.created_at
FROM client c
LEFT JOIN personal_client   p ON p.client_id = c.client_id
LEFT JOIN commercial_client m ON m.client_id = c.client_id
LEFT JOIN contact_info      ci ON ci.client_id = c.client_id
"""

def fetch_recent_clients(limit: int = 100) -> pd.DataFrame:
    sql = _BASE_SELECT + """
    ORDER BY c.created_at DESC
    OFFSET 0 ROWS FETCH NEXT :n ROWS ONLY;
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params={"n": limit})

def query_clients_filtered(
    kinds: Optional[Sequence[str]] = None,
    since_date: Optional[datetime] = None,
    uuid: Optional[str] = None,
    national_id: Optional[str] = None,
    ruc: Optional[str] = None,
    limit: Optional[int] = 200
) -> pd.DataFrame:
    where = ["1=1"]; params = {}
    if kinds:
        holders = []
        for i, k in enumerate(kinds):
            key = f"k{i}"; holders.append(f":{key}"); params[key] = k
        where.append(f"c.client_type IN ({', '.join(holders)})")
    if since_date:
        where.append("c.created_at >= :since"); params["since"] = since_date
    if uuid:
        where.append("c.client_id = :uuid"); params["uuid"] = uuid
    if national_id:
        where.append("p.national_id = :nid"); params["nid"] = national_id
    if ruc:
        where.append("m.ruc = :ruc"); params["ruc"] = ruc

    sql = _BASE_SELECT + f"\nWHERE {' AND '.join(where)}\nORDER BY c.created_at DESC\n"
    if limit: sql += "OFFSET 0 ROWS FETCH NEXT :n ROWS ONLY;"; params["n"] = limit
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)
