# YappySA/infra/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from YappySA.core.settings import settings

engine = create_engine(settings.sqlalchemy_url, fast_executemany=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
