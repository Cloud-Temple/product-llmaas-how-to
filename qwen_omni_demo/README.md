# 🤖 Démonstration Multimodale Qwen3-Omni

Ce projet fournit un exemple complet d'utilisation du modèle **Qwen3-Omni** via l'API LLMaaS.
Il met en valeur les capacités multimodales du modèle, notamment le traitement direct de flux audio et vidéo via l'API de Chat Completions.

Pour plus d'informations sur le modèle, consultez le dépôt officiel : [https://github.com/QwenLM/Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni)

## 🌟 Fonctionnalités

- **Audio-to-Text** : Envoi d'un fichier audio (URL) et réception d'une réponse textuelle (traduction, transcription, réponse).
- **Video-to-Text** : Envoi d'un fichier vidéo (URL) et réception d'une description ou d'une analyse.
- **Client OpenAI** : Utilisation de la librairie standard `openai` pour Python, démontrant la compatibilité de l'API.
- **Affichage Enrichi** : Utilisation de `rich` pour un rendu console moderne.

## 📋 Prérequis

- **Python 3.10** ou supérieur.
- Accès réseau à l'API LLMaaS (`api.ai.cloud-temple.com` ou endpoint interne).
- Une clé API valide.

## 🚀 Installation

1. **Cloner le dépôt** (ou copier ce dossier).

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer l'environnement** :
   ```bash
   cp .env.example .env
   ```
   Ouvrez le fichier `.env` et modifiez les variables :
   - `API_ENDPOINT` : URL de l'API. Par défaut la production (`https://api.ai.cloud-temple.com/v1`). Pour un test interne direct, utiliser l'IP du serveur (`https://172.16.0.17:8000/v1`).
   - `API_KEY` : Votre clé API.
   - `SSL_VERIFY` : `true` pour la prod, `false` pour les environnements de dev/internes self-signed.

## 🎮 Utilisation

Lancez simplement le script principal :

```bash
python3 qwen-omni-demo.py
```

Le script exécutera séquentiellement :
1.  Un test audio (traduction chinois -> anglais).
2.  Un test vidéo (description d'une scène de dessin).

## 🧩 Structure du Projet

```text
exemples/qwen_omni_demo/
├── .env.example       # Modèle de configuration
├── qwen-omni-demo.py  # Script principal (Client API)
├── README.md          # Documentation (FR)
├── README_EN.md       # Documentation (EN)
└── requirements.txt   # Dépendances Python
```

## ⚠️ Dépannage

- **Erreur 502 Bad Gateway** :
  - Vérifiez que le Proxy LLM sur le serveur cible a été mis à jour pour supporter les champs `audio_url` et `video_url` (Voir RFC-0047).
  - Si vous passez par le Load Balancer public, assurez-vous qu'il ne filtre pas ces champs.

- **Erreur 401 Unauthorized** :
  - Vérifiez votre `API_KEY` dans le fichier `.env`.
