# Démonstrateur API de Statut LLMaaS

Ce répertoire contient un exemple d'utilisation de l'API publique de statut de la plateforme LLMaaS Cloud Temple.

## Objectif

L'objectif de ce script est de fournir aux développeurs un exemple concret d'intégration pour :
1.  **Surveiller l'état de santé global** de la plateforme LLMaaS.
2.  **Récupérer les métriques de performance en temps réel** (TTFB, Débit) pour chaque modèle.
3.  **Estimer la consommation énergétique** des requêtes, en combinant les données d'usage de l'API avec les spécifications énergétiques des modèles (kWh/million de tokens).

## Prérequis

- Python 3.8+
- Accès Internet (pour joindre `https://llmaas.status.cloud-temple.app`)

## Installation

1.  Créer un environnement virtuel (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

Lancer le script de tableau de bord :

```bash
python3 status_dashboard.py
```

### Options

Vous pouvez spécifier une liste restreinte de modèles à vérifier via l'option `--models` :

```bash
python3 status_dashboard.py --models "llama3.3:70b,mistral-large-3:675b"
```

## Fonctionnement Technique

Le script interroge deux endpoints de l'API publique :

1.  `GET /api/platform-status` : Pour obtenir l'état global (`operational`, `degraded`, etc.) et la liste des modèles en échec.
2.  `GET /api/platform-status?model=<model_id>` : Pour obtenir les métriques détaillées d'un modèle spécifique.

### Données Énergétiques

L'API de statut actuelle fournit les métriques d'utilisation (tokens) et de performance (vitesse), mais ne fournit pas directement le coefficient de consommation énergétique par modèle.

Ce script intègre donc une **base de connaissances locale** (`MODEL_ENERGY_MAP`) contenant les valeurs de consommation (en kWh par million de tokens) issues de la documentation technique de la plateforme. Il utilise ces valeurs pour calculer une estimation de la consommation énergétique pour la requête de test (sonde) effectuée par l'API de statut.

**Formule de calcul :**
```
Énergie (Wh) = (Total Tokens / 1 000 000) * Conso_Modèle (kWh/M) * 1000
```
