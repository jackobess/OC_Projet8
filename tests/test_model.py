"""
test_model.py — Tests unitaires sur les composants du modèle ML.
"""

import pytest
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_PATH = Path("models/pipeline_p4.joblib")

@pytest.fixture(scope="module")
def pipeline():
    return joblib.load(MODEL_PATH)

class TestPipelineChargement:

    def test_pipeline_charge(self, pipeline):
        """Le pipeline se charge sans erreur."""
        assert pipeline is not None

    def test_pipeline_a_predict(self, pipeline):
        """Le pipeline expose une méthode predict."""
        assert hasattr(pipeline, 'predict')

    def test_pipeline_a_predict_proba(self, pipeline):
        """Le pipeline expose une méthode predict_proba."""
        assert hasattr(pipeline, 'predict_proba')

class TestPrediction:

    def test_predict_retourne_0_ou_1(self, pipeline, sample_input):
        """La prédiction est binaire : 0 ou 1."""
        result = pipeline.predict(sample_input)
        assert result[0] in [0, 1]

    def test_predict_proba_shape(self, pipeline, sample_input):
        """predict_proba retourne 2 probabilités par observation."""
        proba = pipeline.predict_proba(sample_input)
        assert proba.shape == (1, 2)

    def test_predict_proba_somme_1(self, pipeline, sample_input):
        """Les probabilités somment à 1."""
        proba = pipeline.predict_proba(sample_input)
        assert abs(proba[0].sum() - 1.0) < 1e-6

    def test_predict_proba_entre_0_et_1(self, pipeline, sample_input):
        """Chaque probabilité est comprise entre 0 et 1."""
        proba = pipeline.predict_proba(sample_input)
        assert all(0.0 <= p <= 1.0 for p in proba[0])


class TestFeatureEncoder:

    def test_pipeline_accepte_dataframe(self, pipeline, sample_input):
        """Le pipeline accepte un DataFrame pandas en entrée."""
        try:
            pipeline.predict(sample_input)
        except Exception as e:
            pytest.fail(f"Le pipeline a rejeté le DataFrame : {e}")

    def test_pipeline_colonnes_manquantes_leve_erreur(self, pipeline):
        """Un DataFrame incomplet lève une erreur."""
        df_incomplet = pd.DataFrame([{"age": 35, "genre": "M"}])
        with pytest.raises(Exception):
            pipeline.predict(df_incomplet)
