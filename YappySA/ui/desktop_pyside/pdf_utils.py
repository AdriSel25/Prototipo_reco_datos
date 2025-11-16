# ui/desktop_pyside/pdf_utils.py
from __future__ import annotations

import re
from html import escape as html_escape
from typing import List, Optional, Tuple

from PySide6.QtCore import QMarginsF, QSizeF, QRectF, Qt
from PySide6.QtGui import (
    QPdfWriter,
    QPageSize,
    QTextDocument,
    QPainter,
    QFont,
)
from PySide6.QtWidgets import QTableView

# =========================
# Parámetros ajustables
# =========================
ROWS_PER_PAGE = 6          # filas por página (holgura vertical)
FONT_PT       = 10         # tamaño base de tabla
TITLE_PT      = 17         # título
FOOTER_PT     = 9          # pie

# A4 apaisado en puntos (1pt = 1/72")
PAGE_W, PAGE_H = 842, 595

# Márgenes pequeños
MARGINS = QMarginsF(10, 12, 10, 12)  # left, top, right, bottom

# “Guardas” de seguridad para que nada se corte
SAFETY_SCALE_X = 0.985     # leve reducción horizontal
SAFETY_SCALE_Y = 0.985     # leve reducción vertical
RIGHT_GUTTER   = 6.0       # canal a la derecha (pt) para evitar mordida del borde

ZW = "\u200B"  # zero-width space para cortes suaves

# ---------- helpers de datos ----------
def _get_headers(model) -> List[str]:
    cols = model.columnCount()
    return [str(model.headerData(c, Qt.Orientation.Horizontal) or "") for c in range(cols)]

def _get_df_and_headers(m) -> Tuple[Optional["object"], List[str]]:
    for attr in ("df", "_df", "dataframe", "data"):
        df = getattr(m, attr, None)
        if df is not None and hasattr(df, "columns"):
            return df, [str(c) for c in list(df.columns)]
    return None, _get_headers(m)

def _cell_value(m, df, r: int, c: int, header: Optional[str] = None):
    if df is not None:
        try:
            return df.iloc[r][header] if header is not None else df.iloc[r, c]
        except Exception:
            pass
    return m.index(r, c).data()

# ---------- helpers visuales ----------
_alnum8 = re.compile(r"([A-Za-z0-9]{8})(?=[A-Za-z0-9])")
def _soft_break(s: str) -> str:
    if not s:
        return ""
    for ch in ("@", ".", "_", "-", ":", "/", "\\", "+"):
        s = s.replace(ch, f"{ch}{ZW}")
    return _alnum8.sub(rf"\1{ZW}", s)

def _col_widths(headers: List[str]) -> List[int]:
    weights = []
    for h in headers:
        hl = h.lower().strip()
        if "display" in hl or "nombre" in hl:
            w = 24
        elif "email" in hl:
            w = 22
        elif "client_id" in hl or "uuid" in hl:
            w = 16
        elif "national" in hl or "cédula" in hl or "cedula" in hl or hl == "ruc":
            w = 14
        elif "phone" in hl or "tel" in hl or "alias" in hl or "created" in hl or "fecha" in hl:
            w = 12
        elif "client_type" in hl or "tipo" in hl:
            w = 10
        else:
            w = 12
        weights.append(w)
    total = sum(weights) or 1
    return [max(6, round(w * 100 / total)) for w in weights]

def _style() -> str:
    # Body texto oscuro, encabezados con texto blanco
    return f"""
<style>
  html, body {{ margin:0; padding:0; }}
  body {{ font-family:'Segoe UI', Arial, sans-serif; font-size:{FONT_PT}pt; color:#111; }}
  h1   {{ font-size:{TITLE_PT}pt; margin:0 0 6pt 0; font-weight:700; text-align:center; }}

  table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
  th, td {{ border:1px solid #ddd; padding:4px 6px; vertical-align:middle; }}

  /* Encabezados: fondo celeste, texto blanco para TODAS las columnas */
  th {{
    background:#00aaff;
    color:#ffffff;
    text-align:left;
    font-weight:600;
  }}

  tr:nth-child(even) td {{ background:#fafafa; }}
  td {{ white-space:normal; word-break:break-word; overflow-wrap:anywhere; hyphens:auto; }}

  .footer {{ margin-top:6pt; font-size:{FOOTER_PT}pt; color:#666; text-align:right; }}
</style>
"""

def _make_table(headers: List[str], widths: List[int], rows_html: List[str]) -> str:
    colgroup = "<colgroup>" + "".join(
        f'<col style="width:{w}%"/>' for w in widths
    ) + "</colgroup>"

    # Todos los encabezados usan el mismo estilo (texto blanco)
    th_cells = [f"<th>{html_escape(h)}</th>" for h in headers]

    thead = "<thead><tr>" + "".join(th_cells) + "</tr></thead>"
    tbody = "<tbody>" + "".join(rows_html) + "</tbody>"
    return f"<table>{colgroup}{thead}{tbody}</table>"

def _page_html(title: str, headers: List[str], widths: List[int], rows_html: List[str], page_num: int) -> str:
    table_html = _make_table(headers, widths, rows_html)
    return _style() + (
        f"<h1>{html_escape(title)}</h1>"
        + table_html
        + f"<div class='footer'>Página {page_num}</div>"
    )

# ---------- export principal ----------
def export_table_to_pdf(table: QTableView, pdf_path: str, title: str | None = None) -> None:
    """
    Paginado (6 filas). Se escala para ocupar el área útil sin recortes.
    Se reserva un canal a la derecha y se aplica un leve safety scale.
    """
    title = title or "Últimos usuarios actualizados"

    model = table.model()
    df, headers = _get_df_and_headers(model)
    if not headers:
        headers = _get_headers(model)

    cols = len(headers) if df is not None else model.columnCount()
    total_rows = len(df) if df is not None else model.rowCount()
    widths = _col_widths(headers)

    writer = QPdfWriter(pdf_path)
    writer.setResolution(72)  # 1:1
    writer.setPageSize(QPageSize(QSizeF(PAGE_W, PAGE_H), QPageSize.Point, "A4Landscape"))
    writer.setPageMargins(MARGINS)

    # Área útil
    content = QRectF(
        MARGINS.left(),
        MARGINS.top(),
        PAGE_W - (MARGINS.left() + MARGINS.right()),
        PAGE_H - (MARGINS.top() + MARGINS.bottom()),
    )

    painter = QPainter(writer)
    painter.setRenderHint(QPainter.Antialiasing, True)

    try:
        def render_html(html: str):
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Segoe UI", FONT_PT))
            logical_width = 900.0
            doc.setTextWidth(logical_width)
            doc.setHtml(html)

            # Escalas con guardas
            usable_width  = max(1.0, content.width() - RIGHT_GUTTER)
            scale_x = (usable_width  / doc.idealWidth())  * SAFETY_SCALE_X
            scale_y = (content.height() / doc.size().height()) * SAFETY_SCALE_Y
            scale   = min(1.0, scale_x, scale_y)

            painter.save()
            painter.translate(content.left(), content.top())
            painter.scale(scale, scale)
            doc.drawContents(painter)
            painter.restore()

        if total_rows == 0:
            render_html(_page_html(title, headers, widths, [], 1))
            return

        page_num = 1
        for start in range(0, total_rows, ROWS_PER_PAGE):
            end = min(start + ROWS_PER_PAGE, total_rows)

            rows_html: List[str] = []
            for r in range(start, end):
                tds = []
                for c in range(cols):
                    header = headers[c] if df is not None else None
                    val = _cell_value(model, df, r, c, header)
                    raw = "" if val is None else str(val)
                    safe = html_escape(_soft_break(raw), quote=False)
                    tds.append(f"<td>{safe}</td>")
                rows_html.append("<tr>" + "".join(tds) + "</tr>")

            render_html(_page_html(title, headers, widths, rows_html, page_num))

            page_num += 1
            if end < total_rows:
                writer.newPage()

    finally:
        painter.end()
