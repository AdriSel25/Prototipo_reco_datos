from __future__ import annotations
from html import escape
from PySide6.QtGui import QPdfWriter, QPageSize, QTextDocument
from PySide6.QtCore import QMarginsF, QSizeF
from PySide6.QtWidgets import QTableView

def _get_headers(model) -> list[str]:
    for attr in ("df", "_df", "dataframe", "data"):
        df = getattr(model, attr, None)
        if df is not None and hasattr(df, "columns"):
            return [str(c) for c in list(df.columns)]
    cols = model.columnCount()
    return [str(model.headerData(c, 1) or "") for c in range(cols)]  # 1=Qt.Horizontal

def _model_to_html(table: QTableView) -> str:
    m = table.model()
    rows, cols = m.rowCount(), m.columnCount()
    headers = _get_headers(m)

    trs = []
    for r in range(rows):
        tds = []
        for c in range(cols):
            val = m.index(r, c).data()
            tds.append(f"<td>{escape(str(val if val is not None else ''))}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    style = """
    <style>
      body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 8pt; color:#111; margin:0; }
      h1 { font-size: 11pt; margin: 0 0 4pt 0; font-weight: 700; }
      table { border-collapse: collapse; width: 100%; table-layout: fixed; }
      th, td { border: 1px solid #ddd; padding: 2px 4px; vertical-align: middle; }
      th { background: #f3f4f6; text-align: left; font-weight: 600; }
      tr:nth-child(even) { background: #fafafa; }
      td { word-wrap: break-word; overflow-wrap: anywhere; }
    </style>
    """
    thead = "<thead><tr>" + "".join(f"<th>{escape(h)}</th>" for h in headers) + "</tr></thead>"
    tbody = "<tbody>" + "".join(trs) + "</tbody>"
    return style + f"<h1>Últimos usuarios actualizados</h1><table>{thead}{tbody}</table>"

def export_table_to_pdf(table: QTableView, pdf_path: str, title: str | None = None):
    html = _model_to_html(table)  # título fijo; no imagen
    writer = QPdfWriter(pdf_path)
    writer.setResolution(300)
    writer.setPageSize(QPageSize(QSizeF(842, 595), QPageSize.Point, "A4Landscape"))
    try:
        writer.setPageMargins(QMarginsF(8, 8, 8, 8))
    except Exception:
        pass
    doc = QTextDocument()
    doc.setDefaultStyleSheet("")
    doc.setPageSize(QSizeF(842 - 16, 595 - 16))
    doc.setHtml(html)
    doc.print_(writer)
