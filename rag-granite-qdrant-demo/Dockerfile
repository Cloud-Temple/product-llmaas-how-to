# Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers de l'application
COPY . .

# Commande pour exécuter l'application
# Le script attendra que Qdrant soit disponible avant de se lancer.
CMD ["python", "rag_demo.py"]
