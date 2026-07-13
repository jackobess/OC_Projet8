---
title: OC Projet 8
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# OC Projet 8 - Déploiement et monitoring d'un modèle de scoring crédit

API de scoring crédit déployée sur Hugging Face Spaces, avec monitoring/data drift et pipeline CI/CD GitHub Actions.

---

## Stack technique

| Composant | Technologie |
|---|---|
| API | FastAPI + Pydantic |
| Modèle | LightGBM (P6 MLOps 1/2) |
| BDD | PostgreSQL + SQLAlchemy |
| BDD cloud | Neon (PostgreSQL serverless) |
| Monitoring | Evidently AI / NannyML |
| Dashboard | Streamlit |
| Tests | Pytest + pytest-cov |
| CI/CD | GitHub Actions |
| Déploiement | Hugging Face Spaces (Docker) |

---

## Architecture

*à compléter*

---

## Installation

```bash
git clone https://github.com/jackobess/OC_Projet8.git
cd OC_Projet8
pip install -r requirements.txt
```

---

## Configuration locale

Créer un fichier `.env` à la racine :

```env
DATABASE_URL=postgresql://neondb_owner....   #acces Neon/database
API_ENV=local
PYTHONPATH=.
```

---

## Lancement local

```bash
conda activate nom_env
uvicorn app.main:app --reload
```

API : `http://127.0.0.1:8000`  
Swagger : `http://127.0.0.1:8000/docs`

---

## API - Endpoints

### `GET /`
```json
{"message": "API opérationnelle"}
```

### `GET /health`
```json
{"status": "ok", "version": "0.0.0", "environment": "local"}
```

### `POST /predict`
 
Prend en entrée l'ensemble des features attendues par le modèle LightGBM (~700 features post-OHE, cf `model.feature_name_`).
 
**Request body:**
```json
{
  "features": {
    "CODE_GENDER": 0,
    "CNT_CHILDREN": 2,
    "AMT_INCOME_TOTAL": 202500.0,
    "FLAG_OWN_CAR": 1,
    "...": "..."
  }
}
```
 
**Response (succès):**
```json
{
  "prediction": 0,
  "label": "Crédit accordé",
  "probabilite_defaut": 0.1234
}
```
 
**Validations appliquées:**
- Toutes les features attendues par le modèle doivent être présentes (`422` sinon)
- Valeurs uniquement numériques ou booléennes (`400` sinon)
- Champs `FLAG_*` : doivent valoir 0 ou 1
- `CODE_GENDER` : doit valoir 0 ou 1
- `CNT_CHILDREN` : entier positif ou nul
- `AMT_INCOME_TOTAL` : doit être positif
**Logging:** chaque appel (succès ou erreur) est loggué en base PostgreSQL (Neon) : features en entrée, prédiction/probabilité, latence, statut. Utilisé pour l'analyse de data drift (cf étape 3).
 
### `GET /get_accord_sample` / `GET /get_refus_sample`
Retourne un exemple de payload JSON prêt à l'emploi (crédit accordé / refusé) pour tester `/predict`.

---

## Monitoring & Data Drift

[Voir le rapport de drift html](docs/drift_report.html)  

![Drift Report](docs/drift_report.jpg)

---

## Base de données

### Tables de logging  (voir app/models_db.py)

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

---

## Tests

```bash
PYTHONPATH=. 
CI=true 
pytest tests/ -v --cov=app --cov-report=html
```
---

## Hugging Face Spaces

🔗 **API en production** : [https://jackobess-oc-projet8.hf.space](https://jackobess-oc-projet8.hf.space)

📄 Documentation interactive (Swagger) : [https://jackobess-oc-projetslip.hf.space/docs](https://jackobess-oc-projet8.hf.space/docs)

> ⚠️ L'accès à l'API nécessite une clé (`x-api-key` dans les headers). Contactez-moi pour obtenir une clé de test si besoin

---

## Sécurité

- Credentials via variables d'environnement uniquement
- `.env` dans `.gitignore`
- Aucun credential en dur dans le code

---

## Conventions

- Branches : `feature/xxx`, `fix/xxx`, `test/xxx`
- Commits : `feat:`, `fix:`, `docs:`, `ci:`, `chore:`
- Versions : `app/__version__.py` + tags Git

---

## 🚀 Intégration & Déploiement Continus (CI/CD)

Ce projet utilise **GitHub Actions** pour valider le code et automatiser le déploiement sur Hugging Face Spaces (Docker). 

Le pipeline se déclenche automatiquement à chaque `git push`. Vous pouvez contrôler finement son comportement depuis votre terminal grâce aux balises de commit :

| Commande de Commit | Action du Pipeline | Environnement Cible |
| :--- | :--- | :--- |
| `git commit -m "mon message"` | **La totale** : Exécute les 7 tests pytest ➡️ Si OK, build l'image et déploie. | GitHub + Hugging Face |
| `git commit -m "mon message [skip deploy]"` | **Tests uniquement** : Valide le code sans mettre à jour l'API en production. | GitHub Actions uniquement |
| `git commit -m "mon message [skip ci]"` | **Ignorer le pipeline** : Pour les modifications mineures (documentation, typos). | Aucun (Pipeline bypassé) |

_Note : Le déploiement s'appuie sur le secret de dépôt `HF_TOKEN` configuré sur GitHub._

## Run local avec Docker

Build the image:
\`\`\`bash
docker build -t p8-api .
\`\`\`

Run the container:
\`\`\`bash
docker run -p 7860:7860 p8-api
\`\`\`

API docs available at `http://127.0.0.1:7860/docs`
