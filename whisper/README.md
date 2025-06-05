# Exemple de Transcription Audio Avancé avec l'API LLMaaS Cloud Temple

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

Ce répertoire contient un script Python avancé (`transcribe_audio.py`) pour transcrire des fichiers audio en utilisant l'**API de transcription LLMaaS Cloud Temple**. Il inclut de nombreuses fonctionnalités avancées et des exemples de fichiers audio dans différentes langues.

## ✨ Nouvelles Fonctionnalités v2.0

- **🐛 Mode debug** : Affichage détaillé des payloads, requêtes et réponses avec formatage JSON coloré
- **💡 Support du prompt** : Possibilité de fournir un prompt pour guider la transcription Whisper
- **🔍 Support des wildcards** : Traitement de plusieurs fichiers avec des patterns (ex: `*.mp3`, `audio/*.m4a`)
- **🎵 Support M4A** : Ajout du support pour les fichiers M4A et autres formats audio populaires
- **📊 Statistiques** : Résumé détaillé des succès/erreurs pour les traitements par lot
- **🎨 Interface améliorée** : Affichage coloré et formaté avec indicateurs de progression

## 📁 Fichiers Inclus

- `transcribe_audio.py`: Le script Python principal (v2.0) avec toutes les nouvelles fonctionnalités
- `config.json`: Fichier de configuration pour l'URL de l'API, le token et la langue par défaut
- `french.mp3`: Un fichier audio d'exemple en français
- `english.mp3`: Un fichier audio d'exemple en anglais
- `deutch.mp3`: Un fichier audio d'exemple en allemand
- `spanish.mp3`: Un fichier audio d'exemple en espagnol

## 🎯 Formats Audio Supportés

Le script supporte maintenant plusieurs formats audio :

| Format | Extension | Type MIME     |
| ------ | --------- | ------------- |
| WAV    | `.wav`    | `audio/x-wav` |
| MP3    | `.mp3`    | `audio/mpeg`  |
| M4A    | `.m4a`    | `audio/mp4`   |
| FLAC   | `.flac`   | `audio/flac`  |
| OGG    | `.ogg`    | `audio/ogg`   |
| WebM   | `.webm`   | `audio/webm`  |

## 🚀 Prérequis

- Python 3.7+
- La bibliothèque `requests`

## ⚙️ Configuration Initiale

1.  **Copiez les fichiers audio d'exemple** dans ce répertoire si ce n'est pas déjà fait.

2.  **Configurez votre token d'API** :
    Ouvrez le fichier `config.json` et remplacez `"VOTRE_TOKEN_BEARER_ICI"` par votre token d'authentification Cloud Temple réel.
    ```json
    {
      "api_url": "https://api.ai.cloud-temple.com/v1/audio/transcriptions",
      "api_token": "VOTRE_VRAI_TOKEN_ICI",
      "default_language": "fr"
    }
    ```

## 📦 Installation des Dépendances

```bash
# Naviguer vers le répertoire
cd exemples/whisper/

# Créer un environnement virtuel (recommandé)
python3 -m venv venv_whisper_example

# Activer l'environnement virtuel
# Sur macOS/Linux :
source venv_whisper_example/bin/activate
# Sur Windows :
# .\venv_whisper_example\Scripts\activate

# Installer les dépendances
pip install requests
```

## 🎮 Utilisation du Script v2.0

### Arguments Disponibles

```bash
python transcribe_audio.py -h
```

**Arguments principaux :**

- `file_patterns` (requis) : Fichier(s) ou pattern(s) à transcrire (supporte les wildcards)
- `-l, --language` : Code langue (ex: `fr`, `en`, `de`, `es`)
- `-t, --token` : Token d'authentification Bearer
- `--api-url` : URL de l'API de transcription
- `-p, --prompt` : Prompt pour guider la transcription
- `--debug` : Active le mode debug avec affichage des payloads

### 📝 Exemples d'Utilisation

#### Exemples Basiques

```bash
# Transcrire un fichier unique
python transcribe_audio.py french.mp3

# Transcrire avec une langue spécifique
python transcribe_audio.py english.mp3 -l en

# Transcrire avec un token personnalisé
python transcribe_audio.py deutch.mp3 -l de -t VOTRE_TOKEN_PERSONNEL
```

#### Exemples avec Wildcards

```bash
# Transcrire tous les fichiers MP3 du répertoire courant
python transcribe_audio.py *.mp3 -l en

# Transcrire tous les fichiers audio d'un dossier spécifique
python transcribe_audio.py audio/*.m4a

# Transcrire des fichiers avec un pattern spécifique
python transcribe_audio.py "recording_*.wav" -l fr
```

#### Exemples avec Prompt

```bash
# Transcription d'une conférence médicale
python transcribe_audio.py conference.mp3 --prompt "Conférence médicale sur la cardiologie"

# Transcription d'un fichier musical
python transcribe_audio.py concert.m4a --prompt "Concert de musique classique"

# Transcription technique
python transcribe_audio.py meeting.wav --prompt "Réunion technique sur l'intelligence artificielle"
```

#### Exemples avec Mode Debug

```bash
# Debug sur un fichier unique
python transcribe_audio.py french.mp3 --debug

# Debug avec prompt et wildcards
python transcribe_audio.py *.mp3 -l en --prompt "Interview" --debug

# Debug complet
python transcribe_audio.py audio/*.m4a -l fr --prompt "Podcast" --debug -t MON_TOKEN
```

### 🎨 Sortie Attendue

#### Mode Normal
```
[INFO] Utilisation de l'URL API: https://api.ai.cloud-temple.com/v1/audio/transcriptions
[INFO] Traitement de 1 fichier(s) audio...
[INFO] Envoi du fichier 'french.mp3' (245.6 KB) pour transcription en langue 'fr'...

============================================================
📄 Transcription [1/1] - 'french.mp3' (fr)
============================================================
Bonjour, ceci est un test de l'API de transcription audio.
============================================================

📊 RÉSUMÉ FINAL
✅ Succès: 1
📁 Total traité: 1 fichier(s)
```

#### Mode Debug
```
[DEBUG] Mode debug activé
[DEBUG] Configuration chargée depuis: /path/to/config.json
[DEBUG] URL API: https://api.ai.cloud-temple.com/v1/audio/transcriptions
[DEBUG] Langue: fr
[DEBUG] Prompt: Aucun

========== Headers ==========
{
  "Authorization": "Bearer G3H4I5J6K7L8M9N0O1P2...",
  "Accept": "application/json"
}
=============================

========== Request Data ==========
{
  "language": "fr",
  "response_format": "json",
  "temperature": "0"
}
===================================

[DEBUG] Code de réponse HTTP: 200
[DEBUG] En-têtes de réponse: {'content-type': 'application/json', ...}

========== Response JSON ==========
{
  "text": "Bonjour, ceci est un test de l'API de transcription audio."
}
====================================
```

## 💡 Conseils d'Utilisation

### Optimisation avec les Prompts

Le prompt permet de guider Whisper pour améliorer la précision :

- **Contexte spécifique** : `"Réunion d'équipe sur le projet LLMaaS"`
- **Vocabulaire technique** : `"Discussion technique sur l'intelligence artificielle"`
- **Noms propres** : `"Interview avec Jean Dupont, directeur de Cloud Temple"`
- **Domaine médical** : `"Consultation médicale en cardiologie"`
- **Contenu musical** : `"Concert de musique classique, compositeur Mozart"`

### Utilisation des Wildcards

```bash
# Tous les fichiers audio du répertoire
python transcribe_audio.py *.{mp3,wav,m4a}

# Fichiers avec un préfixe spécifique
python transcribe_audio.py "meeting_*.mp3"

# Dans un sous-répertoire
python transcribe_audio.py "recordings/2025/*.wav"

# Plusieurs patterns
python transcribe_audio.py *.mp3 *.wav *.m4a
```

### Mode Debug

Le mode debug affiche :
- 📋 Configuration chargée
- 📤 Payloads des requêtes (headers, data, file info)
- 📥 Réponses complètes de l'API
- 🔧 Informations techniques (codes HTTP, MIME types, tailles)
- 🐛 Messages d'erreur détaillés

## ⚠️ Notes Importantes

- **Token requis** : Un token d'authentification valide est obligatoire
- **Formats supportés** : Le script détecte automatiquement le format et applique le bon type MIME
- **Taille des fichiers** : L'API peut avoir des limites de taille (généralement jusqu'à 25MB)
- **Wildcards** : Utilisez des guillemets pour les patterns complexes : `"*.{mp3,wav}"`
- **Prompt optimal** : Un prompt court et descriptif donne de meilleurs résultats

## 🔧 Dépannage

### Erreurs Communes

1. **Token invalide (401)** : Vérifiez votre token dans `config.json`
2. **Fichier non trouvé** : Vérifiez les chemins et patterns
3. **Format non supporté** : Le script affichera un avertissement mais tentera la transcription
4. **Aucun fichier trouvé** : Vérifiez vos patterns de wildcards

### Mode Debug pour Diagnostic

Utilisez toujours `--debug` pour diagnostiquer les problèmes :

```bash
python transcribe_audio.py problematic_file.mp3 --debug
```

Cela affichera tous les détails de la requête et de la réponse pour identifier le problème.

## 🔄 Comparaison des Versions

| Fonctionnalité          | v1.0 | v2.0         |
| ----------------------- | ---- | ------------ |
| Fichier unique          | ✅   | ✅           |
| Wildcards               | ❌   | ✅           |
| Formats M4A, FLAC, etc. | ❌   | ✅           |
| Prompt Whisper          | ❌   | ✅           |
| Mode debug              | ❌   | ✅           |
| Statistiques            | ❌   | ✅           |
| Interface colorée       | ✅   | ✅ Améliorée |

La version 2.0 est 100% compatible avec la v1.0 tout en ajoutant de nombreuses fonctionnalités avancées !
