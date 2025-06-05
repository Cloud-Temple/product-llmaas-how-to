# Transkryptor Python CLI - Exemple Avancé de Transcription Audio

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

Ce script Python, `transkryptor.py`, est un outil en ligne de commande avancé conçu pour transcrire des fichiers audio, même très volumineux, en utilisant l'**API de transcription LLMaaS Cloud Temple** (compatible Whisper). Il implémente une logique de découpage intelligent des fichiers audio en morceaux (chunks) avec chevauchement, traite ces morceaux par lots parallèles pour optimiser la vitesse, et offre une interface utilisateur soignée avec des modes de débogage et silencieux.

## ✨ Fonctionnalités Principales

-   **🎤 Support des Gros Fichiers Audio**: Conçu pour transcrire des fichiers audio de longue durée sans être limité par la taille maximale des requêtes API.
-   **🧩 Découpage Intelligent (Chunking)**: Divise l'audio en morceaux (chunks) avec une durée et un chevauchement configurables pour assurer une transcription continue et précise.
-   **⚡ Traitement Parallèle par Lots**: Envoie plusieurs chunks simultanément à l'API pour accélérer le processus de transcription global.
-   **📝 Écriture en Temps Réel**: **NOUVELLE FONCTIONNALITÉ** - Écrit la transcription au fur et à mesure dans le fichier de sortie, permettant de voir les résultats progressivement sans attendre la fin complète.
-   **🖥️ Prévisualisation Temps Réel**: **NOUVELLE FONCTIONNALITÉ** - Option `--preview` qui affiche la transcription en temps réel directement dans le terminal avec une interface organisée, barre de progression visuelle et statut en direct.
-   **🎨 Interface Utilisateur Soignée**: Utilise la bibliothèque `rich` pour un affichage clair et coloré, incluant :
    -   Barres de progression pour le traitement global et par lot.
    -   Logs informatifs et bien formatés.
-   **🐛 Mode Debug (`--debug`)**: Affiche des informations détaillées sur chaque étape du processus, y compris les métadonnées des chunks, les paramètres des requêtes API (sans la clé), et les réponses de l'API.
-   **🔇 Mode Silent (`--silent`)**:
    -   Supprime tous les affichages de progression et les logs informatifs.
    -   Affiche la transcription de chaque lot sur `stdout` dès qu'il est complété.
    -   Idéal pour rediriger la sortie vers un fichier ou pour une utilisation dans des pipelines de scripts.
-   **⚙️ Configuration Flexible**: Paramètres configurables via un fichier `config.json` et/ou des arguments de ligne de commande (API URL, clé API, langue, prompt, paramètres de chunking, taille de lot).
-   **📝 Gestion des Prompts**: Permet de fournir un prompt initial pour guider le modèle Whisper et améliorer la pertinence de la transcription pour des contextes spécifiques.
-   **🗣️ Support Multilingue**: Spécifiez la langue de l'audio pour une meilleure précision.
-   **📄 Sortie Verbatim**: Génère une transcription complète du fichier audio.

## 🆕 Nouvelles Fonctionnalités

### 📝 Écriture en Temps Réel
Le script écrit maintenant la transcription directement dans le fichier de sortie au fur et à mesure que chaque chunk est transcrit, au lieu d'attendre la fin complète. Cela permet :
- De voir les résultats progressivement
- De récupérer une transcription partielle même si le processus est interrompu
- Une meilleure utilisation de la mémoire pour les très gros fichiers

### 🖥️ Mode Prévisualisation (`--preview`)
Une nouvelle option `--preview` affiche la transcription en temps réel directement dans le terminal avec une interface moderne :
- **Transcription en temps réel** : Le texte apparaît au fur et à mesure dans le terminal
- **Barre de progression visuelle** : Avancement graphique avec pourcentage et nombre de chunks
- **Interface organisée** : Panneaux séparés pour l'en-tête, la progression, la transcription et les instructions
- **Statut en direct** : Informations sur l'état de la transcription
- **Affichage optimisé** : Troncature automatique pour les très longs textes
- **Compatible terminal** : Fonctionne dans n'importe quel terminal moderne

**Note** : L'option `--preview` utilise Rich (déjà inclus dans les dépendances) et ne nécessite aucune installation supplémentaire.

## 📁 Structure du Répertoire

```
exemples/transkryptor/
├── transkryptor.py         # Script principal
├── audio_utils.py          # Utilitaires pour la manipulation audio
├── api_utils.py            # Utilitaires pour les appels API
├── cli_ui.py               # Utilitaires pour l'interface CLI (couleurs, etc.)
├── requirements.txt        # Dépendances Python
├── config.json             # Votre fichier de configuration (créé à partir de l'exemple)
├── config.example.json     # Modèle pour le fichier de configuration
└── README.md               # Ce fichier
```

## 🚀 Prérequis

-   Python 3.8+
-   **`ffmpeg`**: Pour que `pydub` puisse traiter une large gamme de formats audio (comme MP3, M4A, etc.), `ffmpeg` doit être installé sur votre système et accessible dans le PATH.
    -   Sur macOS: `brew install ffmpeg`
    -   Sur Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`
    -   Sur Windows: Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html) et ajoutez au PATH.
-   Les bibliothèques Python listées dans `requirements.txt` (seront installées à l'étape suivante).
-   Un accès à l'API de transcription LLMaaS et une clé API valide.

## ⚙️ Installation et Configuration

1.  **Clonez le dépôt** (si ce n'est pas déjà fait) et naviguez vers le répertoire `exemples/transkryptor/`.

2.  **Créez un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv venv_transkryptor
    source venv_transkryptor/bin/activate  # Sur macOS/Linux
    # .\venv_transkryptor\Scripts\activate  # Sur Windows
    ```

3.  **Installez les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
    Cela installera `httpx`, `pydub`, `rich`, `python-dotenv`, `soundfile`, et `numpy`.

4.  **Configurez l'application** :
    *   Copiez `config.example.json` vers `config.json`.
        ```bash
        cp config.example.json config.json
        ```
    *   Modifiez `config.json` pour y ajouter votre clé API LLMaaS (`api_token`) et ajustez les autres paramètres si nécessaire :
        ```json
        {
          "api_url": "https://api.ai.cloud-temple.com/v1/audio/transcriptions",
          "api_token": "VOTRE_VRAIE_CLE_API_LLMAAS_ICI",
          "default_language": "fr",
          "default_prompt": "Ceci est une transcription concernant...",
          "chunk_duration_ms": 30000,
          "chunk_overlap_ms": 2000,
          "batch_size": 1,
          "sample_rate_hz": 24000,
          "output_directory": "./transkryptor_outputs"
        }
        ```
    *   Alternativement, vous pouvez passer la clé API et d'autres paramètres directement en ligne de commande.

## 🎮 Utilisation

Le script s'utilise en ligne de commande. Voici l'aide de base :

```bash
python transkryptor.py --help
```

### Exemples d'Utilisation

**Transcription simple d'un fichier :**
```bash
python transkryptor.py chemin/vers/votre/fichier_audio.mp3
```
La transcription sera sauvegardée dans le répertoire spécifié par `output_directory` dans `config.json` (par défaut `./transkryptor_outputs/`) avec un nom basé sur le fichier d'entrée.

**Spécifier un fichier de sortie :**
```bash
python transkryptor.py mon_audio.wav -o transcription_complete.txt
```

**🆕 Utiliser le mode prévisualisation temps réel :**
```bash
python transkryptor.py conference.mp3 --preview -o transcript.txt
```
Cette commande ouvre une fenêtre pour voir la transcription en direct tout en sauvegardant dans un fichier.

**Utiliser une langue et un prompt spécifiques :**
```bash
python transkryptor.py interview_expert.m4a -l en -p "Interview with Dr. Expert about AI ethics."
```

**Mode Debug pour voir les détails :**
```bash
python transkryptor.py court_extrait.flac --debug
```

**Mode Silent pour une sortie brute des lots sur stdout :**
```bash
python transkryptor.py long_podcast.ogg --silent
```
Si vous souhaitez capturer cette sortie dans un fichier :
```bash
python transkryptor.py long_podcast.ogg --silent > podcast_transcription.txt
```

**🆕 Utiliser prévisualisation avec écriture en temps réel :**
```bash
python transkryptor.py presentation.m4a --preview -o presentation_transcript.txt
```
Cet exemple montre la transcription en temps réel dans le terminal et l'écrit progressivement dans un fichier.

**Mode debug (incompatible avec preview) :**
```bash
python transkryptor.py presentation.m4a -o presentation_transcript.txt --debug
```
Pour voir les détails de debug, utilisez cette commande sans l'option --preview.

**Changer la taille des chunks et des lots :**
```bash
python transkryptor.py tres_long_fichier.mp3 --chunk-duration 600000 --chunk-overlap 60000 --batch-size 3
```
(Chunk de 10 minutes, chevauchement de 1 minute, 3 chunks par lot)

## 📋 Options de Ligne de Commande

| Option | Description |
|--------|-------------|
| `AUDIO_FILE_PATH` | Chemin vers le fichier audio à transcrire (requis) |
| `-o, --output-file` | Fichier pour sauvegarder la transcription finale |
| `-c, --config-file` | Chemin vers le fichier de configuration JSON |
| `--api-url` | URL de l'API de transcription LLMaaS |
| `--api-key` | Clé API pour LLMaaS |
| `-l, --language` | Code langue de l'audio (ex: fr, en) |
| `-p, --prompt` | Prompt pour guider la transcription |
| `--chunk-duration` | Durée de chaque morceau en millisecondes |
| `--chunk-overlap` | Chevauchement entre les morceaux en millisecondes |
| `--batch-size` | Nombre de morceaux à traiter en parallèle par lot |
| `--sample-rate` | Fréquence d'échantillonnage en Hz (ex: 16000, 22050, 44100) |
| `--output-dir` | Répertoire pour sauvegarder les transcriptions |
| `--preview` | 🆕 Ouvrir une fenêtre de prévisualisation temps réel |
| `--debug` | Activer le mode de débogage verbeux |
| `--silent` | Mode silencieux: affiche la transcription des lots sur stdout |

## 🛠️ Formats Audio Supportés

Grâce à `pydub`, une large gamme de formats audio devrait être supportée, notamment :
`mp3`, `wav`, `flac`, `ogg`, `m4a`, `aac`, etc.
Le script convertira l'audio en un format WAV mono PCM 16-bit avant de l'envoyer à l'API, si nécessaire.

## 💡 Conseils d'Utilisation

### 🆕 Écriture en Temps Réel
- La transcription est écrite progressivement dans le fichier au fur et à mesure
- Vous pouvez suivre le progrès en ouvrant le fichier de sortie dans un éditeur qui se rafraîchit automatiquement
- En cas d'interruption, vous conservez la transcription partielle

### 🆕 Mode Prévisualisation
- Idéal pour les transcriptions longues où vous voulez voir le progrès
- La fenêtre peut être redimensionnée selon vos préférences
- Utilisez "Copier Tout" pour obtenir rapidement le texte transcrit
- La fenêtre reste ouverte même après la fin de la transcription

### Optimisation des Performances
- Pour des fichiers très longs, augmentez `chunk_duration` (ex: 600000ms = 10min)
- Augmentez `batch_size` si votre connexion internet est stable
- Utilisez le mode `--silent` pour les pipelines automatisés

## 📝 Notes Techniques

-   **`ffmpeg` est crucial** pour le support étendu des formats audio par `pydub`. Si vous rencontrez des erreurs de décodage, vérifiez votre installation de `ffmpeg`.
-   **Écriture en temps réel** : Le fichier est écrit avec un buffering de ligne pour un affichage immédiat des résultats.
-   **Mode prévisualisation** : Utilise Rich pour afficher une interface temps réel directement dans le terminal sans bloquer le processus de transcription.
-   Les performances dépendront de la taille de vos fichiers, de la vitesse de votre connexion internet, et de la charge sur l'API LLMaaS.
-   Le mode debug peut générer une grande quantité de logs.

## 🔧 Dépannage

### Problèmes avec l'option `--preview`
L'option `--preview` utilise Rich pour l'affichage terminal et ne devrait pas poser de problème sur la plupart des systèmes. Si vous rencontrez des difficultés :

- Vérifiez que Rich est bien installé : `pip show rich`
- Assurez-vous d'utiliser un terminal moderne qui supporte les couleurs et les caractères Unicode
- Si l'affichage est perturbé, vous pouvez toujours utiliser l'écriture en temps réel sans prévisualisation : `python transkryptor.py audio.mp3 -o transcript.txt`
- Pour diagnostiquer : utilisez le mode debug pour voir les détails : `python transkryptor.py audio.mp3 -o transcript.txt --debug`

### Problèmes de Formats Audio
Si un format audio n'est pas reconnu :
1. Vérifiez que `ffmpeg` est installé et dans le PATH
2. Essayez de convertir le fichier en WAV avec `ffmpeg` d'abord
3. Consultez les logs en mode `--debug` pour plus de détails

Ce script est un exemple avancé et peut être étendu ou modifié selon vos besoins spécifiques.
