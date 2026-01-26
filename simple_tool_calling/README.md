# Exemple : Simple Tool Calling

Ce répertoire contient un exemple simple de "Tool Calling" (appel d'outil) avec l'API LLMaaS. Il démontre comment un modèle de langage peut interagir avec des fonctions externes pour accomplir des tâches spécifiques.

## Fichiers

- `test_tool_calling.py` : Le script Python principal qui implémente la logique de l'exemple.
- `.env.example` : Un exemple de fichier de configuration pour les variables d'environnement.
- `requirements.txt` : Les dépendances Python nécessaires pour exécuter le script.

## Fonctionnalités

Le script `test_tool_calling.py` utilise une fonction `calculator` simple pour évaluer des expressions mathématiques. Le processus est le suivant :
1.  Le script envoie une question à l'API LLMaaS, en lui fournissant la description de l'outil `calculator`.
2.  Le modèle LLM analyse la question et, s'il détermine que l'outil est pertinent, il génère un appel à la fonction `calculator` avec les arguments nécessaires.
3.  Le script intercepte cet appel, exécute la fonction `calculator` localement.
4.  Le résultat de l'exécution de l'outil est renvoyé au LLM.
5.  Le LLM utilise ce résultat pour formuler une réponse finale à l'utilisateur.

## Options de Ligne de Commande

Le script `test_tool_calling.py` supporte les options suivantes :

-   `--stream` : Active le mode streaming pour les réponses du LLM. Le texte est affiché au fur et à mesure qu'il est généré.
-   `--model <NOM_DU_MODELE>` : Spécifie le modèle LLM à utiliser pour le test (par exemple, `qwen3:30b-a3b`). Si non spécifié, le modèle par défaut du fichier `.env` est utilisé.
-   `--debug` : Active le mode débogage. Affiche les payloads complets (requêtes et réponses) envoyés et reçus de l'API, ainsi que les deltas de streaming en mode `--stream`.

## Prérequis

-   Python 3.x
-   Une clé API LLMaaS valide.

## Installation

1.  **Clonez ce dépôt** (si ce n'est pas déjà fait).
2.  **Naviguez** vers le répertoire de l'exemple :
    ```bash
    cd exemples/simple_tool_calling/
    ```
3.  **Créez un fichier `.env`** en copiant `.env.example` :
    ```bash
    cp .env.example .env
    ```
4.  **Ouvrez le fichier `.env`** et remplacez `"votre_cle_api_ici"` par votre clé API LLMaaS.
5.  **Installez les dépendances Python** :
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

Exécutez le script depuis le répertoire `exemples/simple_tool_calling/` :

```bash
python3 test_tool_calling.py
```

### Exemples d'utilisation avec les options :

-   Exécuter en mode streaming :
    ```bash
    python3 test_tool_calling.py --stream
    ```
-   Spécifier un modèle et activer le débogage :
    ```bash
    python3 test_tool_calling.py --model qwen3:30b-a3b --debug
    ```
-   Combiner toutes les options :
    ```bash
    python3 test_tool_calling.py --stream --model qwen3:30b-a3b --debug
