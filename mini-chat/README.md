# Mini-Chat LLMaaS

Interface en ligne de commande élégante pour interagir avec les modèles de langage de la plateforme LLMaaS, avec support complet du RAG (Retrieval-Augmented Generation).

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

```bash
# Copiez le fichier de configuration
cp .env.example .env

# Éditez .env avec vos paramètres
nano .env
```

**Configuration minimale** :
```env
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="votre_cle_api_ici"
DEFAULT_MODEL="qwen3:30b-a3b"
```

### 3. Démarrage de Qdrant (pour le RAG)

**Option A : Docker (recommandé)**
```bash
# Démarrage simple
docker run -p 6333:6333 qdrant/qdrant

# Ou avec persistance des données
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Option B : Docker Compose**
```bash
# Utilisez le fichier fourni
docker-compose up -d
```

**Option C : Installation locale**
```bash
# Suivez les instructions sur https://qdrant.tech/documentation/quick-start/
```

### 4. Premier Lancement

```bash
# Lancement simple
python mini_chat.py

# Avec un modèle spécifique
python mini_chat.py --model qwen3:4b

# Mode debug pour voir les détails
python mini_chat.py --debug
```

## 🎯 Fonctionnalités Principales

### 💬 Chat Intelligent
- **Streaming en temps réel** : Réponses affichées au fur et à mesure
- **Historique persistant** : Navigation avec les flèches ↑/↓
- **Autocomplétion** : 23 commandes avec Tab
- **Modes flexibles** : Debug, silencieux, non-interactif

### 🛠️ Outils Intégrés
- **🕒 Horloge** : Heure actuelle
- **🧮 Calculatrice** : Expressions mathématiques
- **📁 Fichiers** : Lecture et sauvegarde
- **⚡ Shell** : Exécution de commandes (avec confirmation)
- **🔍 RAG** : Recherche dans une base de connaissances vectorielle

### 🧠 RAG (Retrieval-Augmented Generation)
- **Ingestion automatique** : Commande `/embed` pour ajouter des documents
- **Recherche intelligente** : Seuils de similarité configurables
- **Activation flexible** : Mode automatique ou manuel
- **Diagnostic complet** : Gestion et monitoring de la base Qdrant

## 📋 Guide d'Utilisation

### Configuration RAG

1. **Démarrez Qdrant** (voir section Démarrage Rapide)

2. **Configurez .env** :
```env
# Paramètres Qdrant
QDRANT_URL="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION="minichat_rag"
EMBEDDING_MODEL="granite-embedding:278m"

# Paramètres de chunking (en tokens)
RAG_CHUNK_SIZE=256
RAG_CHUNK_OVERLAP=50
```

3. **Ingérez des documents** :
```bash
# Dans le chat
/embed constitution.txt
```

4. **Activez le RAG** :
```bash
/rag on
```

### Commandes Essentielles

#### Gestion de Session
```bash
/model                    # Changer de modèle
/system <prompt>          # Définir un prompt système
/clear                    # Effacer l'historique
/save_session chat.json   # Sauvegarder la session
/load_session chat.json   # Charger une session
```

#### RAG et Documents
```bash
/embed <fichier>          # Ingérer un document
/rag on|off              # Activer/désactiver le RAG
/rag_threshold 0.8       # Configurer le seuil de similarité
/qdrant_info             # Informations sur la base
/qdrant_list             # Lister les documents
```

#### Diagnostic et Debug
```bash
/context                 # État de l'application
/context all             # Contexte complet + JSON
/debug                   # Mode debug on/off
/tools                   # Liste des outils disponibles
```

## ⚙️ Options de Ligne de Commande

### Options Principales
```bash
python mini_chat.py [OPTIONS]

--model TEXT              # Modèle à utiliser
--max-tokens INTEGER      # Limite de tokens (défaut: 8192)
--temperature FLOAT       # Température (défaut: 0.7)
--system-prompt TEXT      # Prompt système initial
--debug / --no-debug      # Mode debug
```

### Options Avancées
```bash
--api-url TEXT            # URL de l'API (écrase .env)
--api-key TEXT            # Clé API (écrase .env)
--non-interactive         # Mode non-interactif
--no-stream              # Désactiver le streaming
--silent                 # Mode silencieux
--godmode                # Pas de confirmation pour les commandes shell
```

### Options RAG
```bash
--qdrant-url TEXT         # URL Qdrant (défaut: localhost)
--qdrant-port INTEGER     # Port Qdrant (défaut: 6333)
--qdrant-collection TEXT  # Collection (défaut: minichat_rag)
--embedding-model TEXT    # Modèle d'embedding
```

### Options de Session
```bash
--load-session FILE       # Charger une session
--autosave-json FILE      # Sauvegarde auto en JSON
--autosave-md FILE        # Sauvegarde auto en Markdown
--rules FILE              # Fichier de règles Markdown
--prompt TEXT             # Prompt initial
```

## 🔧 Configuration Avancée

### Fichier .env Complet
```env
# API LLMaaS
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="votre_cle_api_ici"
DEFAULT_MODEL="qwen3:30b-a3b"
MAX_TOKENS=8192

# Qdrant pour RAG
QDRANT_URL="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION="minichat_rag"
EMBEDDING_MODEL="granite-embedding:278m"

# Paramètres de chunking (en tokens)
RAG_CHUNK_SIZE=256
RAG_CHUNK_OVERLAP=50
```

### Docker Compose pour Qdrant
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
```

## 🧪 Tests et Validation

### Test de l'Outil RAG
```bash
# Test unitaire de l'outil de recherche
python test_rag_tool.py

# Test avec une question constitutionnelle
echo "Qui peut révoquer le Premier ministre ?" | python mini_chat.py --model qwen3:4b --non-interactive
```

### Diagnostic de l'Installation
```bash
# Vérifier la configuration
python mini_chat.py --debug
/context all

# Tester la connexion Qdrant
/qdrant_info
```

## 🛠️ Dépannage

### Problèmes Courants

**Qdrant non accessible**
```bash
# Vérifier que Qdrant fonctionne
curl http://localhost:6333/health

# Redémarrer Qdrant
docker restart <container_id>
```

**RAG ne fonctionne pas**
```bash
# Dans le chat
/qdrant_info              # Vérifier la connexion
/rag_threshold 0.7        # Réduire le seuil
/context                  # Diagnostic complet
```

**Limite de contexte dépassée**
```bash
/context                  # Voir le diagnostic automatique
/smol                     # Condenser l'historique
/clear                    # Effacer l'historique
```

**Problèmes de modèles**
```bash
# Lister les modèles disponibles
python mini_chat.py --model ""

# Tester avec un modèle plus petit
python mini_chat.py --model qwen3:4b
```

## 📁 Structure du Projet

```
exemples/mini-chat/
├── mini_chat.py              # Point d'entrée principal
├── api_client.py             # Client API LLMaaS
├── qdrant_utils.py           # Utilitaires Qdrant
├── tools_definition.py       # Définitions des outils
├── ui_utils.py               # Interface utilisateur
├── session_manager.py        # Gestion des sessions
├── rag_core.py               # Fonctions RAG
├── command_handler.py        # Gestionnaire de commandes
├── requirements.txt          # Dépendances Python
├── .env.example              # Configuration exemple
├── docker-compose.yml        # Configuration Qdrant
└── test_rag_tool.py          # Tests unitaires
```

## 🎯 Exemples d'Usage

### Chat Simple
```bash
python mini_chat.py --model qwen3:4b
> Bonjour ! Comment allez-vous ?
```

### RAG avec Constitution
```bash
# 1. Démarrer Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 2. Lancer mini-chat
python mini_chat.py --model qwen3:30b-a3b

# 3. Ingérer la constitution
/embed constitution.txt

# 4. Activer le RAG
/rag on

# 5. Poser une question
> Qui peut dissoudre l'Assemblée nationale selon la Constitution ?
```

### Mode Non-Interactif
```bash
echo "Résume-moi les articles 1 à 5 de la Constitution" | \
python mini_chat.py --model qwen3:4b --non-interactive --no-stream
```

### Session Persistante
```bash
# Sauvegarder
python mini_chat.py --autosave-json ma_session.json

# Reprendre plus tard
python mini_chat.py --load-session ma_session.json
```

## 🔄 Mises à Jour

### Version 1.3.1 (Actuelle)
- ✅ **Bug critique résolu** : Outil de recherche vectorielle pleinement fonctionnel
- ✅ **Gestion robuste des types** : Support universel des formats JSON
- ✅ **Tests validés** : 4/4 requêtes traitées sans erreur
- ✅ **Documentation complète** : Guide d'utilisation et dépannage

### Fonctionnalités Précédentes
- 🎯 **RAG intelligent** avec seuils configurables
- 🔧 **Diagnostic avancé** des problèmes de contexte
- 🛠️ **23 commandes** avec autocomplétion
- 📊 **Gestion complète de Qdrant** (listing, suppression, informations)

## 📞 Support

Pour signaler un bug ou demander de l'aide :
1. Utilisez `/context all` pour obtenir le diagnostic complet
2. Consultez la section Dépannage ci-dessus
3. Vérifiez les logs en mode `--debug`

---

**Mini-Chat LLMaaS** - Interface de chat intelligente avec RAG pour la plateforme LLMaaS
