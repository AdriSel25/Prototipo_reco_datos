import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox,
                               QPushButton, QLabel, QWidget, QHBoxLayout, QVBoxLayout)
from YappySA.services.pipeline import run_import_pipeline

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yappy – Importador (SQL Server)")
        self.current_path = ""
        central = QWidget(); self.setCentralWidget(central)
        v = QVBoxLayout(central)

        h = QHBoxLayout()
        btn_open = QPushButton("Abrir Excel")
        btn_open.clicked.connect(self.open_file)
        self.lbl = QLabel("(ningún archivo)")
        h.addWidget(btn_open); h.addWidget(self.lbl)
        v.addLayout(h)

        btn_go = QPushButton("Procesar e Importar")
        btn_go.clicked.connect(self.process)
        v.addWidget(btn_go)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Excel", "", "Excel (*.xlsx *.xls)")
        if path:
            self.current_path = path
            self.lbl.setText(path)

    def process(self):
        if not self.current_path:
            QMessageBox.warning(self, "Atención", "Selecciona un archivo primero.")
            return
        try:
            s = run_import_pipeline(self.current_path)
            QMessageBox.information(self, "Éxito",
                f"Total: {s['total']}\nPersonal: {s['personal']}\nComercial: {s['commercial']}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

def main():
    app = QApplication(sys.argv)
    w = MainWindow(); w.resize(820, 420); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
