# Cas d'Usage LLM as a Service - Cloud Temple

Ce répertoire contient une collection d'exemples de code et de scripts démontrant les différentes fonctionnalités et cas d'utilisation de **l'offre LLM as a Service (LLMaaS) de Cloud Temple**.

## 🆕 Changelog - Dernières Nouveautés

### Version 2.1.0 - Juillet 2025

#### 🔍 **GetFact - Extracteur de Faits**
- ✨ **Support des modèles raisonneurs** : Gestion automatique des réponses incluant des blocs de pensée (`<think>...</think>`)
- 🛠️ **Parsing JSON robuste** : Extraction fiable du contenu JSON même depuis des réponses malformées
- 🐛 **Mode debug avancé** : Logs détaillés incluant le découpage précis, les payloads JSON complets et les réponses brutes de l'API

#### 🎵 **Transkryptor - Transcription Audio**
- 🔄 **Résilience aux erreurs** : Mécanisme de retry avec backoff exponentiel pour une meilleure stabilité
- ✨ **Raffinement de transcription (`--rework`)** : Nouvelle option pour améliorer la transcription via un modèle de langage
- 📄 **Script `rework-only.py`** : Nouveau script dédié pour raffiner des fichiers texte existants
- 🔗 **Contexte continu (`--rework-follow`)** : Maintien du contexte entre les lots pour une meilleure cohérence
- 📊 **Recommandations de qualité** : Configuration optimale basée sur des tests (20s pour contenu complexe, 10s pour dialogues)
- 📦 **Dépendances étendues** : Ajout de `tiktoken` et `langchain-text-splitters` pour un meilleur découpage

#### 📝 **Summarizer - Synthèse de Texte** ✨ *NOUVEL OUTIL*
- 🆕 **Outil complet de synthèse** : Nouveau script pour générer des synthèses précises de fichiers texte ou Markdown de n'importe quelle taille
- 🧩 **Découpage intelligent par tokens** : Utilise `tiktoken` pour un découpage précis respectant les limites des modèles
- ⚡ **Traitement parallèle par lots** : Optimisation de la vitesse avec traitement simultané des chunks
- 🔗 **Continuité contextuelle** : Maintien du contexte entre les sections pour une synthèse cohérente
- 📝 **Prompts configurables** : Support de différents types de synthèse (concis, détaillé, points d'action, Q&A)
- 📖 **Documentation complète** : README français et anglais avec exemples d'usage détaillés

#### 📚 **Exemples RAG (Retrieval-Augmented Generation)** ✨ *NOUVEAUX EXEMPLES*
- 🆕 **Simple RAG Demo** : Un script pédagogique pour comprendre les mécanismes de base du RAG avec des vecteurs en mémoire.
- 🆕 **RAG with Qdrant Demo** : Un exemple complet et conteneurisé utilisant Qdrant comme base de données vectorielle pour des applications RAG plus robustes.

#### 💬 **Mini-Chat - Chat avec RAG et Outils**
- 🧠 **Support RAG complet** : Intégration avec la base vectorielle Qdrant pour des réponses augmentées par vos documents.
- 🛠️ **Outils intégrés** : Inclut calculatrice, horloge, accès aux fichiers, exécution de commandes shell et recherche RAG.
- ⚙️ **Interface en ligne de commande avancée** : Autocomplétion, historique persistant, et gestion fine des sessions.
- 🚀 **Stabilité et performance** : Version 1.3.1 stable et optimisée.

---

## À propos de LLMaaS Cloud Temple

L'API LLMaaS de Cloud Temple vous permet d'intégrer facilement des modèles de langage dans vos applications. Elle est accessible via la Console Cloud Temple où vous pouvez gérer vos clés API, surveiller votre consommation et configurer vos paramètres.

### Accès rapide à l'API

- **URL de base** : `https://api.ai.cloud-temple.com/v1/`
- **Authentification** : Header `Authorization: Bearer YOUR_API_KEY`
- **Format** : JSON (`Content-Type: application/json`)

### Endpoints principaux

- `/chat/completions` : Génération de réponses conversationnelles
- `/completions` : Complétion de texte simple  
- `/models` : Liste des modèles disponibles

### Exemple de requête cURL

```bash
curl -X POST "https://api.ai.cloud-temple.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "granite3.3:8b",
    "messages": [
      {
        "role": "user", 
        "content": "Salut ! Peux-tu te présenter en français ?"
      }
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

### Paramètres disponibles

| Paramètre     | Type    | Description                               |
| ------------- | ------- | ----------------------------------------- |
| `model`       | string  | Le modèle à utiliser                      |
| `messages`    | array   | Liste des messages de la conversation     |
| `max_tokens`  | integer | Nombre maximum de tokens à générer        |
| `temperature` | float   | Contrôle la créativité (0.0-2.0)          |
| `top_p`       | float   | Contrôle la diversité des réponses        |
| `stream`      | boolean | Active le streaming de la réponse         |
| `user`        | string  | Identifiant unique de l'utilisateur final |

## Structure des Exemples

Chaque exemple est organisé dans son propre sous-répertoire avec :
- Un fichier README.md expliquant l'objectif et le fonctionnement
- Les fichiers de code source nécessaires  
- Les fichiers de configuration (`.env.example`, `config.example.json`)
- Les données d'exemple le cas échéant

## 📸 Aperçu Visuel

Découvrez les capacités de l'API LLMaaS Cloud Temple à travers ces captures d'écran des exemples en action :

### 🚀 Streaming en Temps Réel
![Streaming Demo](./screenshoot/streaming_01.png)
*Démonstration du streaming SSE avec affichage token par token et métriques de performance en temps réel*

### 💬 Interface Chat Interactive
![Mini Chat Interface](./screenshoot/minichat_01.png)
*Interface de chat en ligne de commande avec sélection de modèle et configuration des paramètres*

![Mini Chat Conversation](./screenshoot/minichat_02.png)
*Conversation en cours avec l'assistant IA, affichage des tokens et statistiques de performance*

![Mini Chat Tools](./screenshoot/minichat_03.png)
*Utilisation d'outils intégrés (calculatrice, lecture de fichiers, commandes shell) dans le chat*

### 🎵 Transcription Audio Avancée
![Transkryptor Interface](./screenshoot/transkryptor_01.png)
*Interface de transcription audio avec barre de progression et prévisualisation en temps réel*

![Transkryptor Results](./screenshoot/transkryptor_02.png)
*Résultats de transcription avec découpage intelligent et traitement par lots parallèles*

### 📸 Analyse d'Images Multimodale
![PhotoAnalyzer Journal](./photoanalyzer/images/journal.png)
*Image originale d'un journal pour l'analyse multimodale*

![PhotoAnalyzer Vision 1](./screenshoot/journal1.png)
*Première vision du modèle sur l'image du journal*

![PhotoAnalyzer Vision 2](./screenshoot/journal2.png)
*Deuxième vision du modèle sur l'image du journal*

### 📚 Démonstration RAG Simple
![Simple RAG Demo](./screenshoot/simple_rag.png)
*Exécution du script RAG simple, montrant les étapes de vectorisation, recherche et génération augmentée*

## Exemples Disponibles

### 📸 [PhotoAnalyzer](./photoanalyzer/)
PhotoAnalyzer est un outil CLI Python avancé pour l'analyse d'images utilisant l'API LLMaaS avec des modèles multimodaux. Il offre une interface utilisateur soignée avec modes debug, formats de sortie multiples, et support de différents types de prompts d'analyse spécialisés.

### 🔍 [GetFact](./getfact/) 
Extracteur de faits et relations intelligent utilisant l'API LLMaaS. Capable d'extraire automatiquement entités, événements, relations, attributs, informations temporelles et spatiales d'un texte. Supporte les ontologies métier spécialisées (Droit, RH, DevOps, Sécurité, Infrastructure, Infogérance) pour une extraction contextuelle optimisée.

### 📝 [Summarizer](./summarizer/)
Outil de synthèse de texte avancé utilisant l'API LLMaaS. Génère des synthèses précises de fichiers texte ou Markdown de n'importe quelle taille avec découpage intelligent par tokens, traitement parallèle par lots, et continuité contextuelle entre les sections.

### 📚 [Simple RAG Demo](./simple_rag_demo/)
Démonstrateur RAG pédagogique pour illustrer le fonctionnement du Retrieval-Augmented Generation. Utilise l'API LLMaaS pour l'embedding et la génération, avec stockage des vecteurs en mémoire pour une compréhension claire du processus.

### 📚 [RAG with Qdrant Demo](./rag-granite-qdrant-demo/)
Démonstrateur RAG complet et conteneurisé utilisant Qdrant comme base de données vectorielle. L'API LLMaaS est utilisée pour l'embedding des documents et la génération de réponses augmentées.

### 📝 [List Models](./list_models/)
Script simple pour lister tous les modèles disponibles via l'API LLMaaS avec leurs détails, spécifications et statuts.

### 🚀 [Streaming Demo](./streaming-demo/)
Exemple minimal pour démontrer le streaming en temps réel avec l'API LLMaaS. Montre l'activation du streaming SSE (Server-Sent Events), l'affichage token par token, et le calcul des métriques de performance.

### 💬 [Mini Chat](./mini-chat/)
Client de chat en ligne de commande interactif et avancé. Il supporte non seulement les conversations standards avec les modèles LLM, mais intègre également un **système RAG complet** via Qdrant et **23 outils intégrés** (calculatrice, shell, gestion de fichiers, etc.). Idéal pour des cas d'usage complexes nécessitant à la fois conversation et exécution de tâches.

### 🧪 [Test API Models](./test_api_models/)
Script Python pour tester et comparer des modèles LLM via API avec configuration externe, découverte dynamique, sélection de modèles, gestion d'erreurs et résumé des performances.

### 🧪 [Test API Models PowerShell](./test_api_models_powershell/)
Version PowerShell du script de test des modèles, similaire à la version Python mais adaptée aux environnements Windows.

### 🎤 [Whisper](./whisper/)
Exemple d'utilisation de l'API de transcription audio (ASR) avec client Python, démontrant la conversion audio vers texte.

### 🌐 [Translate](./translate/)
Script Python pour traduire des fichiers texte par segments, utilisant un modèle LLM et conservant le contexte entre les segments pour des traductions cohérentes.

### 🎵 [Transkryptor](./transkryptor/)
Outil CLI Python avancé pour la transcription de fichiers audio volumineux, utilisant le découpage intelligent, le traitement par lots parallèles, la normalisation audio et une interface utilisateur soignée.

## Configuration

Chaque exemple inclut un fichier `.env.example` que vous devez copier vers `.env` et remplir avec vos paramètres :

```bash
# Dans chaque dossier d'exemple
cp .env.example .env
# Éditez .env avec votre clé API Cloud Temple
```

## Prérequis

- Python 3.7+
- Clé API LLMaaS Cloud Temple
- Accès à la Console Cloud Temple

## Support

Pour toute question concernant l'API LLMaaS Cloud Temple, consultez la documentation officielle ou contactez le support Cloud Temple.

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Licence

Ces outils sont sous licence GPL 3.0 - voir le fichier [LICENSE](LICENSE) pour plus de détails.
