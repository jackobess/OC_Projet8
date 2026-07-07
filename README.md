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
DATABASE_URL=postgresql://user:password@localhost:5432/oc_projet8
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
*à compléter selon les features du modèle scoring P6*

---

## Monitoring & Data Drift

*à compléter (Evidently / NannyML)*

---

## Base de données

### Tables de logging
| Table | Description |
|---|---|
| `prediction_inputs` | Features envoyées au modèle |
| `prediction_outputs` | Score + statut + erreurs (FK → inputs) |

---

## Tests

```bash
PYTHONPATH=. CI=true pytest tests/ -v --cov=app --cov-report=html
```

---

## CI/CD

À chaque push sur `main` ou `feature/**` :
1. **Test** — pytest + pytest-cov
2. **Deploy** — push automatique vers Hugging Face Spaces  
*inclure `[skip-deploy]` pour pusher sans déployer*

---

## Hugging Face Spaces

*à compléter après déploiement*

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