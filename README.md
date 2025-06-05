# Cas d'Usage LLM as a Service - Cloud Temple

Ce répertoire contient une collection d'exemples de code et de scripts démontrant les différentes fonctionnalités et cas d'utilisation de **l'offre LLM as a Service (LLMaaS) de Cloud Temple**.

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

### 🔌 API en Action
![Test API Models](./screenshoot/api_01.png)
*Script de test des modèles LLM montrant la comparaison de performances entre différents modèles disponibles sur l'API Cloud Temple*

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

## Exemples Disponibles

### 🔍 [GetFact](./getfact/) 
Extracteur de faits et relations intelligent utilisant l'API LLMaaS. Capable d'extraire automatiquement entités, événements, relations, attributs, informations temporelles et spatiales d'un texte. Supporte les ontologies métier spécialisées (Droit, RH, DevOps, Sécurité, Infrastructure, Infogérance) pour une extraction contextuelle optimisée.

### 📝 [List Models](./list_models/)
Script simple pour lister tous les modèles disponibles via l'API LLMaaS avec leurs détails, spécifications et statuts.

### 🚀 [Streaming Demo](./streaming-demo/)
Exemple minimal pour démontrer le streaming en temps réel avec l'API LLMaaS. Montre l'activation du streaming SSE (Server-Sent Events), l'affichage token par token, et le calcul des métriques de performance.

### 💬 [Mini Chat](./mini-chat/)
Client de chat en ligne de commande interactif pour converser avec les modèles LLM, supportant l'historique, les prompts système, la sauvegarde/chargement de session et l'utilisation d'outils.

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
