# YappySA/ui/desktop_pyside/main.py
from __future__ import annotations
import os, sys
import pandas as pd
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QMessageBox, QTableView, QStatusBar, QFrame
)
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
from PySide6.QtCore import Qt

from YappySA.services.pipeline import run_import_pipeline
from YappySA.infra.db.queries import fetch_recent_clients
from YappySA.ui.desktop_pyside.table_model import PandasModel
from YappySA.ui.desktop_pyside.pdf_utils import export_table_to_pdf


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yappy S.A. – Sistema de Gestión de Clientes")
        self.resize(1250, 750)
        self.current_path = ""

        self._apply_theme()
        self._setup_ui()
        self._setup_statusbar()

    # ======================================================
    # 🎨 Paleta y tema visual
    # ======================================================
    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        palette = QPalette()

        # Colores base
        celeste = QColor("#00aaff")
        naranja = QColor("#ff8c00")
        fondo = QColor("#f7f9fc")
        texto = QColor("#1e1e1e")

        palette.setColor(QPalette.Window, fondo)
        palette.setColor(QPalette.WindowText, texto)
        palette.setColor(QPalette.Base, QColor("white"))
        palette.setColor(QPalette.Button, celeste)
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, naranja)
        palette.setColor(QPalette.HighlightedText, Qt.white)
        app.setPalette(palette)

        app.setFont(QFont("Segoe UI", 9))

        # Guardar colores para botones
        self.primary_color = celeste.name()
        self.accent_color = naranja.name()

    # ======================================================
    # 🧱 Construcción de interfaz
    # ======================================================
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # ---------- Encabezado con logo y título ----------
        header = QHBoxLayout()
        logo_path = Path(__file__).resolve().parents[2] / "resources" / "logo_empresa.png"
        logo_label = QLabel()
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        header.addWidget(logo_label)

        title_label = QLabel("Yappy S.A.\nSistema de Gestión de Clientes")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.accent_color};")
        header.addWidget(title_label)
        header.addStretch()
        main_layout.addLayout(header)

        # Línea decorativa naranja bajo el encabezado
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {self.accent_color}; background-color: {self.accent_color}; height: 3px;")
        main_layout.addWidget(line)

        # ---------- Barra de botones ----------
        button_bar = QHBoxLayout()
        button_bar.setSpacing(10)

        def make_button(text, icon_name=None, color=None):
            btn = QPushButton(f" {text}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(QIcon.fromTheme(icon_name) if icon_name else QIcon())
            base_color = color or self.primary_color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {base_color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {self._darken(base_color, 0.85)};
                }}
            """)
            return btn

        self.btn_open = make_button("Abrir Excel", "document-open", self.accent_color)
        self.btn_open.clicked.connect(self.open_file)

        self.btn_import = make_button("Procesar e Importar", "system-run")
        self.btn_import.clicked.connect(self.process)

        self.btn_preview = make_button("Ver últimas 100", "view-refresh")
        self.btn_preview.clicked.connect(self.preview_recent)

        self.btn_export = make_button("Consultar / Exportar…", "document-save")
        self.btn_export.clicked.connect(self.open_export_dialog)

        self.btn_pdf = make_button("Imprimir vista (PDF)", "document-print")
        self.btn_pdf.clicked.connect(self.print_view)

        for b in [self.btn_open, self.btn_import, self.btn_preview, self.btn_export, self.btn_pdf]:
            button_bar.addWidget(b)

        main_layout.addLayout(button_bar)

        # ---------- Tabla ----------
        self.table = QTableView()
        self.model = PandasModel(pd.DataFrame())
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self.accent_color};
                color: white;
                font-weight: bold;
                padding: 4px;
            }}
        """)
        main_layout.addWidget(self.table, 1)

    # ======================================================
    # 🔧 Status bar y helpers
    # ======================================================
    def _setup_statusbar(self):
        status = QStatusBar()
        status.showMessage("Listo.")
        self.setStatusBar(status)
        self.status = status

    def _darken(self, color_hex: str, factor: float) -> str:
        """Oscurece un color hex."""
        c = QColor(color_hex)
        r = max(0, int(c.red() * factor))
        g = max(0, int(c.green() * factor))
        b = max(0, int(c.blue() * factor))
        return QColor(r, g, b).name()

    # ======================================================
    # ⚙️ Funcionalidad existente
    # ======================================================
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)")
        if path:
            self.current_path = path
            self.status.showMessage(f"Archivo seleccionado: {path}")

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

        msg = (f"Total filas: {s.get('total', 0)}\n"
               f"Insertadas: {s.get('inserted', 0)}\n"
               f"Omitidas: {s.get('skipped', 0)}")
        failed_csv = s.get("failed_csv")
        if failed_csv:
            msg += f"\n\nSe creó un CSV con los errores:\n{failed_csv}"
        QMessageBox.information(self, "Resultado de importación", msg)
        self.status.showMessage("Importación completada.")
        self.preview_recent()

    def preview_recent(self):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            df = fetch_recent_clients(limit=100)
            self.model.set_df(df)
            self.status.showMessage("Mostrando los últimos 100 registros.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la vista previa.\n{e}")
        finally:
            QApplication.restoreOverrideCursor()

    def open_export_dialog(self):
        from YappySA.ui.desktop_pyside.query_export_dialog import QueryExportDialog
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
            export_table_to_pdf(self.table, path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF.\n{e}")
            return
        finally:
            QApplication.restoreOverrideCursor()
        QMessageBox.information(self, "PDF generado", f"Archivo guardado: {path}")

# ======================================================
# 🏁 Entry point
# ======================================================
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
