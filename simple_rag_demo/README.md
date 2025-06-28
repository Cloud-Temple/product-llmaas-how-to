# 🤖 Mini Démonstrateur RAG avec l'API LLMaaS

Ce projet est un script Python conçu comme un outil pédagogique pour illustrer de manière claire et visuelle le fonctionnement d'une architecture **RAG (Retrieval-Augmented Generation)**.

Il s'appuie exclusivement sur l'**API LLMaaS de Cloud Temple** et des bibliothèques Python standards, sans la complexité de conteneurs Docker ou de bases de données vectorielles externes. Les vecteurs sont simplement stockés en mémoire, ce qui le rend idéal pour comprendre la mécanique fondamentale du RAG.

---

## 📖 Concepts Clés Démontrés

Ce script met en lumière les étapes fondamentales du processus RAG :

1.  **📚 Corpus de Documents** : Utilise des articles de la Constitution française comme base de connaissances.
2.  **🧠 Embedding** : Vectorise le corpus et la question de l'utilisateur à l'aide du modèle `granite-embedding:278m`.
3.  **🔍 Recherche par Similarité** : Compare la question aux documents en utilisant deux métriques (Similarité Cosinus et Distance Euclidienne) pour trouver le contexte le plus pertinent.
4.  **✍️ Génération Augmentée** : Envoie la question et le contexte trouvé à un modèle de génération (`mistral-small3.2:24b`) pour obtenir une réponse factuelle et contextuelle.

Pour une explication détaillée de ces concepts, consultez notre guide : **[Comprendre le RAG : L'Embedding et la Distance Vectorielle](../../doc/llmaas/rag_explained.md)**.

---

## 🚀 Démarrage Rapide

### Prérequis

- Python 3.8+
- Un token d'API LLMaaS valide.

### 1. Installation

Placez-vous à la racine de ce dossier (`exemples/simple-rag-demo`) et exécutez les commandes suivantes :

```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env à partir de l'exemple
cp .env.example .env
```

### 2. Configuration

Ouvrez le fichier `.env` que vous venez de créer et renseignez votre clé d'API LLMaaS :

```dotenv
# .env
LLMAAS_API_KEY="votre_token_personnel_ici"
LLMAAS_BASE_URL="https://api.ai.cloud-temple.com/v1"
```

### 3. Exécution

Lancez simplement le script depuis votre terminal :

```bash
python rag_demo.py
```

Le script vous guidera à travers les différentes étapes. Pour une vue encore plus détaillée montrant les payloads envoyés à l'API, utilisez l'option `--payload` :

```bash
python rag_demo.py --payload
```

---

## 📊 Exemple de Sortie

Voici à quoi ressemble l'exécution du script lorsque vous posez une question :

  <!-- Remplacez par une vraie capture d'écran si possible -->

```
╭────────────────────────────────── Bienvenue ───────────────────────────────────╮
│  Démonstrateur RAG (Retrieval-Augmented Generation)                            │
│  Utilisation de la Constitution Française comme base de connaissances          │
╰────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 1: Vectorisation du Corpus                                               │
│ Chaque article est converti en vecteur numérique (embedding).                  │
╰────────────────────────────────────────────────────────────────────────────────╯
   => 11 documents vectorisés avec succès.

╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 2: Question de l'Utilisateur                                             │
│ Posez une question sur la Constitution.                                        │
╰────────────────────────────────────────────────────────────────────────────────╯
Votre question > qui nomme le premier ministre?

╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 3: Vectorisation de la Question                                          │
│ La question est convertie en vecteur pour la comparer au corpus.               │
╰────────────────────────────────────────────────────────────────────────────────╯
   => Question vectorisée avec succès.

╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 4: Recherche par Similarité (Retrieval)                                  │
│ Le vecteur de la question est comparé à tous les vecteurs du corpus.           │
╰────────────────────────────────────────────────────────────────────────────────╯
                                Calcul de Proximité
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Article (extrait)            ┃ Similarité Cosinus ↑ ┃ Distance Euclidienne ↓ ┃ Choix (par Cosinus) ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Article 8: Le Président de   │               0.7511 │                 0.6912 │         ✅          │
│ la République nomme le...    │                      │                        │                     │
│ ...                          │                  ... │                    ... │                     │
└──────────────────────────────┴──────────────────────┴────────────────────────┴─────────────────────┘
   => Le document avec le score de similarité cosinus le plus élevé est choisi...

   => Document pertinent trouvé :
╭────────────────────────────────────────────────────────────────────────────────╮
│ Article 8: Le Président de la République nomme le Premier ministre. Il met fin │
│ à ses fonctions sur la présentation par celui-ci de la démission du...         │
╰────────────────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 5: Génération Augmentée (Generation)                                     │
│ Construction d'un prompt enrichi et envoi au modèle de génération.             │
╰────────────────────────────────────────────────────────────────────────────────╯
   => Prompt final envoyé au modèle de génération :
  1 Réponds en français à la question : "qui nomme le premier ministre?", en...
╭────────────────────────────────────────────────────────────────────────────────╮
│ ÉTAPE 6: Affichage de la Réponse Finale                                        │
╰────────────────────────────────────────────────────────────────────────────────╯
╭─ Réponse Finale du Modèle ─────────────────────────────────────────────────────╮
│                                                                                │
│  Selon le texte fourni, c'est le Président de la République qui nomme le       │
│  Premier ministre.                                                             │
│                                                                                │
╰────────────────────────────────────────────────────────────────────────────────╯
