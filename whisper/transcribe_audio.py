# -*- coding: utf-8 -*-
"""
Script de Transcription Audio via l'API LLMaaS.

Ce script envoie un ou plusieurs fichiers audio (WAV, MP3, M4A, etc.) à l'API de transcription
audio de Cloud Temple (compatible Whisper) et affiche le texte transcrit.
Il gère la configuration via un fichier JSON et des arguments de ligne de commande.

Nouvelles fonctionnalités (v2.0.0) :
- Mode debug avec affichage des payloads
- Support du prompt pour guider Whisper
- Support des wildcards pour traiter plusieurs fichiers
- Support du format M4A

Auteur: Cloud Temple - LLMaaS Team
Version: 2.0.0
Date: 2025-06-04
"""
import requests
import argparse
import os
import json
import sys
import glob
from pathlib import Path

# --- Configuration ---
# Construire le chemin absolu vers config.json, en supposant qu'il est dans le même répertoire que le script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
DEFAULT_API_URL = "https://api.ai.cloud-temple.com/v1/audio/transcriptions"
DEFAULT_LANGUAGE = "fr"

# Types MIME supportés
SUPPORTED_MIME_TYPES = {
    ".wav": "audio/x-wav",
    ".mp3": "audio/mpeg", 
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm"
}

# --- Couleurs pour la console ---
class TermColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DEBUG = '\033[90m'  # Gris pour le debug

def print_info(message, silent=False):
    if not silent:
        print(f"{TermColors.OKBLUE}[INFO] {message}{TermColors.ENDC}")

def print_success(message, silent=False):
    if not silent:
        print(f"{TermColors.OKGREEN}[SUCCÈS] {message}{TermColors.ENDC}")

def print_warning(message, silent=False):
    if not silent:
        print(f"{TermColors.WARNING}[ATTENTION] {message}{TermColors.ENDC}")

def print_error(message, silent=False):
    if not silent:
        print(f"{TermColors.FAIL}[ERREUR] {message}{TermColors.ENDC}")

def print_debug(message, silent=False):
    if not silent:
        print(f"{TermColors.DEBUG}[DEBUG] {message}{TermColors.ENDC}")

def fatal_error(message, silent=False):
    print_error(message, silent)
    sys.exit(1)

def pretty_print_json(data, title="JSON", color=TermColors.OKCYAN):
    """Affiche un JSON de manière formatée et colorée."""
    print(f"\n{color}{'='*10} {title} {'='*10}{TermColors.ENDC}")
    try:
        if isinstance(data, str):
            data = json.loads(data)
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        print(f"{color}{formatted_json}{TermColors.ENDC}")
    except (json.JSONDecodeError, TypeError):
        print(f"{color}{str(data)}{TermColors.ENDC}")
    print(f"{color}{'='*(22 + len(title))}{TermColors.ENDC}\n")

def format_file_size(file_path):
    """Retourne la taille d'un fichier formatée."""
    try:
        size = os.path.getsize(file_path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    except OSError:
        return "Taille inconnue"

def load_config(silent=False):
    """Charge la configuration depuis config.json."""
    if not os.path.exists(CONFIG_FILE):
        print_warning(f"Le fichier de configuration '{CONFIG_FILE}' est introuvable.", silent)
        print_warning(f"Utilisation des valeurs par défaut et nécessité de fournir un token via l'option -t.", silent)
        return {"api_url": DEFAULT_API_URL, "api_token": None, "default_language": DEFAULT_LANGUAGE}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Vérifier que les clés essentielles sont présentes, sinon utiliser les valeurs par défaut
            config.setdefault("api_url", DEFAULT_API_URL)
            config.setdefault("api_token", None) # Token peut être None si non défini
            config.setdefault("default_language", DEFAULT_LANGUAGE)
            return config
    except json.JSONDecodeError:
        fatal_error(f"Erreur de décodage du fichier JSON '{CONFIG_FILE}'. Vérifiez sa syntaxe.", silent)
    except Exception as e:
        fatal_error(f"Erreur lors du chargement de '{CONFIG_FILE}': {e}", silent)

def expand_file_patterns(patterns, silent=False):
    """Expanse les patterns avec wildcards et retourne la liste des fichiers trouvés."""
    all_files = []
    for pattern in patterns:
        # Utiliser glob pour traiter les wildcards
        matched_files = glob.glob(pattern)
        if matched_files:
            # Filtrer pour ne garder que les fichiers audio supportés
            audio_files = [f for f in matched_files if os.path.isfile(f) and 
                          os.path.splitext(f)[1].lower() in SUPPORTED_MIME_TYPES]
            all_files.extend(audio_files)
        elif os.path.isfile(pattern):
            # Si c'est un fichier spécifique sans wildcard
            all_files.append(pattern)
        else:
            print_warning(f"Aucun fichier trouvé pour le pattern: {pattern}", silent)
    
    # Supprimer les doublons tout en conservant l'ordre
    seen = set()
    unique_files = []
    for f in all_files:
        abs_path = os.path.abspath(f)
        if abs_path not in seen:
            seen.add(abs_path)
            unique_files.append(f)
    
    return unique_files

def transcribe_audio(api_url, file_path, language, token, prompt=None, debug=False, silent=False):
    """
    Envoie un fichier audio à l'API Cloud Temple pour transcription.

    Args:
        api_url (str): URL de l'API de transcription.
        file_path (str): Chemin vers le fichier audio.
        language (str): Code langue (ex: "fr", "en", "de", "es").
        token (str): Token d'authentification Bearer.
        prompt (str, optional): Prompt pour guider la transcription.
        debug (bool): Mode debug pour afficher les payloads.
        silent (bool): Mode silencieux pour supprimer l'affichage.

    Returns:
        tuple: (success: bool, result: str) - succès et texte transcrit ou message d'erreur.
    """
    if not token or not token.strip():
        return False, f"Token d'authentification manquant ou vide. Veuillez le fournir via l'option -t ou dans '{CONFIG_FILE}'."
    
    if not os.path.exists(file_path):
        return False, f"Le fichier audio '{file_path}' n'a pas été trouvé."

    # Vérifier l'extension du fichier
    file_extension = os.path.splitext(file_path)[1].lower()
    mime_type = SUPPORTED_MIME_TYPES.get(file_extension)
    
    if not mime_type:
        print_warning(f"Extension {file_extension} non officiellement supportée, utilisation de application/octet-stream.", silent)
        mime_type = "application/octet-stream"

    if debug:
        print_debug(f"Extension détectée: {file_extension}", silent)
        print_debug(f"Type MIME: {mime_type}", silent)
        print_debug(f"Taille du fichier: {format_file_size(file_path)}", silent)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        with open(file_path, "rb") as audio_file:
            files = {"file": (os.path.basename(file_path), audio_file, mime_type)}
            data = {
                "language": language, 
                "response_format": "json", 
                "temperature": "0"
            }
            
            # Ajouter le prompt s'il est fourni
            if prompt and prompt.strip():
                data["prompt"] = prompt.strip()
                if debug:
                    print_debug(f"Prompt utilisé: '{prompt.strip()}'", silent)

            if debug:
                print_debug("En-têtes de la requête:", silent)
                debug_headers = headers.copy()
                debug_headers["Authorization"] = f"Bearer {token[:20]}..." if len(token) > 20 else f"Bearer {token}"
                if not silent:
                    pretty_print_json(debug_headers, "Headers", TermColors.DEBUG)
                
                print_debug("Données de la requête:", silent)
                if not silent:
                    pretty_print_json(data, "Request Data", TermColors.DEBUG)
                
                print_debug(f"Fichier: {os.path.basename(file_path)} ({mime_type})", silent)
            
            print_info(f"Envoi du fichier '{TermColors.BOLD}{os.path.basename(file_path)}{TermColors.ENDC}' "
                      f"({format_file_size(file_path)}) pour transcription en langue '{TermColors.BOLD}{language}{TermColors.ENDC}'...", silent)
            
            response = requests.post(api_url, headers=headers, files=files, data=data)

            if debug:
                print_debug(f"Code de réponse HTTP: {response.status_code}", silent)
                print_debug(f"En-têtes de réponse: {dict(response.headers)}", silent)

            if response.status_code == 200:
                try:
                    result = response.json()
                    if debug and not silent:
                        pretty_print_json(result, "Response JSON", TermColors.OKGREEN)
                    
                    transcribed_text = result.get("text", "Aucun texte détecté dans la réponse JSON.")
                    return True, transcribed_text
                except requests.exceptions.JSONDecodeError:
                    if debug:
                        print_debug(f"Réponse brute (non-JSON): {response.text}", silent)
                    return True, f"Réponse reçue (non-JSON, statut 200): {response.text}"
            elif response.status_code == 401:
                return False, "Erreur d'authentification (401). Vérifiez votre token."
            else:
                error_message = f"Erreur API (code {response.status_code}): {response.text}"
                try:
                    error_json = response.json()
                    if debug and not silent:
                        pretty_print_json(error_json, "Error Response JSON", TermColors.FAIL)
                    error_message += f"\nDétail de l'erreur JSON: {error_json}"
                except requests.exceptions.JSONDecodeError:
                    if debug:
                        print_debug(f"Réponse d'erreur brute: {response.text}", silent)
                return False, error_message

    except FileNotFoundError:
        return False, f"Le fichier audio '{file_path}' n'a pas été trouvé."
    except requests.exceptions.RequestException as e:
        return False, f"Erreur de connexion à l'API: {e}"
    except Exception as e:
        return False, f"Une erreur inattendue est survenue: {e}"

def print_transcription_result(file_path, language, success, result, file_index=None, total_files=None):
    """Affiche le résultat de transcription de manière formatée."""
    file_indicator = ""
    if file_index is not None and total_files is not None:
        file_indicator = f" [{file_index}/{total_files}]"
    
    print(f"\n{TermColors.HEADER}{'='*60}{TermColors.ENDC}")
    print(f"{TermColors.HEADER}📄 Transcription{file_indicator} - '{TermColors.BOLD}{os.path.basename(file_path)}{TermColors.ENDC}' "
          f"({TermColors.BOLD}{language}{TermColors.ENDC}){TermColors.HEADER}{TermColors.ENDC}")
    print(f"{TermColors.HEADER}{'='*60}{TermColors.ENDC}")
    
    if success:
        print(f"{TermColors.OKGREEN}{result}{TermColors.ENDC}")
    else:
        print(f"{TermColors.FAIL}❌ {result}{TermColors.ENDC}")
    
    print(f"{TermColors.HEADER}{'='*60}{TermColors.ENDC}\n")

if __name__ == "__main__":
    config_data = load_config()
    config = config_data if isinstance(config_data, dict) else {
        "api_url": DEFAULT_API_URL, 
        "api_token": None, 
        "default_language": DEFAULT_LANGUAGE
    }
    
    # Création du parser avec une description colorée et engageante
    class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def _format_action_invocation(self, action):
            if not action.option_strings or action.nargs == 0:
                return super()._format_action_invocation(action)
            default = self._get_default_metavar_for_optional(action)
            args_string = self._format_args(action, default)
            return ', '.join(action.option_strings) + ' ' + args_string

        def format_help(self):
            help_text = super().format_help()
            # Ajouter des couleurs aux sections importantes
            help_text = help_text.replace('🎙️ Script de Transcription Audio Cloud Temple v2.0 🎙️', 
                                        f'{TermColors.HEADER}{TermColors.BOLD}🎙️ Script de Transcription Audio Cloud Temple v2.0 🎙️{TermColors.ENDC}')
            help_text = help_text.replace('Nouveautés v2.0:', f'{TermColors.OKCYAN}Nouveautés v2.0:{TermColors.ENDC}')
            help_text = help_text.replace('Exemples d\'utilisation:', f'{TermColors.OKGREEN}{TermColors.BOLD}Exemples d\'utilisation:{TermColors.ENDC}')
            help_text = help_text.replace('Formats supportés:', f'{TermColors.WARNING}Formats supportés:{TermColors.ENDC}')
            return help_text

    parser = argparse.ArgumentParser(
        description=f"🎙️ Script de Transcription Audio Cloud Temple v2.0 🎙️\n"
                    f"Ce script envoie un ou plusieurs fichiers audio à l'API Cloud Temple et affiche la transcription.\n"
                    f"Nouveautés v2.0: Mode debug, support du prompt, wildcards et M4A",
        formatter_class=ColoredHelpFormatter,
        epilog=f"""{TermColors.OKGREEN}{TermColors.BOLD}Exemples d'utilisation:{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py french.mp3{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py *.mp3 -l en --debug{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py audio/*.m4a --prompt "Fichier musical"{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py deutch.mp3 -l de -t VOTRE_TOKEN --debug{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py "recording*.wav" --language es{TermColors.ENDC}
{TermColors.OKCYAN}  python transcribe_audio.py *.mp3 --silent > transcriptions.txt{TermColors.ENDC}

{TermColors.WARNING}Formats supportés:{TermColors.ENDC} {TermColors.BOLD}{', '.join(SUPPORTED_MIME_TYPES.keys())}{TermColors.ENDC}
{TermColors.OKBLUE}Le token et la langue par défaut peuvent être configurés dans{TermColors.ENDC} {TermColors.UNDERLINE}'{CONFIG_FILE}'{TermColors.ENDC}"""
    )
    
    parser.add_argument(
        "file_patterns", 
        nargs='+',
        help="Fichier(s) audio à transcrire. Supporte les wildcards (ex: *.mp3, audio/*.m4a, recording*.wav)"
    )
    parser.add_argument(
        "-l", "--language", 
        default=config.get("default_language") or DEFAULT_LANGUAGE,
        help=f"Code langue du fichier audio (ex: fr, en, de, es). Défaut: '{config.get('default_language', DEFAULT_LANGUAGE)}'"
    )
    parser.add_argument(
        "-t", "--token", 
        default=config.get("api_token"),
        help=f"Token d'authentification Bearer pour l'API. Si non fourni, utilise la valeur de '{CONFIG_FILE}'"
    )
    parser.add_argument(
        "--api-url",
        default=config.get("api_url") or DEFAULT_API_URL,
        help=f"URL de l'API de transcription. Défaut: '{config.get('api_url', DEFAULT_API_URL)}'"
    )
    parser.add_argument(
        "-p", "--prompt",
        help="Prompt optionnel pour guider la transcription Whisper (ex: 'Conférence médicale', 'Musique classique')"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug avec affichage détaillé des payloads et requêtes"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Mode silencieux: affiche uniquement les transcriptions sur stdout (idéal pour redirection)"
    )

    args = parser.parse_args()

    # Recharger la config avec le mode silent si nécessaire
    config_data = load_config(args.silent)
    config = config_data if isinstance(config_data, dict) else {
        "api_url": DEFAULT_API_URL, 
        "api_token": None, 
        "default_language": DEFAULT_LANGUAGE
    }

    # Vérification du token
    if not args.token or not args.token.strip() or args.token == "VOTRE_TOKEN_BEARER_ICI":
        fatal_error(f"Token d'authentification manquant ou invalide. "
                   f"Veuillez le fournir via l'option -t ou le configurer dans '{CONFIG_FILE}'.", args.silent)

    if args.debug and not args.silent:
        print_debug("Mode debug activé", args.silent)
        print_debug(f"Configuration chargée depuis: {CONFIG_FILE}", args.silent)
        print_debug(f"URL API: {args.api_url}", args.silent)
        print_debug(f"Langue: {args.language}", args.silent)
        print_debug(f"Prompt: {args.prompt if args.prompt else 'Aucun'}", args.silent)

    print_info(f"Utilisation de l'URL API: {TermColors.UNDERLINE}{args.api_url}{TermColors.ENDC}", args.silent)
    
    # Expansion des patterns de fichiers
    files_to_process = expand_file_patterns(args.file_patterns, args.silent)
    
    if not files_to_process:
        fatal_error("Aucun fichier audio trouvé correspondant aux patterns spécifiés.", args.silent)
    
    if args.debug and not args.silent:
        print_debug(f"Fichiers trouvés: {len(files_to_process)}", args.silent)
        for f in files_to_process:
            print_debug(f"  - {f} ({format_file_size(f)})", args.silent)

    print_info(f"Traitement de {TermColors.BOLD}{len(files_to_process)}{TermColors.ENDC} fichier(s) audio...", args.silent)
    
    # Statistiques
    total_success = 0
    total_errors = 0
    
    # Traitement de chaque fichier
    for i, file_path in enumerate(files_to_process, 1):
        if args.debug and not args.silent:
            print_debug(f"\n--- Traitement du fichier {i}/{len(files_to_process)}: {file_path} ---", args.silent)
        
        success, result = transcribe_audio(
            args.api_url, 
            file_path, 
            args.language, 
            args.token, 
            args.prompt,
            args.debug and not args.silent,
            args.silent
        )
        
        if args.silent:
            # Mode silencieux : afficher uniquement le texte transcrit
            if success:
                print(result.strip())
            # En mode silent, on n'affiche pas les erreurs sur stdout
        else:
            # Mode normal avec formatage
            print_transcription_result(
                file_path, 
                args.language, 
                success, 
                result, 
                i, 
                len(files_to_process)
            )
        
        if success:
            total_success += 1
        else:
            total_errors += 1
    
    # Résumé final (seulement en mode non-silent)
    if not args.silent:
        print(f"\n{TermColors.HEADER}📊 RÉSUMÉ FINAL{TermColors.ENDC}")
        print(f"{TermColors.OKGREEN}✅ Succès: {total_success}{TermColors.ENDC}")
        if total_errors > 0:
            print(f"{TermColors.FAIL}❌ Erreurs: {total_errors}{TermColors.ENDC}")
        print(f"{TermColors.OKCYAN}📁 Total traité: {len(files_to_process)} fichier(s){TermColors.ENDC}")
