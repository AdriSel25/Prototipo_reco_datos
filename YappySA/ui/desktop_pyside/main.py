# YappySA/ui/desktop_pyside/main.py
from __future__ import annotations
import os
from pathlib import Path
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QPushButton, QLabel,
    QWidget, QHBoxLayout, QVBoxLayout, QTableView
)
from PySide6.QtCore import Qt

from YappySA.services.pipeline import run_import_pipeline
from YappySA.infra.db.queries import fetch_recent_clients
from YappySA.ui.desktop_pyside.table_model import PandasModel
from YappySA.ui.desktop_pyside.pdf_utils import export_table_to_pdf


import pandas as pd


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yappy – Importador (SQL Server)")
        self.current_path = ""
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)

        # --- Fila 1: selección de archivo
        h = QHBoxLayout()
        btn_open = QPushButton("Abrir Excel")
        btn_open.clicked.connect(self.open_file)
        self.lbl = QLabel("(ningún archivo)")
        h.addWidget(btn_open)
        h.addWidget(self.lbl, 1)
        v.addLayout(h)

        # --- Fila 2: acciones principales
        h2 = QHBoxLayout()

        btn_import = QPushButton("Procesar e Importar")
        btn_import.clicked.connect(self.process)

        btn_preview = QPushButton("Ver últimas 100")
        btn_preview.clicked.connect(self.preview_recent)

        btn_export = QPushButton("Consultar / Exportar…")
        btn_export.clicked.connect(self.open_export_dialog)

        btn_print = QPushButton("Imprimir vista (PDF)")
        btn_print.clicked.connect(self.print_view)

        btn_open_outputs = QPushButton("Abrir carpeta de outputs")
        btn_open_outputs.clicked.connect(self.open_outputs_dir)

        h2.addWidget(btn_import)
        h2.addWidget(btn_preview)
        h2.addWidget(btn_export)
        h2.addWidget(btn_print)
        h2.addWidget(btn_open_outputs)
        v.addLayout(h2)

        # --- Tabla central
        self.table = QTableView()
        self.model = PandasModel(pd.DataFrame())
        self.table.setModel(self.model)
        v.addWidget(self.table, 1)

    # ========== Acciones ==========
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)"
        )
        if path:
            self.current_path = path
            self.lbl.setText(path)

    def process(self):
        if not self.current_path:
            QMessageBox.warning(self, "Atención", "Selecciona un archivo primero.")
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            s = run_import_pipeline(self.current_path)
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", str(e))
            return
        finally:
            QApplication.restoreOverrideCursor()

        # Resumen con opción de abrir CSV de fallos
        msg = (f"Total filas: {s.get('total', 0)}\n"
               f"Insertadas:  {s.get('inserted', 0)}\n"
               f"Omitidas:    {s.get('skipped', 0)}")
        failed_csv = s.get("failed_csv")
        if failed_csv:
            msg += f"\n\nSe creó un CSV con los errores:\n{failed_csv}"
        buttons = QMessageBox.StandardButton.Ok
        if failed_csv:
            buttons |= QMessageBox.StandardButton.Open
        ans = QMessageBox.information(self, "Resultado de importación", msg, buttons)
        if ans == QMessageBox.StandardButton.Open and failed_csv:
            self._open_file_os(failed_csv)

        # Refresca la vista
        self.preview_recent()

    def preview_recent(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            df = fetch_recent_clients(limit=100)
            self.model.set_df(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la vista previa.\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def open_export_dialog(self):
        try:
            from YappySA.ui.desktop_pyside.query_export_dialog import QueryExportDialog
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el diálogo de exportación.\n{e}")
            return
        QueryExportDialog(self).exec()

    def print_view(self):
        if self.model.rowCount() == 0:
            QMessageBox.information(self, "Sin datos", "No hay datos en la tabla para imprimir.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "consulta.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            export_table_to_pdf(self.table, path)  # ← sin logo ni extras
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF.\n{e}")
            return
        finally:
            QApplication.restoreOverrideCursor()
        ans = QMessageBox.information(self, "PDF generado", f"Archivo: {path}",
                                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open)
        if ans == QMessageBox.StandardButton.Open:
            self._open_file_os(path)


    def open_outputs_dir(self):
        base_dir = Path(__file__).resolve().parents[2]
        out_dir = base_dir / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        self._open_file_os(str(out_dir))

    # ========== Helpers ==========
    def _open_file_os(self, path: str):
        """Abre un archivo o carpeta con la app por defecto del SO (Windows)."""
        try:
            os.startfile(path)
        except Exception:
            QMessageBox.information(self, "Abrir", f"Ruta: {path}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
