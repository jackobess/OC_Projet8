from contextlib import asynccontextmanager
import os

from httpcore import request
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from pathlib import Path
import json
import time
import cProfile
import pstats
import io

from app.database import engine, Base, get_db
from app.models_db import PredictionLog
from app.__version__ import __version__

load_dotenv()
API_ENV = os.getenv("API_ENV", "not sure")
API_KEY = os.getenv("API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide")

# ── Chargement du modèle ──────────────────────────────────────────────────────
MODEL_PATH = Path("models/home_credit_scoring_lgbm.joblib")
model = joblib.load(MODEL_PATH)
EXPECTED_FEATURES = model.feature_name_

# ── Création des tables au démarrage ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("CI") != "true":
       Base.metadata.create_all(bind=engine)
    yield

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="OC Projet 8 - Scoring Crédit API (API_ENV: " + API_ENV + ")",
    description="API de scoring crédit/ Home Credit (Projet n°8 - OpenClassrooms)",
    version=__version__,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)]    
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

def _log_prediction(db: Session, payload: dict, start_time: float,
                     prediction=None, probabilite=None,
                     statut="success", error_code=None, error_message=None):
    """Écrit une ligne de log en DB, sans jamais faire planter la requête si la DB est down."""
    latence_ms = round((time.perf_counter() - start_time) * 1000, 2)
    try:
        log_entry = PredictionLog(
            source=API_ENV,
            input_features=payload,
            prediction=prediction,
            probabilite=probabilite,
            latence_ms=latence_ms,
            statut=statut,
            error_code=error_code,
            error_message=error_message[:255] if error_message else None,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"[DB LOG FAILED] {e}")
        # Le logging ne doit jamais empêcher l'API de répondre
        db.rollback()

@app.post("/predict")
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    start_time = time.perf_counter()
    payload = request.features

    try:
        # Vérification des features manquantes
        missing = [f for f in EXPECTED_FEATURES if f not in payload]
        if missing:
            raise HTTPException(status_code=422, detail=f"Features manquantes: {missing}")

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

        # Création du DataFrame
        df = pd.DataFrame([payload])   #.apply(pd.to_numeric, errors='coerce')

        # /!\ SÉCURITÉ : Forcer l'ordre exact des colonnes attendu par le LightGBM
        df = df[EXPECTED_FEATURES]

        # Inférence
        proba = float(model.predict_proba(df)[0][1])
        prediction = int(proba >= 0.5)

        _log_prediction(db, payload, start_time, prediction=prediction,
                         probabilite=round(proba, 4), statut="success")

        return {
            "prediction": prediction,
            "label": "Crédit refusé" if prediction == 1 else "Crédit accordé",
            "probabilite_defaut": round(proba, 4)
        }

    except HTTPException as http_exc:
        _log_prediction(db, payload, start_time, statut="error",
                         error_code=f"HTTP_{http_exc.status_code}",
                         error_message=str(http_exc.detail))
        raise
    except Exception as e:
        _log_prediction(db, payload, start_time, statut="error",
                         error_code=type(e).__name__, error_message=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur d'inférence: {str(e)}")


if API_ENV == "local":      # ── Endpoint de profiling (LOCAL UNIQUEMENT) ──  Etape 4
    @app.post("/predictcprof")
    def predict_profiled(request: PredictRequest, db: Session = Depends(get_db)):
        profiler = cProfile.Profile()
        profiler.enable()

        result = predict(request, db)

        profiler.disable()

        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(25)
        profiler.dump_stats("predict_profile.prof")
        return {"result": result, "profile": s.getvalue().replace(r"C:\Users\jacob", "...").splitlines()}

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
    