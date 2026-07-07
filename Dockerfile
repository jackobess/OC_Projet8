FROM python:3.10-slim

# 1. Installation de libgomp1 en mode root (système)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Création et bascule sur l'utilisateur non-privilégié pour Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# 3. Installation des dépendances Python
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 4. Copie du reste du code
COPY --chown=user . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
