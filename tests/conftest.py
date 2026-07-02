"""
conftest.py — Fixtures partagées entre tous les tests.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


def override_get_db():
    """Mock de la session BDD — ne se connecte pas à Postgres."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    yield db


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def profil_a_risque():
    """Employé réel ayant quitté l'entreprise (id=1, a_quitte=1)."""
    return {
        "age": 41, "genre": "F", "niveau_education": 2,
        "statut_marital": "Célibataire", "poste": "Cadre Commercial",
        "domaine_etude": "Infra & Cloud", "frequence_deplacement": "Occasionnel",
        "distance_domicile_travail": 1, "nb_formations_suivies": 0,
        "nombre_participation_pee": 0, "augmentation_salaire_prec_pct": 11,
        "heure_supplementaires": 1, "note_evaluation_actuelle": 3,
        "satisfaction_employee_equilibre_pro_perso": 1,
        "satisfaction_employee_equipe": 1,
        "satisfaction_employee_nature_travail": 4,
        "niveau_hierarchique_poste": 2, "note_evaluation_precedente": 3,
        "satisfaction_employee_environnement": 2,
        "annee_experience_totale": 8, "nombre_experiences_precedentes": 8,
        "revenu_mensuel": 5993, "annees_dans_le_poste_actuel": 4,
        "annees_dans_l_entreprise": 6,
        "annees_depuis_la_derniere_promotion": 0,
        "annes_sous_responsable_actuel": 5,
    }


@pytest.fixture
def profil_stable():
    """Employé réel encore en poste (id=2, a_quitte=0)."""
    return {
        "age": 49, "genre": "M", "niveau_education": 1,
        "statut_marital": "Marié(e)", "poste": "Assistant de Direction",
        "domaine_etude": "Infra & Cloud", "frequence_deplacement": "Frequent",
        "distance_domicile_travail": 8, "nb_formations_suivies": 3,
        "nombre_participation_pee": 1, "augmentation_salaire_prec_pct": 23,
        "heure_supplementaires": 0, "note_evaluation_actuelle": 4,
        "satisfaction_employee_equilibre_pro_perso": 3,
        "satisfaction_employee_equipe": 4,
        "satisfaction_employee_nature_travail": 2,
        "niveau_hierarchique_poste": 2, "note_evaluation_precedente": 2,
        "satisfaction_employee_environnement": 3,
        "annee_experience_totale": 10, "nombre_experiences_precedentes": 1,
        "revenu_mensuel": 5130, "annees_dans_le_poste_actuel": 7,
        "annees_dans_l_entreprise": 10,
        "annees_depuis_la_derniere_promotion": 1,
        "annes_sous_responsable_actuel": 7,
    }

@pytest.fixture
def sample_input(profil_stable):
    return pd.DataFrame([profil_stable])
