#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PhotoAnalyzer Python CLI - Analyse d'Images avec IA Multimodale.

Ce script analyse des images en utilisant l'API LLMaaS avec des modèles multimodaux.
Il offre une interface utilisateur soignée avec modes debug, formats de sortie multiples,
et support de différents types de prompts d'analyse.
"""

import os
import argparse
import json
import time
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

# Importations des modules locaux
from cli_ui import print_message, print_debug_data, console, TermColors
from api_utils import analyze_image_api, analyze_image_ollama
from image_utils import load_and_validate_image, encode_image_to_base64, get_image_info

# --- Configuration par défaut ---
DEFAULT_CONFIG_FILENAME = "config.json"
DEFAULT_OUTPUT_DIR = "./photoanalyzer_outputs"
DEFAULT_MODEL = "qwen2.5vl:7b"
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TIMEOUT = 120

# --- Prompts d'analyse prédéfinis ---
ANALYSIS_PROMPTS = {
    "general": "Décris cette image de manière détaillée. Identifie tous les éléments visuels importants, les personnes, objets, lieux, couleurs, et l'ambiance générale.",
    "technical": "Analyse cette image d'un point de vue technique : qualité, composition, éclairage, résolution apparente, et aspects techniques visuels.",
    "people": "Décris les personnes présentes dans cette image : nombre, âges approximatifs, vêtements, expressions, postures et interactions.",
    "objects": "Identifie et décris tous les objets visibles dans cette image, leur état, leur position et leur fonction apparente.",
    "scene": "Décris la scène représentée : lieu, contexte, événement, ambiance, conditions d'éclairage et moment de la journée.",
    "colors": "Analyse les couleurs de cette image : palette principale, contrastes, harmonie chromatique et impact visuel des couleurs.",
    "composition": "Analyse la composition de cette image : cadrage, règle des tiers, lignes directrices, points focaux et équilibre visuel.",
    "emotions": "Analyse l'aspect émotionnel de cette image : ambiance, sentiments transmis, expressions faciales et atmosphère générale.",
    "text": "Identifie et transcris tout texte visible dans cette image (panneaux, affiches, documents, etc.).",
    "security": "Analyse cette image sous l'angle sécuritaire : éléments de sécurité visibles, vulnérabilités potentielles, équipements de protection.",
    "medical": "Analyse cette image d'un point de vue médical si applicable : signes visuels, équipements médicaux, conditions observables (ATTENTION: consultation médicale requise).",
    "count": "Compte précisément tous les éléments dénombrables dans cette image (personnes, objets, véhicules, etc.) et fournis des totaux."
}

class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Formateur d'aide personnalisé pour colorer la sortie d'aide."""
    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        return f"{TermColors.OKCYAN}{', '.join(action.option_strings)}{TermColors.ENDC} {self._format_args(action, self._get_default_metavar_for_optional(action))}"

    def format_help(self):
        help_text = super().format_help()
        help_text = help_text.replace('usage:', f'{TermColors.BOLD}Usage:{TermColors.ENDC}')
        help_text = help_text.replace('options:', f'{TermColors.BOLD}Options:{TermColors.ENDC}')
        help_text = help_text.replace('positional arguments:', f'{TermColors.BOLD}Arguments Positionnels:{TermColors.ENDC}')
        
        return help_text

def load_configuration(config_path: Optional[str], silent: bool, debug_mode: bool) -> Dict[str, Any]:
    """Charge la configuration depuis un fichier JSON et les variables d'environnement."""
    config = {
        "api_url": None,
        "api_key": None,
        "default_model": DEFAULT_MODEL,
        "default_max_tokens": DEFAULT_MAX_TOKENS,
        "default_temperature": DEFAULT_TEMPERATURE,
        "output_directory": DEFAULT_OUTPUT_DIR,
        "default_analysis_type": "general",
        "default_timeout": DEFAULT_TIMEOUT
    }

    # Charger les variables d'environnement
    load_dotenv()
    env_api_key = os.getenv("LLMAAS_API_KEY")
    env_api_url = os.getenv("LLMAAS_API_URL")

    if env_api_key:
        config["api_key"] = env_api_key
    if env_api_url:
        config["api_url"] = env_api_url
    
    # Déterminer le chemin du fichier de configuration
    actual_config_path = config_path or os.path.join(os.path.dirname(__file__), DEFAULT_CONFIG_FILENAME)
    
    if os.path.exists(actual_config_path):
        try:
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Fusionner la configuration du fichier
            config["api_url"] = file_config.get("api_url", config["api_url"])
            config["api_key"] = file_config.get("api_token", config["api_key"])  # 'api_token' dans JSON
            config["default_model"] = file_config.get("default_model", config["default_model"])
            config["default_max_tokens"] = file_config.get("default_max_tokens", config["default_max_tokens"])
            config["default_temperature"] = file_config.get("default_temperature", config["default_temperature"])
            config["output_directory"] = file_config.get("output_directory", config["output_directory"])
            config["default_analysis_type"] = file_config.get("default_analysis_type", config["default_analysis_type"])
            config["default_timeout"] = file_config.get("default_timeout", config["default_timeout"])
            
            print_message(f"Configuration chargée depuis '{actual_config_path}'.", silent=silent, debug_mode=debug_mode)
        except json.JSONDecodeError:
            print_message(f"Erreur de décodage JSON dans '{actual_config_path}'. Utilisation des valeurs par défaut/CLI.", style="error", silent=silent, debug_mode=debug_mode)
        except Exception as e:
            print_message(f"Erreur lors du chargement de '{actual_config_path}': {e}. Utilisation des valeurs par défaut/CLI.", style="error", silent=silent, debug_mode=debug_mode)
    elif config_path and config_path != DEFAULT_CONFIG_FILENAME:
        print_message(f"Fichier de configuration '{config_path}' non trouvé. Utilisation des valeurs par défaut/CLI.", style="warning", silent=silent, debug_mode=debug_mode)
    
    return config

def save_analysis_result(
    result: str,
    output_file: Optional[str],
    output_dir: str,
    image_filename: str,
    analysis_type: str,
    silent: bool,
    debug_mode: bool
) -> Optional[str]:
    """Sauvegarde le résultat de l'analyse dans un fichier."""
    if not output_file:
        return None
    
    output_path = Path(output_file)
    
    # Si ce n'est pas un chemin absolu, utiliser le répertoire de sortie
    if not output_path.is_absolute():
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Si pas d'extension, générer un nom automatique
        if '.' not in output_file:
            timestamp = int(time.time())
            base_name = Path(image_filename).stem
            output_file = f"{base_name}_{analysis_type}_{timestamp}.txt"
        
        output_path = output_dir_path / output_file
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print_message(f"Analyse sauvegardée dans : {output_path}", style="success", silent=silent, debug_mode=debug_mode)
        return str(output_path)
    except IOError as e:
        print_message(f"Erreur lors de la sauvegarde dans '{output_path}': {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None

def run_image_analysis_pipeline(args):
    """Exécute le pipeline d'analyse d'image principal."""
    start_time = time.time()
    
    # Assurer que le répertoire du script est utilisé pour trouver config.json par défaut
    script_dir = os.path.dirname(__file__)
    default_config_path_in_script_dir = os.path.join(script_dir, DEFAULT_CONFIG_FILENAME)

    cfg_input_path = args.config_file
    if args.config_file == DEFAULT_CONFIG_FILENAME and not os.path.exists(args.config_file):
        if os.path.exists(default_config_path_in_script_dir):
            cfg_input_path = default_config_path_in_script_dir

    # Charger la configuration
    cfg = load_configuration(cfg_input_path, args.silent, args.debug)

    # Résoudre les paramètres finaux
    cfg_api_url = args.api_url if args.api_url is not None else cfg["api_url"]
    cfg_ollama_url = args.ollama_url # Nouvelle option
    cfg_api_key = args.api_key if args.api_key is not None else cfg["api_key"]
    cfg_model = args.model if args.model is not None else cfg["default_model"]
    cfg_max_tokens = args.max_tokens if args.max_tokens is not None else cfg["default_max_tokens"]
    cfg_temperature = args.temperature if args.temperature is not None else cfg["default_temperature"]
    cfg_output_directory = args.output_dir if args.output_dir is not None else cfg["output_directory"]
    cfg_analysis_type = args.analysis_type if args.analysis_type is not None else cfg["default_analysis_type"]
    cfg_timeout = args.timeout if args.timeout is not None else cfg["default_timeout"]
    
    image_file_path = args.image_file_path
    output_file = args.output_file
    custom_prompt = args.custom_prompt
    debug_mode = args.debug
    silent_mode = args.silent

    # Si on utilise une URL Ollama, on court-circuite la logique LLMaaS
    if cfg_ollama_url:
        print_message(f"Utilisation du backend Ollama direct : {cfg_ollama_url}", style="info", silent=silent_mode, debug_mode=debug_mode)
    else:
        # Vérifications des paramètres requis pour LLMaaS
        if not cfg_api_url:
            print_message("URL de l'API LLMaaS manquante. Utilisez --api-url ou configurez config.json.", style="error", silent=silent_mode, debug_mode=debug_mode)
            return
        if not cfg_api_key:
            print_message("Clé API LLMaaS manquante. Utilisez --api-key ou configurez config.json/env.", style="error", silent=silent_mode, debug_mode=debug_mode)
            return

    # Affichage de la configuration en mode debug
    if debug_mode and not silent_mode:
        print_debug_data("Configuration Active", cfg, silent=silent_mode, debug_mode=debug_mode)
        resolved_options = {
            "Image File Path": image_file_path,
            "Output File": output_file or "Non spécifié (stdout)",
            "API URL (LLMaaS)": cfg_api_url,
            "Ollama URL": cfg_ollama_url or "Non utilisé",
            "API Key": f"{cfg_api_key[:5]}..." if cfg_api_key else "Non fournie",
            "Model": cfg_model,
            "Max Tokens": cfg_max_tokens,
            "Temperature": cfg_temperature,
            "Timeout": cfg_timeout,
            "Analysis Type": cfg_analysis_type,
            "Custom Prompt": custom_prompt or "Aucun",
            "Output Directory": cfg_output_directory,
            "Debug Mode": debug_mode,
            "Silent Mode": silent_mode
        }
        print_debug_data("Options Résolues pour l'Analyse", resolved_options, silent=silent_mode, debug_mode=debug_mode)

    # Charger et valider l'image
    print_message("Chargement et validation de l'image...", silent=silent_mode, debug_mode=debug_mode)
    
    if not load_and_validate_image(image_file_path, silent=silent_mode, debug_mode=debug_mode):
        return

    # Obtenir les informations sur l'image
    image_info = get_image_info(image_file_path, silent=silent_mode, debug_mode=debug_mode)
    if image_info and debug_mode and not silent_mode:
        print_debug_data("Informations Image", image_info, silent=silent_mode, debug_mode=debug_mode)

    # Encoder l'image en base64
    print_message("Encodage de l'image en base64...", silent=silent_mode, debug_mode=debug_mode)
    
    image_base64 = encode_image_to_base64(image_file_path, silent=silent_mode, debug_mode=debug_mode)
    if not image_base64:
        print_message("Échec de l'encodage de l'image.", style="error", silent=silent_mode, debug_mode=debug_mode)
        return

    # Déterminer le prompt à utiliser
    if custom_prompt:
        final_prompt = custom_prompt
        prompt_source = "prompt personnalisé"
    elif cfg_analysis_type in ANALYSIS_PROMPTS:
        final_prompt = ANALYSIS_PROMPTS[cfg_analysis_type]
        prompt_source = f"prompt prédéfini '{cfg_analysis_type}'"
    else:
        final_prompt = ANALYSIS_PROMPTS["general"]
        prompt_source = "prompt prédéfini 'general' (par défaut)"
        print_message(f"Type d'analyse '{cfg_analysis_type}' non reconnu, utilisation du prompt général.", style="warning", silent=silent_mode, debug_mode=debug_mode)

    print_message(f"Utilisation du {prompt_source}.", silent=silent_mode, debug_mode=debug_mode)
    
    if debug_mode and not silent_mode:
        print_debug_data("Prompt Final", {"prompt": final_prompt}, silent=silent_mode, debug_mode=debug_mode)

    # Validation et préparation des dimensions d'image
    resized_width = args.resized_width
    resized_height = args.resized_height
    
    # Vérifier la cohérence des dimensions CLI (les deux doivent être spécifiées ou aucune)
    if (resized_width is None) != (resized_height is None):
        print_message("Erreur: Les dimensions largeur et hauteur doivent être spécifiées ensemble ou pas du tout.", style="error", silent=silent_mode, debug_mode=debug_mode)
        return
    
    # Pour Qwen2.5-VL, pas besoin de dimensions spécifiques - utiliser résolution native par défaut
    if resized_width is None and resized_height is None:
        # Laisser Qwen2.5-VL utiliser la résolution native de l'image
        print_message("Utilisation de la résolution native de l'image (recommandé pour Qwen2.5-VL).", style="info", silent=silent_mode, debug_mode=debug_mode)
        resized_width = None
        resized_height = None
    else:
        # Validation des dimensions spécifiées si fournies
        if resized_width is not None and resized_width <= 0:
            print_message("Erreur: La largeur doit être positive.", style="error", silent=silent_mode, debug_mode=debug_mode)
            return
        
        if resized_height is not None and resized_height <= 0:
            print_message("Erreur: La hauteur doit être positive.", style="error", silent=silent_mode, debug_mode=debug_mode)
            return
        
        if resized_width is not None and resized_height is not None:
            print_message(f"Utilisation des dimensions spécifiées : {resized_width}x{resized_height}.", style="info", silent=silent_mode, debug_mode=debug_mode)

    # Exécuter l'analyse via l'API
    print_message(f"Analyse de l'image avec le modèle {cfg_model}...", style="info", silent=silent_mode, debug_mode=debug_mode)
    
    # Détecter le format de l'image
    image_format = "jpeg"  # Par défaut
    if image_file_path.lower().endswith('.png'):
        image_format = "png"
    elif image_file_path.lower().endswith('.webp'):
        image_format = "webp"
    elif image_file_path.lower().endswith(('.jpg', '.jpeg')):
        image_format = "jpeg"
    
    # Calculer min_pixels et max_pixels si dimensions spécifiées
    min_pixels = None
    max_pixels = None
    if resized_width is not None and resized_height is not None:
        total_pixels = resized_width * resized_height
        min_pixels = total_pixels
        max_pixels = total_pixels

    analysis_result = None
    if cfg_ollama_url:
        # Appel direct à Ollama
        analysis_result = analyze_image_ollama(
            ollama_url=cfg_ollama_url,
            model=cfg_model,
            image_base64=image_base64,
            prompt=final_prompt,
            silent=silent_mode,
            debug_mode=debug_mode,
            timeout=cfg_timeout
        )
    else:
        # Appel à l'API LLMaaS
        analysis_result = analyze_image_api(
            api_url=cfg_api_url,
            api_key=cfg_api_key,
            model=cfg_model,
            image_base64=image_base64,
            prompt=final_prompt,
            max_tokens=cfg_max_tokens,
            temperature=cfg_temperature,
            silent=silent_mode,
            debug_mode=debug_mode,
            timeout=cfg_timeout,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
            image_format=image_format
        )

    if not analysis_result:
        print_message("Échec de l'analyse de l'image.", style="error", silent=silent_mode, debug_mode=debug_mode)
        return

    # Afficher le résultat
    if not silent_mode:
        console.rule("[bold green]Résultat de l'Analyse")
        console.print(analysis_result)
        console.rule()
    else:
        # En mode silencieux, afficher seulement le résultat
        console.print(analysis_result)

    # Sauvegarder le résultat si demandé
    if output_file:
        saved_path = save_analysis_result(
            analysis_result,
            output_file,
            cfg_output_directory,
            image_file_path,
            cfg_analysis_type,
            silent_mode,
            debug_mode
        )

    # Affichage du temps d'exécution
    end_time = time.time()
    total_duration_sec = end_time - start_time
    print_message(f"Analyse terminée en {total_duration_sec:.2f} secondes.", style="info", silent=silent_mode, debug_mode=debug_mode)

def list_analysis_types():
    """Affiche la liste des types d'analyse disponibles."""
    console.rule("[bold blue]Types d'Analyse Disponibles")
    
    for analysis_type, description in ANALYSIS_PROMPTS.items():
        console.print(f"[bold cyan]{analysis_type}[/bold cyan]:")
        console.print(f"  {description}")
        console.print()

if __name__ == '__main__':
    # Création du parser avec argparse
    parser = argparse.ArgumentParser(
        description=f"{TermColors.HEADER}{TermColors.BOLD}📸 PhotoAnalyzer Python CLI - Analyse d'Images avec IA Multimodale 📸{TermColors.ENDC}\n{(__doc__ or '').strip()}",
        formatter_class=ColoredHelpFormatter,
        epilog=f"""{TermColors.OKGREEN}{TermColors.BOLD}Exemples d'utilisation:{TermColors.ENDC}
  {TermColors.OKCYAN}python photoanalyzer.py image.jpg{TermColors.ENDC}
  {TermColors.OKCYAN}python photoanalyzer.py photo.png -o description.txt --debug{TermColors.ENDC}
  {TermColors.OKCYAN}python photoanalyzer.py image.jpg -t people -m "qwen2.5-vl:7b"{TermColors.ENDC}
  {TermColors.OKCYAN}python photoanalyzer.py screenshot.png -p "Analyse ce contenu technique"{TermColors.ENDC}
  {TermColors.OKCYAN}python photoanalyzer.py photo.jpg --silent > description.txt{TermColors.ENDC}"""
    )

    parser.add_argument('image_file_path', metavar="IMAGE_FILE_PATH", type=str, help="Chemin vers le fichier image à analyser.")
    parser.add_argument('-o', '--output-file', type=str, help="Fichier pour sauvegarder l'analyse (extension ajoutée automatiquement si absente).")
    
    # Options de connexion
    parser.add_argument('-c', '--config-file', type=str, default=DEFAULT_CONFIG_FILENAME, help=f"Chemin vers le fichier de configuration JSON (défaut: {DEFAULT_CONFIG_FILENAME}).")
    parser.add_argument('--api-url', type=str, help="URL de l'API LLMaaS (prioritaire sur la config).")
    parser.add_argument('--api-key', type=str, help="Clé API pour LLMaaS (prioritaire sur la config).")
    parser.add_argument('--ollama-url', type=str, help="URL d'un backend Ollama direct (ex: http://localhost:11434). Court-circuite l'API LLMaaS.")

    # Options d'analyse
    parser.add_argument('-m', '--model', type=str, help=f"Modèle multimodal à utiliser (défaut: {DEFAULT_MODEL}).")
    parser.add_argument('-t', '--analysis-type', type=str, choices=list(ANALYSIS_PROMPTS.keys()), help="Type d'analyse prédéfini à effectuer.")
    parser.add_argument('-p', '--custom-prompt', type=str, help="Prompt personnalisé pour l'analyse (prioritaire sur --analysis-type).")
    parser.add_argument('--max-tokens', type=int, help=f"Nombre maximum de tokens à générer (défaut: {DEFAULT_MAX_TOKENS}).")
    parser.add_argument('--temperature', type=float, help=f"Température pour la génération (0.0-1.0) (défaut: {DEFAULT_TEMPERATURE}).")
    parser.add_argument('--timeout', type=int, help=f"Timeout pour la requête API en secondes (défaut: {DEFAULT_TIMEOUT}).")
    parser.add_argument('--output-dir', type=str, help=f"Répertoire pour sauvegarder les analyses (défaut: {DEFAULT_OUTPUT_DIR}).")
    parser.add_argument('--resized-width', type=int, help="Largeur de redimensionnement de l'image (doit être multiple de 28).")
    parser.add_argument('--resized-height', type=int, help="Hauteur de redimensionnement de l'image (doit être multiple de 28).")
    parser.add_argument('--list-types', action='store_true', help="Afficher la liste des types d'analyse disponibles et quitter.")
    parser.add_argument('--debug', action='store_true', help="Activer le mode de débogage verbeux.")
    parser.add_argument('--silent', action='store_true', help="Mode silencieux: affiche uniquement le résultat de l'analyse.")
    
    parsed_args = parser.parse_args()
    
    # Gestion de l'option --list-types
    if parsed_args.list_types:
        list_analysis_types()
        sys.exit(0)
    
    # Vérifier si le fichier image existe
    if not os.path.exists(parsed_args.image_file_path):
        try:
            print_message(f"Erreur: Le fichier image spécifié '{parsed_args.image_file_path}' n'existe pas.", style="error")
        except NameError:
            print(f"ERREUR: Le fichier image spécifié '{parsed_args.image_file_path}' n'existe pas.")
        sys.exit(1)

    run_image_analysis_pipeline(parsed_args)
