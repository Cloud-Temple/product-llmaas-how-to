# Dockerfile pour le Serveur MCP
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY mcp_server.py .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port du serveur
EXPOSE 8000

# Commande de démarrage par défaut
# Note : On utilise l'hôte 0.0.0.0 pour être accessible hors du conteneur
ENTRYPOINT ["python", "mcp_server.py"]
CMD ["--port", "8000"]
