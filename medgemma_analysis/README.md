# Exemple d'Analyse d'Image Médicale avec MedGemma

Ce répertoire contient un exemple d'utilisation du modèle **MedGemma** (basé sur Gemma 3) pour l'analyse d'images médicales via l'API LLMaaS.

## Contenu

- `analyze_medical_image.py` : Le script Python principal.
- `radio.png` : Une image de radiographie d'exemple (fournie).
- `requirements.txt` : Les dépendances Python nécessaires.

## Prérequis

1.  Avoir Python 3.8+ installé.
2.  Avoir une clé API LLMaaS valide.

## Installation

1.  Créez un environnement virtuel (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

3.  Configurez votre clé API :
    Créez un fichier `.env` à la racine de ce répertoire (ou exportez les variables d'environnement) :
    ```bash
    API_KEY=votre_cle_api_ici
    API_URL=https://api.ai.cloud-temple.com/v1
    ```
    *(Vous pouvez copier `.env.example` s'il existe)*

## Utilisation

Pour analyser l'image d'exemple `radio.png` :

```bash
python analyze_medical_image.py radio.png
```

Pour ajouter un contexte médical spécifique (ex: âge, symptômes) :

```bash
python analyze_medical_image.py radio.png --context "Patient de 74 ans avec douleurs très fortes au poignet"
```

Pour activer le mode streaming (affichage progressif de la réponse) :

```bash
python analyze_medical_image.py radio.png --stream
```

## Fonctionnement

Le script :
1.  Encode l'image fournie en Base64.
2.  Construit une requête multimodale (Texte + Image) pour l'API.
3.  Utilise le modèle `medgemma:27b`.
4.  Envoie un prompt spécifique demandant une analyse détaillée des structures anatomiques et des anomalies potentielles.
5.  Affiche la réponse du modèle formatée en Markdown dans la console.
