#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Test en Boucle de l'API LLMaaS (Python).

Ce script permet de tester de manière exhaustive l'API LLMaaS en envoyant
des prompts à une liste de modèles spécifiés ou à tous les modèles disponibles.
Il offre des options pour configurer le nombre de passes, la température,
le nombre maximal de tokens, le parallélisme des requêtes et des modèles,
et génère des statistiques détaillées sur les performances.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.1.0 
Date: 2025-06-02
"""

import argparse
import json
import os
import time
import sys
from datetime import timedelta
from typing import List, Dict, Any, Optional, Tuple
import concurrent.futures
import threading

import requests # Correction: Ré-ajout de l'importation de la bibliothèque requests

# Importations de la bibliothèque Rich pour un affichage console amélioré
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.markup import escape

# La console Rich est initialisée pour permettre un affichage coloré et formaté.
# `force_terminal=True` assure que les couleurs sont toujours utilisées, même si la sortie est redirigée.
console = Console(force_terminal=True)

#region Fonctions d'affichage et utilitaires
"""
Cette section contient des fonctions utilitaires pour l'affichage formaté dans la console,
le formatage des données et la conversion des unités.
"""

def print_color(text: str, style: str, end: str = "\n"):
    """
    Affiche du texte dans la console avec une couleur et un style spécifiés.
    Utilise la bibliothèque Rich pour un rendu amélioré.

    Args:
        text (str): Le texte à afficher.
        style (str): Le style Rich à appliquer (ex: "bold red", "cyan", "magenta").
        end (str): Caractère de fin de ligne (par défaut: nouvelle ligne).
    """
    console.print(text, style=style, end=end)

def print_debug(message: str, debug_mode: bool, title: str = "[DEBUG]"):
    """
    Affiche un message de débogage si le mode debug est activé.

    Args:
        message (str): Le message de débogage.
        debug_mode (bool): Indique si le mode débogage est actif.
        title (str): Préfixe du message (par défaut: "[DEBUG]").
    """
    if debug_mode:
        print_color(f"{title} {message}", "cyan")

def print_error(message: str):
    """
    Affiche un message d'erreur en rouge gras.

    Args:
        message (str): Le message d'erreur.
    """
    print_color(f"[ERREUR] {message}", "bold red")

def print_success(message: str):
    """
    Affiche un message de succès en vert gras.

    Args:
        message (str): Le message de succès.
    """
    print_color(f"[SUCCÈS] {message}", "bold green")

def print_info(message: str):
    """
    Affiche un message d'information en jaune.

    Args:
        message (str): Le message d'information.
    """
    print_color(f"[INFO] {message}", "yellow")

def format_json_for_display(data: Any) -> str:
    """
    Formate une chaîne ou un objet JSON pour un affichage lisible.
    Tente de charger la chaîne comme JSON si ce n'est pas déjà un objet.

    Args:
        data (Any): Les données à formater (peut être une chaîne JSON ou un objet Python).

    Returns:
        str: La représentation JSON formatée ou la chaîne originale si non valide.
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        return str(data) # Retourne la chaîne originale si elle n'est pas un JSON valide

def format_elapsed_time(time_delta: timedelta) -> str:
    """
    Formate un objet timedelta en une chaîne de temps lisible (ms, s, min).

    Args:
        time_delta (timedelta): L'objet timedelta représentant une durée.

    Returns:
        str: La durée formatée.
    """
    total_seconds = time_delta.total_seconds()
    if total_seconds < 1:
        return f"{total_seconds * 1000:.0f} ms"
    if total_seconds < 60:
        return f"{total_seconds:.2f} s"
    return f"{total_seconds / 60:.2f} min"

def get_formatted_size(text: str) -> str:
    """
    Calcule la taille d'une chaîne en octets et la formate en Ko ou Mo si nécessaire.

    Args:
        text (str): La chaîne de caractères.

    Returns:
        str: La taille formatée (ex: "123 octets", "1.23 Ko", "4.56 Mo").
    """
    if not text: return "0 octets"
    bytes_count = len(text.encode('utf-8'))
    if bytes_count < 1024: return f"{bytes_count} octets"
    if bytes_count < 1024 * 1024: return f"{bytes_count / 1024:.2f} Ko"
    return f"{bytes_count / (1024 * 1024):.2f} Mo"
#endregion

#region Chargement de la configuration
"""
Cette section gère le chargement des paramètres de configuration depuis un fichier JSON
et leur surcharge éventuelle par les arguments de la ligne de commande.
"""

def load_config(config_file: str, args: argparse.Namespace) -> Tuple[Optional[str], Optional[str], int, float, int, int]:
    """
    Charge la configuration depuis un fichier JSON et applique les surcharges
    des arguments de la ligne de commande.

    Args:
        config_file (str): Nom du fichier de configuration (ex: "config.json").
        args (argparse.Namespace): Arguments parsés depuis la ligne de commande.

    Returns:
        Tuple[Optional[str], Optional[str], int, float, int, int]:
            - api_endpoint (str): L'URL de l'API LLM.
            - api_token (str): Le token d'authentification API.
            - effective_passes (int): Nombre de passes par modèle.
            - effective_temperature (float): Température par défaut pour les requêtes.
            - effective_max_tokens (int): Nombre maximal de tokens à générer.
            - effective_timeout_sec (int): Timeout en secondes pour les requêtes API.
            Retourne (None, None, 0, 0.0, 0, 0) en cas d'erreur.
    """
    # Détermine le chemin absolu du fichier de configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, config_file)
    print_debug(f"Chargement de la configuration depuis: {config_path}", args.debug)

    # Valeurs par défaut définies dans le script, utilisées si non spécifiées dans le fichier ou en CLI
    script_default_passes = 1
    script_default_temperature = 0.7
    script_default_max_tokens = 1024
    script_default_timeout = 30

    # Initialisation des valeurs effectives avec les défauts du script
    effective_passes = script_default_passes
    effective_temperature = script_default_temperature
    effective_max_tokens = script_default_max_tokens
    effective_timeout_sec = script_default_timeout
    
    api_endpoint = None
    api_token = None

    try:
        # Vérifie si le fichier de configuration existe
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")

        # Charge le contenu JSON du fichier
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Extrait les informations de l'API (endpoint et token)
        api_cfg = config.get('api', {})
        api_endpoint = api_cfg.get('endpoint')
        api_token = api_cfg.get('token')

        # Valide la présence des informations API critiques
        if not (api_endpoint and api_token):
            raise ValueError("Configuration API incomplète. 'api.endpoint' et 'api.token' sont requis.")

        # Extrait les valeurs par défaut pour les tests
        defaults_cfg = config.get('defaults', {})
        effective_passes = defaults_cfg.get('passes', effective_passes)
        effective_temperature = defaults_cfg.get('temperature', effective_temperature)
        effective_max_tokens = defaults_cfg.get('max_tokens', effective_max_tokens)
        effective_timeout_sec = defaults_cfg.get('timeout', effective_timeout_sec)

        # Les arguments de la ligne de commande ont la priorité sur les valeurs du fichier de configuration
        if args.passes is not None: effective_passes = args.passes
        if args.temperature is not None: effective_temperature = args.temperature
        if args.max_tokens is not None: effective_max_tokens = args.max_tokens
        if args.endpoint is not None: api_endpoint = args.endpoint # Surcharge de l'endpoint par CLI

        print_debug("Configuration chargée avec succès.", args.debug)
        print_debug(f"API Endpoint: {api_endpoint}", args.debug)
        print_debug(f"Passes: {effective_passes}", args.debug)
        print_debug(f"Température: {effective_temperature}", args.debug)
        print_debug(f"Max Tokens: {effective_max_tokens}", args.debug)
        print_debug(f"Timeout (secondes): {effective_timeout_sec}", args.debug)

        return api_endpoint, api_token, effective_passes, effective_temperature, effective_max_tokens, effective_timeout_sec

    except Exception as e:
        # Gère les erreurs de fichier ou de format de configuration
        print_error(f"Erreur lors du chargement de la configuration '{config_file}': {e}")
        return None, None, 0, 0.0, 0, 0
#endregion

#region Récupération des modèles disponibles
"""
Cette section contient la fonction permettant de récupérer la liste des modèles
disponibles via l'API LLMaaS.
"""

def get_available_models(endpoint: str, token: str, timeout: int, debug_mode: bool) -> Optional[List[Dict[str, Any]]]:
    """
    Récupère la liste des modèles disponibles depuis l'API LLMaaS.

    Args:
        endpoint (str): L'URL de base de l'API LLM.
        token (str): Le token d'authentification.
        timeout (int): Le timeout en secondes pour la requête HTTP.
        debug_mode (bool): Indique si le mode débogage est actif.

    Returns:
        Optional[List[Dict[str, Any]]]: Une liste de dictionnaires représentant les modèles,
                                         ou None en cas d'erreur.
    """
    print_info("Récupération de la liste des modèles disponibles...")
    # En-têtes HTTP nécessaires pour l'authentification et le type de contenu attendu
    headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}
    models_uri = f"{endpoint}/models" # Construction de l'URI pour l'endpoint /models
    print_debug(f"Requête GET vers {models_uri}", debug_mode)
    try:
        # Envoie la requête GET à l'API
        response = requests.get(models_uri, headers=headers, timeout=timeout)
        # Lève une exception HTTPError pour les codes de statut 4xx ou 5xx
        response.raise_for_status()
        models_data = response.json() # Parse la réponse JSON

        # Valide le format attendu de la réponse (un dictionnaire avec une clé 'data' qui est une liste)
        if not isinstance(models_data, dict) or 'data' not in models_data or not isinstance(models_data['data'], list):
            raise ValueError("Format de réponse API inattendu.")
        
        model_count = len(models_data['data'])
        print_success(f"Liste des modèles récupérée ({model_count} modèles)")
        if debug_mode:
            # Affiche la liste des IDs de modèles en mode debug
            print_debug(f"Modèles: {', '.join([m.get('id', 'N/A') for m in models_data['data']])}", debug_mode)
        return models_data['data']
    except requests.exceptions.RequestException as e:
        # Gère les erreurs liées aux requêtes HTTP (connexion, timeout, statut HTTP)
        print_error(f"Erreur récupération modèles: {e}")
        if debug_mode and e.response is not None:
            # Affiche les détails de la réponse d'erreur en mode debug
            print_debug(f"Status: {e.response.status_code} {e.response.reason}", debug_mode)
            print_debug(f"[PAYLOAD ERREUR REÇU]", debug_mode, title="")
            console.print(Syntax(format_json_for_display(e.response.text), "json", theme="monokai", line_numbers=False))
        return None
    except Exception as e:
        # Gère toute autre exception inattendue
        print_error(f"Erreur inattendue lors de la récupération des modèles: {e}")
        return None
#endregion

#region Exécution des tests
"""
Cette section contient la logique principale pour invoquer les tests sur les modèles LLM,
gérer le parallélisme des requêtes et des modèles, et collecter les résultats.
"""

def invoke_model_test(model_obj: Dict[str, Any], user_prompt: str, pass_count: int, temp: float,
                      max_token_count: int, endpoint: str, token: str, timeout: int,
                      debug_mode: bool, parallel_requests_count: int, parallel_models_count: int,
                      progress_bar: Optional[Progress] = None, model_task_id: Optional[Any] = None) -> Dict[str, Any]:
    """
    Exécute un ensemble de tests pour un modèle LLM donné, en gérant le parallélisme des requêtes.

    Args:
        model_obj (Dict[str, Any]): Dictionnaire contenant les informations du modèle (id, aliases).
        user_prompt (str): Le prompt à envoyer au modèle.
        pass_count (int): Le nombre de fois que le test doit être exécuté pour ce modèle.
        temp (float): La température pour la génération de texte.
        max_token_count (int): Le nombre maximal de tokens à générer.
        endpoint (str): L'URL de l'API LLM.
        token (str): Le token d'authentification.
        timeout (int): Le timeout en secondes pour les requêtes HTTP.
        debug_mode (bool): Indique si le mode débogage est actif.
        parallel_requests_count (int): Nombre de requêtes à envoyer en parallèle pour chaque modèle.
        parallel_models_count (int): Nombre de modèles à tester en parallèle (utilisé pour la verbosité).
        progress_bar (Optional[Progress]): L'objet Rich Progress pour la mise à jour de la barre de progression.
        model_task_id (Optional[Any]): L'ID de la tâche de progression Rich associée à ce modèle.

    Returns:
        Dict[str, Any]: Un dictionnaire contenant les résultats agrégés pour le modèle.
    """
    # Extrait l'ID du modèle et son nom d'affichage (alias préféré si disponible)
    model_id_api = model_obj.get('id', 'inconnu')
    display_name = model_id_api
    if model_obj.get('aliases') and isinstance(model_obj['aliases'], list) and len(model_obj['aliases']) > 0:
        display_name = model_obj['aliases'][0]

    # Initialise le dictionnaire pour stocker les résultats de toutes les passes pour ce modèle
    model_results = {
        "ModelId": model_id_api,
        "DisplayName": display_name,
        "Responses": [None] * pass_count, # Pré-alloue une liste pour stocker les réponses dans l'ordre
        "TotalTime": timedelta(0),       # Temps total cumulé pour toutes les requêtes réussies
        "SuccessCount": 0,               # Nombre de requêtes réussies
        "ErrorCount": 0,                 # Nombre de requêtes en erreur
        "TotalPromptTokens": 0,          # Total des tokens de prompt
        "TotalCompletionTokens": 0,      # Total des tokens de complétion
        "TotalReasoningTokens": 0,       # Total des tokens de raisonnement
        "TotalTokensPerSecondList": []   # Liste des vitesses (tokens/s) pour les requêtes réussies
    }
    # Verrou pour protéger l'accès concurrent aux `model_results` lors de l'exécution parallèle des requêtes
    results_lock = threading.Lock()
    
    # Détermine si la sortie doit être verbeuse (détaillée) pour ce modèle.
    # C'est le cas si le mode debug est activé, ou si un seul modèle est testé en parallèle
    # (ce qui signifie que l'affichage détaillé ne perturbera pas d'autres barres de progression).
    is_verbose_model_output = debug_mode or (parallel_models_count == 1)

    # Met à jour la barre de progression Rich si elle est disponible et que la sortie n'est pas verbeuse.
    # En mode verbeux, l'affichage détaillé par passe remplace la barre de progression individuelle.
    if progress_bar and model_task_id and not is_verbose_model_output:
        progress_bar.update(model_task_id, description=f"{display_name} (Req: {parallel_requests_count})", completed=0, total=pass_count)
    elif is_verbose_model_output:
        # Affiche un en-tête de section pour le modèle en mode verbeux
        print_color(f"\n=======================================", "magenta")
        print_color(f"Test du modèle: {display_name} (ID API: {model_id_api})", "magenta")
        print_color(f"Passes: {pass_count}, Parallélisme Requêtes: {parallel_requests_count}", "magenta")
        print_color(f"=======================================", "magenta")
    # Si non verbose et pas de barre de progression (ce cas ne devrait pas se produire en mode parallèle),
    # on pourrait envisager de logger un message simple ici.

    # En-têtes HTTP pour la requête POST
    headers = {"accept": "application/json", "Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    # Corps de la requête JSON pour l'API /chat/completions
    body_object = {
        "model": model_id_api,
        "messages": [{"role": "user", "content": user_prompt}],
        "stream": False, # Requête non-streamée pour ce script de test
        "temperature": temp,
        "top_p": 1,
        "n": 1,
        "max_tokens": max_token_count,
        "user": "test-script-user-python" # Identifiant utilisateur pour la traçabilité
    }
    # Convertit l'objet Python en chaîne JSON
    body_json_str = json.dumps(body_object)
    if debug_mode:
        # Affiche le payload JSON envoyé en mode debug
        print_debug(f"[PAYLOAD MODÈLE {display_name} ENVOYÉ]", debug_mode, title="")
        console.print(Syntax(format_json_for_display(body_object), "json", theme="monokai", line_numbers=True))

    def _execute_single_pass(pass_index: int) -> Dict[str, Any]:
        """
        Exécute une seule requête API vers le modèle et collecte les résultats.
        Cette fonction est exécutée par chaque thread/processus en mode parallèle.

        Args:
            pass_index (int): L'index de la passe (0 à pass_count-1).

        Returns:
            Dict[str, Any]: Les informations détaillées de la réponse pour cette passe.
        """
        pass_num_display = pass_index + 1 # Numéro de passe pour l'affichage (commence à 1)
        
        if is_verbose_model_output:
            print_color(f"Passe {pass_num_display}/{pass_count} pour {display_name}: ", "blue", end="")
        
        start_time = time.monotonic() # Enregistre le temps de début de la requête
        # Initialise le dictionnaire pour stocker les informations de cette passe
        response_info = {
            "Result": "", "Time": timedelta(0), "Status": "Error", "Size": "N/A",
            "PromptTokens": 0, "CompletionTokens": 0, "ReasoningTokens": 0,
            "ModelUsed": "N/A", "TokensPerSecond": 0.0, "RequestId": "N/A", "BackendInfo": "N/A",
            "PassIndex": pass_index # Conserve l'index pour le tri ultérieur
        }
        try:
            # Envoie la requête POST à l'API /chat/completions
            response = requests.post(f"{endpoint}/chat/completions", headers=headers, data=body_json_str.encode('utf-8'), timeout=timeout)
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
            
            end_time = time.monotonic(); elapsed = timedelta(seconds=end_time - start_time)
            response_info["Time"] = elapsed # Calcule le temps écoulé
            response_info["Status"] = "Success" # Marque la passe comme réussie
            
            response_data = response.json() # Parse la réponse JSON du modèle
            if debug_mode:
                # Affiche le payload JSON reçu en mode debug
                print_debug(f"[PAYLOAD REÇU (Modèle: {display_name}, Passe {pass_num_display} - Succès)]", debug_mode, title="")
                console.print(Syntax(format_json_for_display(response_data), "json", theme="monokai", line_numbers=True))

            # Extrait l'ID de la requête depuis les en-têtes de réponse
            response_info["RequestId"] = response.headers.get('x-request-id', 'N/A')
            
            # Extrait le contenu de la réponse du modèle
            choices = response_data.get('choices', [])
            if choices and isinstance(choices, list) and choices[0].get('message', {}).get('content'):
                response_info["Result"] = choices[0]['message']['content']
                response_info["Size"] = get_formatted_size(response_info["Result"]) # Calcule la taille de la réponse
            
            # Extrait le nom du modèle réellement utilisé (peut différer de celui demandé si alias)
            response_info["ModelUsed"] = response_data.get('model', 'N/A')
            
            # Extrait les informations d'utilisation des tokens
            usage = response_data.get('usage', {})
            response_info["PromptTokens"] = usage.get('prompt_tokens', 0)
            response_info["CompletionTokens"] = usage.get('completion_tokens', 0)
            response_info["ReasoningTokens"] = usage.get('reasoning_tokens', 0) 

            # Calcule la vitesse de génération en tokens par seconde
            if response_info["CompletionTokens"] > 0 and elapsed.total_seconds() > 0:
                response_info["TokensPerSecond"] = round(response_info["CompletionTokens"] / elapsed.total_seconds(), 2)

            # Extrait les informations sur le backend (machine, moteur) si disponibles
            backend_data = response_data.get('backend', {})
            if backend_data:
                response_info["BackendInfo"] = f"Machine: {backend_data.get('machine_name', 'N/A')}, Moteur: {backend_data.get('engine_type', 'N/A')}"

        except requests.exceptions.RequestException as e:
            # Gère les erreurs de requête HTTP
            end_time = time.monotonic(); elapsed = timedelta(seconds=end_time - start_time)
            response_info["Time"] = elapsed
            # Construit un message d'erreur détaillé
            error_message = f"Erreur API: {e.response.status_code} {e.response.reason}" if e.response else f"Erreur Réseau/Script: {e}"
            if debug_mode and e.response is not None: 
                # Affiche le payload d'erreur en mode debug
                print_debug(f"[PAYLOAD ERREUR REÇU (Modèle: {display_name}, Passe {pass_num_display})]", debug_mode, title="")
                console.print(Syntax(format_json_for_display(e.response.text), "json", theme="monokai", line_numbers=True))
                try:
                    # Tente d'extraire un message d'erreur plus spécifique du JSON de réponse
                    err_json = e.response.json()
                    if isinstance(err_json, dict) and 'detail' in err_json: error_message += f" - {err_json['detail']}"
                except json.JSONDecodeError: pass # Ignore si la réponse d'erreur n'est pas du JSON
            response_info["Result"] = error_message
            response_info["Status"] = "Error" # Marque la passe comme en erreur
        
        # Met à jour les résultats agrégés du modèle.
        # Un verrou est utilisé pour garantir la sécurité des threads lors de l'accès concurrent.
        with results_lock:
            model_results["TotalTime"] += response_info["Time"]
            if response_info["Status"] == "Success":
                model_results["SuccessCount"] += 1
                model_results["TotalPromptTokens"] += response_info["PromptTokens"]
                model_results["TotalCompletionTokens"] += response_info["CompletionTokens"]
                model_results["TotalReasoningTokens"] += response_info["ReasoningTokens"]
                if response_info["TokensPerSecond"] > 0:
                     model_results["TotalTokensPerSecondList"].append(response_info["TokensPerSecond"])
            else:
                model_results["ErrorCount"] += 1
            model_results["Responses"][pass_index] = response_info # Stocke les infos de la passe en respectant l'ordre
        return response_info

    # Exécution des passes en parallèle ou séquentiellement
    if parallel_requests_count > 1:
        # Utilise ThreadPoolExecutor pour exécuter les requêtes en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_requests_count) as executor:
            # Soumet chaque passe comme une tâche au pool d'exécution
            futures = [executor.submit(_execute_single_pass, i) for i in range(pass_count)]
            # Itère sur les futures à mesure qu'elles se terminent
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result() # Récupère le résultat (ou lève l'exception si la tâche a échoué)
                except Exception as exc:
                    print_error(f"Une passe pour {display_name} a généré une exception: {exc}")
                # Met à jour la barre de progression si elle est utilisée
                if progress_bar and model_task_id and not is_verbose_model_output:
                    progress_bar.update(model_task_id, advance=1)
    else: # Exécution séquentielle des passes (pas de parallélisme des requêtes)
        for i in range(pass_count):
            _execute_single_pass(i)
            # Met à jour la barre de progression si elle est utilisée
            if progress_bar and model_task_id and not is_verbose_model_output:
                 progress_bar.update(model_task_id, advance=1, description=f"{display_name} ({i+1}/{pass_count})")
    
    # Affichage du résumé détaillé pour ce modèle après toutes les passes, si le mode verbeux est actif
    if is_verbose_model_output:
        # Trie les réponses par leur index de passe pour un affichage ordonné
        for resp_info in sorted(model_results["Responses"], key=lambda r: r["PassIndex"]): 
            pass_idx_display = resp_info["PassIndex"] + 1
            status_color = "bold green" if resp_info["Status"] == "Success" else "bold red"
            print_color(f"  Passe {pass_idx_display}: {resp_info['Status']}", status_color)
            if resp_info["Status"] == "Success":
                # Affiche un aperçu de la réponse (tronquée à 100 caractères)
                escaped_result = escape(resp_info['Result'][:100])
                truncated_suffix = '...' if len(resp_info['Result']) > 100 else ''
                print_color(f"    Réponse: {escaped_result}{truncated_suffix}", "white")
                # Affiche les métriques détaillées de la passe
                print_color(f"    Temps: {format_elapsed_time(resp_info['Time'])} | Taille: {resp_info['Size']} | Modèle API: {resp_info['ModelUsed']}", "dim")
                print_color(f"    Tokens: P={resp_info['PromptTokens']}, C={resp_info['CompletionTokens']}, R={resp_info['ReasoningTokens']} | Vitesse: {resp_info['TokensPerSecond']} toks/s", "dim")
                print_color(f"    Req ID: {resp_info['RequestId']} | Backend: {resp_info['BackendInfo']}", "dim")
            else:
                # Affiche le message d'erreur en cas d'échec
                escaped_error = escape(resp_info['Result'])
                print_color(f"    Erreur: {escaped_error}", "red")
                print_color(f"    Temps: {format_elapsed_time(resp_info['Time'])}", "dim")
    
    # Mise à jour finale de la barre de progression du modèle si elle existe (mode non-verbeux)
    if progress_bar and model_task_id and not is_verbose_model_output:
        # Calcule le taux de succès et la vitesse moyenne pour l'affichage final de la barre
        success_rate = f"{model_results['SuccessCount']}/{model_results['SuccessCount'] + model_results['ErrorCount']}"
        avg_tps_list = model_results['TotalTokensPerSecondList']
        avg_tps_str = f"{sum(avg_tps_list) / len(avg_tps_list):.2f} toks/s" if avg_tps_list else "N/A"
        final_desc = f"{display_name} - [bold green]OK[/]: {success_rate}, Tok/s: {avg_tps_str}"
        if model_results["ErrorCount"] > 0:
            final_desc = f"{display_name} - [bold red]ÉCHECS[/]: {success_rate}, Tok/s: {avg_tps_str}"
        progress_bar.update(model_task_id, description=final_desc, completed=pass_count) # Marque la tâche comme terminée

    return model_results
#endregion

#region Affichage du résumé
"""
Cette section est dédiée à l'affichage du tableau récapitulatif final des résultats
de tous les modèles testés.
"""

def show_results_summary(results: List[Dict[str, Any]]):
    """
    Affiche un tableau récapitulatif des résultats de tous les modèles testés.

    Args:
        results (List[Dict[str, Any]]): Une liste de dictionnaires, chaque dictionnaire
                                         contenant les résultats agrégés pour un modèle.
    """
    print_color("\n===================================================================================================================", "magenta")
    print_color("                                             TABLEAU RÉCAPITULATIF                                             ", "magenta")
    print_color("===================================================================================================================", "magenta")

    # Crée un tableau Rich avec les colonnes définies
    table = Table(show_header=True, header_style="bold magenta", border_style="dim", min_width=120)
    table.add_column("Modèle", style="dim", width=25)
    table.add_column("Succès", justify="right")
    table.add_column("Erreurs", justify="right")
    table.add_column("Tps Moyen", justify="right")
    table.add_column("Tps Total", justify="right")
    table.add_column("Prompt Tok (moy)", justify="right")
    table.add_column("Compl Tok (moy)", justify="right")
    table.add_column("Reas Tok (moy)", justify="right")
    table.add_column("Tok/s (moy)", justify="right")

    # Parcourt les résultats de chaque modèle pour ajouter une ligne au tableau
    for result in results:
        total_req = result["SuccessCount"] + result["ErrorCount"]
        # Calcule le temps moyen par requête
        avg_time_str = format_elapsed_time(timedelta(seconds=result["TotalTime"].total_seconds() / total_req if total_req > 0 else 0))
        # Calcule les moyennes de tokens et de vitesse, gérant les divisions par zéro
        avg_prompt = f"{result['TotalPromptTokens'] / result['SuccessCount']:.0f}" if result["SuccessCount"] > 0 else "0"
        avg_compl = f"{result['TotalCompletionTokens'] / result['SuccessCount']:.0f}" if result["SuccessCount"] > 0 else "0"
        avg_reas = f"{result['TotalReasoningTokens'] / result['SuccessCount']:.0f}" if result["SuccessCount"] > 0 else "0"
        avg_tps = f"{sum(result['TotalTokensPerSecondList']) / len(result['TotalTokensPerSecondList']):.2f}" if result["TotalTokensPerSecondList"] else "0.00"
        
        # Applique un style rouge gras si des erreurs ont été rencontrées pour ce modèle
        err_style = "[bold red]" if result["ErrorCount"] > 0 else ""
        table.add_row(
            result["DisplayName"],
            str(result["SuccessCount"]),
            f"{err_style}{result['ErrorCount']}{err_style}",
            avg_time_str,
            format_elapsed_time(result["TotalTime"]),
            avg_prompt,
            avg_compl,
            avg_reas,
            avg_tps
        )
    console.print(table) # Affiche le tableau dans la console
    print_color("===================================================================================================================", "magenta")
#endregion

#region Programme principal
"""
Fonction principale du script qui orchestre le chargement de la configuration,
la sélection des modèles, l'exécution des tests et l'affichage des résultats.
"""

def main():
    """
    Fonction principale du script.
    Configure les arguments de la ligne de commande, charge la configuration,
    récupère les modèles, exécute les tests et affiche le résumé.
    """
    # Configure l'analyseur d'arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Teste l'API LLM.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--models", type=str, default="", help="Modèles à tester (séparés par virgule). Tous par défaut.")
    parser.add_argument("-p", "--prompt", type=str, default="Ecris-moi un mot de plus de 10 lettres au hasard sans fioriture ?", help="Prompt.")
    parser.add_argument("--passes", type=int, default=None, help="Nombre de passes par modèle.")
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="Active le mode debug pour afficher des informations détaillées, y compris les payloads JSON envoyés et reçus."
    )
    parser.add_argument("-c", "--config-file", type=str, default="config.json", help="Fichier de configuration JSON.")
    parser.add_argument("-t", "--temperature", type=float, default=None, help="Température.")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max tokens à générer.")
    parser.add_argument("-e", "--endpoint", type=str, default=None, help="Endpoint API (surcharge config).")
    parser.add_argument("-pm", "--parallel-models", type=int, default=1, help="Nombre de modèles à tester en parallèle.")
    parser.add_argument("-pr", "--parallel-requests", type=int, default=1, help="Nombre de requêtes à envoyer en parallèle pour chaque modèle.")
    args = parser.parse_args() # Parse les arguments fournis en ligne de commande
    
    # Charge la configuration et les paramètres de test
    api_endpoint, api_token, passes, temperature, max_tokens, timeout_sec = load_config(args.config_file, args)
    if not api_endpoint or not api_token:
        sys.exit(1) # Quitte si la configuration API est incomplète

    # Affiche un en-tête et les paramètres de test initiaux
    print_color("\n==========================================================", "bold green")
    print_color("      TEST DES MODÈLES LLM - PYTHON      ", "bold green")
    print_color("==========================================================", "bold green")
    console.print(f"[yellow]Prompt:[/] {args.prompt}")
    console.print(f"[yellow]Passes par modèle:[/] {passes}")
    console.print(f"[yellow]Température:[/] {temperature}")
    console.print(f"[yellow]Max Tokens:[/] {max_tokens}")
    console.print(f"[yellow]Endpoint API:[/] {api_endpoint}")
    console.print(f"[yellow]Parallélisme Modèles:[/] {args.parallel_models}")
    console.print(f"[yellow]Parallélisme Requêtes:[/] {args.parallel_requests}")
    if args.debug: console.print("[cyan]Mode Debug: ACTIVÉ[/]")
    print_color("==========================================================", "bold green")

    # Récupère la liste des modèles disponibles depuis l'API
    available_models_list = get_available_models(api_endpoint, api_token, timeout_sec, args.debug)
    if available_models_list is None:
        sys.exit(1) # Quitte si la récupération des modèles échoue

    # Détermine les modèles à tester : tous les modèles disponibles ou une sélection spécifique
    models_to_test = []
    if args.models:
        requested_model_ids = [m.strip() for m in args.models.split(',')]
        available_map = {m.get('id'): m for m in available_models_list}
        for mid in requested_model_ids:
            if mid in available_map:
                models_to_test.append(available_map[mid])
                print_debug(f"Modèle '{mid}' ajouté pour test.", args.debug)
            else:
                print_error(f"Modèle demandé '{mid}' non trouvé.")
        if not models_to_test:
            print_error("Aucun des modèles demandés n'a été trouvé. Arrêt."); sys.exit(1)
    else:
        models_to_test = available_models_list
        print_info(f"Test de tous les {len(models_to_test)} modèles disponibles.")

    # Affiche la liste des modèles qui seront testés
    if models_to_test:
        print_color("\n----------------------------------------------------------", "yellow")
        print_color("MODÈLES SÉLECTIONNÉS POUR LE TEST:", "yellow")
        print_color("----------------------------------------------------------", "yellow")
        table_models = Table(show_header=True, header_style="bold blue", border_style="dim")
        table_models.add_column("ID Modèle (API)", style="dim", width=30)
        table_models.add_column("Nom d'Affichage", style="dim", width=30)
        for model_item in models_to_test:
            api_id = model_item.get('id', 'N/A')
            display = api_id
            aliases = model_item.get('aliases')
            if aliases and isinstance(aliases, list) and aliases[0]:
                display = aliases[0]
            table_models.add_row(api_id, display)
        console.print(table_models)
        print_color("----------------------------------------------------------", "yellow")
    else:
        print_error("Aucun modèle sélectionné pour le test."); sys.exit(1)
        
    all_results = [] # Liste pour stocker les résultats de tous les modèles
    # Initialise la barre de progression globale Rich
    with Progress(
        TextColumn("[progress.description]{task.description}"), # Description de la tâche
        BarColumn(),                                         # Barre de progression visuelle
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), # Pourcentage d'avancement
        TimeRemainingColumn(),                               # Temps restant estimé
        console=console,
        transient=False # Garde les barres de progression terminées visibles
    ) as progress_bar:
        
        # Logique pour l'exécution parallèle des modèles (si --parallel-models > 1 et pas en mode debug)
        if args.parallel_models > 1 and not args.debug:
            model_tasks = {} # Dictionnaire pour mapper les IDs de modèle aux IDs de tâche Rich
            for model_obj in models_to_test:
                model_id = model_obj.get('id')
                if not model_id: 
                    print_error(f"Modèle sans ID rencontré lors de la création des tâches de progression: {model_obj}. Il sera ignoré.")
                    continue
                
                aliases = model_obj.get('aliases')
                display_n = aliases[0] if aliases and isinstance(aliases, list) and len(aliases) > 0 else model_id
                # Ajoute une tâche individuelle pour chaque modèle à la barre de progression globale
                model_tasks[model_id] = progress_bar.add_task(f"{display_n} (0/{passes})", total=passes, start=True)

            # Utilise ThreadPoolExecutor pour exécuter les tests de modèles en parallèle
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel_models) as executor:
                future_to_model_id = {} # Mappe les objets Future aux IDs de modèle
                for model_obj in models_to_test:
                    model_id = model_obj.get('id')
                    if not model_id or model_id not in model_tasks:
                        continue # Ignore les modèles sans ID ou sans tâche de progression
                    
                    task_id_for_model = model_tasks[model_id]
                    # Soumet la fonction invoke_model_test pour chaque modèle au pool d'exécution
                    future = executor.submit(invoke_model_test, model_obj, args.prompt, passes, temperature, max_tokens,
                                             api_endpoint, api_token, timeout_sec, args.debug,
                                             args.parallel_requests, args.parallel_models,
                                             progress_bar, task_id_for_model)
                    future_to_model_id[future] = model_id
                
                # Attend que toutes les tâches se terminent et collecte les résultats
                for future in concurrent.futures.as_completed(future_to_model_id):
                    model_id = future_to_model_id[future]
                    current_task_id = model_tasks.get(model_id)
                    try:
                        model_result = future.result() # Récupère le résultat de la tâche
                        all_results.append(model_result)
                    except Exception as exc:
                        # Gère les exceptions majeures qui pourraient survenir lors de l'exécution d'un test de modèle
                        print_error(f"Le test du modèle {model_id} a généré une exception majeure: {exc}")
                        if current_task_id is not None:
                            display_name_for_error = model_id
                            original_model_obj = next((m for m in models_to_test if m.get('id') == model_id), None)
                            if original_model_obj:
                                aliases_err = original_model_obj.get('aliases')
                                display_name_for_error = aliases_err[0] if aliases_err and isinstance(aliases_err, list) and len(aliases_err) > 0 else model_id
                            progress_bar.update(current_task_id, description=f"{display_name_for_error} - [bold red]ERREUR Exception[/]", completed=passes)

        else: # Exécution séquentielle des modèles (ou mode debug, qui utilise l'affichage verbeux)
            # Crée une tâche de progression globale pour l'ensemble des modèles
            overall_progress_task = progress_bar.add_task("[cyan]Progression globale des modèles...", total=len(models_to_test))
            for model_obj in models_to_test:
                model_id_overall = model_obj.get('id', 'N/A')
                aliases_overall = model_obj.get('aliases')
                display_n_overall = aliases_overall[0] if aliases_overall and isinstance(aliases_overall, list) and len(aliases_overall) > 0 else model_id_overall
                # Met à jour la description de la tâche globale avec le modèle en cours de test
                progress_bar.update(overall_progress_task, description=f"Test en cours: {display_n_overall}")
                
                # Appelle invoke_model_test pour chaque modèle.
                # Les barres de progression individuelles ne sont pas utilisées ici car l'affichage est verbeux.
                model_result = invoke_model_test(model_obj, args.prompt, passes, temperature, max_tokens,
                                                 api_endpoint, api_token, timeout_sec, args.debug,
                                                 args.parallel_requests, args.parallel_models,
                                                 None, None)
                all_results.append(model_result)
                progress_bar.advance(overall_progress_task) # Avance la barre de progression globale

    # Affiche le tableau récapitulatif des résultats si des tests ont été exécutés
    if all_results:
        # Trie les résultats pour un affichage cohérent, basé sur l'ordre initial des modèles
        model_order_map = {model.get("id"): i for i, model in enumerate(models_to_test)}
        all_results.sort(key=lambda r: model_order_map.get(r.get("ModelId"), float('inf')))
        show_results_summary(all_results)
    else:
        print_info("Aucun test n'a été exécuté.")
    print_color("\nTests terminés!", "bold green")

# Point d'entrée du script
if __name__ == "__main__":
    main()
#endregion
