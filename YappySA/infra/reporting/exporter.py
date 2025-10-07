from __future__ import annotations
from pathlib import Path
import pandas as pd
from datetime import datetime

def export_dataframe(df: pd.DataFrame, path: str, fmt: str = "csv"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if fmt.lower() == "csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    elif fmt.lower() in ("xlsx", "excel"):
        df.to_excel(path, index=False)
    else:
        raise ValueError(f"Formato no soportado: {fmt}")

def export_failed_rows(rows: list[dict]) -> str | None:
    """
    Crea outputs/failed_YYYYmmdd_HHMMSS.csv con las filas no procesadas.
    Retorna la ruta del archivo o None si rows está vacío.
    """
    if not rows:
        return None
    base_dir = Path(__file__).resolve().parents[3]  # .../<repo-root>
    out_dir = base_dir / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"failed_{ts}.csv"
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8")
    return str(path)
