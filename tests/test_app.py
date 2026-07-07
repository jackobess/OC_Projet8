import pytest
from fastapi.testclient import TestClient
from app.main import app

# Initialisation du client de test FastAPI
client = TestClient(app)

def test_health_check():
    """Vérifie que l'API est fonctionnelle au démarrage."""
    response = client.get("/")
    assert response.status_code == 200
    assert "API opérationnelle" in response.json().get("message", "")


def test_predict_accord():
    """Vérifie qu'un profil 'accord' renvoie bien un statut 200 et la bonne décision."""
    # 1. Récupération du payload d'accord via ton endpoint
    sample_res = client.get("/get_accord_sample")
    assert sample_res.status_code == 200
    payload = sample_res.json()

    # 2. Envoi au modèle pour prédiction
    response = client.post("/predict2", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "prediction" in data
    assert data["prediction"] == 0  # Vérifie que c'est bien l'entier attendu pour l'accord

def test_predict_refus():
    """Vérifie qu'un profil 'refus' renvoie bien un statut 200 et le rejet."""
    # 1. Récupération du payload de refus
    sample_res = client.get("/get_refus_sample")
    assert sample_res.status_code == 200
    payload = sample_res.json()

    # 2. Envoi au modèle
    response = client.post("/predict2", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "prediction" in data
    assert data["prediction"] == 1  # Vérifie que c'est bien l'entier attendu pour le refus

def test_predict_invalid_request():
    """Vérifie qu'un payload vide ou mal formé renvoie une erreur 422 (FastAPI/Pydantic validation)."""
    # Envoi d'un dictionnaire vide
    response = client.post("/predict2", json={})
    assert response.status_code == 422


def test_predict_with_extra_columns():
    """Vérifie que l'API ignore proprement les colonnes bonus et ne plante pas."""
    sample_res = client.get("/get_accord_sample")
    payload = sample_res.json()

    # Ajout d'une colonne sauvage non attendue par le modèle ou Pydantic
    payload["COLONNE_INUTILE_TEST"] = 999.9

    response = client.post("/predict2", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()

def test_predict_missing_features_rejected():
    """Vérifie que l'API rejette avec une erreur 422 si des variables obligatoires manquent."""
    # 1. On récupère un payload valide
    sample_res = client.get("/get_accord_sample")
    features_internes = sample_res.json()["features"]

    # 2. On supprime une colonne obligatoire (ex: AMT_CREDIT)
    p_missing = {"features": features_internes.copy()}
    if "AMT_CREDIT" in p_missing["features"]:
        del p_missing["features"]["AMT_CREDIT"]

    # 3. Envoi et assertion
    response = client.post("/predict2", json=p_missing)
    assert response.status_code == 422
    assert "Features manquantes" in response.json()["detail"]
    
def test_predict_business_rules_rejected():
    """Vérifie que l'API rejette les violations de types (422) et de règles métiers (400)."""
    sample_res = client.get("/get_accord_sample")
    payload_valide = sample_res.json()
    
    # On extrait le vrai dictionnaire des variables
    features_internes = payload_valide["features"]

    # Règle 1 : Test type String (Bloqué par notre API -> 400)
    p_bad_type = {"features": features_internes.copy()}
    p_bad_type["features"]["AMT_CREDIT"] = "string_interdite"
    response = client.post("/predict2", json=p_bad_type)
    assert response.status_code == 400 
    assert "must be numeric or boolean" in response.json()["detail"]

    # Règle 2 : Test FLAG_ incorrect (On trouve un FLAG_ dynamiquement)
    p_bad_flag = {"features": features_internes.copy()}
    flag_col = [k for k in features_internes.keys() if k.startswith("FLAG_")][0]
    p_bad_flag["features"][flag_col] = 99
    response = client.post("/predict2", json=p_bad_flag)
    assert response.status_code == 400
    assert "must be 0 or 1" in response.json()["detail"]

    # Règle 3 : Test CODE_GENDER hors limites (400)
    if "CODE_GENDER" in features_internes:
        p_bad_gender = {"features": features_internes.copy()}
        p_bad_gender["features"]["CODE_GENDER"] = 5
        response = client.post("/predict2", json=p_bad_gender)
        assert response.status_code == 400
        assert "CODE_GENDER must be 0 or 1" in response.json()["detail"]

    # Règle 4 : Test CNT_CHILDREN négatif (400)
    if "CNT_CHILDREN" in features_internes:
        p_bad_children = {"features": features_internes.copy()}
        p_bad_children["features"]["CNT_CHILDREN"] = -1
        response = client.post("/predict2", json=p_bad_children)
        assert response.status_code == 400
        assert "CNT_CHILDREN must be a positive integer" in response.json()["detail"]

    # Règle 5 : Test AMT_INCOME_TOTAL négatif (400)
    if "AMT_INCOME_TOTAL" in features_internes:
        p_bad_income = {"features": features_internes.copy()}
        p_bad_income["features"]["AMT_INCOME_TOTAL"] = -5000
        response = client.post("/predict2", json=p_bad_income)
        assert response.status_code == 400
        assert "AMT_INCOME_TOTAL must be positive" in response.json()["detail"]
