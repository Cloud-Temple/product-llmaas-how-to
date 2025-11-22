#  Démonstration DeepSeek-OCR (Vision-Langage)

Bienvenue dans la démonstration du modèle **DeepSeek-OCR** sur la plateforme LLMaaS de Cloud Temple.

Cet outil vous permet de transformer n'importe quel document visuel (image, scan, PDF) en texte structuré (Markdown), prêt à être utilisé.

---

##  Pourquoi DeepSeek-OCR ?

Contrairement aux outils OCR traditionnels qui lisent juste du texte "au kilomètre", DeepSeek-OCR (basé sur l'architecture Janus-Pro) comprend la **structure** de votre document.

Il est capable de :
-  Convertir des **tableaux** complexes en format Markdown.
-  Maintenir la hiérarchie des **titres** et paragraphes.
-  Transcrire des formules mathématiques en **LaTeX**.
-  Traiter des documents **PDF multipages** page par page.

---

##  Installation

Suivez ces étapes pour préparer votre environnement.

### 1. Préparer l'environnement Python
Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances.

```bash
# Création de l'environnement virtuel (une seule fois)
python3 -m venv venv

# Activation de l'environnement
source venv/bin/activate
```

### 2. Installer les dépendances
Nous utilisons des bibliothèques puissantes pour gérer les images (`Pillow`), les PDF (`PyMuPDF`) et l'affichage (`rich`).

```bash
pip install -r requirements.txt
```

### 3. Configurer l'accès API
Le script a besoin de votre clé API pour communiquer avec le modèle.

1. Copiez le modèle de configuration :
   ```bash
   cp .env.example .env
   ```
2. Ouvrez le fichier `.env` et collez votre clé API :
   ```ini
   API_KEY="sk-..."
   # L'URL par défaut est déjà configurée pour la production Cloud Temple
   ```

---

##  Guide d'Utilisation

💡 **Note pour les développeurs :** Le code source `ocr_demo.py` a été abondamment commenté étape par étape. N'hésitez pas à l'ouvrir pour comprendre exactement comment interagir avec l'API et gérer les images.

Le script est conçu pour être simple et flexible.

### Syntaxe de base
```bash
python ocr_demo.py [SOURCE] [OPTIONS]
```

### Cas d'usage courants

#### 1. Tester rapidement (Ticket de caisse)
Lancez le script sans argument pour analyser un ticket de caisse exemple (image hébergée sur Wikimedia Commons).
```bash
python ocr_demo.py
```

#### 2. Analyser un fichier local (Exemples fournis)
Vous pouvez utiliser les fichiers d'exemple inclus dans ce dossier.

```bash
# Analyser une capture d'écran LinkedIn (Image PNG)
python ocr_demo.py "linkeding.png"

# Analyser un rapport technique (PDF multipages)
# Le script traitera chaque page séquentiellement
python ocr_demo.py "Gemma3Report.pdf"
```

#### 3. Analyser un document depuis Internet
Donnez simplement l'URL. Le script se chargera de le télécharger (Image ou PDF).
```bash
python ocr_demo.py "https://upload.wikimedia.org/wikipedia/commons/0/0b/ReceiptSwiss.jpg"
```

---

## Options Avancées

Personnalisez le comportement du script selon vos besoins.

| Option | Description | Exemple |
|--------|-------------|---------|
| `--mode` | **markdown** (défaut) : Préserve la structure.<br>**text** : Extrait le texte brut sans mise en forme.<br>**figure** : Décrit un graphique ou une image. | `--mode text` |
| `--raw` | Affiche le code brut (utile pour copier-coller le résultat Markdown sans le rendu visuel du terminal). | `--raw` |

**Exemple combiné :**
Analyser le rapport PDF local, en mode texte brut, et afficher le résultat brut :
```bash
python ocr_demo.py "Gemma3Report.pdf" --mode text --raw
```

---

## 🔍 Comment ça marche ? (Sous le capot)

Pour garantir la meilleure qualité, le script effectue plusieurs traitements intelligents avant d'interroger l'IA :

1.  **Gestion des PDF** : 
    Si vous donnez un PDF, nous utilisons `PyMuPDF` pour convertir chaque page en une image haute résolution (Zoom 2.0x), garantissant que même les petits caractères sont lisibles par le modèle.

2.  **Optimisation d'image** :
    Les images sont validées et converties en format **RGB** (pour éviter les problèmes de transparence des PNG). Si une image est gigantesque (>4096px), elle est redimensionnée pour rester compatible avec l'API.

3.  **L'Intelligence Artificielle** :
    L'image optimisée est envoyée au modèle `deepseek-ai/DeepSeek-OCR` hébergé sur nos serveurs GPU (L40S/RTX). Nous utilisons un prompt spécifique (`Convert the document to markdown.`) et une température de `0.0` pour forcer le modèle à être le plus fidèle possible au document original.

---

## Dépannage

**Erreur : `ModuleNotFoundError: No module named ...`**
> Vous avez oublié d'activer votre environnement virtuel ou d'installer les dépendances.
> Tapez `source venv/bin/activate` puis `pip install -r requirements.txt`.

**Erreur : `401 Unauthorized`**
> Votre clé API est invalide ou manquante dans le fichier `.env`. Vérifiez qu'elle commence bien par `sk-`.

**Erreur : `File not found`**
> Vérifiez le chemin de votre fichier. Utilisez des guillemets si le nom contient des espaces : `"mon fichier.pdf"`.
