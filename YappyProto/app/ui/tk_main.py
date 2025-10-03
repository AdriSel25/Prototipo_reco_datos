from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd

# Importa utilidades del módulo común
from app.utils.data_utils import (
    load_excel_normalized,
    validate_df,
    classify_row,
    export_outputs,
)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yappy – Cargador de Clientes)")
        self.geometry("760x300")
        self.excel_path = tk.StringVar(value="(ninguno)")
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}
        tk.Label(self, text="Archivo Excel:").grid(row=0, column=0, sticky="w", **pad)
        tk.Label(self, textvariable=self.excel_path, fg="#555").grid(row=0, column=1, columnspan=3, sticky="w", **pad)

        tk.Button(self, text="Abrir Excel", command=self.pick_excel).grid(row=1, column=0, **pad)
        tk.Button(self, text="Procesar (validar + clasificar + exportar)", command=self.process).grid(row=1, column=1, columnspan=2, **pad)
        tk.Button(self, text="Abrir carpeta de salida", command=self.open_outputs).grid(row=1, column=3, **pad)

        note = ("Formato esperado de columnas:\n"
                "name, email, national_id, client_type, company_name, alias, phone\n"
                "Sugerencia: client_type = personal/commercial")
        tk.Label(self, text=note, fg="#666", justify="left").grid(row=2, column=0, columnspan=4, sticky="w", **pad)

    def pick_excel(self):
        path = filedialog.askopenfilename(
            title="Seleccionar Excel",
            filetypes=[("Excel", "*.xlsx"), ("Excel antiguo", "*.xls")]
        )
        if path:
            self.excel_path.set(path)

    def process(self):
        path = self.excel_path.get()
        if not path or path == "(ninguno)":
            messagebox.showwarning("Atención", "Selecciona un archivo Excel primero.")
            return
        try:
            df = load_excel_normalized(path)
            errors = validate_df(df)
            if errors:
                messagebox.showerror("Errores de validación", "\n".join(errors))
                return

            df["__class"] = df.apply(classify_row, axis=1)
            personal = df[df["__class"] == "PERSONAL"].drop(columns=["__class"], errors="ignore")
            commercial = df[df["__class"] == "COMMERCIAL"].drop(columns=["__class"], errors="ignore")

            out_dir = export_outputs(personal, commercial)
            msg = (f"Procesado OK\n\n"
                   f"Personal:   {len(personal)}\n"
                   f"Comercial:  {len(commercial)}\n\n"
                   f"Archivos en: {out_dir}")
            messagebox.showinfo("Éxito", msg)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_outputs(self):
        try:
            # Windows
            os.startfile("outputs")
        except Exception:
            messagebox.showinfo("Info", "Abre manualmente la carpeta 'outputs' en la raíz del proyecto.")

if __name__ == "__main__":
    App().mainloop()
