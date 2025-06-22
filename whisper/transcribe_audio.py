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
import requests # Gardé pour l'instant pour la compatibilité si aiohttp échoue, mais sera supprimé à terme
import argparse
import os
import json
import sys
import glob
import time
import asyncio
import aiohttp
import aiofiles
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

# La fonction synchrone originale `transcribe_audio` et `print_transcription_result` sont supprimées.
# Seules les versions asynchrones subsistent.
# Le wrapper `transcribe_audio_async_wrapper` est également supprimé.

async def transcribe_audio(api_url, file_path, language, token, prompt=None, debug=False, silent=False, task_id=None):
    """
    Envoie un fichier audio à l'API Cloud Temple pour transcription (version asynchrone).
    ... (docstring reste similaire mais mentionner async)
    """
    if not token or not token.strip():
        return False, f"Token d'authentification manquant ou vide. Veuillez le fournir via l'option -t ou dans '{CONFIG_FILE}'."
    
    # Utiliser Path pour une meilleure gestion des chemins
    audio_path = Path(file_path)
    if not await asyncio.to_thread(audio_path.exists): # Vérification asynchrone de l'existence du fichier
        return False, f"Le fichier audio '{file_path}' n'a pas été trouvé."

    file_extension = audio_path.suffix.lower()
    mime_type = SUPPORTED_MIME_TYPES.get(file_extension)
    
    if not mime_type:
        print_warning(f"Extension {file_extension} non officiellement supportée, utilisation de application/octet-stream.", silent)
        mime_type = "application/octet-stream"

    if debug:
        file_size_str = await asyncio.to_thread(format_file_size, file_path)
        print_debug(f"[{task_id}] Extension détectée: {file_extension}", silent)
        print_debug(f"[{task_id}] Type MIME: {mime_type}", silent)
        print_debug(f"[{task_id}] Taille du fichier: {file_size_str}", silent)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        form_data = aiohttp.FormData()
        form_data.add_field('language', language)
        form_data.add_field('response_format', 'json')
        form_data.add_field('temperature', '0') # Garder la température à 0 pour la cohérence

        if prompt and prompt.strip():
            form_data.add_field('prompt', prompt.strip())
            if debug:
                print_debug(f"[{task_id}] Prompt utilisé: '{prompt.strip()}'", silent)
        
        async with aiofiles.open(audio_path, "rb") as afp:
            audio_content = await afp.read()
        form_data.add_field('file', audio_content, filename=audio_path.name, content_type=mime_type)
        
        if debug:
            # Affichage partiel pour FormData
            print_debug(f"[{task_id}] En-têtes de la requête (aiohttp):", silent)
            debug_headers_display = headers.copy()
            debug_headers_display["Authorization"] = f"Bearer {token[:20]}..." if len(token) > 20 else f"Bearer {token}"
            if not silent:
                # Affichage des champs non-fichier
                data_fields_for_debug = {
                    "language": language, "response_format": "json", "temperature": "0"
                }
                if prompt and prompt.strip(): data_fields_for_debug["prompt"] = prompt.strip()
                async with print_lock: # Protéger l'affichage
                    pretty_print_json(debug_headers_display, f"Task {task_id} Headers", TermColors.DEBUG)
                    pretty_print_json(data_fields_for_debug, f"Task {task_id} Request Data (non-file parts)", TermColors.DEBUG)
            print_debug(f"[{task_id}] Fichier: {audio_path.name} ({mime_type})", silent)

        print_info(f"[{task_id}] Envoi du fichier '{TermColors.BOLD}{audio_path.name}{TermColors.ENDC}' "
                  f"({await asyncio.to_thread(format_file_size, file_path)}) pour transcription en langue '{TermColors.BOLD}{language}{TermColors.ENDC}'...", silent)

        # Utiliser un timeout pour la session aiohttp
        timeout = aiohttp.ClientTimeout(total=300) # Timeout total de 5 minutes, ajustable
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_url, headers=headers, data=form_data) as response:
                response_text = await response.text()
                if debug:
                    print_debug(f"[{task_id}] Code de réponse HTTP: {response.status}", silent)
                    print_debug(f"[{task_id}] En-têtes de réponse: {dict(response.headers)}", silent)

                if response.status == 200:
                    try:
                        result_json = await response.json(content_type=None) # Accepter tout type de contenu pour le JSON
                        if debug and not silent:
                            async with print_lock:
                                pretty_print_json(result_json, f"Task {task_id} Response JSON", TermColors.OKGREEN)
                        
                        transcribed_text = result_json.get("text", "Aucun texte détecté dans la réponse JSON.")
                        return True, transcribed_text
                    except (json.JSONDecodeError, aiohttp.ContentTypeError) as json_err:
                        if debug:
                            print_debug(f"[{task_id}] Réponse brute (non-JSON ou erreur de décodage): {response_text}. Erreur: {json_err}", silent)
                        # Retourner le texte brut si le JSON échoue mais le statut est 200
                        return True, f"Réponse reçue (statut 200, non-JSON ou erreur décodage): {response_text}"
                elif response.status == 401:
                    return False, "Erreur d'authentification (401). Vérifiez votre token."
                else:
                    error_message = f"Erreur API (code {response.status}): {response_text}"
                    try:
                        error_json = json.loads(response_text)
                        if debug and not silent:
                            async with print_lock:
                                pretty_print_json(error_json, f"Task {task_id} Error Response JSON", TermColors.FAIL)
                        error_message += f"\nDétail de l'erreur JSON: {error_json}"
                    except json.JSONDecodeError:
                        if debug:
                            print_debug(f"[{task_id}] Réponse d'erreur brute: {response_text}", silent)
                    return False, error_message

    except FileNotFoundError: # Devrait être attrapé par la vérification Path.exists() plus haut
        return False, f"Le fichier audio '{file_path}' n'a pas été trouvé."
    except aiohttp.ClientError as e:
        return False, f"Erreur de connexion à l'API (aiohttp) pour la tâche {task_id}: {e}"
    except Exception as e:
        return False, f"Une erreur inattendue est survenue dans la tâche {task_id}: {e}"

print_lock = asyncio.Lock() # Remplacer threading.Lock par asyncio.Lock

async def main_async(args, config):
    """Fonction principale asynchrone pour gérer les transcriptions."""
    # Utiliser des variables locales à main_async pour les stats, puis les retourner
    local_total_success = 0
    local_total_errors = 0

    if not args.token or not args.token.strip() or args.token == "VOTRE_TOKEN_BEARER_ICI":
        fatal_error(f"Token d'authentification manquant ou invalide. "
                   f"Veuillez le fournir via l'option -t ou le configurer dans '{CONFIG_FILE}'.", args.silent)

    if args.debug and not args.silent:
        print_debug("Mode debug activé", args.silent)
        print_debug(f"Configuration chargée depuis: {CONFIG_FILE}", args.silent)
        print_debug(f"URL API: {args.api_url}", args.silent)
        print_debug(f"Langue: {args.language}", args.silent)
        print_debug(f"Prompt: {args.prompt if args.prompt else 'Aucun'}", args.silent)
        print_debug(f"Passes: {args.runs}", args.silent)
        print_debug(f"Concurrence: {args.concurrency}", args.silent)

    print_info(f"Utilisation de l'URL API: {TermColors.UNDERLINE}{args.api_url}{TermColors.ENDC}", args.silent)
    
    files_to_process_patterns = expand_file_patterns(args.file_patterns, args.silent)
    
    if not files_to_process_patterns:
        fatal_error("Aucun fichier audio trouvé correspondant aux patterns spécifiés.", args.silent)
    
    if args.debug and not args.silent:
        print_debug(f"Fichiers trouvés (avant répétition pour les passes): {len(files_to_process_patterns)}", args.silent)
        for f_path in files_to_process_patterns:
            print_debug(f"  - {f_path} ({format_file_size(f_path)})", args.silent)

    # Créer la liste complète des tâches à exécuter (fichier * nombre de passes)
    all_tasks_to_run = []
    task_counter = 0
    for run_idx in range(args.runs):
        for file_idx, file_path in enumerate(files_to_process_patterns):
            task_counter +=1
            all_tasks_to_run.append({
                "file_path": file_path,
                "run_index": run_idx + 1,
                "file_index_in_run": file_idx + 1,
                "total_files_in_run": len(files_to_process_patterns),
                "task_id": task_counter # ID unique pour chaque requête
            })

    print_info(f"Lancement de {TermColors.BOLD}{len(all_tasks_to_run)}{TermColors.ENDC} tâche(s) de transcription au total, "
              f"avec une concurrence maximale de {TermColors.BOLD}{args.concurrency}{TermColors.ENDC} tâche(s).", args.silent)

    semaphore = asyncio.Semaphore(args.concurrency)
    tasks_coroutines = [] # Renommé pour plus de clarté

    async def transcribe_with_semaphore(task_info):
        # Cette fonction retourne maintenant True pour succès, False pour échec.
        # Le comptage se fera dans main_async après asyncio.gather.
        async with semaphore:
            success, result = await transcribe_audio(
                args.api_url,
                task_info["file_path"],
                args.language,
                args.token,
                args.prompt,
                args.debug,
                args.silent,
                task_info["task_id"]
            )
            
            # Utiliser print_lock pour l'affichage
            if args.silent:
                if success:
                    # En mode silencieux, on pourrait vouloir un format plus simple ou pas de lock
                    # Pour l'instant, on garde le lock pour éviter tout entremêlement si on ajoute des logs
                    async with print_lock:
                        print(result.strip())
            else:
                await print_transcription_result( # print_transcription_result est maintenant asynchrone
                    task_info["file_path"],
                    args.language,
                    success,
                    result,
                    task_info["file_index_in_run"],
                    task_info["total_files_in_run"],
                    task_info["run_index"],
                    args.runs,
                    task_info["task_id"]
                )
            
            # La mise à jour des compteurs est retirée d'ici
            return success # Retourner le statut pour une éventuelle gestion centralisée des résultats

    for task_info_item in all_tasks_to_run:
        tasks_coroutines.append(transcribe_with_semaphore(task_info_item))

    # Exécuter toutes les coroutines avec asyncio.gather
    # return_exceptions=True permet de ne pas arrêter gather à la première exception
    results = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
    
    # Compter les succès et erreurs à partir des résultats de gather
    for result_item in results:
        if isinstance(result_item, Exception):
            # Gérer les exceptions levées par les tâches si nécessaire
            # Pour l'instant, on les compte comme des erreurs.
            print_error(f"Une tâche a échoué avec une exception: {result_item}", args.silent)
            local_total_errors += 1
        elif result_item is True: # Si la tâche a retourné True (succès)
            local_total_success += 1
        else: # Si la tâche a retourné False (échec géré)
            local_total_errors += 1
            
    return local_total_success, local_total_errors, len(all_tasks_to_run)


# Adapter print_transcription_result pour être asynchrone à cause du print_lock asynchrone
async def print_transcription_result(file_path, language, success, result, file_index=None, total_files=None, run_index=None, total_runs=None, task_id=None):
    """Affiche le résultat de transcription de manière formatée (version asynchrone)."""
    prefix = ""
    if task_id is not None:
        prefix = f"[Tâche {task_id}] "
    
    file_indicator = ""
    # Ajustement pour une meilleure clarté de l'indicateur de fichier/passe
    if run_index is not None and total_runs is not None:
        if total_files > 1 : # Si plusieurs fichiers par passe
             file_indicator = f" [Passe {run_index}/{total_runs} | Fichier {file_index}/{total_files}]"
        else: # Si un seul fichier par passe (ou si total_files n'est pas pertinent pour le run_index)
             file_indicator = f" [Passe {run_index}/{total_runs}]"
    elif file_index is not None and total_files is not None: # Cas d'un seul run global, mais plusieurs fichiers
        file_indicator = f" [Fichier {file_index}/{total_files}]"

    header_line = f"{TermColors.HEADER}{'='*60}{TermColors.ENDC}"
    title_line = (f"{TermColors.HEADER}{prefix}📄 Transcription{file_indicator} - "
                  f"'{TermColors.BOLD}{os.path.basename(file_path)}{TermColors.ENDC}' "
                  f"({TermColors.BOLD}{language}{TermColors.ENDC}){TermColors.HEADER}{TermColors.ENDC}")

    async with print_lock: # Utiliser le asyncio.Lock
        print(f"\n{header_line}")
        print(title_line)
        print(header_line)
        if success:
            print(f"{TermColors.OKGREEN}{result}{TermColors.ENDC}")
        else:
            print(f"{TermColors.FAIL}❌ {result}{TermColors.ENDC}")
        print(f"{header_line}\n")


if __name__ == "__main__":
    # Initialisation des compteurs de statistiques au début de la section __main__
    final_success_count = 0
    final_error_count = 0
    total_tasks_executed = 0 # Assurer l'initialisation

    config_data = load_config() # Charger la config en mode non-silencieux initialement
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
    
    # --- Nouvelles options pour les tests de charge ---
    parser.add_argument(
        "-r", "--runs",
        type=int,
        default=1,
        help="Nombre total de passes à exécuter. Défaut: 1"
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=1,
        help="Nombre de requêtes parallèles par passe. Défaut: 1"
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
        print_debug(f"Passes: {args.runs}", args.silent)
        print_debug(f"Concurrence: {args.concurrency}", args.silent)

    print_info(f"Utilisation de l'URL API: {TermColors.UNDERLINE}{args.api_url}{TermColors.ENDC}", args.silent)
    
    # Expansion des patterns de fichiers
    files_to_process = expand_file_patterns(args.file_patterns, args.silent)
    
    if not files_to_process:
        fatal_error("Aucun fichier audio trouvé correspondant aux patterns spécifiés.", args.silent)
    
    if args.debug and not args.silent:
        print_debug(f"Fichiers trouvés: {len(files_to_process)}", args.silent)
        for f in files_to_process:
            print_debug(f"  - {f} ({format_file_size(f)})", args.silent)

    # --- Logique de test de charge (maintenant asynchrone) ---
    global_start_time = time.time()
    
    # Exécuter la logique principale asynchrone
    loop = asyncio.get_event_loop()
    try:
        # Récupérer les stats depuis main_async
        # final_success_count, final_error_count, et total_tasks_executed sont mis à jour ici.
        final_success_count, final_error_count, total_tasks_executed = loop.run_until_complete(main_async(args, config))
    except KeyboardInterrupt:
        print_warning("\nInterruption par l'utilisateur. Arrêt des tâches...", args.silent)
        # Les valeurs de final_success_count, final_error_count, total_tasks_executed 
        # resteront à leurs valeurs initiales (0) si l'interruption se produit avant la fin de main_async.
        # Gérer l'annulation des tâches en cours si nécessaire (plus complexe avec gather)
        # Pour l'instant, on laisse les tâches se terminer ou être annulées par l'arrêt de la boucle
        sys.exit(1)
    finally:
        # S'assurer que la boucle d'événements est correctement fermée
        # loop.close() # Peut causer des erreurs si la boucle est déjà fermée ou utilisée ailleurs

        global_end_time = time.time()
        total_duration = global_end_time - global_start_time
        
        # Résumé final (seulement en mode non-silent)
        if not args.silent:
            print(f"\n{TermColors.HEADER}📊 RÉSUMÉ FINAL DES TESTS DE CHARGE{TermColors.ENDC}")
            print(f"{TermColors.OKCYAN}Durée totale: {total_duration:.2f} secondes{TermColors.ENDC}")
            print(f"{TermColors.OKCYAN}Nombre de passes configurées: {args.runs}{TermColors.ENDC}")
            print(f"{TermColors.OKCYAN}Concurrence maximale: {args.concurrency}{TermColors.ENDC}")
            
            # Le nombre de fichiers par passe n'est plus directement pertinent de la même manière
            # On affiche le nombre total de fichiers uniques traités si args.runs > 1
            # ou simplement le nombre de fichiers si args.runs == 1
            num_unique_files = len(expand_file_patterns(args.file_patterns, True)) # True pour silent
            if args.runs > 1:
                 print(f"{TermColors.OKCYAN}Nombre de fichiers uniques par passe: {num_unique_files}{TermColors.ENDC}")
            else:
                 print(f"{TermColors.OKCYAN}Nombre de fichiers traités: {num_unique_files}{TermColors.ENDC}")

            print(f"{TermColors.BOLD}Requêtes totales effectuées: {total_tasks_executed}{TermColors.ENDC}")
            print(f"{TermColors.OKGREEN}✅ Succès: {final_success_count}{TermColors.ENDC}")
            if final_error_count > 0:
                print(f"{TermColors.FAIL}❌ Erreurs: {final_error_count}{TermColors.ENDC}")
            
            if total_duration > 0 and total_tasks_executed > 0:
                rps = total_tasks_executed / total_duration
                print(f"{TermColors.OKCYAN}Performance: {rps:.2f} requêtes/seconde{TermColors.ENDC}")
            
            # Le "temps moyen par passe" est moins significatif avec la concurrence totale.
            # On pourrait calculer le temps moyen par tâche si pertinent.
            if total_tasks_executed > 0:
                avg_task_time = total_duration / total_tasks_executed
                print(f"{TermColors.OKCYAN}Temps moyen par tâche (incluant attente sémaphore): {avg_task_time:.2f} secondes{TermColors.ENDC}")
