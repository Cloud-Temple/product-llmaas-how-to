# Outil de Synthèse de Texte Avancé

Cet outil Python permet de générer des synthèses précises de fichiers texte ou Markdown de n'importe quelle taille, en utilisant un Large Language Model (LLM) via l'API LLMaaS. Il gère le découpage intelligent du texte, le traitement parallèle par lots, et la continuité contextuelle entre les sections.

## Fonctionnalités

*   **Découpage par Tokens** : Utilise `tiktoken` pour un découpage précis en tokens, garantissant que les chunks respectent les limites des modèles.
*   **Traitement Parallèle par Lots** : Les chunks sont regroupés en lots, et les requêtes LLM pour les chunks d'un même lot sont exécutées en parallèle pour optimiser la vitesse.
*   **Continuité Contextuelle** : Option (activée par défaut) pour inclure le résumé du lot précédent dans le prompt du LLM pour le lot actuel, assurant une synthèse cohérente sur de très longs documents.
*   **Synthèse Finale Unifiée** : Par défaut, le script effectue une passe de synthèse finale sur l'ensemble des synthèses de chunks. Cette étape est particulièrement utile pour les documents longs (générant de nombreux chunks) afin de créer un résumé unifié et cohérent. Elle peut être désactivée avec l'option `--no-final-summary`.
*   **Prompts Configurables** : Utilise un fichier `prompts.yaml` pour définir différents types de prompts de synthèse (ex: concis, détaillé, points d'action, Q&A), y compris le prompt pour la synthèse finale.
*   **Barres de Progression Visuelles** : Affiche une barre de progression esthétique avec `rich.progress` pour un suivi clair de l'avancement.
*   **Mode Debug** : Un mode debug configurable via variable d'environnement permet d'afficher les payloads des requêtes et réponses LLM pour faciliter le débogage.
*   **Configuration Flexible** : Les paramètres de l'API LLMaaS et le modèle par défaut sont configurables via un fichier `.env`. Les paramètres de chunking, de traitement par lots et de génération LLM sont configurables via les arguments de ligne de commande.
*   **Nettoyage des Réponses** : Gère automatiquement la suppression des balises `<think>...</think>` des réponses des LLM raisonneurs.

## Prérequis

*   Python 3.8+
*   `pip` (gestionnaire de paquets Python)

## Installation

1.  **Cloner le dépôt** (si ce n'est pas déjà fait) :
    ```bash
    git clone [URL_DU_DEPOT]
    cd [NOM_DU_DEPOT]/exemples/summarizer
    ```
2.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate # Sur Linux/macOS
    # venv\Scripts\activate # Sur Windows
    ```
3.  **Installer les dépendances Python** :
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Fichier `.env`** :
    Créez un fichier nommé `.env` dans le répertoire `exemples/summarizer/` en vous basant sur le fichier `exemples/summarizer/.env.example`.

    ```bash
    cp .env.example .env
    ```
    Modifiez le fichier `.env` pour configurer l'URL de votre API LLMaaS et votre clé d'API :
    ```dotenv
    LLMAAS_API_BASE_URL=http://localhost:8000/v1
    LLMAAS_API_KEY=votre_cle_api_ici
    LLMAAS_DEFAULT_MODEL=gemma3:8b
    DEBUG_MODE=false
    ```

2.  **Fichier `prompts.yaml`** :
    Ce fichier contient les définitions des prompts de synthèse. Vous pouvez ajouter ou modifier des prompts selon vos besoins.
    Exemple de structure :
    ```yaml
    concise_summary:
      system_prompt: |
        Vous êtes un assistant expert en synthèse. Votre tâche est de fournir un résumé concis et précis du texte fourni.
        Concentrez-vous sur les points clés et les informations essentielles.
      user_template: |
        Veuillez synthétiser le texte suivant de manière concise :
        ---
        {text}
        ---
    ```
    Le `{text}` dans `user_template` est un placeholder qui sera remplacé par le contenu du chunk.

## Utilisation

Exécutez le script `summarizer.py` directement depuis le répertoire `exemples/summarizer/` :

```bash
python3 summarizer.py --input chemin/vers/votre_fichier.md --output ma_synthese.md --prompt concise_summary --model gemma3:8b
```

### Arguments de la ligne de commande

*   `--input`, `-i` (obligatoire) : Chemin vers le fichier texte/Markdown d'entrée à synthétiser.
*   `--output`, `-o` (optionnel) : Chemin vers le fichier de sortie où la synthèse sera écrite. Par défaut : `summary.md`.
*   `--model`, `-m` (optionnel) : Nom du modèle LLM à utiliser. Par défaut, utilise la valeur de `LLMAAS_DEFAULT_MODEL` dans `.env`.
*   `--prompt`, `-p` (obligatoire) : Nom du prompt de synthèse à utiliser, tel que défini dans `prompts.yaml` (ex: `concise_summary`, `detailed_summary`).
*   `--chunk_size`, `-cs` (optionnel) : Taille maximale d'un chunk en tokens. Par défaut : `2000`.
*   `--chunk_overlap`, `-co` (optionnel) : Nombre de tokens de chevauchement entre les chunks. Par défaut : `200`.
*   `--max_tokens_per_chunk`, `-mt` (optionnel) : Nombre maximal de tokens que le LLM doit générer pour chaque chunk. Par défaut : `500`.
*   `--batch_size`, `-bs` (optionnel) : Nombre de chunks à traiter en parallèle par lot. Par défaut : `5`.
*   `--no_previous_summary_context`, `-npc` (flag) : Si présent, désactive l'inclusion du résumé du lot précédent dans le contexte du LLM. Par défaut, le contexte est inclus.

### Exemple d'exécution

```bash
# Pour une synthèse concise d'un fichier d'exemple
python3 summarizer.py -i ../../README.md -o readme_summary.md -p concise_summary -m gemma3:8b

# Pour une synthèse détaillée sans contexte précédent, avec un batch_size plus grand
python3 summarizer.py -i long_document.txt -o detailed_report.md -p detailed_summary -m deepseek-r1:32b -bs 10 --no_previous_summary_context

# Pour extraire les points d'action d'une réunion
python3 summarizer.py -i meeting_notes.md -o action_items.txt -p action_items -m cogito:14b
```

## Débogage

Activez le mode debug en définissant `DEBUG_MODE=true` dans votre fichier `.env`. Cela affichera les payloads JSON envoyés et reçus de l'API LLMaaS dans la console, ce qui est utile pour le débogage.

```dotenv
DEBUG_MODE=true
```

## Structure du Projet

```
exemples/
└── summarizer/
    ├── summarizer.py           # Script principal contenant toute la logique
    ├── .env.example            # Exemple de fichier d'environnement
    ├── prompts.yaml            # Définition des prompts de synthèse
    ├── requirements.txt        # Dépendances Python
    └── README.md               # Documentation du script
