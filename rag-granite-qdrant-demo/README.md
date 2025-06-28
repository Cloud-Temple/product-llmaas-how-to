# Démonstrateur RAG avec Qdrant et l'API LLMaaS

Ce projet est un démonstrateur d'une architecture RAG (Retrieval-Augmented Generation) complète et conteneurisée.

L'architecture utilise l'API LLMaaS pour les deux étapes clés du processus RAG :
1.  **Embedding via LLMaaS** : L'API est utilisée pour générer les embeddings (vecteurs) des documents et des questions avec le modèle `granite-embedding:278m`.
2.  **Génération via LLMaaS** : L'API est également utilisée pour la génération de la réponse finale avec le modèle `granite3.3:8b`, en se basant sur le contexte fourni par la recherche vectorielle.
3.  **Base Vectorielle** : Qdrant est utilisé pour stocker les vecteurs et effectuer la recherche de similarité.

## Prérequis

- Docker et Docker Compose
- Un accès à l'API LLMaaS.

## Configuration

Avant de lancer, assurez-vous que le fichier `.env` est correctement configuré à partir du fichier `.env.example` :

- `QDRANT_URL`: Doit pointer vers le service Qdrant. La valeur par défaut `http://qdrant:6333` est correcte pour `docker-compose`.
- `LLMAAS_API_BASE`: L'URL de base de votre API LLMaaS (ex: `https://api.ai.cloud-temple.com/v1`).
- `LLMAAS_API_KEY`: Votre clé d'accès pour l'API LLMaaS.
- `EMBEDDING_MODEL_NAME`: Le nom du modèle d'embedding disponible sur l'API LLMaaS (ex: `granite-embedding:278m`).
- `LLM_MODEL_NAME`: Le nom du modèle de génération disponible sur l'API LLMaaS (ex: `granite3.3:8b`).

## Instructions d'exécution

### 1. Lancer l'application

Placez-vous à la racine de ce dossier (`exemples/rag-granite-qdrant-demo`) et exécutez la commande suivante :

```bash
docker-compose up --build
```

Cette commande va :
1.  **Construire l'image Docker** pour l'application Python (`rag-app`).
2.  **Démarrer les conteneurs** pour l'application et pour la base de données Qdrant.
3.  Le script `rag_demo.py` s'exécutera et affichera en détail chaque étape du processus RAG.

### 2. Arrêter l'application

Pour arrêter les services, appuyez sur `Ctrl+C` dans le terminal où `docker-compose` est en cours d'exécution, puis exécutez :

```bash
docker-compose down
