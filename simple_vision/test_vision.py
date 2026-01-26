# -*- coding: utf-8 -*-
"""
Exemple simple d'utilisation de l'API Vision de LLMaaS.

Ce script montre comment envoyer une image locale avec une question
à un modèle de vision (multimodal) et afficher sa réponse.
"""
import os
import base64
import httpx
import json
import argparse
from dotenv import load_dotenv

# --- Configuration ---
# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
API_KEY = os.getenv("API_KEY")
# Utiliser un modèle de vision. llava est un choix courant.
MODEL = os.getenv("DEFAULT_MODEL", "granite3.2-vision:2b")
IMAGE_PATH = "image_example.png" # L'image doit être dans le même répertoire

# --- Fonctions ---

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode une image en base64 pour l'inclure dans la requête API.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier image '{image_path}' n'a pas été trouvé.")
        return ""
    except Exception as e:
        print(f"❌ Erreur lors de l'encodage de l'image: {e}")
        return ""

def generate_example_image():
    """
    Génère une image simple pour le test si elle n'existe pas.
    Nécessite la bibliothèque Pillow (PIL).
    """
    try:
        from PIL import Image, ImageDraw
        if not os.path.exists(IMAGE_PATH):
            print(f"🖼️  L'image '{IMAGE_PATH}' n'existe pas, génération en cours...")
            # Crée une image simple : un carré rouge sur fond blanc
            img = Image.new('RGB', (200, 200), color = 'white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
            img.save(IMAGE_PATH)
            print("✅ Image d'exemple générée.")
    except ImportError:
        print("⚠️  Avertissement: La bibliothèque Pillow n'est pas installée.")
        print("   Veuillez installer 'Pillow' (`pip install Pillow`) pour générer l'image d'exemple,")
        print(f"   ou placez manuellement un fichier nommé '{IMAGE_PATH}' dans ce répertoire.")
    except Exception as e:
        print(f"❌ Erreur lors de la génération de l'image: {e}")


# --- Logique principale ---

def run_vision_test(stream: bool = False):
    """
    Fonction principale qui exécute le scénario de test de vision.
    """
    if not API_KEY:
        print("❌ Erreur: La variable d'environnement API_KEY n'est pas définie.")
        return

    # Générer l'image d'exemple si nécessaire
    generate_example_image()

    # Encoder l'image en base64
    base64_image = encode_image_to_base64(IMAGE_PATH)
    if not base64_image:
        return

    print(f"🤖 Modèle utilisé : {MODEL}")
    print(f"🖼️ Image envoyée : {IMAGE_PATH}")
    print(f"📡 Mode Streaming : {'Activé' if stream else 'Désactivé'}")
    print("-" * 30)

    # Construction du payload au format multimodal
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Que vois-tu sur cette image ? Décris la forme et la couleur principale."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500, # Limiter la longueur de la description
        "stream": stream
    }

    print("➡️ Envoi de la requête au LLM de vision...")
    final_answer = ""
    try:
        with httpx.Client() as client:
            if not stream:
                # Mode non-streaming
                response = client.post(
                    f"{API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=payload,
                    timeout=120, # Les modèles de vision peuvent être plus longs
                )
                response.raise_for_status()
                response_data = response.json()
                final_answer = response_data["choices"][0]["message"]["content"]
            else:
                # Mode streaming
                with client.stream(
                    "POST",
                    f"{API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=payload,
                    timeout=120,
                ) as response:
                    response.raise_for_status()
                    print("⏳ Réception de la réponse en streaming...")
                    for line in response.iter_lines():
                        if line.startswith("data:"):
                            data_str = line[len("data: "):]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                                if content:
                                    final_answer += content
                                    print(content, end="", flush=True)
                            except json.JSONDecodeError:
                                print(f"\n⚠️  Avertissement: Impossible de parser le chunk JSON: {data_str}")
                                continue
    except httpx.HTTPStatusError as e:
        print(f"\n❌ Erreur API (HTTP Status): {e}")
        # Essayer de lire le corps de la réponse d'erreur, même en streaming
        try:
            error_body = e.response.read().decode()
            print(f"Corps de la réponse d'erreur : {error_body}")
        except Exception as read_exc:
            print(f"Impossible de lire le corps de la réponse d'erreur : {read_exc}")
        return
    except httpx.RequestError as e:
        print(f"\n❌ Erreur API (Request): {e}")
        return

    print("\n\n" + "="*30)
    print("✅ Réponse finale du modèle :")
    print(f"💬 \"{final_answer.strip()}\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exemple d'utilisation de l'API Vision de LLMaaS.")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Activer le mode streaming pour recevoir la réponse."
    )
    args = parser.parse_args()
    
    run_vision_test(stream=args.stream)
