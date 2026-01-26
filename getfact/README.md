# GetFact - Extracteur de Faits et Relations

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LLMaaS](https://img.shields.io/badge/LLMaaS-Compatible-green.svg)

Ce script permet d'extraire automatiquement les faits et les relations entre faits d'un fichier texte en utilisant l'API LLMaaS de Cloud Temple. Il peut optionnellement utiliser une ontologie fournie pour améliorer la précision de l'extraction et sauvegarde les résultats au format JSON ou YAML.

## 🌟 Fonctionnalités

- **Extraction intelligente** : Identifie automatiquement les entités, événements, relations, attributs, informations temporelles et spatiales
- **Support d'ontologie** : Utilise optionnellement un fichier d'ontologie (JSON/YAML/TXT) pour guider l'extraction
- **Découpage intelligent** : Traite les documents longs en les découpant en chunks logiques
- **Formats de sortie** : Sauvegarde au format JSON ou YAML avec structure organisée
- **Mode interactif** : Validation/modification possible de l'extraction de chaque chunk
- **Interface riche** : Affichage coloré avec barres de progression et résumés détaillés
- **Configuration flexible** : Paramètres configurables via ligne de commande et variables d'environnement
- **Support des modèles raisonneurs** : Gère automatiquement les réponses des modèles qui incluent des blocs de pensée (ex: `<think>...</think>`) avant le JSON.
- **Parsing JSON robuste** : Extrait de manière fiable le contenu JSON même à partir de réponses malformées ou contenant du texte parasite.

## 🧠 Ontologies Spécialisées

GetFact inclut 6 ontologies métier prêtes à l'emploi pour une extraction contextuelle optimisée. Ces fichiers se trouvent dans le dossier `ontologies/`.

| Ontologie               | Domaine                        | Fichier                               | Description & Usage                                                                                                                                                                                               |
| ----------------------- | ------------------------------ | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🏛️ **Juridique**     | Droit, contentieux, compliance | `ontologie_droit.yaml`                | **Entités** : Avocats, Juges, Articles de loi, Contrats.<br>**Relations** : "enfreint", "stipule que", "poursuit en justice".<br>**Usage** : Analyse de contrats, de jugements, de documents de conformité.       |
| 👥 **RH**              | Ressources humaines, SIRH      | `ontologie_rh.yaml`                   | **Entités** : Candidats, Postes, Compétences, Diplômes.<br>**Relations** : "a pour compétence", "a travaillé chez", "postule pour".<br>**Usage** : Analyse de CV, comptes-rendus d'entretiens, plans de carrière. |
| 💻 **Développement**   | DevOps, ingénierie logicielle  | `ontologie_developpement.yaml`        | **Entités** : Langages, Frameworks, Bugs, Features, PR.<br>**Relations** : "dépend de", "corrige", "implémente".<br>**Usage** : Analyse de documentation technique, tickets Jira, code reviews.                   |
| 🔒 **Sécurité**        | Cybersécurité, RSSI            | `ontologie_securite_logique.yaml`     | **Entités** : Menaces, Vulnérabilités (CVE), Actifs, Attaquants.<br>**Relations** : "exploite", "mitige", "affecte".<br>**Usage** : Rapports d'incidents, audits de sécurité, analyse de menaces.                 |
| ☁️ **Infrastructure** | Cloud, datacenters, réseaux    | `ontologie_infrastructure_cloud.yaml` | **Entités** : VM, Conteneurs, VPC, Load Balancers.<br>**Relations** : "hébergé sur", "connecté à", "protégé par".<br>**Usage** : Rapports d'inventaire, documents d'architecture, logs d'infrastructure.          |
| 🤝 **Infogérance**     | Services managés, ITIL         | `ontologie_infogerance.yaml`          | **Entités** : SLA, Tickets, Incidents, Changements.<br>**Relations** : "résolu par", "escaladé vers", "impacte".<br>**Usage** : Suivi de qualité de service, rapports d'activité, gestion des incidents.          |

### Exemples d'usage par domaine

```bash
# Analyse juridique - contrat commercial
python getfact.py --file contrat.txt --ontology ontologie_droit.yaml

# RH - analyse de CV
python getfact.py --file cv_candidat.txt --ontology ontologie_rh.yaml

# Sécurité - rapport d'incident
python getfact.py --file incident_secu.txt --ontology ontologie_securite_logique.yaml

# Infrastructure - rapport de performance
python getfact.py --file perf_report.txt --ontology ontologie_infrastructure_cloud.yaml
```

## 📋 Types de Faits Extraits

| Type           | Description                                       | Exemples                                  |
| -------------- | ------------------------------------------------- | ----------------------------------------- |
| **Entités**    | Personnes, organisations, lieux, objets, concepts | Jean Dupont, Cloud Temple, Paris, serveur |
| **Événements** | Actions, processus, incidents, situations         | réunion, déploiement, incident, formation |
| **Relations**  | Connexions entre entités                          | travaille pour, situé à, dépend de        |
| **Attributs**  | Propriétés, caractéristiques, qualités            | couleur, taille, performance, statut      |
| **Temporel**   | Dates, durées, séquences temporelles              | 2025-06-04, 2 heures, avant/après         |
| **Spatial**    | Localisations, positions relatives                | nord de, à côté de, datacenter            |

## 🚀 Installation

```bash
# Installation des dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Editez le fichier .env avec vos paramètres
```

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
# Clé API LLMaaS (obligatoire)
LLMAAS_API_KEY=your_api_key_here

# URL de l'API LLMaaS
LLMAAS_API_URL=https://api.ai.cloud-temple.com/v1

# Modèle à utiliser pour l'extraction
LLMAAS_GETFACT_MODEL=qwen3:14b

# Format de sortie par défaut (json ou yaml)
LLMAAS_OUTPUT_FORMAT=json

# Nombre maximum de tokens pour les réponses
# Recommandé : 16384 pour réduire le risque de réponses tronquées (finish_reason=length)
LLMAAS_MAX_TOKENS=16384

# Taille des chunks en mots
LLMAAS_CHUNK_SIZE_WORDS=500

# Répertoire de sortie
LLMAAS_OUTPUT_DIR=extracted_facts

# Prompt système personnalisé optionnel
LLMAAS_CUSTOM_PROMPT=""
```

## 💡 Utilisation

### Utilisation basique

```bash
# Extraction simple d'un fichier texte
python getfact.py --file document.txt

# Avec ontologie pour guider l'extraction
python getfact.py --file document.txt --ontology exemple_ontologie.yaml

# Sortie en format YAML
python getfact.py --file document.txt --output-format yaml
```

### Options avancées

```bash
# Mode interactif avec validation
python getfact.py --file document.txt --interactive

# Types de faits spécifiques
python getfact.py --file document.txt --fact-types entities events relationships

# Modèle et paramètres personnalisés
python getfact.py --file document.txt --model granite3:8b --max-tokens 2048

# Mode debug pour voir le découpage
python getfact.py --file document.txt --debug

# Avec prompt système personnalisé
python getfact.py --file document.txt --custom-prompt "Concentrez-vous sur les aspects financiers et les montants"
```

### Prompt système personnalisé

La fonctionnalité de prompt personnalisé permet d'ajouter des instructions spécifiques pour guider l'extraction selon vos besoins :

```bash
# Focus sur la conformité réglementaire
python getfact.py --file audit_report.txt \
  --custom-prompt "Portez une attention particulière aux non-conformités, références réglementaires et actions correctives"

# Extraction orientée performance
python getfact.py --file system_logs.txt \
  --custom-prompt "Identifiez prioritairement les métriques de performance, temps de réponse et goulots d'étranglement"

# Analyse de sentiment dans les retours clients
python getfact.py --file feedback_clients.txt \
  --custom-prompt "Extrayez les émotions, sentiments positifs/négatifs et niveau de satisfaction client"
```

**Via variable d'environnement :**
```bash
export LLMAAS_CUSTOM_PROMPT="Focalisez sur les risques opérationnels et financiers"
python getfact.py --file risk_assessment.txt
```

### Aide et version

```bash
# Afficher l'aide complète
python getfact.py --help

# Afficher la version
python getfact.py --version
```

## 📄 Formats de Fichiers

### Fichier d'entrée
- **Formats supportés** : TXT, MD, ou tout fichier texte UTF-8
- **Taille** : Découpage automatique en chunks pour les gros documents
- **Encodage** : UTF-8 recommandé

### Ontologie (optionnelle)
L'ontologie peut être fournie dans plusieurs formats :

#### JSON
```json
{
  "entities": {
    "person": ["nom", "prénom", "titre"],
    "organization": ["nom", "type", "secteur"],
    "location": ["ville", "pays", "région"]
  },
  "relationships": {
    "employment": ["travaille pour", "employé par"],
    "location": ["situé à", "basé à"],
    "hierarchy": ["dirige", "supervise"]
  }
}
```

#### YAML
```yaml
entities:
  person:
    - nom
    - prénom  
    - titre
  organization:
    - nom
    - type
    - secteur
relationships:
  employment:
    - "travaille pour"
    - "employé par"
```

#### TXT (format libre)
```
Types d'entités importantes :
- Personnes : nom, prénom, fonction
- Organisations : nom, secteur d'activité
- Lieux : ville, pays

Relations à identifier :
- Hiérarchie : qui dirige qui
- Localisation : où se trouve quoi
- Temporalité : quand se passe quoi
```

## 📊 Format de Sortie

### Structure JSON/YAML

```json
{
  "facts": [
    {
      "id": "fact_1",
      "type": "entity",
      "content": "Jean Dupont est ingénieur DevOps",
      "entities_involved": ["Jean Dupont", "ingénieur DevOps"],
      "confidence": 0.95,
      "source_text": "Jean Dupont, ingénieur DevOps chez Cloud Temple",
      "context": "Présentation de l'équipe",
      "chunk_source": 1
    }
  ],
  "relationships": [
    {
      "id": "rel_1",
      "type": "employment",
      "source_fact_id": "fact_1",
      "target_fact_id": "fact_2",
      "relationship_description": "Jean Dupont travaille pour Cloud Temple",
      "confidence": 0.90,
      "chunk_source": 1
    }
  ],
  "summary": {
    "total_facts": 42,
    "total_relationships": 15,
    "fact_types_count": {
      "entity": 18,
      "event": 12,
      "relationship": 8,
      "attribute": 4
    },
    "main_entities": ["Jean Dupont", "Cloud Temple", "Paris"],
    "key_themes": ["infrastructure", "équipe", "projet"],
    "chunks_processed": 3
  },
  "metadata": {
    "extraction_version": "1.0.0",
    "timestamp": "2025-06-04T20:15:30",
    "source_file": "document.txt"
  }
}
```

## 🎯 Exemples d'Usage

### Analyse de CV
```bash
python getfact.py --file cv_candidat.txt --fact-types entities attributes temporal
```

### Analyse de rapport d'incident
```bash
python getfact.py --file incident_report.txt --ontology exemple_ontologie.yaml --interactive
```

### Extraction pour base de connaissances
```bash
python getfact.py --file documentation.md --output-format yaml --chunk-size-words 800
```

## 🔧 Modèles Recommandés

| Modèle           | Usage              | Avantages                          |
| ---------------- | ------------------ | ---------------------------------- |
| `qwen3:14b`      | Usage général      | Bon équilibre précision/vitesse    |
| `granite3:8b`    | Documents courts   | Rapide, efficace                   |
| `deepseek-r1:7b` | Analyse complexe   | Raisonnement avancé                |
| `cogito:7b`      | Textes spécialisés | Excellent pour domaines techniques |

## 📈 Optimisation des Performances

### Paramètres recommandés selon la taille du document

| Taille document | chunk-size-words | max-tokens | Modèle      |
| --------------- | ---------------- | ---------- | ----------- |
| < 1000 mots     | 500              | 4096       | granite3:8b |
| 1000-5000 mots  | 400              | 8192       | qwen3:14b   |
| > 5000 mots     | 300              | 16384      | qwen3:14b   |

### Conseils d'optimisation
- **Ontologie** : Utilisez une ontologie spécialisée pour votre domaine
- **Chunks** : Réduisez la taille pour des textes denses en informations
- **Mode interactif** : Utilisez-le pour affiner votre approche sur de petits échantillons
- **Types de faits** : Limitez aux types pertinents pour votre cas d'usage

## 🐛 Dépannage

### Erreurs courantes

**Erreur de clé API**
```
Erreur: La variable d'environnement LLMAAS_API_KEY n'est pas définie.
```
→ Vérifiez votre fichier `.env` et la valeur de `LLMAAS_API_KEY`

**Réponse JSON invalide**
```
Attention: Réponse JSON invalide pour le chunk 2
```
→ Le script est maintenant plus robuste et tente d'extraire le JSON même si la réponse est malformée.

### Cas particulier : réponse tronquée (`finish_reason=length`)
Sur des chunks volumineux, le modèle peut produire une réponse trop longue, qui est **tronquée** par l'API. Cela se manifeste souvent par :
- `finish_reason=length` côté API
- des erreurs JSON du type `Unterminated string` ou `Expecting property name enclosed in double quotes`

✅ **Mitigation implémentée** : le script détecte automatiquement ce cas et relance une seconde requête **plus concise** (retry) afin d'obtenir un JSON complet.

💡 **Conseils complémentaires** si vous rencontrez encore le problème :
- Réduire la taille des chunks : `--chunk-size-words 250`
- Réduire le nombre de types de faits : `--fact-types entities events relationships`
- Utiliser un modèle plus concis / plus adapté

**Timeout API**
```
Erreur API pour le chunk 1: timeout
```
→ Le modèle peut être surchargé, réessayez ou changez de modèle

### Mode debug
Utilisez `--debug` pour un diagnostic avancé. Cette option active des logs très détaillés, incluant :
- Le découpage précis du texte en chunks.
- Le `payload` JSON complet envoyé à l'API pour chaque chunk.
- La réponse brute (code de statut, en-têtes et corps) reçue de l'API.

```bash
# Activer le mode de débogage pour une analyse approfondie
python getfact.py --file document.txt --debug
```

## 🤝 Contribution

Cet exemple fait partie du projet LLMaaS de Cloud Temple. Pour toute suggestion d'amélioration :

1. Ouvrez une issue pour discuter des changements proposés
2. Respectez le style de code et les conventions existantes
3. Testez vos modifications avec différents types de documents
4. Documentez les nouvelles fonctionnalités

## 📄 Licence

Ce script est distribué sous la même licence que le projet LLMaaS principal.