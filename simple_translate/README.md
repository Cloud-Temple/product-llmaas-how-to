# Exemple de Traduction avec TranslateGemma

Ce script illustre comment utiliser les modèles **TranslateGemma** (4B, 12B, 27B) disponibles via l'API LLMaaS.

Contrairement aux modèles de chat standards, TranslateGemma nécessite un **format de prompt très spécifique** pour fonctionner correctement. Ce script implémente ce format et vous permet de traduire du texte facilement.

## Prérequis

- Python 3.7+
- Une clé API Cloud Temple LLMaaS

## Installation

1.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

2.  Configurez votre environnement :
    Copiez le fichier `.env.example` en `.env` et ajoutez votre clé API.
    ```bash
    cp .env.example .env
    # Éditez .env avec votre éditeur favori
    ```

## Utilisation

Le script contient un exemple simple de traduction Anglais vers Français.

```bash
python simple_translate.py
```

## Personnalisation

Vous pouvez modifier le script `simple_translate.py` pour changer :
- Le texte à traduire (`text_to_translate`).
- Les langues source et cible (`source_lang`, `source_code`, `target_lang`, `target_code`).
- Le modèle utilisé (via la variable d'environnement `LLMAAS_MODEL` ou directement dans le code).

**Note sur le modèle :** Par défaut, le script utilise `translategemma:27b`. Assurez-vous que ce modèle est disponible ou changez pour `translategemma:4b` ou `translategemma:12b` selon vos besoins.
