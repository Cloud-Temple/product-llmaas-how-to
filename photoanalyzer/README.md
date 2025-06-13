# PhotoAnalyzer - Analyseur d'Images Multimodal

PhotoAnalyzer est un outil CLI Python avancé pour l'analyse d'images utilisant l'API LLMaaS avec des modèles multimodaux. Il offre une interface utilisateur soignée avec modes debug, formats de sortie multiples, et support de différents types de prompts d'analyse spécialisés.

## 🚀 Fonctionnalités Principales

### Analyse Multimodale Avancée
- **12 types d'analyse prédéfinis** : général, technique, personnes, objets, scène, couleurs, composition, émotions, texte, sécurité, médical, comptage
- **Prompts personnalisés** : Support de prompts sur mesure pour des analyses spécifiques
- **Détection automatique du contenu** : Optimisation des prompts selon le type d'image détecté

### Gestion d'Images Robuste
- **Formats supportés** : JPEG, PNG, GIF, BMP, TIFF, WebP
- **Validation complète** : Vérification de format, taille, dimensions
- **Optimisation automatique** : Redimensionnement et compression intelligents
- **Informations détaillées** : Métadonnées, EXIF, transparence, animation

### Interface Utilisateur Avancée
- **Mode debug exhaustif** : Informations détaillées sur le traitement
- **Mode silencieux** : Sortie propre pour la redirection
- **Affichage coloré** : Interface Rich avec panneaux formatés
- **Aide intégrée** : Documentation complète des options

### Configuration Flexible
- **Fichier JSON** : Configuration centralisée via `config.json`
- **Variables d'environnement** : Support `.env` pour les paramètres sensibles
- **Arguments CLI** : Surcharge complète via ligne de commande
- **Sauvegarde automatique** : Génération de noms de fichiers intelligente

## 📋 Prérequis

- Python 3.8 ou supérieur
- Accès à l'API LLMaaS Cloud Temple
- Modèles multimodaux disponibles (ex: `qwen2.5-vl:7b`)

## 🛠️ Installation

1. **Installer les dépendances Python** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurer l'authentification** :
   ```bash
   # Option 1: Variables d'environnement
   cp .env.example .env
   # Éditer .env avec vos vraies valeurs
   
   # Option 2: Fichier de configuration
   cp config.example.json config.json
   # Éditer config.json avec vos paramètres
   ```

3. **Vérifier l'installation** :
   ```bash
   python photoanalyzer.py --help
   ```

## 🎯 Utilisation

### Exemples de Base

```bash
# Analyse générale d'une image
python photoanalyzer.py image.jpg

# Analyse avec type spécifique
python photoanalyzer.py photo.png -t people

# Analyse avec prompt personnalisé
python photoanalyzer.py screenshot.png -p "Décris les éléments techniques visibles"

# Sauvegarde dans un fichier
python photoanalyzer.py image.jpg -o description.txt

# Mode debug pour diagnostics
python photoanalyzer.py image.jpg --debug
```

### Types d'Analyse Disponibles

| Type | Description |
|------|-------------|
| `general` | Description détaillée générale (défaut) |
| `technical` | Analyse technique (qualité, composition, éclairage) |
| `people` | Focus sur les personnes (nombre, âges, expressions) |
| `objects` | Identification et description des objets |
| `scene` | Description de la scène et du contexte |
| `colors` | Analyse des couleurs et de l'harmonie chromatique |
| `composition` | Analyse de la composition visuelle |
| `emotions` | Analyse des émotions et de l'ambiance |
| `text` | Transcription du texte visible |
| `security` | Analyse sécuritaire (équipements, vulnérabilités) |
| `medical` | Analyse médicale (avec avertissement) |
| `count` | Comptage précis d'éléments |

```bash
# Lister tous les types disponibles
python photoanalyzer.py --list-types
```

### Configuration Avancée

#### Via Fichier JSON (`config.json`)
```json
{
  "api_url": "https://api.ai.cloud-temple.com",
  "api_token": "votre_cle_api",
  "default_model": "qwen2.5-vl:7b",
  "default_max_tokens": 1000,
  "default_temperature": 0.3,
  "default_analysis_type": "general",
  "output_directory": "./photoanalyzer_outputs"
}
```

#### Via Variables d'Environnement (`.env`)
```bash
LLMAAS_API_URL=https://api.ai.cloud-temple.com
LLMAAS_API_KEY=votre_cle_api
LLMAAS_DEFAULT_MODEL=qwen2.5-vl:7b
PHOTOANALYZER_OUTPUT_DIR=./outputs
```

## 📝 Options de Ligne de Commande

### Arguments Obligatoires
- `IMAGE_FILE_PATH` : Chemin vers l'image à analyser

### Options Principales
- `-o, --output-file` : Fichier de sauvegarde de l'analyse
- `-t, --analysis-type` : Type d'analyse prédéfini
- `-p, --custom-prompt` : Prompt personnalisé (prioritaire)
- `-m, --model` : Modèle multimodal à utiliser

### Configuration API
- `--api-url` : URL de l'API LLMaaS
- `--api-key` : Clé d'authentification API
- `--ollama-url` : URL d'un backend Ollama direct (ex: http://localhost:11434). Court-circuite l'API LLMaaS.
- `-c, --config-file` : Fichier de configuration JSON

### Paramètres du Modèle
- `--max-tokens` : Tokens maximum à générer (défaut: 1000)
- `--temperature` : Température de génération (0.0-1.0, défaut: 0.3)

### Options d'Affichage
- `--debug` : Mode debug verbeux
- `--silent` : Mode silencieux (sortie propre)
- `--list-types` : Afficher les types d'analyse disponibles

### Utilitaires
- `--output-dir` : Répertoire de sortie personnalisé
- `--help` : Afficher l'aide complète

## 🔧 Exemples d'Usage Avancés

### Analyse de Photos de Personnes
```bash
# Analyse focalisée sur les personnes
python photoanalyzer.py equipe.jpg -t people -o analyse_equipe.txt

# Comptage précis de personnes
python photoanalyzer.py groupe.jpg -t count --debug
```

### Analyse de Captures d'Écran
```bash
# Analyse technique d'interface
python photoanalyzer.py interface.png -t technical

# Extraction de texte
python photoanalyzer.py document.png -t text --silent > texte_extrait.txt
```

### Analyse Sécuritaire
```bash
# Évaluation sécuritaire d'un site
python photoanalyzer.py site_industriel.jpg -t security -o rapport_securite.txt
```

### Workflows Batch
```bash
# Traitement de plusieurs images
for img in *.jpg; do
    python photoanalyzer.py "$img" -t general -o "${img%.*}_analyse.txt" --silent
done
```

## 🔍 Mode Debug

Le mode debug (`--debug`) affiche des informations détaillées :

- **Validation image** : Format, dimensions, taille, métadonnées
- **Encodage Base64** : Statistiques de compression
- **Requête API** : Payload, modèle, paramètres
- **Réponse API** : Tokens, durée, raison d'arrêt
- **Configuration** : Paramètres résolus et sources

```bash
python photoanalyzer.py image.jpg --debug
```

## 📊 Gestion des Sorties

### Sauvegarde Automatique
```bash
# Génération automatique du nom avec timestamp
python photoanalyzer.py photo.jpg -o auto

# Résultat: photo_general_1672531200.txt
```

### Formats de Sortie
- **Console** : Affichage formaté avec Rich
- **Fichier texte** : Sauvegarde brute du résultat
- **Mode silencieux** : Sortie propre pour redirection

## 🐛 Dépannage

### Erreurs Communes

**Image non trouvée**
```bash
ERREUR: Le fichier image spécifié 'image.jpg' n'existe pas.
```
→ Vérifiez le chemin et l'existence du fichier

**Format non supporté**
```bash
Format de fichier '.bmp' non supporté.
```
→ Convertissez en JPEG/PNG ou vérifiez les formats supportés

**Erreur API**
```bash
Erreur API (HTTP 401): Unauthorized
```
→ Vérifiez votre clé API dans la configuration

**Image trop volumineuse**
```bash
# Erreur de taille de fichier avant envoi
Le fichier image est trop volumineux (52.3 MB). Taille maximale: 50 MB.
# Erreur de taille de requête après encodage (souvent sur Nginx)
413 Request Entity Too Large
```
→ Réduisez la taille de l'image manuellement ou utilisez le script d'optimisation fourni.

### Utilitaire d'Optimisation d'Image (`resize_image.py`)

Si vous rencontrez l'erreur `413 Request Entity Too Large`, cela signifie que l'image, même si ses dimensions sont acceptables, est trop lourde une fois encodée en base64. Le script `resize_image.py` est fourni pour vous aider à réduire la taille du fichier.

**Utilisation :**
```bash
# Utilisation de base (redimensionne si > 2048px)
python3 exemples/photoanalyzer/resize_image.py chemin/vers/votre/image.png

# Forcer un redimensionnement plus agressif
python3 exemples/photoanalyzer/resize_image.py chemin/vers/votre/image.png --max-dim 800 --quality 75
```

- `--max-dim <pixels>` : Définit la dimension maximale (largeur ou hauteur).
- `--quality <1-100>` : Définit la qualité de compression pour les images JPEG.

Le script créera une nouvelle image avec le suffixe `_optimized`. Utilisez ensuite cette nouvelle image pour l'analyse.

### Diagnostic Approfondi
```bash
# Test de connectivité API
python photoanalyzer.py image.jpg --debug | grep "API"

# Validation d'image complète
python photoanalyzer.py image.jpg --debug | grep -A 10 "Validation Image"
```

## 🧪 Tests et Validation

### Test de Configuration
```bash
# Vérifier la configuration
python photoanalyzer.py --list-types

# Test avec image simple
python photoanalyzer.py test_image.jpg -t general --debug
```

### Benchmarking
```bash
# Mesurer les performances
time python photoanalyzer.py large_image.jpg -t general --silent
```

## 🔒 Sécurité et Confidentialité

- **Clés API** : Stockées dans `.env` (non versionnées)
- **Images sensibles** : Pas de cache local, traitement en mémoire
- **Logs debug** : Pas d'exposition des données sensibles
- **HTTPS** : Toutes les communications API chiffrées

## 📚 Intégration et Extensibilité

### Utilisation en tant que Module
```python
from api_utils import analyze_image_api
from image_utils import encode_image_to_base64

# Utilisation directe
image_b64 = encode_image_to_base64("image.jpg")
result = analyze_image_api(api_url, api_key, model, image_b64, prompt)
```

### Extension des Types d'Analyse
Modifiez `ANALYSIS_PROMPTS` dans `photoanalyzer.py` pour ajouter de nouveaux types :

```python
ANALYSIS_PROMPTS["custom"] = "Votre prompt personnalisé..."
```

## 🔄 Mise à Jour et Maintenance

### Mise à Jour des Dépendances
```bash
pip install -r requirements.txt --upgrade
```

### Nettoyage des Fichiers Temporaires
```bash
rm -rf ./photoanalyzer_outputs/*.tmp
```

## 📈 Performances et Optimisation

- **Images optimales** : ≤ 2048px de côté, format JPEG/PNG
- **Modèles recommandés** : `qwen2.5-vl:7b` pour l'équilibre vitesse/qualité
- **Tokens recommandés** : 500-1500 selon la complexité de l'analyse
- **Température optimale** : 0.1-0.3 pour analyses factuelles, 0.5-0.7 pour créatives

## 🆘 Support et Documentation

- **Documentation API** : [API LLMaaS Cloud Temple](https://api.ai.cloud-temple.com/swagger/)
- **Issues techniques** : Voir les logs en mode `--debug`
- **Modèles supportés** : Consulter `/v1/models` avec capacité `multimodal: true`

---

**Note** : PhotoAnalyzer nécessite des modèles multimodaux compatibles avec le format OpenAI pour l'analyse d'images. Assurez-vous que votre instance LLMaaS dispose de modèles comme `qwen2.5-vl`, `gemma3`, `granite3.2-vision` ou équivalents avec support vision.
