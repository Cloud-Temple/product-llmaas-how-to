# Exemple : Lister les Modèles LLMaaS avec Style

Ce script Python (`list_models.py`) est un exemple élégant pour interroger l'endpoint `/v1/models` de l'**API LLMaaS Cloud Temple** et afficher la liste des modèles disponibles dans un tableau bien formaté en utilisant la bibliothèque `rich`, avec une catégorisation fonctionnelle des modèles.

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Fonctionnalités

- Chargement de la configuration (URL de l'API et token) depuis un fichier `.env`.
- Appel à l'API LLMaaS pour récupérer la liste des modèles.
- Gestion des erreurs de connexion et des réponses HTTP.
- Affichage des modèles dans un tableau clair et coloré, triés par ID.
- Catégorisation fonctionnelle des modèles (Langage Généraliste, Embedding, Vision, OCR, etc.).
- Indication visuelle de la progression lors de l'appel API.

## Prérequis

- Python 3.7+
- Les dépendances listées dans `requirements.txt`

## Installation

1.  **Clonez le dépôt** (si ce n'est pas déjà fait) :
    ```bash
    git clone <url_du_depot_llmaas>
    cd chemin/vers/llmaas/exemples/list_models_pretty
    ```

2.  **Créez un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installez les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurez vos identifiants API** :
    - Copiez le fichier `.env.example` en `.env` :
      ```bash
      cp .env.example .env
      ```
    - Modifiez le fichier `.env` avec votre URL d'API LLMaaS et votre token d'accès :
      ```env
      LLMAAS_API_URL="https://votre-api.llmaas.com"
      LLMAAS_API_TOKEN="votre_token_personnel"
      ```

## Utilisation

Une fois l'installation et la configuration terminées, exécutez simplement le script :

```bash
python list_models.py
```

Le script affichera un tableau listant les modèles disponibles, avec leur ID, propriétaire, type d'objet, **type de modèle (catégorie fonctionnelle)**, date de création et alias.

## Structure du Répertoire

```
list_models_pretty/
├── .env.example        # Exemple de fichier de configuration d'environnement
├── list_models.py      # Le script Python principal
├── README.md           # Ce fichier d'instructions
└── requirements.txt    # Liste des dépendances Python
```

## Personnalisation

- **URL de l'API et Token** : Modifiez le fichier `.env` pour pointer vers votre instance LLMaaS.
- **Affichage du Tableau** : Le script utilise `rich.table.Table`. Vous pouvez personnaliser les colonnes, les styles et le tri directement dans la fonction `display_models_table` du script `list_models.py`.
- **Catégorisation des Modèles** : La fonction `categorize_model()` dans `list_models.py` détermine la catégorie fonctionnelle de chaque modèle. Vous pouvez modifier cette fonction pour adapter la logique de catégorisation à vos besoins.

---

Développé avec soin par Cline.
