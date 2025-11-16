# run_yappysa.py
from __future__ import annotations

import os
import sys
from pathlib import Path


def _set_workdir_to_exe_folder() -> Path:
    """
    Fija el directorio de trabajo a la carpeta donde está el ejecutable
    (en modo PyInstaller) o a la carpeta de este script (en desarrollo).

    Devuelve la ruta base detectada.
    """
    if getattr(sys, "frozen", False):
        # Ejecutándose como .exe
        base_dir = Path(sys.executable).resolve().parent
    else:
        # Ejecutándose como script normal
        base_dir = Path(__file__).resolve().parent

    os.chdir(base_dir)
    return base_dir


def _load_env_file(env_path: Path) -> None:
    """
    Carga manualmente variables desde un archivo .env muy simple
    (KEY=VALUE por línea), solo si existe.

    Esto garantiza que Pydantic Settings vea MSSQL_SERVER__*, MSSQL_DB__*, etc.
    """
    if not env_path.is_file():
        return

    try:
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # No pisamos valores ya definidos en el entorno
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        # Si falla la carga, seguimos; Pydantic se encargará de avisar
        print(f"[run_yappysa] Aviso: no se pudo cargar .env ({e})", file=sys.stderr)


def main() -> None:
    base_dir = _set_workdir_to_exe_folder()

    # Cargar .env manualmente ANTES de importar nada de YappySA.core.settings
    _load_env_file(base_dir / ".env")

    # Importar la app principal después de tener el entorno listo
    from YappySA.ui.desktop_pyside.main import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
