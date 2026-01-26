"""
Script de démonstration pour le modèle Qwen3-Omni (Multimodal).
Ce script utilise l'API OpenAI standard pour envoyer des requêtes avec audio et vidéo.
Il démontre également les capacités de Function Calling à partir de l'audio.

Plus d'informations : https://github.com/QwenLM/Qwen3-Omni
"""

import os
import json
import httpx
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

# Chargement de la configuration depuis le fichier .env
load_dotenv()

# Initialisation de la console Rich pour un affichage soigné
console = Console()

# Configuration de l'API
API_BASE = os.getenv("API_ENDPOINT")
API_KEY = os.getenv("API_KEY", "EMPTY")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-omni:30b")
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() == "true"

# Vérification de la configuration critique
if not API_BASE:
    console.print("[bold red]Erreur :[/] API_ENDPOINT non défini dans .env")
    exit(1)

# Initialisation du client OpenAI
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE,
    http_client=httpx.Client(verify=SSL_VERIFY)
)

# --- Prompts Système ---

# Prompt par défaut pour les interactions vocales (Traduction, Commandes)
# Source : Cookbooks (adapté)
PROMPT_VOICE_ASSISTANT = """You are a virtual voice assistant. 
You are communicating with the user.
Interact with users using short (no more than 50 words), brief, straightforward language."""

# Prompt spécifique pour le Dialogue Audio-Visuel
# Source : audio_visual_dialogue.ipynb
PROMPT_CONVERSATIONAL = """You are a voice assistant with specific characteristics. 
Interact with users using brief, straightforward language, maintaining a natural tone. 
Never use formal phrasing, mechanical expressions, bullet points, overly structured language. 
Your output must consist only of the spoken content you want the user to hear. 
Do not include any descriptions of actions, emotions, sounds, or voice changes. 
Do not use asterisks, brackets, parentheses, or any other symbols to indicate tone or actions. 
You must answer users' audio or text questions, do not directly describe the video content. 
You communicate in the same language as the user unless they request otherwise. 
When you are uncertain (e.g., you can't see/hear clearly, don't understand, or the user makes a comment rather than asking a question), use appropriate questions to guide the user to continue the conversation. 
Keep replies concise and conversational, as if talking face-to-face."""

# Définition des outils pour le test de Function Calling
TOOLS_DEFINITION = [
    {
        'type': 'function',
        'function': {
            'name': 'web_search',
            'description': 'Utilize the web search engine to retrieve relevant information based on multiple queries.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'queries': {
                        'type': 'array',
                        'items': {'type': 'string', 'description': 'The search query.'},
                        'description': 'The list of search queries.'
                    }
                },
                'required': ['queries']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'car_ac_control',
            'description': "Control the vehicle's air conditioning system to turn it on/off and set the target temperature",
            'parameters': {
                'type': 'object',
                'properties': {
                    'temperature': {'type': 'number', 'description': 'Target set temperature in Celsius degrees'},
                    'ac_on': {'type': 'boolean', 'description': 'Air conditioning status (true=on, false=off)'}
                },
                'required': ['temperature', 'ac_on']
            }
        }
    }
]

def print_header():
    """Affiche l'en-tête de la démonstration."""
    console.print(Panel.fit(
        f"[bold cyan]Démo Qwen3-Omni (Multimodal)[/]\n"
        f"[dim]Endpoint : {API_BASE}[/]\n"
        f"[dim]Modèle   : {MODEL_NAME}[/]",
        border_style="cyan"
    ))

def run_test(title, content_block, user_text, system_prompt=None):
    """
    Exécute un test unitaire simple (Chat Completion).
    """
    console.print(f"\n[bold yellow]=== Test : {title} ===[/]")
    
    messages = []
    
    # Ajout du System Prompt seulement s'il est défini
    if system_prompt:
        console.print(f"[dim]System Prompt : {system_prompt[:60].replace(chr(10), ' ')}...[/]")
        messages.append({"role": "system", "content": system_prompt})
    else:
        console.print("[dim]System Prompt : Aucun (Utilisation par défaut du modèle)[/]")

    messages.append({
        "role": "user",
        "content": [
            content_block,
            {"type": "text", "text": user_text}
        ]
    })

    if user_text:
        console.print(f"[dim]Prompt Utilisateur :[/] {user_text}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Génération en cours...", total=None)
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=200
            )
            
        response = completion.choices[0].message.content or ""
        console.print(Panel(response, title="Réponse du Modèle", border_style="green"))
        
    except Exception as e:
        console.print(f"[bold red]Erreur :[/] {e}")

def run_tool_test(title, content_block):
    """
    Exécute un test de Function Calling.
    """
    console.print(f"\n[bold yellow]=== Test : {title} (Tool Use) ===[/]")
    
    messages = [
        {"role": "system", "content": PROMPT_VOICE_ASSISTANT},
        {"role": "user", "content": [content_block]}
    ]

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Analyse Audio & Sélection d'Outil...", total=None)
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS_DEFINITION,
                tool_choice="auto",
                max_tokens=200
            )
            
        message = completion.choices[0].message
        
        # Affichage du contenu textuel s'il y en a
        if message.content:
             console.print(Panel(message.content, title="Pensée / Réponse Textuelle", border_style="blue"))

        # Affichage des appels d'outils
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                console.print(Panel(
                    JSON.from_data(tool_args),
                    title=f"Tool Call: [bold magenta]{tool_name}[/]",
                    border_style="magenta"
                ))
        else:
            console.print("[yellow]Aucun outil appelé par le modèle.[/]")
            
    except Exception as e:
        console.print(f"[bold red]Erreur :[/] {e}")

def main():
    """Fonction principale."""
    print_header()
    
    # Test 1 : Audio Translation
    # Use Case : Assistant Vocal
    audio_url_1 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/translate_to_chinese.wav"
    run_test(
        "Audio Translation",
        {"type": "audio_url", "audio_url": {"url": audio_url_1}},
        "Please process this audio and translate/answer. after that, Write an alternative in french.",
        system_prompt=PROMPT_VOICE_ASSISTANT
    )
    
    # Test 2 : Audio Description
    # Use Case : Analyse Audio
    # Prompt : Aucun (Zero-shot)
    audio_url_2 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/caption1.mp3"
    run_test(
        "Audio Description",
        {"type": "audio_url", "audio_url": {"url": audio_url_2}},
        "Give the detailed description of the audio."
    )

    # Test 3 : Audio Function Calling
    # Use Case : Assistant Vocal (Actionnable)
    # Prompt : Géré automatiquement par l'API tools ou PROMPT_VOICE_ASSISTANT
    audio_url_3 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/functioncall_case.wav"
    run_tool_test(
        "Audio Function Calling",
        {"type": "audio_url", "audio_url": {"url": audio_url_3}}
    )
    
    # Test 4 : Entrée Vidéo
    # Use Case : Analyse Vidéo
    # Prompt : Aucun (Zero-shot)
    video_url = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/draw.mp4"
    run_test(
        "Vidéo Description",
        {"type": "video_url", "video_url": {"url": video_url}},
        "Describe what is happening in this video."
    )

    # Test 5 : Conversational Video Interaction
    # Use Case : Chat Vidéo (Persona Spécifique)
    # Prompt : PROMPT_CONVERSATIONAL (Spécifique)
    run_test(
        "Conversational Video Interaction",
        {"type": "video_url", "video_url": {"url": video_url}},
        "Hello! I see you are drawing something. Can you tell me what it is?",
        system_prompt=PROMPT_CONVERSATIONAL
    )

    # Test 6 : Video Scene Change Detection
    # Use Case : Analyse Vidéo Avancée
    # Prompt : Aucun (Zero-shot)
    video_url_2 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/video4.mp4"
    run_test(
        "Video Scene Change Detection",
        {"type": "video_url", "video_url": {"url": video_url_2}},
        "How the scenes in the video change?"
    )

    # Test 7 : Mixed Audio Analysis
    # Use Case : Analyse Audio Complexe
    # Prompt : Aucun (Zero-shot)
    audio_url_4 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/mixed_audio2.mp3"
    run_test(
        "Mixed Audio Analysis",
        {"type": "audio_url", "audio_url": {"url": audio_url_4}},
        "Determine which sound effects and musical instruments are present in the audio."
    )

    # Test 8 : Object Grounding
    # Use Case : Vision Technique (JSON)
    # Prompt : Aucun (Zero-shot avec consigne dans le user prompt)
    image_url_1 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/grounding1.jpeg"
    run_test(
        "Object Grounding",
        {"type": "image_url", "image_url": {"url": image_url_1}},
        "Locate the object: bird. Return the bounding box in JSON format."
    )

    # Test 9 : Video Navigation
    # Use Case : Raisonnement Spatial
    # Prompt : Aucun (Zero-shot)
    video_url_3 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/video2.mp4"
    run_test(
        "Video Navigation",
        {"type": "video_url", "video_url": {"url": video_url_3}},
        "If I want to stop at the window. Which direction should I take?"
    )

    # Test 10 : OCR
    # Use Case : Extraction Texte
    # Prompt : Aucun (Zero-shot)
    image_url_2 = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-Omni/cookbook/ocr1.jpeg"
    run_test(
        "OCR (Text Extraction)",
        {"type": "image_url", "image_url": {"url": image_url_2}},
        "Extract the text from the image."
    )

if __name__ == "__main__":
    main()
