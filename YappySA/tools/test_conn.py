from YappySA.core.settings import settings
from sqlalchemy import create_engine, text

print("URL:", settings.sqlalchemy_url)
engine = create_engine(settings.sqlalchemy_url, future=True)
with engine.connect() as conn:
    v = conn.execute(text("SELECT @@VERSION")).scalar_one()
    print("Conectado OK ->", v)
