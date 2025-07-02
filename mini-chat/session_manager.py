# -*- coding: utf-8 -*-
"""
Gestionnaire de Sessions pour Mini-Chat LLMaaS.

Ce module contient les fonctions pour sauvegarder et charger l'historique
des conversations et les paramètres de session au format JSON, ainsi que
pour exporter l'historique au format Markdown.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-30
"""

import datetime
import json
import os
from typing import List, Dict, Any, Optional

# Importer la console depuis ui_utils pour les messages
from ui_utils import console, Markdown, Panel

def save_session_json(session_data: Dict[str, Any], filename: str):
    """
    Sauvegarde les données de session (historique et métadonnées) dans un fichier JSON.

    Args:
        session_data: Dictionnaire contenant les données de session.
        filename: Chemin du fichier JSON où sauvegarder la session.
    """
    try:
        if not filename.lower().endswith(".json"):
            filename += ".json"
        dir_name = os.path.dirname(filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]Session sauvegardée en JSON dans '{os.path.abspath(filename)}'[/green]")
    except Exception as e:
        console.print(f"[red]Erreur lors de la sauvegarde de la session JSON : {e}[/red]")

def load_session_from_json(filename: str) -> Optional[Dict[str, Any]]:
    """
    Charge les données de session depuis un fichier JSON.

    Args:
        filename: Chemin du fichier JSON à charger.

    Returns:
        Dictionnaire contenant les données de session, ou None si le chargement échoue.
    """
    try:
        if not os.path.exists(filename):
            console.print(f"[red]Erreur: Le fichier de session '{filename}' n'existe pas.[/red]")
            return None
        with open(filename, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        if "metadata" not in session_data or "history" not in session_data:
            console.print(f"[red]Erreur: Fichier de session '{filename}' mal formaté (metadata ou history manquant).[/red]")
            return None
        return session_data
    except Exception as e:
        console.print(f"[red]Erreur lors du chargement de la session JSON depuis '{filename}': {e}[/red]")
        return None

def save_chat_markdown(messages_history: List[Dict[str, Any]], filename: str, session_metadata: Optional[Dict[str,Any]] = None):
    """
    Sauvegarde l'historique de la conversation au format Markdown.

    Args:
        messages_history: Liste des messages de la conversation.
        filename: Chemin du fichier Markdown où sauvegarder l'historique.
        session_metadata: Métadonnées de la session à inclure en en-tête du fichier.
    """
    try:
        if not filename.lower().endswith(".md"):
            filename += ".md"
        dir_name = os.path.dirname(filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Historique du Chat LLMaaS ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n")
            if session_metadata:
                f.write("## Paramètres de Session\n")
                for key, value in session_metadata.items():
                    if value is not None:
                        f.write(f"- **{key.replace('_', ' ').capitalize()}**: `{value}`\n")
                f.write("\n")
            for msg in messages_history:
                role = msg.get("role", "unknown").capitalize()
                content = msg.get("content")
                tool_calls = msg.get("tool_calls")
                f.write(f"## {role}\n\n")
                if content:
                    f.write(f"{content}\n\n")
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
    except Exception as e:
        console.print(f"[red]Erreur lors de la sauvegarde Markdown : {e}[/red]")

__all__ = [
    "save_session_json",
    "load_session_from_json",
    "save_chat_markdown",
]
