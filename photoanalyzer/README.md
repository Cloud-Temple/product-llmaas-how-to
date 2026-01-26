# PhotoAnalyzer - Analyse d'Images Multimodale

PhotoAnalyzer est un outil CLI puissant pour l'analyse d'images utilisant l'API LLMaaS avec des modèles multimodaux de pointe comme **Qwen3-VL** et **Qwen3-Omni**.

## 🚀 Fonctionnalités

- **Analyse détaillée** : Description précise du contenu, des objets, des personnes et de l'ambiance.
- **Support Multimodal Avancé** : Compatible avec les derniers modèles de vision (`qwen3-vl`, `qwen3-omni`).
- **Prompts Spécialisés** : Modes d'analyse prédéfinis (technique, émotions, sécurité, médical, etc.).
- **Formats Flexibles** : Supporte JPG, PNG, WEBP.
- **Sortie Structurée** : Affichage soigné dans le terminal et export en fichier texte.

## 🛠️ Installation

1.  **Prérequis** : Python 3.8+ installé.
2.  **Installation des dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration** :
    Copiez le fichier d'exemple `.env` (si présent) ou configurez vos clés via `config.json` ou variables d'environnement.
    ```bash
    # Exemple de .env
    LLMAAS_API_URL=https://api.ai.cloud-temple.com/
    LLMAAS_API_KEY=votre_cle_api_ici
    ```

## 📖 Utilisation

### Analyse Simple
```bash
python photoanalyzer.py images/bird.png
```

### Choix du Modèle
Utilisez les modèles **Qwen3** pour de meilleures performances :
```bash
# Modèle léger par défaut
python photoanalyzer.py images/bird.png --model qwen3-vl:8b

# Modèle très puissant (recommandé)
python photoanalyzer.py images/bird.png --model qwen3-omni:30b
```

### Types d'Analyse
Utilisez l'option `-t` pour cibler l'analyse :
```bash
# Analyse technique (composition, lumière)
python photoanalyzer.py images/journal.png -t technical

# Analyse des émotions
python photoanalyzer.py images/woman.jpg -t emotions

# Transcription de texte (OCR contextuel)
python photoanalyzer.py document.jpg -t text
```

### Options Avancées
- **Sauvegarde** : `-o resultat.txt` pour enregistrer la sortie.
- **Prompt Personnalisé** : `-p "Trouve-moi toutes les erreurs sur ce schéma électrique"` (écrase le type d'analyse).
- **Mode Silencieux** : `--silent` pour n'afficher que le résultat brut (utile pour les pipes).
- **Debug** : `--debug` pour voir les détails de la requête API.

## 🤖 Modèles Supportés

- **`qwen3-vl:8b`** : Rapide et efficace pour la plupart des tâches.
- **`qwen3-omni:30b`** : Très haute précision, excellente compréhension des détails et du contexte complexe.
- **`granite3.2-vision:2b`** : Ultra-léger pour des analyses simples.

## 📁 Structure du Projet

- `photoanalyzer.py` : Script principal CLI.
- `api_utils.py` : Gestion des appels API (compatible OpenAI Vision).
- `image_utils.py` : Traitement et validation des images.
- `cli_ui.py` : Gestion de l'interface utilisateur (Rich).
