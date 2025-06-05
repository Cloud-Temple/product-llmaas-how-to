# Exemple de Script de Traduction de Fichiers

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

Cet exemple fournit un script Python (`translate.py`) permettant de traduire le contenu d'un fichier texte d'une langue source vers une langue cible en utilisant l'**API LLMaaS Cloud Temple**.

## Objectif

L'objectif principal est de démontrer comment :
1.  Interagir avec l'API LLMaaS pour des tâches de traduction.
2.  Traiter un fichier texte par segments (chunks) pour gérer de longs documents.
3.  Maintenir la cohérence de la traduction en passant le segment précédemment traduit comme contexte au modèle.
4.  Offrir une interface en ligne de commande flexible pour spécifier le fichier, la langue cible, le modèle, et d'autres paramètres.
5.  Proposer un mode interactif pour valider ou ajuster la traduction au fur et à mesure.

## Fonctionnalités

-   Sélection du fichier à traduire via l'option `--file`.
-   Spécification de la langue cible en utilisant les codes ISO 639-1 (ex: `en`, `fr`) via `--target-language`.
-   Option `--list-languages` pour afficher les codes de langues courants.
-   Choix du modèle LLM à utiliser (`--model`).
-   Configuration du prompt système (`--system-prompt`), du nombre maximal de tokens par chunk (`--max-tokens`), de la taille des chunks en mots (`--chunk-size-words`), et du répertoire de sortie (`--output-dir`).
-   **Configuration par défaut via fichier `.env`** : La plupart des options (modèle, URL API, langue cible, max tokens, taille des chunks, prompt système, répertoire de sortie) peuvent être définies par défaut dans un fichier `.env`. Voir `.env.example`.
-   Traduction par "chunks" (segments de texte) avec passage du contexte du chunk précédent pour améliorer la cohérence.
-   **Découpage intelligent des chunks** : Tente d'agréger les petits paragraphes et de respecter les frontières naturelles du texte, tout en s'assurant que les chunks ne dépassent pas la taille configurée.
-   Mode interactif optionnel (`--interactive`) pour valider la traduction de chaque chunk (la modification n'est pas encore implémentée).
-   Sauvegarde du texte traduit dans un nouveau fichier dans le répertoire de sortie.
-   **Affichage de la progression amélioré** : Utilisation d'une barre de progression `rich` détaillée pendant la traduction, incluant un aperçu du chunk en cours.
-   Option de débogage (`--debug`) pour visualiser le processus de découpage des chunks.

## Installation

```bash
# Cloner le dépôt (si ce n'est pas déjà fait)
# git clone ...
# cd llmaas/exemples/translate

# Créer un environnement virtuel (recommandé)
python -m venv .venv
source .venv/bin/activate # Sur Linux/macOS
# .venv\Scripts\activate # Sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
# Copier exemples/translate/.env.example vers exemples/translate/.env
# et y renseigner au minimum LLMAAS_API_KEY.
# Vous pouvez aussi y définir des valeurs par défaut pour le modèle, la langue cible, etc.
# cp .env.example .env
# nano .env
```

## Utilisation

Pour afficher l'aide complète :
```bash
python translate.py --help
```

Pour lister les codes de langues courants :
```bash
python translate.py --list-languages
```

Exemple de traduction d'un fichier en anglais :
```bash
python translate.py --file chemin/vers/mon_fichier_source.txt --target-language en
```

Exemple avec le mode interactif et débogage du découpage :
```bash
python translate.py --file mon_document.txt --target-language fr --interactive --debug
```

Le fichier traduit sera sauvegardé par défaut dans le sous-répertoire `translated_files/` (configurable via `--output-dir` ou `LLMAAS_OUTPUT_DIR` dans `.env`).
