from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]       # .../YappySA
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Variables de entorno
    MSSQL_SERVER: str = Field(...)
    MSSQL_DB: str = Field(...)
    MSSQL_USER: str | None = Field(default=None)
    MSSQL_PWD: str | None = Field(default=None)
    ODBC_DRIVER: str = Field(default="ODBC Driver 17 for SQL Server")
    TRUSTED_CONN: bool = Field(default=False)  # true/1/yes habilita autenticación integrada

    # Dónde leer el .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
    )

    @property
    def sqlalchemy_url(self) -> str:
        drv = self.ODBC_DRIVER.replace(" ", "+")
        if self.TRUSTED_CONN:
            # Autenticación de Windows (sin usuario/contraseña)
            return f"mssql+pyodbc://@{self.MSSQL_SERVER}/{self.MSSQL_DB}?driver={drv}&trusted_connection=yes"
        # Autenticación SQL normal
        return f"mssql+pyodbc://{self.MSSQL_USER}:{self.MSSQL_PWD}@{self.MSSQL_SERVER}/{self.MSSQL_DB}?driver={drv}"

settings = Settings()
