# Exemple d'API Vision

Ce répertoire contient un exemple simple montrant comment utiliser les capacités de vision (multimodales) de l'API LLMaaS.

## Fonctionnement

Le script `test_vision.py` :
1.  Génère une image d'exemple (`image_example.png`) s'il n'en existe pas.
2.  Encode cette image en base64.
3.  Construit une requête au format multimodal OpenAI, en incluant un prompt textuel et l'image encodée.
4.  Envoie la requête à l'endpoint `/v1/chat/completions`.
5.  Affiche la description de l'image générée par le modèle.

## Prérequis

- Python 3.8+
- Les dépendances listées dans `requirements.txt`.

## Installation

1.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

2.  Configurez vos identifiants :
    -   Copiez `.env.example` vers un nouveau fichier nommé `.env`.
    -   Modifiez le fichier `.env` et ajoutez votre `API_KEY` et l'URL de l'API si elle est différente de celle par défaut.

    ```dotenv
    # .env
    API_URL="https://api.ai.cloud-temple.com/v1"
    API_KEY="VOTRE_TOKEN_BEARER_ICI"
    DEFAULT_MODEL="granite3.2-vision:2b"
    ```

## Utilisation

### Exécution simple

Pour lancer le test en mode standard (non-streaming) :
```bash
python3 test_vision.py
```

### Exécution en Streaming

Pour tester la réponse en streaming, utilisez l'option `--stream` :
```bash
python3 test_vision.py --stream
