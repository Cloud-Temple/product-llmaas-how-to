# Script PowerShell Avancé pour Tester l'API LLMaaS Cloud Temple

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Objectif
Ce script PowerShell (`test_api_models.ps1`) permet de tester et comparer les réponses de différents modèles de langage (LLM) accessibles via l'**API LLMaaS Cloud Temple**. Il offre des fonctionnalités avancées pour la configuration, la sélection des modèles, la personnalisation des requêtes et l'affichage des résultats.

## Fonctionnalités
1.  **Configuration Externe :** Lit l'endpoint de l'API et le token d'authentification depuis un fichier `config.json`. Permet également de définir des valeurs par défaut pour les passes, la température, le nombre max de tokens et le timeout.
2.  **Découverte Dynamique des Modèles :** Récupère automatiquement la liste des modèles disponibles depuis l'endpoint `/models` de l'API.
3.  **Sélection des Modèles :** Permet de spécifier les modèles à tester via le paramètre `-Models` (liste d'IDs séparés par des virgules). Si omis, tous les modèles disponibles sont testés.
4.  **Personnalisation du Prompt :** Le prompt envoyé aux modèles peut être défini via le paramètre `-Prompt`.
5.  **Tests Multiples :** Effectue un nombre configurable de passes (requêtes) pour chaque modèle (paramètre `-Passes`) pour évaluer la cohérence et la performance.
6.  **Paramètres de Génération :** Permet de contrôler la température (`-Temperature`) et le nombre maximum de tokens (`-MaxTokens`) pour les requêtes.
7.  **Mode Debug :** Une option `-Debug` active l'affichage d'informations détaillées sur les requêtes, les réponses et les erreurs, y compris le corps des réponses d'erreur de l'API.
8.  **Gestion d'Erreurs Améliorée :** Intercepte les erreurs API (par ex. 403 Forbidden) et tente d'extraire et d'afficher le message détaillé fourni dans la réponse JSON (par ex. "Prompt blocked for security reasons") sans planter le script.
9.  **Sortie Colorée :** Utilise des couleurs pour distinguer les informations, les succès et les échecs dans la console.
10. **Tableau Récapitulatif :** Affiche un résumé final comparant les performances (succès, erreurs, temps moyen, temps total) de chaque modèle testé.

## Prérequis
-   PowerShell 5.1 ou supérieur.
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
```powershell
powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 [Paramètres...]
```
*Note :* `-ExecutionPolicy Bypass` peut être nécessaire si la politique d'exécution de votre système empêche l'exécution de scripts.

**Exemples :**

1.  **Tester tous les modèles avec les paramètres par défaut :**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1
    ```

2.  **Tester des modèles spécifiques (`cogito:3b` et `qwen3:4b`) avec 5 passes :**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Models "cogito:3b,qwen3:4b" -Passes 5
    ```

3.  **Tester tous les modèles avec un prompt personnalisé et en mode debug :**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Prompt "Explique la photosynthèse en une phrase." -Debug
    ```

4.  **Tester un modèle avec une température et un nombre de tokens spécifiques :**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Models "llama3.1" -Temperature 0.5 -MaxTokens 100
    ```

5.  **Utiliser un fichier de configuration spécifique :**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -ConfigFile "../autre_config.json"
    ```

## Notes
-   Le script tente de forcer l'encodage de sortie en UTF-8, mais l'affichage correct des caractères accentués peut toujours dépendre de la configuration de votre console PowerShell (police, page de code).
-   La gestion d'erreur tente d'extraire les détails des réponses JSON d'erreur de l'API, mais le format exact peut varier selon l'implémentation de l'API.
