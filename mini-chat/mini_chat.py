# -*- coding: utf-8 -*-
"""
Mini-Chat LLMaaS : Client de Chat en Ligne de Commande.

Ce script fournit une interface de chat interactive en ligne de commande pour
interagir avec les modèles de langage via l'API LLMaaS.
Il supporte l'historique des conversations, la gestion des prompts système,
la sélection de modèles, la configuration des paramètres de l'API,
la sauvegarde et le chargement de sessions, ainsi que l'utilisation d'outils (fonctions).

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-02
"""

import asyncio
import datetime
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple

import click
import httpx
from dotenv import load_dotenv
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

# Initialisation de Rich Console
console = Console()

# Charger les variables d'environnement depuis .env
load_dotenv()

# Importer les définitions d'outils et les fonctions client API
from tools_definition import TOOL_FUNCTIONS_MAP, TOOLS_AVAILABLE
from api_client import get_available_models, stream_chat_completions

API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
API_KEY = os.getenv("API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")


# --- Fonctions UI ---

def select_model_interactive(models: List[str], current_model: Optional[str]) -> Optional[str]:
    if not models:
        console.print("[yellow]Aucun modèle n'a pu être récupéré de l'API.[/yellow]")
        return current_model
    console.print("\n[bold green]Modèles disponibles :[/bold green]")
    for i, model_name in enumerate(models):
        console.print(f"{i + 1}. {model_name}")
    current_model_index = -1
    if current_model and current_model in models:
        current_model_index = models.index(current_model)
        console.print(f"\nModèle actuel : [cyan]{current_model}[/cyan] (numéro {current_model_index + 1})")
    while True:
        try:
            choice_str = Prompt.ask(f"Choisissez un numéro de modèle (ou laissez vide pour garder '{current_model if current_model else 'aucun'}')")
            if not choice_str and current_model: return current_model
            if not choice_str and not current_model:
                 console.print("[yellow]Veuillez choisir un modèle pour commencer.[/yellow]")
                 continue
            choice = int(choice_str)
            if 1 <= choice <= len(models): return models[choice - 1]
            else: console.print(f"[red]Choix invalide. Entrez un numéro entre 1 et {len(models)}.[/red]")
        except ValueError: console.print("[red]Entrée invalide. Veuillez entrer un numéro.[/red]")
        except Exception as e:
            console.print(f"[red]Erreur lors de la sélection: {e}[/red]")
            return current_model

def display_tool_call_request(tool_call: Dict[str, Any]):
    func_name = tool_call.get("function", {}).get("name")
    raw_func_args = tool_call.get("function", {}).get("arguments", "{}")
    
    func_args: Dict[str, Any]
    if isinstance(raw_func_args, str):
        try:
            func_args = json.loads(raw_func_args)
        except json.JSONDecodeError:
            func_args = {"raw_arguments": raw_func_args} # Garder comme chaîne si non-JSON
    elif isinstance(raw_func_args, dict):
        func_args = raw_func_args # C'est déjà un dictionnaire
    else:
        func_args = {"unknown_arguments_type": str(raw_func_args)}

    group_elements = Group(
        Text(f"Appel à l'outil : {func_name}", style="bold cyan"),
        Text(f"ID de l'appel : {tool_call.get('id', 'N/A')}"),
        Text("Arguments :"),
        Syntax(json.dumps(func_args, indent=2), "json", theme="dracula", line_numbers=True)
    )
    console.print(Panel(group_elements, title="🛠️ Demande d'outil", border_style="yellow", expand=False))

def display_tool_call_response(tool_call_id: str, function_name: str, result: str):
    display_result = result
    if len(result) > 500: display_result = result[:500] + "\n[... Résultat tronqué ...]"
    panel_content = f"[bold green]Résultat de l'outil : {function_name}[/bold green]\n"
    panel_content += f"ID de l'appel : {tool_call_id}\n"
    panel_content += "Réponse :\n"
    if "\n" in display_result or len(display_result) > 80:
         console.print(Panel(Markdown(f"```\n{display_result}\n```"), title="⚙️ Réponse d'outil", border_style="green", expand=False))
    else:
         console.print(Panel(Text(display_result), title="⚙️ Réponse d'outil", border_style="green", expand=False))

def display_stats(usage_info: Optional[Dict[str, Any]], backend_info: Optional[Dict[str, Any]]):
    if not usage_info: return
    stats_line = Text("📊 ", style="dim white")
    prompt_tokens = usage_info.get("prompt_tokens", 0)
    completion_tokens = usage_info.get("completion_tokens", 0)
    reasoning_tokens_val = usage_info.get("reasoning_tokens", 0)
    calculated_total = prompt_tokens + completion_tokens + reasoning_tokens_val
    total_tokens = usage_info.get("total_tokens", calculated_total)
    tokens_per_sec = usage_info.get("tokens_per_second")
    stats_line.append("Entrée: ", style="white"); stats_line.append(str(prompt_tokens), style="cyan")
    stats_line.append(" | Complétion: ", style="white"); stats_line.append(str(completion_tokens), style="cyan")
    stats_line.append(" | Raisonnement: ", style="white"); stats_line.append(str(reasoning_tokens_val), style="cyan")
    stats_line.append(" | Total: ", style="white"); stats_line.append(str(total_tokens), style="bold cyan")
    if tokens_per_sec is not None:
        stats_line.append(" | Vitesse: ", style="white"); stats_line.append(f"{tokens_per_sec:.2f} t/s", style="green")
    if usage_info.get("estimated"): stats_line.append(" (estimé)", style="yellow")
    # backend_text = None
    # if backend_info:
    #     backend_text = Text("⚙️ Backend: ", style="dim white")
    #     items = [Text(f"{backend_info[k]}", style="blue") if k == "machine_name" else Text(f"({backend_info[k]})", style="dim blue") for k in ["machine_name", "engine_type"] if backend_info.get(k)]
    #     backend_text.append(" ".join(str(item) for item in items))
    console.print(Panel(stats_line, border_style="dim white", expand=False, padding=(0,1)))
    # if backend_text: console.print(Panel(backend_text, border_style="dim white", expand=False, padding=(0,1)))

# --- Fonctions de Sauvegarde et Chargement ---
def save_session_json(session_data: Dict[str, Any], filename: str):
    try:
        if not filename.lower().endswith(".json"): filename += ".json"
        dir_name = os.path.dirname(filename)
        if dir_name: os.makedirs(dir_name, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]Session sauvegardée en JSON dans '{os.path.abspath(filename)}'[/green]")
    except Exception as e: console.print(f"[red]Erreur lors de la sauvegarde de la session JSON : {e}[/red]")

def load_session_from_json(filename: str) -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(filename):
            console.print(f"[red]Erreur: Le fichier de session '{filename}' n'existe pas.[/red]")
            return None
        with open(filename, 'r', encoding='utf-8') as f: session_data = json.load(f)
        if "metadata" not in session_data or "history" not in session_data:
            console.print(f"[red]Erreur: Fichier de session '{filename}' mal formaté (metadata ou history manquant).[/red]")
            return None
        return session_data
    except Exception as e:
        console.print(f"[red]Erreur lors du chargement de la session JSON depuis '{filename}': {e}[/red]")
        return None

def save_chat_markdown(messages_history: List[Dict[str, Any]], filename: str, session_metadata: Optional[Dict[str,Any]] = None):
    try:
        if not filename.lower().endswith(".md"): filename += ".md"
        dir_name = os.path.dirname(filename)
        if dir_name: os.makedirs(dir_name, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Historique du Chat LLMaaS ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n")
            if session_metadata:
                f.write("## Paramètres de Session\n")
                for key, value in session_metadata.items():
                    if value is not None: f.write(f"- **{key.replace('_', ' ').capitalize()}**: `{value}`\n")
                f.write("\n")
            for msg in messages_history:
                role = msg.get("role", "unknown").capitalize()
                content = msg.get("content")
                tool_calls = msg.get("tool_calls")
                f.write(f"## {role}\n\n")
                if content: f.write(f"{content}\n\n")
                if tool_calls:
                    f.write("Appels d'outils:\n")
                    for tc in tool_calls:
                        func_name = tc.get("function", {}).get("name", "N/A")
                        func_args = tc.get("function", {}).get("arguments", "{}")
                        f.write(f"- **Outil:** `{func_name}`\n")
                        f.write(f"  - **ID:** `{tc.get('id', 'N/A')}`\n")
                        f.write(f"  - **Arguments:**\n    ```json\n    {func_args}\n    ```\n\n")
                if msg.get("role") == "tool":
                    tool_call_id = msg.get("tool_call_id", "N/A")
                    f.write(f"Réponse de l'outil (ID: `{tool_call_id}`):\n")
                    f.write(f"```\n{content}\n```\n\n")
            console.print(f"[green]Chat sauvegardé en Markdown dans '{os.path.abspath(filename)}'[/green]")
    except Exception as e: console.print(f"[red]Erreur lors de la sauvegarde Markdown : {e}[/red]")

# --- Logique principale du Chat ---
async def chat_loop(
    api_url_param: str, 
    api_key_param: str, 
    initial_model: Optional[str], 
    initial_max_tokens: int, 
    initial_debug: bool,
    initial_temperature: float,
    initial_system_prompt: Optional[str] = None,
    initial_rules_prompt: Optional[str] = None, # Ajout pour les règles
    initial_user_prompt: Optional[str] = None, # Ajout pour le prompt initial
    autosave_json_path: Optional[str] = None,
    autosave_md_path: Optional[str] = None,
    load_session_path: Optional[str] = None,
    god_mode: bool = False,
    silent_mode_initial: bool = False,
    non_interactive_initial: bool = False, # Nouveau
    stream_enabled_initial: bool = True # Nouveau
):
    if not non_interactive_initial:
        console.print(Panel(Markdown("# Bienvenue au Mini-Chat LLMaaS !"), title="👋", border_style="green"))
        console.print("Tapez `/help` pour voir les commandes disponibles.")

    current_model = initial_model
    current_temperature = initial_temperature
    current_max_tokens = initial_max_tokens
    
    # Combinaison du prompt système initial et des règles
    combined_system_prompt = initial_system_prompt if initial_system_prompt else ""
    if initial_rules_prompt:
        if combined_system_prompt:
            combined_system_prompt += f"\n\n--- Règles Additionnelles ---\n{initial_rules_prompt}"
        else:
            combined_system_prompt = f"--- Règles Applicables ---\n{initial_rules_prompt}"
    current_system_prompt = combined_system_prompt if combined_system_prompt else None
    
    debug_active = initial_debug
    silent_mode = silent_mode_initial
    non_interactive_mode = non_interactive_initial
    streaming_enabled = stream_enabled_initial

    if non_interactive_mode or initial_user_prompt: # Si non-interactif OU si un prompt initial est fourni
        streaming_enabled = False # Forcer le non-stream

    messages: List[Dict[str, Any]] = []

    if load_session_path:
        loaded_session = load_session_from_json(load_session_path)
        if loaded_session:
            meta = loaded_session.get("metadata", {})
            current_model = initial_model if initial_model else meta.get("model", current_model)
            current_temperature = initial_temperature if initial_temperature != 0.7 else meta.get("temperature", current_temperature)
            current_max_tokens = initial_max_tokens if initial_max_tokens != 1024 else meta.get("max_tokens", current_max_tokens)
            current_system_prompt = initial_system_prompt if initial_system_prompt is not None else meta.get("system_prompt", current_system_prompt)
            debug_active = initial_debug if initial_debug != False else meta.get("debug", debug_active) # False est le défaut Click
            messages = loaded_session.get("history", [])
            console.print(f"[green]Session chargée depuis '{load_session_path}'[/green]")
        else:
            console.print(f"[red]Échec du chargement de '{load_session_path}'. Démarrage d'une nouvelle session.[/red]")
    
    if not messages and current_system_prompt:
        messages = [{"role": "system", "content": current_system_prompt}]
    
    available_models = await get_available_models(api_url_param, api_key_param)
    
    if silent_mode:
        if not current_model: # Si --model n'a pas été fourni, current_model est None (car DEFAULT_MODEL est appliqué dans main)
            console.print("[bold red]Mode silencieux : Aucun modèle spécifié via --model ou DEFAULT_MODEL dans .env, ou modèle invalide. Arrêt.[/bold red]")
            return
        if available_models and current_model not in available_models:
            console.print(f"[bold red]Mode silencieux : Modèle '{current_model}' non trouvé dans la liste des modèles disponibles. Arrêt.[/bold red]")
            return
        if not available_models and current_model: # On fait confiance au modèle fourni si la liste n'est pas récupérable
            pass # On continue avec le current_model
        elif not available_models and not current_model: # Devrait être impossible si la logique ci-dessus est correcte
             console.print("[bold red]Mode silencieux : Aucun modèle disponible et aucun modèle spécifié. Arrêt.[/bold red]"); return

    else: # Mode non silencieux, logique interactive existante
        if not available_models and not current_model:
            console.print("[bold red]Aucun modèle disponible ou défini. Arrêt.[/bold red]"); return
        
        if not current_model and available_models:
            current_model = select_model_interactive(available_models, None)
            if not current_model: console.print("[bold red]Aucun modèle sélectionné. Arrêt.[/bold red]"); return
        elif current_model and available_models and current_model not in available_models:
            console.print(f"[yellow]Modèle '{current_model}' non listé. Choix manuel.[/yellow]")
            new_selected_model = select_model_interactive(available_models, current_model)
            if not new_selected_model: console.print("[bold red]Aucun modèle sélectionné. Arrêt.[/bold red]"); return
            current_model = new_selected_model
        elif not available_models and current_model:
             console.print(f"[yellow]Liste des modèles indisponible. Utilisation de '{current_model}'.[/yellow]")

    if not silent_mode:
        console.print(f"Modèle: [cyan]{current_model}[/cyan] | Temp: {current_temperature:.1f} | MaxTokens: {current_max_tokens} | Debug: {'On' if debug_active else 'Off'}")
        if current_system_prompt: console.print(f"Prompt Système: [italic yellow]'{current_system_prompt}'[/italic yellow]")

    # Gérer le prompt initial s'il est fourni
    first_turn = True
    if initial_user_prompt:
        messages.append({"role": "user", "content": initial_user_prompt})
        if not silent_mode: # N'affiche le prompt initial que si on n'est pas en mode silencieux
            console.print(f"\n[bold green]Vous (via --prompt):[/bold green] {initial_user_prompt}")
        # On ne met pas le `user_input` à `initial_user_prompt` pour ne pas le traiter comme une commande
    
    while True:
        try:
            if initial_user_prompt and first_turn:
                # Le premier tour a déjà été géré par le prompt initial
                user_input = "" # Pour sauter la demande de Prompt.ask et aller directement à la logique API
                first_turn = False
            else:
                user_input = Prompt.ask("\n[bold green]Vous[/bold green]")

            if user_input.lower() in ["/quit", "/exit"]: console.print(Markdown("--- Au revoir ! ---")); break
            if user_input.lower() == "/help":
                console.print(Panel(Markdown(
                    "**Commandes disponibles en cours de chat:**\n\n"
                    "- `/quit` ou `/exit`: Quitter le chat.\n"
                    "- `/history`: Afficher l'historique de la conversation actuelle.\n"
                    "- `/clear`: Effacer l'historique (conserve les paramètres de session comme le prompt système).\n"
                    "- `/model`: Changer de modèle (réinitialise l'historique, conserve le prompt système).\n"
                    "- `/system <prompt>`: Définir ou modifier le prompt système (réinitialise l'historique).\n"
                    "- `/system_clear`: Supprimer le prompt système (réinitialise l'historique).\n"
                    "- `/save_session <fichier.json>`: Sauvegarder la session actuelle (paramètres et historique).\n"
                    "- `/load_session <fichier.json>`: Charger une session (écrase la session actuelle).\n"
                    "- `/savemd <fichier.md>`: Sauvegarder l'historique actuel en Markdown.\n"
                    "- `/tools`: Lister les outils disponibles et leur description.\n"
                    "- `/debug`: Activer/désactiver le mode debug pour l'affichage des payloads API.\n"
                    "- `/silent`: Activer/désactiver le mode silencieux (moins d'output).\n"
                    "- `/stream`: Activer/désactiver le mode streaming pour la réponse de l'IA.\n"
                    "- `/smol`: Demander au modèle de condenser l'historique actuel en un prompt efficace.\n"
                    "- `/help`: Afficher cette aide.\n\n"
                    "Pour les options de lancement du script, utilisez `python mini_chat.py --help`."
                ), title=" Aide Mini-Chat ", border_style="blue", expand=False))
                continue
            if user_input.lower() == "/smol":
                if not messages or all(m.get("role") == "system" for m in messages):
                    console.print("[yellow]Historique vide ou ne contient que des messages système. Rien à condenser.[/yellow]")
                    continue

                console.print("[cyan]Demande de condensation du contexte au LLM...[/cyan]")

                if not current_model:
                    console.print("[red]Erreur: Aucun modèle n'est actuellement sélectionné pour la condensation.[/red]")
                    continue
                
                history_to_condense = [msg for msg in messages if msg.get("role") != "system"]
                history_str = "\n".join([f"{m['role']}: {m.get('content', '') or m.get('tool_calls', '')}" for m in history_to_condense])
                
                condensation_prompt_messages = [
                    {"role": "system", "content": "Tu es un assistant expert en résumé et en formulation de prompts efficaces. Ta tâche est de condenser l'historique de conversation suivant en un unique prompt utilisateur concis. Ce prompt doit préserver l'intention principale de la conversation, la tâche en cours, et toutes les informations cruciales nécessaires pour que je (un autre LLM) puisse continuer la conversation ou achever la tâche sans perdre de contexte. Le résultat doit être SEULEMENT le prompt condensé, sans aucune phrase d'introduction ou de conclusion de ta part."},
                    {"role": "user", "content": f"Voici l'historique à condenser :\n\n---\n{history_str}\n---\n\nProduis maintenant le prompt utilisateur condensé et efficace."}
                ]
                
                condensed_context, _, _, _ = await stream_chat_completions(
                    api_url_param, api_key_param, current_model, 
                    condensation_prompt_messages, 
                    max_tokens=current_max_tokens, # Utiliser les max_tokens actuels, ou une valeur plus faible si désiré
                    debug_mode=debug_active, 
                    temperature=0.1, # Température basse pour une condensation plus factuelle
                    stream_enabled=False, # Forcer le non-streaming pour cette opération
                    silent_mode=True # Exécuter silencieusement cette requête interne
                )

                if condensed_context:
                    messages.clear()
                    if current_system_prompt:
                        messages.append({"role": "system", "content": current_system_prompt})
                    messages.append({"role": "user", "content": condensed_context.strip()})
                    console.print("[green]Contexte condensé par le LLM et appliqué.[/green]")
                    console.print(f"[italic]Nouveau contexte utilisateur (condensé) :[/italic]\n{condensed_context.strip()}")
                else:
                    console.print("[red]Échec de la condensation du contexte par le LLM.[/red]")
                continue
            if user_input.lower() == "/stream":
                streaming_enabled = not streaming_enabled
                console.print(f"Mode streaming {'[bold green]activé[/bold green]' if streaming_enabled else '[bold red]désactivé[/bold red]'}.")
                continue
            if user_input.lower() == "/tools":
                if not silent_mode:
                    console.print("\n[bold blue]Outils disponibles:[/bold blue]")
                    if TOOLS_AVAILABLE:
                        for tool_spec in TOOLS_AVAILABLE:
                            f_def = tool_spec.get("function",{})
                            console.print(f"- [cyan]{f_def.get('name','N/A')}[/cyan]: {f_def.get('description','N/A')}")
                    else: console.print("[yellow]Aucun outil configuré.[/yellow]")
                else:
                    console.print("[italic dim]Mode silencieux actif. Commande /tools ignorée pour l'affichage.[/italic dim]")
                continue
            if user_input.lower() == "/silent":
                silent_mode = not silent_mode
                console.print(f"Mode silencieux {'[bold green]activé[/bold green]' if silent_mode else '[bold red]désactivé[/bold red]'}."); continue
            if user_input.lower().startswith("/system "):
                new_prompt = user_input[len("/system "):].strip()
                current_system_prompt = new_prompt if new_prompt else current_system_prompt
                messages = [{"role": "system", "content": current_system_prompt}] if current_system_prompt else []
                console.print(f"Prompt système {'mis à jour' if new_prompt else 'conservé'}. Historique réinitialisé."); continue
            if user_input.lower() == "/system_clear":
                current_system_prompt = None; messages = []
                console.print("Prompt système supprimé. Historique réinitialisé."); continue
            if user_input.lower().startswith("/save_session "):
                filename = user_input[len("/save_session "):].strip()
                if filename:
                    session_data = {"metadata": {"model": current_model, "temperature": current_temperature, 
                                                 "max_tokens": current_max_tokens, "system_prompt": current_system_prompt,
                                                 "api_url": api_url_param, "debug": debug_active}, 
                                    "history": messages}
                    save_session_json(session_data, filename)
                else: console.print("[yellow]Nom de fichier manquant.[/yellow]")
                continue
            if user_input.lower().startswith("/load_session "):
                filename = user_input[len("/load_session "):].strip()
                if filename:
                    loaded_s = load_session_from_json(filename)
                    if loaded_s:
                        meta = loaded_s.get("metadata",{})
                        current_model = meta.get("model",current_model)
                        current_temperature = meta.get("temperature",current_temperature)
                        current_max_tokens = meta.get("max_tokens",current_max_tokens)
                        current_system_prompt = meta.get("system_prompt",current_system_prompt)
                        debug_active = meta.get("debug", debug_active) 
                        messages = loaded_s.get("history",[])
                        console.print(f"[green]Session chargée depuis '{filename}'.[/green]")
                        console.print(f"Modèle: [cyan]{current_model}[/cyan] | Temp: {current_temperature:.1f} | MaxTokens: {current_max_tokens} | Debug: {'On' if debug_active else 'Off'}")
                        if current_system_prompt: console.print(f"Prompt Système: [italic yellow]'{current_system_prompt}'[/italic yellow]")
                        else: console.print(f"Prompt Système: [italic]Aucun[/italic]")
                else: console.print("[yellow]Nom de fichier manquant.[/yellow]")
                continue
            if user_input.lower().startswith("/savemd "):
                filename = user_input[len("/savemd "):].strip()
                if filename: 
                    md_meta = {"model": current_model, "temperature": current_temperature, 
                               "max_tokens": current_max_tokens, "system_prompt": current_system_prompt,
                               "api_url": api_url_param, "debug": debug_active}
                    save_chat_markdown(messages, filename, md_meta)
                else: console.print("[yellow]Nom de fichier manquant.[/yellow]")
                continue
            if user_input.lower() == "/debug":
                debug_active = not debug_active
                console.print(f"Mode debug {'[bold green]activé[/bold green]' if debug_active else '[bold red]désactivé[/bold red]'}."); continue
            if user_input.lower() == "/history":
                if not messages: console.print("[yellow]Historique vide.[/yellow]"); continue
                console.print(Panel(Markdown("### Historique"), title="📜",border_style="blue"))
                for msg in messages:
                    role = msg.get('role','?').capitalize(); style = "green" if role=="User" else "magenta" if role=="Assistant" else "yellow"
                    console.print(f"[bold {style}]{role}:[/bold {style}] {msg.get('content') or msg.get('tool_calls','')}")
                continue
            if user_input.lower() == "/clear":
                messages = [{"role": "system", "content": current_system_prompt}] if current_system_prompt else []
                console.print("[yellow]Historique effacé.[/yellow]"); continue
            if user_input.lower() == "/model":
                if silent_mode:
                    console.print("[italic dim]Mode silencieux actif. Commande /model ignorée.[/italic dim]")
                elif not available_models: 
                    available_models = await get_available_models(api_url_param, api_key_param)
                    if available_models:
                        new_model = select_model_interactive(available_models, current_model)
                        if new_model and new_model != current_model:
                            current_model = new_model; messages = [{"role": "system", "content": current_system_prompt}] if current_system_prompt else []
                            console.print(f"Modèle: [cyan]{current_model}[/cyan]. Historique réinitialisé.")
                    else:
                        console.print("[yellow]Liste des modèles indisponible.[/yellow]")
                elif available_models : # available_models existe déjà
                    new_model = select_model_interactive(available_models, current_model)
                    if new_model and new_model != current_model:
                        current_model = new_model; messages = [{"role": "system", "content": current_system_prompt}] if current_system_prompt else []
                        if not silent_mode: console.print(f"Modèle: [cyan]{current_model}[/cyan]. Historique réinitialisé.")
                continue
            
            # Si user_input est vide ET qu'on n'est pas au premier tour avec un prompt initial,
            # on ne fait rien et on redemande une entrée.
            if not user_input and not (initial_user_prompt and first_turn):
                continue

            # Si user_input est vide, c'est qu'on vient du --prompt initial (géré par first_turn=False plus haut),
            # on ne l'ajoute pas à nouveau. Sinon, on l'ajoute.
            if user_input:
                messages.append({"role": "user", "content": user_input})
            
            # Boucle de traitement des appels d'outils et de la réponse de l'assistant
            # S'exécute au moins une fois si on a un prompt initial, ou si user_input n'est pas vide.
            while True:
                if not current_model: console.print("[red]Erreur: Modèle non sélectionné.[/red]"); break
                
                # S'assurer qu'il y a au moins un message utilisateur si on n'a pas de message système
                # ou si le dernier message n'est pas de l'assistant (pour éviter double appel API sans user input)
                if not messages or (messages[-1]["role"] == "assistant" and not tool_calls_received): # tool_calls_received serait d'un tour précédent
                    if not any(m["role"] == "user" for m in messages): # Vérifie s'il y a un message utilisateur dans l'historique
                         # Ce cas ne devrait plus arriver avec la vérification `if not user_input and not (initial_user_prompt and first_turn):`
                        console.print("[yellow]Veuillez entrer un message.[/yellow]")
                        break # Sort de la boucle interne pour redemander une entrée utilisateur

                response_content, usage, tool_calls_received, backend = await stream_chat_completions(
                    api_url_param, api_key_param, current_model, messages, current_max_tokens, debug_active, current_temperature, streaming_enabled
                )

                # Construction de assistant_message pour clarifier les types pour Pylance
                # et s'assurer que les arguments des tool_calls sont des chaînes JSON pour l'historique
                processed_tool_calls_for_history = []
                if tool_calls_received:
                    for tc_received in tool_calls_received:
                        processed_tc = tc_received.copy() # Évite de modifier l'original si c'est un objet partagé
                        if "function" in processed_tc and "arguments" in processed_tc["function"]:
                            args_val = processed_tc["function"]["arguments"]
                            if isinstance(args_val, dict):
                                processed_tc["function"]["arguments"] = json.dumps(args_val)
                            elif isinstance(args_val, str) and not args_val.strip(): # Si c'est une chaîne vide
                                processed_tc["function"]["arguments"] = "{}"
                            # Si c'est déjà une chaîne JSON non vide, on ne touche pas
                        processed_tool_calls_for_history.append(processed_tc)

                if processed_tool_calls_for_history:
                    assistant_message: Dict[str, Any] = {
                        "role": "assistant",
                        "content": response_content or "", # Peut être None ou vide si seulement des tool_calls
                        "tool_calls": processed_tool_calls_for_history
                    }
                else:
                    assistant_message: Dict[str, Any] = {
                        "role": "assistant",
                        "content": response_content or ""
                    }
                messages.append(assistant_message)
                
                if tool_calls_received:
                    for tool_call in tool_calls_received:
                        if not silent_mode: display_tool_call_request(tool_call)
                        func_name = tool_call.get("function", {}).get("name")
                        func_args_str = tool_call.get("function", {}).get("arguments", "{}")
                        tool_call_id_str = tool_call.get("id", "N/A")
                        if func_name in TOOL_FUNCTIONS_MAP:
                            try:
                                if isinstance(func_args_str, str):
                                    if not func_args_str.strip(): # Si la chaîne est vide ou ne contient que des espaces
                                        func_args = {}
                                    else:
                                        func_args = json.loads(func_args_str)
                                elif isinstance(func_args_str, dict):
                                    func_args = func_args_str # C'est déjà un dictionnaire
                                else:
                                    # Pourrait être None ou un autre type non attendu si l'API change
                                    console.print(f"[yellow]Avertissement: type d'arguments non standard reçu: {type(func_args_str)}. Tentative avec des arguments vides.[/yellow]")
                                    func_args = {}
                                
                                func_to_call = TOOL_FUNCTIONS_MAP[func_name]
                                tool_kwargs = func_args.copy()
                                # Passer les arguments supplémentaires nécessaires à certains outils
                                tool_kwargs['god_mode'] = god_mode # Toujours passer god_mode
                                if func_name == "execute_shell_command":
                                    tool_kwargs['console_instance'] = console
                                # Potentiellement d'autres outils pourraient avoir besoin de 'console_instance' ou d'autres paramètres globaux
                                # Retrait du console.status pour le test
                                # with console.status(f"[yellow]Outil {func_name}...[/yellow]", spinner="earth"):
                                #     await asyncio.sleep(0.5); tool_result = func_to_call(**tool_kwargs)
                                console.print(f"[yellow]Outil {func_name}...[/yellow]") # Affichage simple
                                await asyncio.sleep(0.5) # Garder un petit délai pour simuler le traitement
                                tool_result = func_to_call(**tool_kwargs)
                                if not silent_mode: display_tool_call_response(tool_call_id_str, func_name, tool_result)
                                messages.append({"tool_call_id": tool_call_id_str, "role": "tool", "content": str(tool_result)})
                            except Exception as e:
                                error_msg = f"Erreur outil {func_name}: {e}"; console.print(f"[red]{error_msg}[/red]")
                                messages.append({"tool_call_id": tool_call_id_str, "role": "tool", "content": str(error_msg)})
                        else:
                            error_msg = f"Outil inconnu: {func_name}"; console.print(f"[red]{error_msg}[/red]")
                            messages.append({"tool_call_id": tool_call_id_str, "role": "tool", "content": str(error_msg)})
                    # Après avoir traité les appels d'outils, on relance la boucle pour obtenir une réponse finale de l'assistant
                    continue 
                
                # Si pas d'appel d'outil, on affiche les stats et on sort de la boucle interne
                if not silent_mode: display_stats(usage, backend)
                
                if non_interactive_mode: # Si mode non interactif, on termine après la première réponse complète.
                    if not silent_mode: # N'affiche ce message que si on n'est pas en mode silencieux
                        console.print(Markdown("--- Fin du mode non interactif ---"))
                    break # Sort de la boucle while True interne (traitement API)
                
                break # Sort de la boucle while True interne (traitement API)
        
        except KeyboardInterrupt: console.print(Markdown("\n--- Chat interrompu ---")); break
        except Exception as e: console.print(f"[bold red]Erreur boucle de chat: {e}[/bold red]"); break
        
        # Si on est en mode non interactif, on sort de la boucle principale après le premier tour complet.
        if non_interactive_mode:
            break
            
    # Sauvegarde automatique à la fin de la session
    if autosave_json_path or autosave_md_path:
        session_metadata_to_save = {
            "model": current_model, 
            "temperature": current_temperature, 
            "max_tokens": current_max_tokens,
            "system_prompt": current_system_prompt,
            "api_url": api_url_param, 
            "debug": debug_active
        }
        
        if autosave_json_path:
            session_data_for_json = {
                "metadata": session_metadata_to_save,
                "history": messages
            }
            save_session_json(session_data_for_json, autosave_json_path)
        
        if autosave_md_path:
            save_chat_markdown(messages, autosave_md_path, session_metadata_to_save)

# --- Point d'entrée CLI ---
@click.command()
@click.option('--model', 'cli_model', default=None, help="Modèle à utiliser (ex: gemma3:4b).")
@click.option('--max-tokens', 'cli_max_tokens', default=1024, type=int, help="Max tokens pour réponse (défaut: 1024).")
@click.option('--temperature', 'cli_temperature', default=0.7, type=float, help="Température (défaut: 0.7).")
@click.option('--system-prompt', '-sp', 'cli_system_prompt', default=None, help="Prompt système initial.")
@click.option('--debug/--no-debug', 'cli_debug', default=False, help="Activer/désactiver mode debug API.")
@click.option('--api-url', 'cli_api_url', default=None, help="URL API LLMaaS (écrase .env).")
@click.option('--api-key', 'cli_api_key', default=None, help="Clé API LLMaaS (écrase .env).")
@click.option('--load-session', 'cli_load_session_path', default=None, type=click.Path(exists=True, dir_okay=False, resolve_path=True), help="Charger session depuis JSON.")
@click.option('--autosave-json', 'cli_autosave_json_path', default=None, type=click.Path(resolve_path=True), help="Sauvegarder session en JSON à la fin.")
@click.option('--autosave-md', 'cli_autosave_md_path', default=None, type=click.Path(resolve_path=True), help="Sauvegarder historique en Markdown à la fin.")
@click.option('--godmode', 'cli_god_mode', is_flag=True, default=False, help="Activer le mode GOD MODE (aucune confirmation pour les commandes shell).")
@click.option('--silent', 'cli_silent_mode', is_flag=True, default=False, help="Mode silencieux (moins d'output).")
@click.option('--rules', 'cli_rules_path', default=None, type=click.Path(exists=True, dir_okay=False, resolve_path=True), help="Fichier Markdown de règles à ajouter au prompt système.")
@click.option('--prompt', 'cli_initial_user_prompt', default=None, help="Prompt initial à envoyer au LLM.")
@click.option('--non-interactive', 'cli_non_interactive', is_flag=True, default=False, help="Mode non interactif (termine après la première réponse).")
@click.option('--no-stream', 'cli_no_stream', is_flag=True, default=False, help="Désactiver le streaming de la réponse.")
def main(
    cli_model: Optional[str], cli_max_tokens: int, cli_temperature: float, 
    cli_debug: bool, 
    cli_api_url: Optional[str], cli_api_key: Optional[str],
    cli_system_prompt: Optional[str],
    cli_autosave_json_path: Optional[str],
    cli_autosave_md_path: Optional[str],
    cli_load_session_path: Optional[str],
    cli_god_mode: bool,
    cli_silent_mode: bool,
    cli_rules_path: Optional[str],
    cli_initial_user_prompt: Optional[str],
    cli_non_interactive: bool, # Nouveau
    cli_no_stream: bool # Nouveau
):
    """Mini-Chat LLMaaS: Interagissez avec les modèles de langage via l'API."""
    global API_URL, API_KEY, DEFAULT_MODEL 

    if cli_api_url: API_URL = cli_api_url
    if cli_api_key: API_KEY = cli_api_key
    
    initial_model_to_use = cli_model if cli_model else DEFAULT_MODEL
    
    rules_prompt_content: Optional[str] = None
    if cli_rules_path:
        try:
            with open(cli_rules_path, 'r', encoding='utf-8') as f_rules:
                rules_prompt_content = f_rules.read()
            if not cli_silent_mode:
                console.print(f"[info]Règles chargées depuis '{cli_rules_path}'[/info]")
        except Exception as e:
            console.print(f"[red]Erreur lors du chargement du fichier de règles '{cli_rules_path}': {e}[/red]")


    if not API_KEY:
        console.print("[bold red]Erreur: Clé API (API_KEY) non configurée.[/bold red]"); return

    asyncio.run(chat_loop(
        API_URL, API_KEY, initial_model_to_use, 
        cli_max_tokens, cli_debug, cli_temperature, 
        cli_system_prompt,
        rules_prompt_content, 
        cli_initial_user_prompt, 
        cli_autosave_json_path, cli_autosave_md_path, cli_load_session_path,
        cli_god_mode,
        cli_silent_mode,
        cli_non_interactive, # Nouveau
        not cli_no_stream # Nouveau (inversé car l'option est --no-stream)
    ))

if __name__ == "__main__":
    main()
