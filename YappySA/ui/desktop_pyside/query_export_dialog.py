from __future__ import annotations
from datetime import datetime
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QCheckBox,
    QDateEdit, QPushButton, QRadioButton, QFileDialog, QMessageBox, QTableView
)
from PySide6.QtCore import Qt, QDate
import pandas as pd

from YappySA.infra.db.queries import query_clients_filtered
from YappySA.infra.reporting.exporter import export_dataframe
from YappySA.ui.desktop_pyside.table_model import PandasModel


# ------------------------------------
# Helper: parsear múltiples valores
# ------------------------------------
def _parse_multi_values(text: str | None):
    """
    Convierte un texto tipo:
      'uuid1, uuid2; uuid3'
    en:
      ['uuid1', 'uuid2', 'uuid3']

    Acepta separadores: coma, punto y coma, salto de línea.
    Devuelve:
      - None si no hay nada útil
      - list[str] si hay uno o más valores
    """
    if not text:
        return None
    parts = [p.strip() for p in re.split(r"[,\n;]", text) if p.strip()]
    return parts or None


class QueryExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Consultar / Exportar")
        self.resize(900, 600)
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)

        # --------- Filtros ---------
        grid = QGridLayout()
        row = 0

        # Tipos de cliente
        self.cb_personal = QCheckBox("Personales")
        self.cb_commercial = QCheckBox("Comerciales")
        self.cb_personal.setChecked(True)
        self.cb_commercial.setChecked(True)
        grid.addWidget(QLabel("Tipos:"), row, 0)
        grid.addWidget(self.cb_personal, row, 1)
        grid.addWidget(self.cb_commercial, row, 2)
        row += 1

        # Fecha desde
        self.cb_date = QCheckBox("Desde fecha:")
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setEnabled(False)
        self.cb_date.toggled.connect(self.date_from.setEnabled)
        grid.addWidget(self.cb_date, row, 0)
        grid.addWidget(self.date_from, row, 1)
        row += 1

        # Campos de filtro (ahora aceptan múltiples valores)
        self.le_uuid = QLineEdit()
        self.le_uuid.setPlaceholderText(
            "UUID(s) exactos: uno o varios separados por coma, ; o salto de línea"
        )

        self.le_nid = QLineEdit()
        self.le_nid.setPlaceholderText(
            "Cédula(s) (national_id) – uno o varios"
        )

        self.le_ruc = QLineEdit()
        self.le_ruc.setPlaceholderText(
            "RUC(s) comerciales – uno o varios"
        )

        grid.addWidget(QLabel("UUID:"), row, 0)
        grid.addWidget(self.le_uuid, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("Cédula:"), row, 0)
        grid.addWidget(self.le_nid, row, 1, 1, 2)
        row += 1

        grid.addWidget(QLabel("RUC:"), row, 0)
        grid.addWidget(self.le_ruc, row, 1, 1, 2)
        row += 1

        v.addLayout(grid)

        # --------- Formato de exportación ---------
        f = QHBoxLayout()
        self.rb_csv = QRadioButton("CSV")
        self.rb_xlsx = QRadioButton("Excel")
        self.rb_csv.setChecked(True)
        f.addWidget(QLabel("Formato:"))
        f.addWidget(self.rb_csv)
        f.addWidget(self.rb_xlsx)
        f.addStretch()
        v.addLayout(f)

        # --------- Botones ---------
        h = QHBoxLayout()
        btn_preview = QPushButton("Previsualizar")
        btn_export = QPushButton("Exportar…")
        btn_preview.clicked.connect(self.on_preview)
        btn_export.clicked.connect(self.on_export)
        h.addWidget(btn_preview)
        h.addWidget(btn_export)
        h.addStretch()
        v.addLayout(h)

        # --------- Tabla de preview ---------
        self.table = QTableView()
        self.model = PandasModel(pd.DataFrame())
        self.table.setModel(self.model)
        v.addWidget(self.table, 1)

    # --------- Helpers ---------
    def _gather(self):
        # Tipos
        kinds = []
        if self.cb_personal.isChecked():
            kinds.append("PERSONAL")
        if self.cb_commercial.isChecked():
            kinds.append("COMMERCIAL")

        # Fecha
        since = None
        if self.cb_date.isChecked():
            qd = self.date_from.date()
            since = datetime(qd.year(), qd.month(), qd.day())

        # Múltiples valores: UUID, cédula, RUC
        uuid_list = _parse_multi_values(self.le_uuid.text().strip())
        nid_list = _parse_multi_values(self.le_nid.text().strip())
        ruc_list = _parse_multi_values(self.le_ruc.text().strip())

        return kinds, since, uuid_list, nid_list, ruc_list

    def _do_query(self, limit=None) -> pd.DataFrame:
        kinds, since, uuid_list, nid_list, ruc_list = self._gather()
        if not kinds:
            raise ValueError("Selecciona al menos un tipo de cliente.")

        return query_clients_filtered(
            kinds=kinds,
            since_date=since,
            uuid=uuid_list,
            national_id=nid_list,
            ruc=ruc_list,
            limit=limit,
        )

    # --------- Slots ---------
    def on_preview(self):
        try:
            df = self._do_query(limit=200)
            self.model.set_df(df)
            if df.empty:
                QMessageBox.information(
                    self, "Sin resultados",
                    "No se encontraron filas con esos filtros."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_export(self):
        try:
            df = self._do_query(limit=None)
            if df.empty:
                QMessageBox.information(
                    self, "Sin resultados",
                    "No se encontraron filas para exportar."
                )
                return

            default = "consulta.csv" if self.rb_csv.isChecked() else "consulta.xlsx"
            filt = "CSV (*.csv)" if self.rb_csv.isChecked() else "Excel (*.xlsx)"
            path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", default, filt)
            if not path:
                return

            fmt = "csv" if self.rb_csv.isChecked() else "xlsx"
            export_dataframe(df, path, fmt=fmt)
            QMessageBox.information(self, "Listo", f"Archivo guardado:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
