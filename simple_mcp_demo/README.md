# Exemple : MCP HTTP/SSE Demo

**Un exemple ultra-pédagogique d'utilisation du Model Context Protocol (MCP) en HTTP/SSE avec l'API LLMaaS**

---

## 📚 Table des Matières

1. [Introduction](#introduction)
2. [Architecture HTTP/SSE](#architecture-httpsse)
3. [Sécurité et Authentification](#sécurité-et-authentification)
4. [Fichiers du projet](#fichiers-du-projet)
5. [Fonctionnement détaillé](#fonctionnement-détaillé)
6. [Prérequis](#prérequis)
7. [Installation](#installation)
8. [Utilisation](#utilisation)
9. [Avantages de l'architecture HTTP](#avantages-de-larchitecture-http)
10. [Dépannage](#dépannage)

---

## Introduction

Cet exemple démontre comment utiliser le **Model Context Protocol (MCP)** avec l'API LLMaaS de Cloud Temple dans une architecture **Client-Serveur Web**.

Contrairement aux implémentations basiques qui lancent des sous-processus (stdio), cet exemple montre une architecture **distribuée** et **réaliste** où le serveur MCP est un **service web indépendant** et **sécurisé**.

Le cas d'usage reste simple : **demander l'heure actuelle** au modèle, qui utilisera un outil MCP distant pour obtenir cette information.

---

## Architecture HTTP/SSE

Le **Model Context Protocol (MCP)** définit comment un modèle interagit avec des outils. Dans cette version HTTP/SSE :

- **HTTP (Hypertext Transfer Protocol)** : Utilisé par le client pour envoyer des requêtes JSON-RPC au serveur (ex: lister les outils, exécuter un outil).
- **SSE (Server-Sent Events)** : Utilisé par le serveur pour envoyer des notifications ou des événements au client en temps réel.

```
┌─────────────────────────────────────────────────┐
│  Client MCP (mcp_client_demo.py)                │
│  • Se connecte via HTTP au serveur MCP          │
│  • Envoie le header Authorization: Bearer ...   │
│  • Discute avec l'API LLMaaS                    │
└───────────────────────┬─────────────────────────┘
                        │
           Requêtes HTTP│(JSON-RPC) + Auth
                        ▼
┌─────────────────────────────────────────────────┐
│  Serveur MCP (mcp_server.py)                    │
│  • Service Web sur http://localhost:8000        │
│  • Protégé par clé API                          │
│  • Expose l'outil "get_current_time"            │
└─────────────────────────────────────────────────┘
```

---

## Sécurité et Authentification

Cet exemple montre comment sécuriser l'accès à un serveur MCP.

### Côté Serveur
Le serveur est protégé par un middleware qui vérifie le header `Authorization`.
On définit la clé au démarrage :
```bash
python3 mcp_server.py --auth-key ma_super_cle_secrete
```

### Côté Client
Le client doit fournir cette clé pour se connecter. La clé est lue depuis le fichier `.env` :
```env
MCP_SERVER_AUTH_KEY=ma_super_cle_secrete
```

Si la clé ne correspond pas, le serveur rejette la connexion (403 Forbidden).

---

## Fichiers du projet

| Fichier | Description | Rôle |
|---------|-------------|------|
| `mcp_server.py` | **Service Web Sécurisé** | Serveur HTTP autonome avec authentification. |
| `mcp_client_demo.py` | **Client HTTP** | Client utilisant le SDK standard `mcp` et gérant l'auth. |
| `docker-compose.yml` | **Déploiement Docker** | Configuration pour lancer le serveur via Docker Compose. |
| `Dockerfile` | **Image Docker** | Définition de l'image du serveur MCP. |
| `requirements.txt` | Dépendances | Contient `mcp`, `httpx`, `fastapi`, `uvicorn`, `python-dotenv`. |
| `.env.example` | Configuration | Modèle pour configurer les clés API. |
| `README.md` | Documentation | Ce fichier. |

---

## Fonctionnement détaillé

### 1. Le Serveur (`mcp_server.py`)

C'est un service web basé sur **FastAPI** qui encapsule **FastMCP**.
- Il utilise un **middleware de sécurité** pour vérifier le token Bearer.
- Il écoute sur `0.0.0.0:8000`.
- Il expose les endpoints MCP standards.

### 2. Le Flux de Session SSE (Session ID)

Un point clé pour comprendre MCP sur HTTP : **Qui donne l'ID de session ?**

1.  Le Client se connecte en `GET /sse`.
2.  Le Serveur génère un **Session ID** unique.
3.  Le Serveur envoie un événement `endpoint` au client dans le flux SSE.
    - Contenu : `/messages/?session_id=...`
4.  Le Client utilise ensuite cette URL (avec le session_id) pour toutes ses requêtes `POST`.

### 3. Le Client (`mcp_client_demo.py`)

C'est un script asynchrone qui :
1. Lit la configuration et la clé d'auth dans `.env`.
2. Se connecte à `http://localhost:8000/sse` en passant le header `Authorization`.
3. Initialise la session MCP.
4. Récupère les outils disponibles.
5. Orchestre la conversation avec le LLM.

---

## Prérequis

- **Python 3.8+**
- Une **clé API LLMaaS** valide
- Port 8000 libre

---

## Installation

### 1. Naviguer vers le répertoire

```bash
cd simple_mcp_demo/
```

### 2. Créer le fichier .env

```bash
cp .env.example .env
```
Éditez `.env` avec votre clé API LLMaaS et définissez une clé pour le serveur MCP si vous le souhaitez.

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Utilisation

Cette architecture nécessite **deux terminaux**.

### Option A : Lancement Manuel (Sans Docker)

**Terminal 1 : Démarrer le Serveur**
```bash
python3 mcp_server.py --auth-key ma_cle_secrete
```

**Terminal 2 : Lancer le Client**
Assurez-vous que `MCP_SERVER_AUTH_KEY=ma_cle_secrete` est bien dans votre `.env`.
```bash
python3 mcp_client_demo.py --debug
```

### Option B : Lancement via Docker 🐳

Si vous préférez ne pas installer les dépendances serveur sur votre machine :

1.  **Démarrer le serveur** :
    ```bash
    docker compose up -d
    ```
    Le serveur sera accessible sur `http://localhost:8000` avec la clé par défaut `ma_cle_docker_secrete` (modifiable dans le `docker-compose.yml`).

2.  **Configurer le client** :
    Mettez à jour votre `.env` local :
    ```env
    MCP_SERVER_AUTH_KEY=ma_cle_docker_secrete
    ```

3.  **Lancer le client** (depuis votre machine) :
    ```bash
    python3 mcp_client_demo.py --debug
    ```

4.  **Arrêter le serveur** :
    ```bash
    docker compose down
    ```

---

### Terminal 2 : Lancer le Client (Suite Option A)

Assurez-vous que `MCP_SERVER_AUTH_KEY=ma_cle_secrete` est bien dans votre `.env`.

```bash
python3 mcp_client_demo.py --debug
```

*Le client va :*
1. Lire la clé d'auth
2. Se connecter au serveur (Auth OK)
3. Exécuter le scénario complet

---

## Avantages de l'architecture HTTP

Pourquoi utiliser HTTP/SSE plutôt que l'approche simple (stdio) ?

1.  **Indépendance** : Le serveur peut être redémarré sans couper le client.
2.  **Sécurité** : Contrôle d'accès via token, indispensable pour une architecture distribuée.
3.  **Partage** : Un seul serveur MCP peut servir plusieurs clients.
4.  **Déploiement** : Le serveur peut être hébergé sur une machine différente.

---

## Dépannage

### "403 Forbidden" ou "Unauthorized"
- Vérifiez que la clé passée avec `--auth-key` au serveur est IDENTIQUE à celle dans le `.env` du client.

### "Connection refused"
- Vérifiez que `mcp_server.py` tourne bien.
- Vérifiez l'URL dans `.env`.

### "Module not found"
- `pip install -r requirements.txt`
