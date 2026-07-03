from contextlib import asynccontextmanager
import os

from httpcore import request
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from pathlib import Path

#from app.database import engine, Base, get_db
#from app.models_db import PredictionInput, PredictionOutput
from app.__version__ import __version__

load_dotenv()
API_ENV = os.getenv("API_ENV", "local")

# ── Chargement du modèle ──────────────────────────────────────────────────────
MODEL_PATH = Path("models/model.joblib")
model = joblib.load(MODEL_PATH)
EXPECTED_FEATURES = model.feature_name_

# ── Création des tables au démarrage ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("CI") != "true":
 #       Base.metadata.create_all(bind=engine)
       plop="plop"
    yield

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="OC Projet 8 - Scoring Crédit API (API_ENV: " + API_ENV + ")",
    description="API de scoring crédit/ Home Credit (Projet n°8 - OpenClassrooms)",
    version=__version__,
    lifespan=lifespan
)

# ── Schéma Pydantic ───────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    features: Dict[str, Any]

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "API opérationnelle v" + __version__}

@app.get("/health")
def health():
    return {"status": "ok", "version": __version__, "environment": API_ENV}

@app.post("/predict")
def predict(request: PredictRequest):#, db: Session = Depends(get_db)):

    # Vérification des features
    missing = [f for f in EXPECTED_FEATURES if f not in request.features]
    if missing:
        raise HTTPException(status_code=422, detail=f"Features manquantes: {missing}")

    # 1. Log input AVANT inférence
    input_log = PredictionInput(source=API_ENV, features=str(request.features))
    db.add(input_log)
    db.commit()
    db.refresh(input_log)

    # 2. Inférence
    try:
        df = pd.DataFrame([request.features])
        proba = float(model.predict_proba(df)[0][1])
        prediction = int(proba >= 0.5)

        # 3. Log output — succès
        output_log = PredictionOutput(
            input_id=input_log.id,
            prediction=prediction,
            probabilite=round(proba, 4),
            statut="success"
        )
        db.add(output_log)
        db.commit()

        return {
            "prediction": prediction,
            "label": "Crédit refusé" if prediction == 1 else "Crédit accordé",
            "probabilite_defaut": round(proba, 4)
        }

    except Exception as e:
        # 3. Log output — erreur
        output_log = PredictionOutput(
            input_id=input_log.id,
            statut="error",
            error_code=type(e).__name__,
            error_message=str(e)[:255]
        )
        db.add(output_log)
        db.commit()
        raise

@app.post("/predict2")
def predict2(request: PredictRequest):
    missing = [f for f in EXPECTED_FEATURES if f not in request.features]
    if missing:
        raise HTTPException(status_code=422, detail=f"Features manquantes: {missing}")

    df = pd.DataFrame([request.features]).apply(pd.to_numeric, errors='coerce')
    proba = float(model.predict_proba(df)[0][1])
    prediction = int(proba >= 0.5)

    return {
        "prediction": prediction,
        "label": "Crédit refusé" if prediction == 1 else "Crédit accordé",
        "probabilite_defaut": round(proba, 4)
    }
