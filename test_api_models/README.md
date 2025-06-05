# Script Python Avancé pour Tester l'API LLMaaS Cloud Temple

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Objectif
Ce script Python (`test_api_models.py`) permet de tester et comparer les réponses de différents modèles de langage (LLM) accessibles via l'**API LLMaaS Cloud Temple**. Il offre des fonctionnalités avancées pour la configuration, la sélection des modèles, la personnalisation des requêtes et l'affichage des résultats. Il s'agit d'une adaptation du script PowerShell original.

## Fonctionnalités
1.  **Configuration Externe :** Lit l'endpoint de l'API et le token d'authentification depuis un fichier `config.json`. Permet également de définir des valeurs par défaut pour les passes, la température, le nombre max de tokens et le timeout.
2.  **Découverte Dynamique des Modèles :** Récupère automatiquement la liste des modèles disponibles depuis l'endpoint `/models` de l'API.
3.  **Sélection des Modèles :** Permet de spécifier les modèles à tester via l'argument `--models` (liste d'IDs séparés par des virgules). Si omis, tous les modèles disponibles sont testés.
4.  **Personnalisation du Prompt :** Le prompt envoyé aux modèles peut être défini via l'argument `--prompt`.
5.  **Tests Multiples :** Effectue un nombre configurable de passes (requêtes) pour chaque modèle (argument `--passes`) pour évaluer la cohérence et la performance.
6.  **Paramètres de Génération :** Permet de contrôler la température (`--temperature`) et le nombre maximum de tokens (`--max-tokens`) pour les requêtes.
7.  **Mode Debug :** Une option `--debug` active l'affichage d'informations détaillées sur les requêtes, les réponses et les erreurs, y compris le corps des réponses d'erreur de l'API.
8.  **Gestion d'Erreurs Améliorée :** Intercepte les erreurs API (par ex. 403 Forbidden) et tente d'extraire et d'afficher le message détaillé fourni dans la réponse JSON (par ex. "Prompt blocked for security reasons") sans planter le script.
9.  **Sortie Colorée :** Utilise des couleurs (via la bibliothèque `rich`) pour distinguer les informations, les succès et les échecs dans la console.
10. **Tableau Récapitulatif :** Affiche un résumé final (via `rich.table`) comparant les performances (succès, erreurs, temps moyen, temps total, tokens/seconde, etc.) de chaque modèle testé.
11. **Parallélisme des Modèles :** Permet de tester plusieurs modèles simultanément pour accélérer le processus (argument `--parallel-models`).
12. **Parallélisme des Requêtes :** Permet d'envoyer plusieurs requêtes en parallèle à un même modèle pour tester sa capacité à gérer la charge (argument `--parallel-requests`).
13. **Statistiques Détaillées :** Affiche des informations sur les tokens par seconde et les détails du backend (si fournis par l'API) pour chaque réponse.

## Prérequis
-   Python 3.7+
-   Les bibliothèques listées dans `requirements.txt` (principalement `requests` et `rich`). Installez-les avec :
    ```bash
    pip install -r requirements.txt
    ```
-   Un fichier `config.json` dans le même répertoire que le script, contenant au minimum :
    ```json
    {
        "api": {
            "endpoint": "URL_DE_VOTRE_API",
            "token": "VOTRE_TOKEN_BEARER"
        }
    }
    ```
    Optionnellement, une section `defaults` peut être ajoutée pour surcharger les valeurs par défaut du script :
    ```json
    {
        "api": { ... },
        "defaults": {
            "passes": 5,
            "temperature": 0.8,
            "max_tokens": 512,
            "timeout": 60
        }
    }
    ```

## Utilisation

**Syntaxe de base :**
```bash
python test_api_models.py [Arguments...]
```
**Arguments principaux :**
*   `--models "<id1>,<id2>..."` : Liste des IDs de modèles à tester. Si omis, teste tous les modèles disponibles.
*   `--prompt "<votre_prompt>"` : Le prompt à envoyer.
*   `--passes <nombre>` : Nombre de requêtes par modèle.
*   `--temperature <valeur>` : Température pour la génération (ex: 0.7).
*   `--max-tokens <nombre>` : Nombre maximum de tokens en sortie.
*   `-e`, `--endpoint <URL>` : URL complète de l'endpoint API à utiliser (ex: `http://preprod.api.ai.cloud-temple.com/v1`). Surcharge la valeur du fichier de configuration si spécifié.
*   `--debug` : Active l'affichage détaillé.
*   `--config-file <chemin>` : Utilise un fichier de configuration spécifique.
*   `--parallel-models <nombre>` : Nombre de modèles à tester en parallèle (défaut: 1).
*   `--parallel-requests <nombre>` : Nombre de requêtes à envoyer en parallèle pour chaque modèle (défaut: 1).

**Exemples :**

1.  **Tester tous les modèles avec les paramètres par défaut :**
    ```bash
    python test_api_models.py
    ```

2.  **Tester des modèles spécifiques (`cogito:3b` et `qwen3:4b`) avec 5 passes :**
    ```bash
    python test_api_models.py --models "cogito:3b,qwen3:4b" --passes 5
    ```

3.  **Tester tous les modèles avec un prompt personnalisé et en mode debug :**
    ```bash
    python test_api_models.py --prompt "Explique la photosynthèse en une phrase." --debug
    ```

4.  **Tester un modèle avec une température et un nombre de tokens spécifiques :**
    ```bash
    python test_api_models.py --models "llama3.1" --temperature 0.5 --max-tokens 100
    ```

5.  **Utiliser un fichier de configuration spécifique :**
    ```bash
    python test_api_models.py --config-file "../autre_config.json"
    ```
6.  **Utiliser un endpoint spécifique via la ligne de commande :**
    ```bash
    python test_api_models.py --endpoint "http://mon-autre-api.local/v1" --models "cogito:3b"
    ```

7.  **Tester 3 modèles en parallèle, chacun avec 2 requêtes en parallèle :**
    ```bash
    python test_api_models.py --models "cogito:3b,qwen3:4b,gemma3:1b" --passes 5 --parallel-models 3 --parallel-requests 2
    ```

8.  **Tester tous les modèles, 2 modèles à la fois en parallèle, avec 3 passes par modèle, chaque passe ayant 4 requêtes en parallèle :**
    ```bash
    python test_api_models.py --passes 3 --parallel-models 2 --parallel-requests 4
    ```

## Notes
-   La gestion d'erreur tente d'extraire les détails des réponses JSON d'erreur de l'API, mais le format exact peut varier selon l'implémentation de l'API.
-   L'utilisation d'un grand nombre de requêtes parallèles (`--parallel-requests`) combinée à un grand nombre de modèles parallèles (`--parallel-models`) peut solliciter fortement votre machine et l'API cible. Utilisez avec discernement.
