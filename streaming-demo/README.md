# Démonstration Streaming LLMaaS Cloud Temple

## 📋 Description

Exemple simple et minimal pour démontrer les capacités de **streaming en temps réel** de l'**API LLMaaS Cloud Temple** avec des Server-Sent Events (SSE).

📖 **Documentation complète** : [docs.cloud-temple.com](https://docs.cloud-temple.com)

Cette démonstration montre comment :
- ✅ Activer le streaming avec `"stream": true`
- ✅ Traiter les événements SSE en temps réel 
- ✅ Afficher les tokens au fur et à mesure de leur génération
- ✅ Calculer les métriques de performance (vitesse de génération)

## 🚀 Utilisation Rapide

### Configuration initiale
```bash
# Installation des dépendances
pip install -r requirements.txt

# Copie et configuration du fichier de config
cp config.example.json config.json
# Éditez config.json avec votre token API
```

### Exécution basique
```bash
python streaming_demo.py
```

### Avec des options avancées
```bash
# Modèle spécifique
python streaming_demo.py --model gemma3:4b

# Mode debug (affiche tous les payloads)
python streaming_demo.py --debug

# Prompt personnalisé
python streaming_demo.py "Explique-moi le concept de streaming en informatique"

# Combinaison complète
python streaming_demo.py --model granite3.3:8b --debug "Raconte-moi une histoire"
```

## 📊 Exemple d'Affichage

```
🔧 Configuration:
   - API: https://api.ai.cloud-temple.com/v1
   - Modèle: granite3.3:2b
   - Streaming: Activé (SSE)

🚀 Démonstration Streaming LLMaaS
📊 Modèle: granite3.3:2b
💭 Question: Écris-moi une courte histoire sur un robot qui découvre l'art.

🎬 Réponse en streaming:
==================================================
Il était une fois un petit robot nommé ARIA...
[Texte affiché token par token en temps réel]
==================================================
✅ Streaming terminé!
📊 Tokens reçus: 158
⏱️  Durée: 3.42s
🚀 Vitesse: 46.2 tokens/s
```

## 🔧 Fonctionnalités Techniques

### **Configuration Externe**
- Fichier `config.json` pour l'API et les paramètres par défaut
- Template `config.example.json` pour l'initialisation
- Chargement automatique avec validation JSON
- Support pour chemin de config personnalisé (`--config`)

### **Mode Debug Avancé**
- Affichage détaillé des payloads de requête/réponse avec `--debug`
- Visualisation des chunks SSE bruts
- Logs de parsing JSON et extraction de contenu
- Statistiques de performance complètes
- Gestion d'erreurs enrichie

### **Server-Sent Events (SSE)**
- Protocole HTTP streaming optimisé
- Réception des tokens en temps réel
- Gestion robuste des événements malformés

### **Interface CLI Moderne**
- Support argparse avec aide détaillée
- Arguments positionnels et options nommées
- Exemples d'utilisation intégrés
- Messages d'erreur explicites

### **Métriques de Performance**
- Comptage automatique des tokens
- Calcul du débit (tokens/seconde)
- Mesure de la latence totale
- Mode debug avec statistiques JSON

### **Gestion d'Erreurs**
- Timeouts configurables via config.json
- Gestion des erreurs de connexion
- Interruption propre avec Ctrl+C
- Validation robuste des fichiers de configuration

## 🎯 Modèles Recommandés

| Modèle | Taille | Vitesse | Cas d'Usage |
|--------|--------|---------|-------------|
| `granite3.3:2b` | 2B | ~45 t/s | Démonstrations rapides |
| `gemma3:4b` | 4B | ~58 t/s | Qualité équilibrée |
| `qwen3:8b` | 8B | ~29 t/s | Réponses sophistiquées |
| `cogito:3b` | 3B | ~63 t/s | Raisonnement logique |

## 💡 Points Clés du Code

### Activation du Streaming
```python
payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "stream": True,  # 🔑 Point crucial
    "max_tokens": 300,
    "temperature": 0.8
}
```

### Traitement SSE
```python
for line in response.iter_lines():
    if line.startswith("data: "):
        data_content = line[6:]  # Enlever "data: "
        
        if data_content == "[DONE]":
            break
            
        chunk = json.loads(data_content)
        content = chunk["choices"][0]["delta"].get("content", "")
        
        if content:
            print(content, end="", flush=True)
```

## ⚡ Avantages du Streaming

1. **Expérience Utilisateur** : Affichage immédiat, pas d'attente
2. **Performance Perçue** : Réactivité optimale même pour les longs textes
3. **Contrôle** : Possibilité d'interrompre la génération à tout moment
4. **Efficacité** : Utilisation optimale de la bande passante

## 🔗 Liens Utiles

- [Documentation complète Cloud Temple](https://docs.cloud-temple.com)
- [Console Cloud Temple](https://console.cloud-temple.com)
- [Autres exemples](../README.md)
