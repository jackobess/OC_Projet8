"""
test_api.py — Tests fonctionnels des endpoints FastAPI.
"""

import pytest


class TestEndpointsBase:

    def test_root_status_200(self, client):
        """GET / retourne 200."""
        r = client.get("/")
        assert r.status_code == 200

    def test_root_message(self, client):
        """GET / retourne un message d'état."""
        r = client.get("/")
        assert "message" in r.json()

    def test_health_status_200(self, client):
        """GET /health retourne 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_contient_version(self, client):
        """GET /health retourne la version de l'API."""
        r = client.get("/health")
        assert "version" in r.json()

    def test_health_contient_environment(self, client):
        """GET /health retourne l'environnement."""
        r = client.get("/health")
        assert "environment" in r.json()


class TestPredictFormat:

    def test_predict_status_200(self, client, profil_stable):
        """POST /predict retourne 200 avec un profil valide."""
        r = client.post("/predict", json=profil_stable)
        assert r.status_code == 200

    def test_predict_contient_prediction(self, client, profil_stable):
        """La réponse contient le champ 'prediction'."""
        r = client.post("/predict", json=profil_stable)
        assert "prediction" in r.json()

    def test_predict_contient_label(self, client, profil_stable):
        """La réponse contient le champ 'label'."""
        r = client.post("/predict", json=profil_stable)
        assert "label" in r.json()

    def test_predict_contient_probabilite(self, client, profil_stable):
        """La réponse contient le champ 'probabilite_attrition'."""
        r = client.post("/predict", json=profil_stable)
        assert "probabilite_attrition" in r.json()

    def test_predict_prediction_binaire(self, client, profil_stable):
        """La prédiction est 0 ou 1."""
        r = client.post("/predict", json=profil_stable)
        assert r.json()["prediction"] in [0, 1]

    def test_predict_probabilite_entre_0_et_1(self, client, profil_stable):
        """La probabilité est comprise entre 0 et 1."""
        r = client.post("/predict", json=profil_stable)
        proba = r.json()["probabilite_attrition"]
        assert 0.0 <= proba <= 1.0


class TestPredictCasReels:

    def test_profil_a_risque(self, client, profil_a_risque):
        """Profil réel ayant quitté → prédiction cohérente (retourne 0 ou 1)."""
        r = client.post("/predict", json=profil_a_risque)
        assert r.status_code == 200
        assert r.json()["prediction"] in [0, 1]

    def test_profil_stable(self, client, profil_stable):
        """Profil réel encore en poste → prédiction cohérente (retourne 0 ou 1)."""
        r = client.post("/predict", json=profil_stable)
        assert r.status_code == 200
        assert r.json()["prediction"] in [0, 1]

    def test_label_coherent_avec_prediction(self, client, profil_stable):
        """Le label est cohérent avec la prédiction."""
        r = client.post("/predict", json=profil_stable)
        data = r.json()
        if data["prediction"] == 1:
            assert data["label"] == "A risque de quitter"
        else:
            assert data["label"] == "Devrait rester"


class TestPredictValidation:

    def test_genre_invalide_retourne_422(self, client, profil_stable):                          # Genre invalide => 422
        payload = {**profil_stable, "genre": "X"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_frequence_deplacement_invalide_retourne_422(self, client, profil_stable):          # Freq. Déplacement invalide => 422
        payload = {**profil_stable, "frequence_deplacement": "Rare"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_heure_supp_invalide_retourne_422(self, client, profil_stable):                     # Heures supp. invalides => 422
        payload = {**profil_stable, "heure_supplementaires": 22}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422
 
    def test_statut_marital_invalide_retourne_422(self, client, profil_stable):                 # Statut marital invalide => 422
        payload = {**profil_stable, "statut_marital": "C'est compliqué"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422
        
    def test_satisfaction_hors_plage_retourne_422(self, client, profil_stable):                 # Satisfaction hors plage [1-4] => 422
        payload = {**profil_stable, "satisfaction_employee_equipe": 9}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_niveau_education_hors_plage_retourne_422(self, client, profil_stable):             # Niveau d'éducation hors plage [1-5] => 422
        payload = {**profil_stable, "niveau_education": 0}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_niveau_hierarchique_hors_plage_retourne_422(self, client, profil_stable):          # Niveau hierarchique hors plage [1-5] => 422
        payload = {**profil_stable, "niveau_hierarchique_poste": 10}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_poste_invalide_retourne_422(self, client, profil_stable):                          # Poste invalide => 422
        payload = {**profil_stable, "poste": "Astronaute"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

    def test_domaine_etude_invalide_retourne_422(self, client, profil_stable):                  # Domaine d'étude invalide => 422
        payload = {**profil_stable, "domaine_etude": "Data Science"}
        r = client.post("/predict", json=payload)
        assert r.status_code == 422

#    def test_body_vide_retourne_422(self, client):
#        """Un body vide retourne 422."""
#        r = client.post("/predict", json={})
#        assert r.status_code == 422

    def test_not_json_retourne_422(self, client):                                               # Body non JSON => 422
        """Un body non json retourne 422."""
        r = client.post("/predict", content="plop")
        assert r.status_code == 422
