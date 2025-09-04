import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

# === Funciones base (simuladas) ===
def generar_reporte():
    filtros = []
    if var_id.get(): filtros.append("ID")
    if var_fecha.get(): filtros.append("Fecha")
    if var_cedula.get(): filtros.append("Cédula")

    clientes = []
    if var_personales.get(): clientes.append("Personales")
    if var_comerciales.get(): clientes.append("Comerciales")

    formatos = []
    if var_csv.get(): formatos.append("CSV")
    if var_excel.get(): formatos.append("Excel")

    if not clientes:
        messagebox.showwarning("Error", "Debe seleccionar al menos un tipo de cliente.")
        return

    if not formatos:
        messagebox.showwarning("Error", "Debe seleccionar al menos un formato de salida.")
        return

    resumen = (
        f"\n--- REPORTE SOLICITADO ---\n"
        f"Filtros: {', '.join(filtros) or 'Ninguno'}\n"
        f"Clientes: {', '.join(clientes)}\n"
        f"Formato: {', '.join(formatos)}"
    )
    messagebox.showinfo("Reporte generado", resumen)

# === Ventana principal ===
root = tk.Tk()
root.title("Generador de Reportes - Clientes")
root.geometry("600x480")
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

frame = ttk.Frame(root, padding=20)
frame.grid(row=0, column=0, sticky="nsew")

# Configurar expansibilidad del grid
for i in range(3):
    frame.columnconfigure(i, weight=1)
frame.rowconfigure(0, weight=1)

# === Frames de secciones ===
consulta_frame = ttk.LabelFrame(frame, text="Consulta", padding=10)
consulta_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
clientes_frame = ttk.LabelFrame(frame, text="Clientes", padding=10)
clientes_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
formato_frame = ttk.LabelFrame(frame, text="Formato de archivo", padding=10)
formato_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

# === Variables ===
var_id = tk.BooleanVar()
var_fecha = tk.BooleanVar()
var_cedula = tk.BooleanVar()
var_comerciales = tk.BooleanVar()
var_personales = tk.BooleanVar()
var_csv = tk.BooleanVar()
var_excel = tk.BooleanVar()

# === Checkbuttons ===
ttk.Checkbutton(consulta_frame, text="ID's", variable=var_id).pack(anchor="w")
ttk.Checkbutton(consulta_frame, text="Fecha actualización", variable=var_fecha).pack(anchor="w")
ttk.Checkbutton(consulta_frame, text="Cédula", variable=var_cedula).pack(anchor="w")

ttk.Checkbutton(clientes_frame, text="Comerciales", variable=var_comerciales).pack(anchor="w")
ttk.Checkbutton(clientes_frame, text="Personales", variable=var_personales).pack(anchor="w")

ttk.Checkbutton(formato_frame, text="CSV", variable=var_csv).pack(anchor="w")
ttk.Checkbutton(formato_frame, text="Excel", variable=var_excel).pack(anchor="w")

# === Botón de solicitud ===
ttk.Button(frame, text="Solicitar", command=generar_reporte).grid(row=1, column=1, pady=(20, 10))

# === Logo (parte inferior, respetando proporciones) ===
try:
    logo_path = os.path.join(os.path.dirname(__file__), "resources", "logo_empresa.png")
    img = Image.open(logo_path)
    img.thumbnail((200, 173), Image.Resampling.LANCZOS)  # Máximo 200x173 manteniendo proporciones
    logo = ImageTk.PhotoImage(img)

    logo_label = tk.Label(frame, image=logo)
    logo_label.image = logo
    logo_label.grid(row=2, column=1, pady=(10, 0))

except Exception as e:
    logo_label = tk.Label(frame, text=f"[Logo no encontrado: {e}]", fg="gray")
    logo_label.grid(row=2, column=1, pady=(10, 0))

root.mainloop()
