# Mini-Chat LLMaaS Cloud Temple

Ce script Python permet d'interagir avec les modèles de langage de la **plateforme LLMaaS Cloud Temple** via une interface en ligne de commande "jolie et agréable".

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Fonctionnalités

- Choix interactif du modèle.
- Chat en mode streaming.
- Support des outils (tools) :
    - Horloge : Donne l'heure actuelle.
    - Calculatrice : Évalue des expressions mathématiques.
    - Lecture de fichier : Lit le contenu d'un fichier local.
    - Sauvegarde de contenu : Sauvegarde du texte dans un fichier.
    - Exécution de commande shell : Exécute des commandes shell (avec confirmation).
- Interface utilisateur améliorée avec la bibliothèque `rich`.
- Aide intégrée et commande `/tools` pour lister les outils.
- Option pour définir la taille maximale des tokens de la réponse.
- Possibilité de définir un **prompt système**.
- Mode debug pour afficher les payloads API.
- Affichage des statistiques de la requête (tokens, vitesse).
- **Sauvegarde et chargement** de sessions de chat (paramètres + historique) en JSON.
- Sauvegarde de l'historique en Markdown.

## Prérequis

- Python 3.8+
- Une clé API LLMaaS valide.

## Installation

1.  Clonez ce dépôt (si ce n'est pas déjà fait).
2.  Naviguez vers le répertoire `exemples/mini-chat/`.
3.  Créez un environnement virtuel (recommandé) :
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Sur Linux/macOS
    # .venv\Scripts\activate    # Sur Windows
    ```
4.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
5.  Configurez vos identifiants API :
    - Copiez `.env.example` vers `.env`.
    - Éditez `.env` et renseignez votre `API_URL` et `API_KEY`.

        ```env
        API_URL="https://api.ai.cloud-temple.com/v1"
        API_KEY="votre_cle_api_ici"
        ```

## Utilisation

```bash
python mini_chat.py [OPTIONS]
```

**Options principales :**

- `--model TEXT` : Nom du modèle à utiliser (ex: `gemma3:4b`).
- `--max-tokens INTEGER` : Max tokens pour la réponse (défaut: 1024).
- `--temperature FLOAT` : Température pour la génération (défaut: 0.7).
- `--system-prompt TEXT` ou `-sp TEXT`: Prompt système initial.
- `--debug / --no-debug` : Active/désactive l'affichage des payloads API.
- `--api-url TEXT` : URL de l'API LLMaaS (écrase `.env`).
- `--api-key TEXT` : Clé API LLMaaS (écrase `.env`).
- `--load-session CHEMIN_FICHIER_JSON`: Charge une session de chat sauvegardée.
- `--autosave-json CHEMIN_FICHIER_JSON`: Sauvegarde automatiquement la session en JSON à la fin.
- `--autosave-md CHEMIN_FICHIER_MD`: Sauvegarde automatiquement l'historique en Markdown à la fin.
- `--godmode`: Active le mode GOD MODE (aucune confirmation pour les commandes shell).
- `--silent`: Mode silencieux (moins d'output, n'affiche pas les outils ni les statistiques).
- `--rules CHEMIN_FICHIER_MD`: Fichier Markdown de règles à ajouter au prompt système.
- `--prompt TEXT`: Prompt initial à envoyer au LLM au démarrage.
- `--non-interactive`: Mode non interactif (termine après la première réponse complète du LLM). N'affiche pas le message de bienvenue.
- `--no-stream`: Désactive le streaming de la réponse de l'IA.
- `--help` : Affiche l'aide.

**Commandes en cours de chat :**

- `/quit` ou `/exit` : Quitte le chat.
- `/history` : Affiche l'historique de la conversation.
- `/clear` : Efface l'historique (conserve les paramètres de session comme le prompt système).
- `/model` : Change de modèle (réinitialise l'historique, conserve le prompt système).
- `/system <prompt>` : Définit ou modifie le prompt système (réinitialise l'historique).
- `/system_clear` : Supprime le prompt système (réinitialise l'historique).
- `/save_session <fichier.json>` : Sauvegarde la session actuelle (paramètres et historique).
- `/load_session <fichier.json>` : Charge une session (écrase la session actuelle).
- `/savemd <fichier.md>` : Sauvegarde l'historique actuel en Markdown.
- `/tools` : Liste les outils disponibles et leur description (non affiché en mode silencieux).
- `/smol` : Demande au modèle de condenser l'historique actuel en un prompt efficace.
- `/debug` : Active/désactive le mode debug.
- `/silent`: Active/désactive le mode silencieux.
- `/stream`: Active/désactive le mode streaming pour la réponse de l'IA.
- `/help` : Affiche l'aide détaillée des commandes.
