#!/usr/bin/env python3
"""
Démonstration de la synthèse vocale (TTS) avec l'API LLMaaS.
============================================================

Ce script est un exemple pédagogique montrant comment interagir avec l'API de synthèse vocale
de la plateforme LLMaaS (compatible OpenAI).

Objectifs de cet exemple :
1. Montrer comment authentifier et structurer une requête vers l'endpoint /v1/audio/speech.
2. Illustrer la gestion du streaming de réponse pour les fichiers audio potentiellement volumineux.
3. Proposer une interface utilisateur en ligne de commande (CLI) agréable avec 'rich'.
4. Implémenter une lecture audio cross-platform simple.

Usage:
    python tts_demo.py "Bonjour, ceci est un test." --voice alloy --output test.mp3 --play
"""

import os
import sys
import time
import argparse
import subprocess
import platform
import tempfile
from pathlib import Path

# Importation conditionnelle des librairies tierces
# Cela permet d'afficher un message d'erreur clair si l'utilisateur n'a pas installé les dépendances.
try:
    import httpx  # Client HTTP moderne et asynchrone (utilisé ici en mode synchrone pour la simplicité)
    from dotenv import load_dotenv # Gestion des fichiers .env
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Erreur: Les dépendances requises ne sont pas installées.")
    print("Veuillez installer les dépendances avec: pip install -r requirements.txt")
    sys.exit(1)

# Chargement des variables d'environnement depuis le fichier .env s'il existe
load_dotenv()

# --- Configuration ---

# URL de l'API LLMaaS
# Priorité : Argument CLI > Variable d'environnement API_URL > Valeur par défaut
DEFAULT_API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com")

# Clé API
# Priorité : Argument CLI > Variable d'environnement API_KEY > None
DEFAULT_API_KEY = os.getenv("API_KEY")

# Modèle par défaut
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "tts-1")

# Voix par défaut
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "alloy")

# Initialisation de la console Rich pour les affichages
console = Console()

def parse_args():
    """
    Configure et analyse les arguments de la ligne de commande.
    
    Returns:
        argparse.Namespace: Les arguments parsés.
    """
    parser = argparse.ArgumentParser(
        description="Client de démonstration TTS pour LLMaaS",
        epilog="Exemple: python tts_demo.py 'Bonjour le monde' -v alloy -p"
    )
    
    # Arguments positionnels
    parser.add_argument("text", nargs="?", help="Le texte à convertir en audio")
    
    # Options de source
    parser.add_argument("-f", "--file", help="Fichier texte à lire (ignorer si 'text' est fourni)")
    
    # Options TTS
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, 
                        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer", "coral", "ash", "ballad", "xi", "sage", "chef"],
                        help=f"La voix à utiliser (défaut: {DEFAULT_VOICE})")
    
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Le modèle TTS (défaut: {DEFAULT_MODEL})")
    
    parser.add_argument("-o", "--output", help="Fichier de sortie (défaut: output.<format>)")
    
    parser.add_argument("--format", default="mp3", 
                        choices=["mp3", "opus", "aac", "flac", "wav", "pcm"],
                        help="Format audio de sortie (défaut: mp3)")
    
    # Options API
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="URL de l'API LLMaaS")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Clé API (ou via env API_KEY)")
    
    # Options utilitaires
    parser.add_argument("-p", "--play", action="store_true", help="Jouer l'audio directement après génération")
    parser.add_argument("--timeout", type=float, default=300.0, help="Timeout de la requête en secondes (défaut: 300)")
    parser.add_argument("--debug", action="store_true", help="Afficher les détails techniques (payloads, headers)")
    
    return parser.parse_args()

def play_audio(file_path):
    """
    Joue le fichier audio en utilisant le lecteur par défaut du système d'exploitation.
    Cette fonction tente d'être cross-platform (Windows, macOS, Linux).
    
    Args:
        file_path (str): Le chemin vers le fichier audio à lire.
    """
    system = platform.system()
    
    console.print(f"[cyan]Lecture de {file_path}...[/]")
    
    try:
        if system == "Darwin":  # macOS
            # 'afplay' est un utilitaire standard en ligne de commande sur macOS
            subprocess.run(["afplay", file_path], check=True)
            
        elif system == "Windows":
            # Sous Windows, os.startfile ouvre le fichier avec l'application associée
            if hasattr(os, "startfile"):
                os.startfile(file_path) # type: ignore
            else:
                # Fallback pour certains environnements Windows (ex: Git Bash)
                subprocess.run(["start", file_path], shell=True, check=True)
                
        elif system == "Linux":
            # Sur Linux, c'est plus complexe car il n'y a pas de standard unique.
            # On essaie une liste de lecteurs communs.
            players = ["ffplay", "mpg123", "aplay", "paplay", "xdg-open"]
            played = False
            
            for player in players:
                try:
                    # Configuration spécifique pour ffplay pour qu'il n'ouvre pas de fenêtre (-nodisp)
                    # et se ferme à la fin (-autoexit)
                    args = [player, file_path]
                    if player == "ffplay":
                        args.extend(["-nodisp", "-autoexit", "-loglevel", "quiet"])
                    
                    # On redirige stdout/stderr pour ne pas polluer la console
                    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    played = True
                    break # Succès, on sort de la boucle
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue # Ce lecteur n'est pas dispo ou a échoué, on tente le suivant
            
            if not played:
                console.print("[yellow]Aucun lecteur audio compatible trouvé (essayé: ffplay, mpg123, aplay, paplay, xdg-open).[/]")
        else:
            console.print(f"[yellow]Lecture automatique non supportée sur le système {system}.[/]")
            
    except Exception as e:
        console.print(f"[red]Erreur lors de la lecture audio : {e}[/]")

def generate_speech(client, api_url, api_key, text, voice, model, output_format, timeout=300.0, debug=False):
    """
    Effectue l'appel API vers l'endpoint TTS et télécharge le fichier audio.
    
    Args:
        client (httpx.Client): Le client HTTP pré-configuré.
        api_url (str): L'URL de base de l'API.
        api_key (str): Le token d'authentification.
        text (str): Le texte à synthétiser.
        voice (str): La voix choisie.
        model (str): Le modèle TTS.
        output_format (str): Le format audio désiré (mp3, wav, etc.).
        timeout (float): Temps maximum d'attente pour la réponse.
        debug (bool): Si True, affiche des infos techniques.
        
    Returns:
        tuple: (bytes du fichier audio, temps de génération en secondes) ou (None, 0) en cas d'erreur.
    """
    
    # Construction de l'URL complète
    # On gère le cas où l'utilisateur a déjà inclus /v1 dans l'URL de base
    base_url = api_url.rstrip('/')
    if base_url.endswith("/v1"):
        url = f"{base_url}/audio/speech"
    else:
        url = f"{base_url}/v1/audio/speech"
    
    # Préparation des en-têtes (Authentification Bearer standard)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload JSON conforme à l'API OpenAI /v1/audio/speech
    payload = {
        "model": model,
        "input": text,
        "voice": voice,
        "response_format": output_format
    }
    
    # Affichage de debug : montre exactement ce qui est envoyé
    if debug:
        console.print(Panel(Syntax(str(payload), "json", theme="monokai"), title="[bold blue]Payload envoyé[/]", expand=False))

    start_time = time.time()
    
    try:
        # Nous utilisons client.stream() au lieu de client.post() direct.
        # Pourquoi ? Pour gérer les fichiers audio potentiellement volumineux sans tout charger en RAM d'un coup,
        # et surtout pour afficher une barre de progression fluide pendant le téléchargement.
        # Le timeout est important car la génération audio peut être longue (surtout le premier token).
        with client.stream("POST", url, headers=headers, json=payload, timeout=timeout) as response:
            
            # Vérification du code de statut HTTP
            if response.status_code != 200:
                # En cas d'erreur, on lit le corps de la réponse pour afficher le message d'erreur de l'API
                error_content = response.read().decode('utf-8')
                console.print(f"[bold red]Erreur API ({response.status_code}):[/]")
                console.print(error_content)
                return None, 0

            # Tentative de récupération de la taille totale pour la barre de progression
            # Note: Avec le chunked transfer encoding, 'content-length' peut être absent.
            total_bytes = int(response.headers.get("content-length", 0))
            
            # Récupération des métadonnées intéressantes depuis les headers de réponse
            request_id = response.headers.get("x-request-id", "N/A")
            # x-tts-duration-ms est un header spécifique ajouté par LLMaaS pour le suivi
            tts_duration = response.headers.get("x-tts-duration-ms", "N/A")
            
            if debug:
                table = Table(title="Métadonnées Réponse")
                table.add_column("Header", style="cyan")
                table.add_column("Valeur", style="green")
                table.add_row("Status", str(response.status_code))
                table.add_row("Request ID", request_id)
                table.add_row("TTS Duration (Backend)", f"{tts_duration} ms")
                table.add_row("Content Type", response.headers.get("content-type", "unknown"))
                console.print(table)

            # Lecture du flux audio chunk par chunk
            audio_data = bytearray()
            
            # Configuration de la barre de progression Rich
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                DownloadColumn(), # Affiche ex: 1.2 MB / 5.0 MB
                TransferSpeedColumn(), # Affiche ex: 500 KB/s
                console=console
            ) as progress:
                task = progress.add_task("Téléchargement audio...", total=total_bytes if total_bytes > 0 else None)
                
                # Boucle de lecture du flux
                for chunk in response.iter_bytes():
                    audio_data.extend(chunk)
                    progress.update(task, advance=len(chunk))
            
            generation_time = time.time() - start_time
            return bytes(audio_data), generation_time

    except httpx.RequestError as e:
        console.print(f"[bold red]Erreur de connexion :[/] {e}")
        return None, 0
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue :[/] {e}")
        return None, 0

def main():
    """Point d'entrée principal du script."""
    args = parse_args()
    
    # Affichage du titre
    rprint(Panel.fit("[bold cyan]LLMaaS TTS Demo[/bold cyan]\n[italic]Génération de voix par IA[/italic]"))

    # 1. Validation de la clé API
    if not args.api_key:
        console.print("[bold red]Erreur :[/] Clé API manquante.")
        console.print("Veuillez configurer le fichier [bold].env[/] (voir .env.example) ou utiliser l'option [bold]--api-key[/].")
        sys.exit(1)

    # 2. Récupération du texte à synthétiser
    text_to_speak = ""
    if args.text:
        text_to_speak = args.text
    elif args.file:
        # Lecture depuis un fichier
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text_to_speak = f.read().strip()
        except Exception as e:
            console.print(f"[bold red]Erreur de lecture du fichier :[/] {e}")
            sys.exit(1)
    
    # 3. Mode Interactif (fallback)
    if not text_to_speak:
        console.print("[yellow]Aucun texte fourni en argument. Mode interactif activé.[/]")
        text_to_speak = console.input("[bold green]Entrez le texte à synthétiser : [/]")
        if not text_to_speak:
            console.print("[red]Texte vide. Annulation.[/]")
            sys.exit(0)

    # 4.1 Normalisation du texte (Astuce pour VibeVoice/TTS-1)
    # Les modèles TTS génératifs sont souvent plus stables avec une ponctuation de fin explicite.
    # Si le texte ne finit pas par une ponctuation forte, on ajoute un point.
    if text_to_speak and text_to_speak[-1] not in ".!?":
        console.print("[dim]Note: Ajout automatique d'un point final pour améliorer la fin de phrase.[/]")
        text_to_speak += "."

    # 4.2 Détermination du mode de sortie
    # Si --output n'est pas spécifié, on ne sauvegarde pas (sauf fichier temporaire pour la lecture)
    output_file = args.output
    
    # 5. Affichage du résumé de la configuration
    console.print(f"\n[bold]Paramètres de génération :[/]")
    console.print(f" • [cyan]Modèle :[/] {args.model}")
    console.print(f" • [cyan]Voix :[/] {args.voice}")
    console.print(f" • [cyan]Format :[/] {args.format}")
    if output_file:
        console.print(f" • [cyan]Sortie :[/] {output_file}")
    else:
        console.print(f" • [cyan]Sortie :[/] [yellow]Pas de sauvegarde disque[/]")
    if args.play:
        console.print(f" • [cyan]Action :[/] Lecture automatique")
    
    console.print(f" • [cyan]Texte ([/]{len(text_to_speak)} chars[cyan]) :[/] \"{text_to_speak[:100]}{'...' if len(text_to_speak)>100 else ''}\"\n")

    # 6. Exécution de la requête API
    # On utilise verify=False ici pour simplifier les tests en environnement de développement interne
    # (si les certificats sont auto-signés). En production réelle, retirez verify=False.
    with httpx.Client(verify=False) as client:
        audio_content, duration = generate_speech(
            client, 
            args.api_url, 
            args.api_key, 
            text_to_speak, 
            args.voice, 
            args.model, 
            args.format,
            timeout=args.timeout,
            debug=args.debug
        )

    # 7. Traitement du résultat (Sauvegarde et/ou Lecture)
    if audio_content:
        file_size_kb = len(audio_content) / 1024
        
        # Cas A : Sauvegarde demandée explicitement
        if output_file:
            try:
                with open(output_file, "wb") as f:
                    f.write(audio_content)
                
                rprint(Panel(
                    f"[bold green]Génération réussie ![/]\n\n"
                    f"Fichier : [bold]{output_file}[/]\n"
                    f"Taille  : {file_size_kb:.1f} KB\n"
                    f"Temps   : {duration:.2f} s",
                    title="Résultat",
                    border_style="green"
                ))
                
                if args.play:
                    play_audio(output_file)
                    
            except Exception as e:
                console.print(f"[bold red]Erreur lors de l'écriture du fichier :[/] {e}")
                sys.exit(1)

        # Cas B : Pas de sauvegarde, mais lecture demandée
        elif args.play:
            try:
                # Création d'un fichier temporaire pour permettre la lecture par le système
                # On utilise suffix pour que le lecteur identifie le format (mp3, wav...)
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{args.format}") as temp_file:
                    temp_file.write(audio_content)
                    temp_path = temp_file.name
                
                rprint(Panel(
                    f"[bold green]Génération réussie ![/]\n\n"
                    f"Mode    : Lecture sans sauvegarde\n"
                    f"Taille  : {file_size_kb:.1f} KB\n"
                    f"Temps   : {duration:.2f} s",
                    title="Résultat",
                    border_style="green"
                ))
                
                play_audio(temp_path)
                
                # Nettoyage du fichier temporaire après lecture (ou tentative)
                # Note : Comme play_audio lance un subprocess, la suppression immédiate pourrait couper le son
                # si le subprocess est non-bloquant (comme start sous Windows).
                # Pour cet exemple simple, on laisse le fichier temporaire (il sera nettoyé par l'OS plus tard)
                # ou on attend un peu. Pour afplay/ffplay c'est bloquant donc on peut supprimer.
                try:
                    os.unlink(temp_path)
                except:
                    pass # On ignore les erreurs de suppression (ex: fichier verrouillé sous Windows)
                    
            except Exception as e:
                console.print(f"[bold red]Erreur lors de la lecture temporaire :[/] {e}")
                sys.exit(1)
        
        # Cas C : Ni sauvegarde ni lecture
        else:
            rprint(Panel(
                f"[bold green]Génération réussie ![/]\n\n"
                f"[yellow]Aucune action de sortie demandée (--output ou --play).[/]\n"
                f"Taille  : {file_size_kb:.1f} KB\n"
                f"Temps   : {duration:.2f} s",
                title="Résultat",
                border_style="yellow"
            ))

    else:
        # En cas d'échec de la génération (audio_content est None)
        sys.exit(1)

if __name__ == "__main__":
    main()
