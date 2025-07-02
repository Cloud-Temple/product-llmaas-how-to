# -*- coding: utf-8 -*-
"""
Utilitaires d'Interface Utilisateur pour Mini-Chat LLMaaS.

Ce module contient les fonctions responsables de l'affichage et des interactions
avec l'utilisateur via la console, y compris la sélection de modèles,
l'affichage des appels et réponses d'outils, les statistiques d'usage,
et le nettoyage du contenu des réponses du modèle.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-30
"""

import json
import os
import re
from typing import List, Dict, Any, Optional

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

# Initialisation de Rich Console pour les utilitaires UI
console = Console()

def select_model_interactive(models: List[str], current_model: Optional[str]) -> Optional[str]:
    """
    Permet à l'utilisateur de sélectionner un modèle parmi une liste interactivement.

    Args:
        models: Liste des noms de modèles disponibles.
        current_model: Le nom du modèle actuellement sélectionné (peut être None).

    Returns:
        Le nom du modèle choisi par l'utilisateur, ou le modèle actuel si non modifié,
        ou None si aucun modèle n'est choisi et qu'il n'y en avait pas d'actuel.
    """
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
    """
    Affiche une demande d'appel d'outil générée par le modèle.

    Args:
        tool_call: Dictionnaire représentant l'appel d'outil.
    """
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
    """
    Affiche la réponse obtenue après l'exécution d'un outil.

    Args:
        tool_call_id: L'ID de l'appel d'outil.
        function_name: Le nom de la fonction d'outil exécutée.
        result: Le résultat textuel de l'exécution de l'outil.
    """
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
    """
    Affiche les statistiques d'utilisation des tokens et les informations du backend.

    Args:
        usage_info: Dictionnaire contenant les informations d'usage (prompt_tokens, completion_tokens, etc.).
        backend_info: Dictionnaire contenant les informations sur le backend utilisé.
    """
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
    console.print(Panel(stats_line, border_style="dim white", expand=False, padding=(0,1)))

def clean_thinking_content(text: str) -> str:
    """
    Supprime le contenu entre les balises <think> et </think> (incluses).
    Ces balises sont utilisées par le modèle pour ses pensées internes et ne doivent pas
    être conservées dans l'historique de la conversation.

    Args:
        text: La chaîne de caractères à nettoyer.

    Returns:
        La chaîne de caractères sans les balises de pensée.
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

# La console est exportée pour être utilisée par d'autres modules si nécessaire
__all__ = [
    "console",
    "select_model_interactive",
    "display_tool_call_request",
    "display_tool_call_response",
    "display_stats",
    "clean_thinking_content",
    "Panel", # Exportation de Panel
    "Markdown", # Exportation de Markdown
]
