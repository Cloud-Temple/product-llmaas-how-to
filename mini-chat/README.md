# Mini-Chat LLMaaS v3.0

Une interface de chat en ligne de commande (CLI) moderne, robuste et modulaire pour interagir avec les modèles LLMaaS. Cette version 3.0 a été entièrement réarchitecturée pour offrir une meilleure stabilité, une maintenance facilitée et une expérience utilisateur enrichie.

## 🌟 Nouveautés de la v3.0

- **Architecture Modulaire** : Séparation claire entre la configuration, l'état, la logique métier et l'interface utilisateur.
- **Robustesse Accrue** : Gestion centralisée des erreurs, typage strict et validation des entrées.
- **RAG Simplifié** : Intégration fluide de l'embedding et de la recherche vectorielle avec Qdrant.
- **Support Outils Amélioré** : Exécution fiable des outils (calculatrice, heure, fichiers, etc.) même en mode streaming.
- **Modèle par Défaut** : Utilisation de `openai/gpt-oss-120b` pour des performances optimales.

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Naviguez vers le répertoire
cd mini-chat

# Créez un environnement virtuel (recommandé)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Installez les dépendances
pip install -r requirements.txt
```

### 2. Configuration

Copiez le fichier d'exemple et configurez votre clé API :

```bash
cp .env.example .env
# Éditez .env avec votre clé API LLMaaS
```

**Configuration minimale (.env)** :
```env
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="votre_cle_api_ici"
DEFAULT_MODEL="openai/gpt-oss-120b"
```

### 3. Démarrage de Qdrant (Optionnel - Pour le RAG)

Pour activer la mémoire à long terme et la recherche documentaire :

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Lancement

```bash
# Mode interactif standard
python mini_chat.py

# Avec un modèle spécifique
python mini_chat.py --model gemma3:27b

# Mode "One-Shot" (commande unique)
python mini_chat.py --non-interactive --prompt "Explique-moi la relativité restreinte en 3 phrases."
```

## 🎮 Commandes Interactives

Une fois dans le chat, utilisez les commandes slash `/` pour contrôler l'application :

| Commande | Description |
|----------|-------------|
| `/rag on|off` | Active ou désactive le mode RAG (Recherche Vectorielle). |
| `/embed <fichier>` | Lit, découpe et indexe un fichier texte dans la base vectorielle. |
| `/history` | Affiche l'historique complet de la session courante. |
| `/clear` | Efface l'historique de la conversation (garde le système). |
| `/quit` | Quitte l'application. |

## 🧠 Fonctionnalités Avancées (RAG)

Le système RAG (Retrieval-Augmented Generation) permet au modèle d'accéder à vos propres documents.

1.  **Indexation** :
    ```text
    /embed constitution.txt
    ```
    *Le système découpe le fichier en morceaux, calcule les embeddings et les stocke dans Qdrant.*

2.  **Activation** :
    ```text
    /rag on
    ```

3.  **Utilisation** :
    Posez simplement votre question. Si le RAG est actif, le système cherchera d'abord les passages pertinents dans vos documents et les fournira au modèle comme contexte.

## 🛠️ Outils Intégrés (Tool Calling)

Le modèle a accès à plusieurs outils qu'il peut décider d'utiliser de manière autonome :
- **Calculatrice** : Pour les opérations mathématiques précises.
- **Date/Heure** : Pour connaître le moment présent.
- **Système de Fichiers** : Lecture et écriture de fichiers (dans le répertoire courant).
- **Shell** : Exécution de commandes système (nécessite validation utilisateur).

## 🏗️ Architecture Technique

Le code est organisé pour être lisible et maintenable :

- **`mini_chat.py`** : Point d'entrée. Contient la boucle principale (`MiniChatCLI`) et l'orchestration (`ChatService`).
- **`api_client.py`** : Gestion bas niveau des appels API (streaming, gestion des chunks).
- **`qdrant_utils.py`** : Interface avec la base de données vectorielle.
- **`rag_core.py`** : Logique de découpage de texte (chunking).
- **`tools_definition.py`** : Définition des schémas JSON des outils.

## 📞 Support

Pour toute question ou problème, vérifiez d'abord que votre clé API est valide et que Qdrant tourne (si vous utilisez le RAG).

Vous pouvez également lancer le script de test automatisé pour valider votre configuration RAG :
```bash
python test_rag_scenario.py
```
