# Traducteur de Documents Intelligent (LLMaaS)

Ce script Python permet de traduire des documents texte de n'importe quelle taille en utilisant l'API LLMaaS de Cloud Temple.

## Fonctionnalités Clés

-   **Support de tous les modèles** : Compatible avec Qwen, Mistral, Llama, et spécifiquement optimisé pour **TranslateGemma**.
-   **Découpage Intelligent (Chunking)** : Gère les documents dépassant la fenêtre de contexte du modèle en les découpant intelligemment par paragraphes, sans couper les phrases.
-   **Contexte Glissant** : Maintient la cohérence de la traduction (style, terminologie) entre les segments.
-   **Mode Interactif** : Permet de valider ou corriger la traduction segment par segment.
-   **Robuste** : Gestion des erreurs API et sauvegarde automatique.

## Prérequis

-   Python 3.7+
-   Une clé API LLMaaS Cloud Temple

## Installation

1.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

2.  Configurez votre clé API (optionnel, peut être passée en ligne de commande) :
    ```bash
    cp .env.example .env
    # Éditez .env pour y mettre votre clé API
    ```

## Utilisation

### Exemples de données

Un fichier texte d'exemple est fourni dans `data/example_text_en.txt`. Il contient un texte structuré sur l'Intelligence Artificielle et le RAG, idéal pour tester le chunking.

### Traduction Standard

Pour traduire un fichier en utilisant un modèle généraliste (ex: Qwen, Mistral) :

```bash
python translate.py --file data/example_text_en.txt --target-language fr --model qwen3:14b
```

### Utilisation avec TranslateGemma

TranslateGemma nécessite un format de prompt spécifique. Le script le détecte automatiquement si le nom du modèle contient "translategemma", ou vous pouvez le forcer.
**Note :** Pour TranslateGemma, il est recommandé de spécifier la langue source.

```bash
python translate.py \
  --file data/example_text_en.txt \
  --model translategemma:27b \
  --source-language en \
  --target-language fr
```

### Options Disponibles

| Argument | Description | Défaut |
| :--- | :--- | :--- |
| `--file` | Chemin du fichier à traduire (requis). | - |
| `--target-language` | Code ISO de la langue cible (ex: `fr`, `es`). | - |
| `--source-language` | Code ISO de la langue source (ex: `en`). Requis pour TranslateGemma. | `en` |
| `--model` | Nom du modèle LLM à utiliser. | `qwen3:14b` |
| `--prompt-format` | Format du prompt : `auto` (détection), `standard` (chat), `translategemma`. | `auto` |
| `--chunk-size-words` | Taille cible des segments en mots. | `300` |
| `--max-tokens` | Limite de tokens pour la réponse (traduction). | `2048` |
| `--interactive` | Active le mode interactif pour valider chaque chunk. | `False` |
| `--list-languages` | Affiche la liste des 55+ langues supportées. | - |
| `--debug` | Affiche des détails sur le découpage du texte. | `False` |

### Exemple de Chunking

Pour voir comment le script découpe votre texte sans lancer la traduction (mode debug), utilisez un modèle factice ou coupez le réseau, ou utilisez simplement l'option `--debug` avec un petit fichier.

Le script essaie de :
1.  Couper aux doubles sauts de ligne (paragraphes).
2.  Regrouper les paragraphes pour approcher `chunk_size_words`.
3.  Si un paragraphe est trop gros, il le coupe proprement aux espaces.

## Dépannage

-   **Erreur 401** : Vérifiez votre clé API.
-   **Erreur 429** : Vous dépassez les quotas de débit. Le script ne gère pas le "backoff" automatique complexe, relancez plus tard.
-   **Traduction coupée** : Augmentez `--max-tokens` ou réduisez `--chunk-size-words`.
