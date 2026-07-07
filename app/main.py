from contextlib import asynccontextmanager
import os

from httpcore import request
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from pathlib import Path
import json

#from app.database import engine, Base, get_db
#from app.models_db import PredictionInput, PredictionOutput
from app.__version__ import __version__

load_dotenv()
API_ENV = os.getenv("API_ENV", "local")

# ── Chargement du modèle ──────────────────────────────────────────────────────
MODEL_PATH = Path("models/home_credit_scoring_lgbm.joblib")
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
    # Vérification des features manquantes
    missing = [f for f in EXPECTED_FEATURES if f not in request.features]
    if missing:
        raise HTTPException(status_code=422, detail=f"Features manquantes: {missing}")

    # Boucle globale sur la request
    payload = request.features

    # Boucle globale sur les features
    for key, value in payload.items():
        # Règle 1 : Uniquement numérique ou booléen
        if not isinstance(value, (int, float, bool)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation Error: {key} must be numeric or boolean."
            )
        
        # Règle 2 : Les champs FLAG_ doivent être 0 ou 1
        if key.startswith("FLAG_") and value not in [0, 1, 0.0, 1.0]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation Error: {key} must be 0 or 1."
            )

    # Règle 3 : CODE_GENDER (0 ou 1)
    if "CODE_GENDER" in payload and payload["CODE_GENDER"] not in [0, 1, 0.0, 1.0]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: CODE_GENDER must be 0 or 1."
        )

    # Règle 4: CNT_CHILDREN positif ou nul
    if "CNT_CHILDREN" in payload and (not isinstance(payload["CNT_CHILDREN"], int) or payload["CNT_CHILDREN"] < 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: CNT_CHILDREN must be a positive integer."
        )

    # Règle 5 : AMT_INCOME_TOTAL positif
    if "AMT_INCOME_TOTAL" in payload and payload["AMT_INCOME_TOTAL"] < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation Error: AMT_INCOME_TOTAL must be positive."
        )

    # Création du DataFrame et conversion des types
    df = pd.DataFrame([request.features]).apply(pd.to_numeric, errors='coerce')
    
    # /!\ SÉCURITÉ : Forcer l'ordre exact des colonnes attendu par le LightGBM
    df = df[EXPECTED_FEATURES]

    # 3. Inférence
    try:
        proba = float(model.predict_proba(df)[0][1])
        prediction = int(proba >= 0.5)

        return {
            "prediction": prediction,
            "label": "Crédit refusé" if prediction == 1 else "Crédit accordé",
            "probabilite_defaut": round(proba, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'inférence: {str(e)}")

@app.get("/get_accord_sample")
def get_accord_sample():
    try:
        with open("tests/payloads/client_accord.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fichier client_accord.json introuvable")

@app.get("/get_refus_sample")
def get_refus_sample():
    try:
        with open("tests/payloads/client_refus.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fichier client_refus.json introuvable")