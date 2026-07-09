"""
database.py — Connexion SQLAlchemy à PostgreSQL.
DATABASE_URL est lue depuis le fichier .env (ou variables d'environnement).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL non définie — vérifie ton .env")

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    """Dépendance FastAPI — fournit une session et la ferme après la requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
