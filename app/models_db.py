"""
models_db.py — Modèle ORM SQLAlchemy (table de logging des prédictions).

  - prediction_logs : une ligne par appel à /predict, features stockées en JSON blob
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.database import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    timestamp       = Column(DateTime, default=datetime.utcnow)
    source          = Column(String(20), nullable=True)   # "local", "HF_Prod", etc.
    input_features  = Column(JSON)                         # blob complet des ~800 features
    prediction      = Column(Integer, nullable=True)
    probabilite     = Column(Float, nullable=True)
    latence_ms      = Column(Float, nullable=True)
    statut          = Column(String(10), default="success")
    error_code      = Column(String(50), nullable=True)
    error_message   = Column(String(255), nullable=True)
    