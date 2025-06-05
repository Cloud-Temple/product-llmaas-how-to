#!/usr/bin/env python3
"""
Démonstration Simple du Streaming LLMaaS
==========================================

Auteur: Cloud Temple
Version: 1.1.0
Date: 05/06/2025

Exemple simple et minimal pour démontrer les capacités de streaming
de l'API LLMaaS avec des Server-Sent Events (SSE).
Supporte la configuration externe et le mode debug détaillé.
"""

import json
import sys
import time
import argparse
import os
from pathlib import Path
import httpx

def load_config(config_path="config.json"):
    """Charge la configuration depuis un fichier JSON."""
    if not Path(config_path).exists():
        print_colored(f"❌ Fichier de configuration non trouvé: {config_path}\n", "red")
        print_colored("💡 Copiez config.example.json vers config.json et configurez votre token\n", "yellow")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_colored(f"❌ Erreur de format JSON dans {config_path}: {e}\n", "red")
        sys.exit(1)

def print_colored(text, color="white"):
    """Affichage coloré simple."""
    colors = {
        "green": "\033[92m",
        "blue": "\033[94m", 
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}", end="", flush=True)

def debug_print(message, data=None):
    """Affichage debug avec formatage JSON."""
    print_colored(f"🔍 DEBUG: {message}\n", "cyan")
    if data is not None:
        if isinstance(data, (dict, list)):
            print_colored(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "magenta")
        else:
            print_colored(f"{data}\n", "magenta")
    print_colored("-" * 60 + "\n", "cyan")

def demo_streaming(config, model=None, prompt=None, debug=False):
    """Démonstration du streaming avec un modèle donné."""
    
    # Utiliser les valeurs par défaut du config si non spécifiées
    model = model or config["defaults"]["model"]
    prompt = prompt or "Écris-moi une courte histoire sur un robot qui découvre l'art."
    
    print_colored("🚀 Démonstration Streaming LLMaaS\n", "blue")
    print_colored(f"📊 Modèle: {model}\n", "yellow")
    print_colored(f"💭 Question: {prompt}\n", "yellow")
    print_colored(f"🔧 Mode Debug: {'Activé' if debug else 'Désactivé'}\n\n", "yellow")
    
    # Configuration de la requête
    headers = {
        "Authorization": f"Bearer {config['api']['token']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": True,  # 🔑 Activation du streaming
        "max_tokens": config["defaults"]["max_tokens"],
        "temperature": config["defaults"]["temperature"]
    }
    
    if debug:
        debug_print("Configuration chargée", config)
        debug_print("En-têtes de requête", headers)
        debug_print("Payload de requête", payload)
    
    print_colored("🎬 Réponse en streaming:\n", "green")
    print_colored("=" * 50 + "\n", "blue")
    
    try:
        url = f"{config['api']['endpoint']}/chat/completions"
        
        if debug:
            debug_print("URL de requête", url)
        
        with httpx.stream("POST", url, headers=headers, json=payload, 
                         timeout=config["defaults"]["timeout"]) as response:
            
            if debug:
                debug_print("Code de statut HTTP", response.status_code)
                debug_print("En-têtes de réponse", dict(response.headers))
            
            if response.status_code != 200:
                print_colored(f"❌ Erreur HTTP {response.status_code}: {response.text}\n", "red")
                return
            
            # Traitement des événements SSE
            token_count = 0
            start_time = time.time()
            
            for line in response.iter_lines():
                if debug and line:
                    debug_print("Ligne SSE brute", line)
                
                if line.startswith("data: "):
                    data_content = line[6:]  # Enlever "data: "
                    
                    if data_content == "[DONE]":
                        if debug:
                            debug_print("Signal de fin reçu", "[DONE]")
                        break
                    
                    try:
                        chunk = json.loads(data_content)
                        
                        if debug:
                            debug_print("Chunk JSON parsé", chunk)
                        
                        # Extraction du contenu du token
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                if debug:
                                    debug_print("Contenu extrait", content)
                                print_colored(content, "green")
                                token_count += 1
                                
                    except json.JSONDecodeError as e:
                        if debug:
                            debug_print("Erreur JSON", f"Impossible de parser: {data_content} - {e}")
                        continue  # Ignorer les lignes malformées
            
            # Statistiques finales
            elapsed_time = time.time() - start_time
            print_colored(f"\n\n" + "=" * 50 + "\n", "blue")
            print_colored(f"✅ Streaming terminé!\n", "green")
            print_colored(f"📊 Tokens reçus: {token_count}\n", "yellow")
            print_colored(f"⏱️  Durée: {elapsed_time:.2f}s\n", "yellow")
            print_colored(f"🚀 Vitesse: {token_count/elapsed_time:.1f} tokens/s\n", "yellow")
            
            if debug:
                debug_print("Statistiques finales", {
                    "tokens": token_count,
                    "duree_s": elapsed_time,
                    "vitesse_tps": token_count/elapsed_time if elapsed_time > 0 else 0
                })
            
    except httpx.TimeoutException:
        print_colored("❌ Timeout - La requête a pris trop de temps\n", "red")
    except httpx.RequestError as e:
        print_colored(f"❌ Erreur de connexion: {e}\n", "red")
        if debug:
            debug_print("Erreur de connexion détaillée", str(e))
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Streaming interrompu par l'utilisateur\n", "yellow")

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Démonstration du streaming LLMaaS avec SSE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  %(prog)s                                    # Utiliser les paramètres par défaut
  %(prog)s --model gemma3:4b                 # Modèle spécifique
  %(prog)s --debug                           # Mode debug activé
  %(prog)s --model qwen3:8b --debug          # Modèle + debug
  %(prog)s "Votre prompt personnalisé"       # Prompt spécifique
  %(prog)s --model granite3.3:8b "Expliquez-moi l'IA"  # Tout personnalisé
        """
    )
    
    parser.add_argument(
        "prompt", 
        nargs="?", 
        help="Prompt à envoyer au modèle (optionnel)"
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Modèle à utiliser (remplace la config par défaut)"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Active le mode debug avec affichage détaillé des payloads"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        help="Chemin vers le fichier de configuration (défaut: config.json)"
    )
    
    args = parser.parse_args()
    
    # Chargement de la configuration
    config = load_config(args.config)
    
    print_colored("🔧 Configuration:\n", "blue")
    print_colored(f"   - API: {config['api']['endpoint']}\n", "yellow")
    print_colored(f"   - Modèle: {args.model or config['defaults']['model']}\n", "yellow")
    print_colored(f"   - Streaming: Activé (SSE)\n", "yellow")
    print_colored(f"   - Debug: {'Activé' if args.debug else 'Désactivé'}\n", "yellow")
    print_colored(f"   - Config: {args.config}\n\n", "yellow")
    
    demo_streaming(
        config=config,
        model=args.model,
        prompt=args.prompt,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
