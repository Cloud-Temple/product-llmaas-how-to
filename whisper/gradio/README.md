# Scripts de Test pour la Transcription Audio

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

Ce répertoire contient divers scripts pour tester et interagir avec des services de transcription audio, y compris l'**API de transcription audio LLMaaS Cloud Temple**.

## Fichiers

- `gradio-cloud-temple.py`: Interface utilisateur basée sur Gradio pour interagir avec l'API de transcription audio de Cloud Temple. Permet l'authentification par token.
- `run_cloud_temple_interface.sh`: Script shell pour installer les dépendances nécessaires et lancer l'interface `gradio-cloud-temple.py`.
- `gradio-client.py`: Une interface utilisateur Gradio similaire, potentiellement une version antérieure ou générique, qui n'inclut pas la gestion de l'authentification par token et utilise une URL de serveur par défaut.
- `whisper-api.py`: Une implémentation locale d'une API de transcription audio utilisant la bibliothèque `whisper` d'OpenAI. Fournit des endpoints `/transcribe` et `/translate` via FastAPI.
- `vllm-whisper-api.py`: Un script de test de performance qui utilise vLLM pour charger le modèle Whisper "large-v3" et effectuer des transcriptions sur des exemples audio prédéfinis. Ce n'est pas une implémentation d'API.
- `qwen_audio_test.py`: Un script de test utilisant la bibliothèque `transformers` pour interagir avec le modèle multimodal "Qwen/Qwen2-Audio-7B-Instruct" pour des tâches liées à l'audio.
- `requirements-cloud-temple.txt`: Liste des dépendances Python requises pour exécuter `gradio-cloud-temple.py`.
- `requirements.txt`: Liste des dépendances Python requises pour exécuter les API locales (`whisper-api.py`, `vllm-whisper-api.py`) et potentiellement d'autres scripts.
- `test_audio.wav`: Un fichier audio de test.

## Utilisation de l'Interface Cloud Temple

L'interface `gradio-cloud-temple.py` permet de tester facilement l'API de transcription audio de Cloud Temple via une interface web interactive.

### Comment Tester l'API Cloud Temple

La manière la plus simple de commencer est d'utiliser le script shell `run_cloud_temple_interface.sh`. Ce script gère automatiquement l'installation des dépendances et le lancement de l'interface Gradio.

#### Prérequis

Assurez-vous d'avoir Python 3 installé sur votre système.

#### Lancement du Script de Test

Exécutez le script shell depuis le répertoire `scripts/test_whisper/` :

```bash
./run_cloud_temple_interface.sh
```

Ce script effectuera les actions suivantes :

1. Vérifier l'installation de Python 3.
2. Créer un environnement virtuel Python (`venv`) s'il n'existe pas.
3. Activer l'environnement virtuel.
4. Installer les dépendances requises listées dans `requirements-cloud-temple.txt`.
5. Lancer l'interface Gradio (`gradio-cloud-temple.py`).

L'interface web s'ouvrira automatiquement dans votre navigateur par défaut.

#### Utilisation de l'Interface Web

Une fois l'interface Gradio lancée :

1. **Entrez votre token d'authentification** pour l'API Cloud Temple dans le champ "Token d'authentification".
2. Cliquez sur le bouton **"Mettre à jour le token"**. Le statut du token s'affichera.
3. Cliquez sur le bouton du microphone dans la section "Entrée audio" pour **commencer l'enregistrement**.
4. **Parlez clairement** dans votre microphone.
5. La transcription de votre discours apparaîtra en temps réel dans la zone de texte "Texte transcrit".

Vous pouvez également utiliser le fichier `test_audio.wav` pour tester la transcription sans utiliser le microphone.

#### Fonctionnalités de l'Interface Cloud Temple

- **Authentification configurable** : Entrez votre token d'API dans l'interface.
- **Transcription en temps réel** : Parlez dans votre microphone et voyez la transcription s'afficher.
- **Optimisé pour le français** : L'API est configurée par défaut pour la langue française.
- **Interface utilisateur intuitive** : Design simple et instructions claires.

#### Exemple d'utilisation (via l'interface web)

1. Lancez l'interface en suivant les étapes ci-dessus.
2. Dans l'interface web qui s'ouvre, entrez votre token d'authentification.
3. Cliquez sur "Mettre à jour le token".
4. Cliquez sur le bouton du microphone pour commencer l'enregistrement.
5. Parlez clairement dans votre microphone.
6. La transcription apparaîtra automatiquement dans la zone de texte.

## API Locales et Autres Scripts de Test

Ce répertoire contient également des scripts pour exécuter des API de transcription audio localement ou tester d'autres modèles :

- `whisper-api.py`: Une implémentation locale d'une API de transcription audio utilisant la bibliothèque `whisper` d'OpenAI. Fournit des endpoints `/transcribe` et `/translate` via FastAPI. Vous pouvez l'exécuter avec `uvicorn whisper-api:app --reload` ou `gunicorn --timeout 60 -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000 whisper-api:app`.
- `vllm-whisper-api.py`: Un script de test de performance qui utilise vLLM pour charger le modèle Whisper "large-v3" et effectuer des transcriptions sur des exemples audio prédéfinis. Ce n'est pas une implémentation d'API à proprement parler.
- `qwen_audio_test.py`: Script spécifique utilisant la bibliothèque `transformers` pour interagir avec le modèle multimodal "Qwen/Qwen2-Audio-7B-Instruct" pour des tâches liées à l'audio.

Pour exécuter ces scripts, vous devrez peut-être installer les dépendances listées dans `requirements.txt`.

## Dépannage

- **Erreur d'authentification** : Vérifiez que votre token est valide et correctement saisi dans l'interface Cloud Temple.
- **Problèmes de connexion** : Assurez-vous que l'URL de l'API Cloud Temple (`https://api.ai.cloud-temple.com/v1/audio/transcriptions`) est accessible depuis votre réseau. Pour les API locales, assurez-vous que le serveur est correctement lancé et accessible.
- **Qualité de transcription** : Pour de meilleurs résultats, parlez clairement et dans un environnement calme.

## Personnalisation (Interface Cloud Temple)

Vous pouvez modifier le script `gradio-cloud-temple.py` pour ajuster :

- L'URL de l'API (`server_url` dans la classe `AudioProcessor`).
- La langue de transcription (paramètre `language` dans `process_audio_chunk`).
- Les paramètres de traitement audio (taux d'échantillonnage, format, etc.).

## Comparaison des Scripts d'Interface/API

- `gradio-cloud-temple.py` : Utilise l'API Cloud Temple avec authentification par token.
- `gradio-client.py` : Version originale utilisant une autre API.
- `whisper-api.py` : API locale utilisant le modèle Whisper standard.
- `vllm-whisper-api.py` : Script de test de performance pour Whisper avec vLLM.

## Notes techniques (Interface Cloud Temple)

- Le script `gradio-cloud-temple.py` utilise la bibliothèque Gradio pour l'interface utilisateur.
- Les chunks audio sont traités et envoyés à l'API via des requêtes HTTP.
- L'historique des transcriptions est géré pour améliorer l'expérience utilisateur.
