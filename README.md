# YappySA – Sistema de gestión de clientes (ESCRITORIO)

Prototipo empresarial para **importar**, **validar**, **clasificar** y **exportar** datos de clientes personales y comerciales.
Interfaz **PySide6**, backend en **Python**, almacenamiento en **SQL Server** y reportes **PDF/CSV/XLSX**.

## 1. Requisitos
- Windows 10/11
- Python 3.11+ (si ejecutas desde código)
- SQL Server (local o remoto)
- ODBC Driver 18 for SQL Server
- (Opcional) PyInstaller para generar el .exe

## 2. Instalación (desde código)
```bash
git clone <repo_url>
cd YappySA
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
