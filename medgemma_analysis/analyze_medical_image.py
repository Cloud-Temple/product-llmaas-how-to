# -*- coding: utf-8 -*-
"""
Exemple d'analyse d'image médicale avec MedGemma (Gemma 3).

Ce script permet d'envoyer une image médicale (scanner, radio, etc.)
au modèle spécialisé MedGemma pour obtenir une analyse et une description.

Usage:
    python analyze_medical_image.py path/to/image.png
    python analyze_medical_image.py path/to/image.jpg --stream
"""
import os
import sys
import base64
import httpx
import json
import argparse
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

# --- Configuration ---
load_dotenv()

# Configuration par défaut
DEFAULT_API_URL = "https://api.ai.cloud-temple.com/v1"
# Le nom du modèle tel qu'il est défini dans la configuration LLMaaS
MODEL_NAME = "medgemma:27b"

console = Console()

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Encode une image en base64 pour l'inclure dans la requête API.
    """
    if not os.path.exists(image_path):
        console.print(f"[bold red]❌ Erreur:[/bold red] Le fichier image '{image_path}' n'a pas été trouvé.")
        return None
    
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'encodage de l'image:[/bold red] {e}")
        return None

def analyze_image(image_path: str, api_key: str, api_url: str, context: Optional[str] = None, stream: bool = False):
    """
    Envoie l'image au modèle MedGemma pour analyse.
    """
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return

    console.print(Panel.fit(
        f"[bold blue]Modèle:[/bold blue] {MODEL_NAME}\n"
        f"[bold blue]Image:[/bold blue] {image_path}\n"
        f"[bold blue]Contexte:[/bold blue] {context if context else 'Aucun'}\n"
        f"[bold blue]Mode Streaming:[/bold blue] {'Activé' if stream else 'Désactivé'}",
        title="🔍 Analyse Médicale en cours",
        border_style="blue"
    ))

    # Prompt médical spécifique
    base_prompt = (
        "Analyze this medical image in detail and explain your analyze. "
        "Describe the anatomical structures visible, any potential abnormalities, "
        "and suggest what might be the clinical findings. "
        "Please remain objective and technical. do not invent anything"
    )

    if context:
        prompt = f"Context provided by the user: {context}\n\n{base_prompt}"
    else:
        prompt = base_prompt

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.2, # Température basse pour plus de factuel
        "stream": stream
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            if stream:
                with client.stream("POST", f"{api_url}/chat/completions", headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        console.print(f"[bold red]❌ Erreur API ({response.status_code}):[/bold red]")
                        console.print(response.read().decode())
                        return

                    console.print("\n[bold green]Rapport du modèle:[/bold green]\n")
                    full_response = ""
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    full_response += content
                                    console.print(content, end="")
                            except json.JSONDecodeError:
                                pass
                    print() # Newline at the end
            else:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    progress.add_task(description="Analyse par MedGemma...", total=None)
                    response = client.post(f"{api_url}/chat/completions", headers=headers, json=payload)
                
                if response.status_code != 200:
                    console.print(f"[bold red]❌ Erreur API ({response.status_code}):[/bold red]")
                    console.print(response.text)
                    return

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                console.print("\n[bold green]Rapport du modèle:[/bold green]")
                console.print(Markdown(content))

    except httpx.RequestError as e:
        console.print(f"[bold red]❌ Erreur de connexion:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]❌ Erreur inattendue:[/bold red] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse d'image médicale avec MedGemma")
    parser.add_argument("image_path", help="Chemin vers l'image médicale (JPG, PNG)")
    parser.add_argument("-c", "--context", help="Contexte médical supplémentaire (ex: 'Patient de 45 ans, douleur thoracique')")
    parser.add_argument("--stream", action="store_true", help="Activer le mode streaming")
    args = parser.parse_args()

    # Récupération de la clé API
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL", DEFAULT_API_URL)

    if not api_key:
        console.print("[bold yellow]⚠️  Attention:[/bold yellow] La variable d'environnement API_KEY n'est pas définie.")
        console.print("Veuillez créer un fichier .env ou exporter la variable.")
        sys.exit(1)

    analyze_image(args.image_path, api_key, api_url, args.context, args.stream)
