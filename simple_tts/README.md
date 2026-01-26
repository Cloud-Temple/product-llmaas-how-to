# Démonstration TTS LLMaaS (Text-to-Speech)

Ce dossier contient un exemple simple et élégant d'utilisation de l'API de synthèse vocale (TTS) de la plateforme LLMaaS.

Il utilise l'endpoint compatible OpenAI `/v1/audio/speech` pour convertir du texte en fichier audio.

## Fonctionnalités

*   **Interface Console Riche** : Utilise la bibliothèque `rich` pour un affichage coloré, des panneaux d'information et des barres de progression.
*   **Support Complet de l'API** : Permet de choisir le modèle, la voix, le format de sortie et le texte.
*   **Mode Interactif** : Si aucun texte n'est fourni en argument, le script vous demandera de le saisir.
*   **Lecture de Fichier** : Peut lire le texte à synthétiser depuis un fichier local.
*   **Lecture Audio Directe** : Peut jouer automatiquement le fichier généré avec l'option `--play` (supporte macOS, Windows et Linux avec ffplay/mpg123/aplay).
*   **Gestion d'Erreurs** : Affiche clairement les erreurs API ou de connexion.

## Prérequis

*   Python 3.8+
*   Un token d'accès à l'API LLMaaS (Bearer Token)

## Installation et Configuration

1.  Accédez au répertoire de l'exemple :
    ```bash
    cd exemples/simple_tts
    ```

2.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

3.  Configurez l'environnement :
    *   Copiez le fichier d'exemple :
        ```bash
        cp .env.example .env
        ```
    *   Éditez le fichier `.env` pour y ajouter votre clé API et personnaliser l'URL si nécessaire.

## Utilisation

Le script utilisera automatiquement la configuration définie dans `.env`.

### Exemples de commandes

**1. Synthèse simple (texte en argument) :**

```bash
python tts_demo.py "Bienvenue sur la plateforme Cloud Temple AI."
```
*Génère un fichier mp3 avec la voix par défaut (alloy).*

**2. Synthèse et lecture immédiate :**

```bash
python tts_demo.py "Ceci est un test audio." --play
```

**3. Changer la voix et le format :**

```bash
python tts_demo.py "Ceci est une voix différente." --voice onyx --format wav --output ma_voix.wav
```

**4. Lire depuis un fichier texte :**

```bash
python tts_demo.py -f mon_livre.txt --voice shimmer
```

**5. Mode Interactif :**

```bash
python tts_demo.py
```
*Le script vous demandera de saisir le texte.*

**6. Mode Debug (pour voir les détails de la requête/réponse) :**

```bash
python tts_demo.py "Test technique" --debug
```

**7. Ajuster le Timeout (pour les longs textes) :**

```bash
python tts_demo.py "Texte très long..." --timeout 600
```
*Le timeout par défaut est de 300 secondes.*

## Voix Disponibles

*   `alloy` (Femme, Américain) - *Défaut*
*   `echo` (Homme, Américain)
*   `fable` (Homme, Américain)
*   `onyx` (Femme, Américain)
*   `nova` (Femme, Américain)
*   `shimmer` (Femme, Américain)
*   `coral` (Femme, Américain)
*   `ash` (Homme, Chinois/Anglais)
*   `ballad` (Homme, Indien/Anglais)
*   `xi` (Homme, Chinois)
*   `sage` (Femme, Chinois)
*   `chef` (Homme, Français)
