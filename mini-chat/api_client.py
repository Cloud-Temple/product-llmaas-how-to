# -*- coding: utf-8 -*-
"""
Client API pour Mini-Chat LLMaaS.

Ce module fournit les fonctions nécessaires pour interagir avec l'API LLMaaS,
notamment pour récupérer la liste des modèles disponibles et pour envoyer
des requêtes de complétion de chat, en gérant le streaming et les appels d'outils.

Auteur: Cloud Temple - LLMaaS Team
Version: 2.0.0 (Refactored)
Date: 2026-01-25
"""
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple

import httpx
from rich.console import Console
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text

from tools_definition import TOOLS_AVAILABLE

console = Console()

async def get_available_models(api_url: str, api_key: str) -> List[str]:
    """Récupère la liste des modèles disponibles depuis l'API LLMaaS."""
    if not api_key:
        console.print("[bold red]Erreur: Clé API non configurée.[/bold red]")
        return []
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(f"{api_url}/models", headers=headers, timeout=10)
            response.raise_for_status()
            models_data = response.json()
            return sorted([model["id"] for model in models_data.get("data", [])])
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la récupération des modèles: {e}[/bold red]")
    return []

async def stream_chat_completions(
    api_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, Any]],
    max_tokens: int,
    debug_mode: bool,
    temperature: float = 0.7,
    stream_enabled: bool = True,
    silent_mode: bool = False
) -> Tuple[Optional[str], Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Envoie une requête de chat à l'API et gère la réponse (streaming ou non).
    Gère les tool calls et le nettoyage des balises <think>.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream_enabled,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "tools": TOOLS_AVAILABLE,
        "tool_choice": "auto",
    }

    if debug_mode:
        console.print("\n[bold blue]--- Payload API ---[/bold blue]")
        console.print(Syntax(json.dumps(payload, indent=2), "json", theme="dracula"))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream_enabled else "application/json"
    }

    full_content = ""
    tool_calls = []
    usage = None
    backend_details = None
    
    # Variables pour la reconstruction des tool calls en streaming
    current_tool_index = None
    current_tool_id = None
    current_tool_name = None
    current_tool_args = ""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = time.monotonic()
            
            if stream_enabled:
                if not silent_mode:
                    console.print(f"[bold magenta]{model}:[/bold magenta] ", end="")

                async with client.stream("POST", f"{api_url}/chat/completions", json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        console.print(f"\n[bold red]Erreur API ({response.status_code}): {error_text.decode()}[/bold red]")
                        return None, None, [], None

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if not choices:
                                # Parfois les chunks de fin n'ont pas de choices ou c'est un message système
                                if chunk.get("usage"):
                                    usage = chunk["usage"]
                                if chunk.get("backend"):
                                    backend_details = chunk["backend"]
                                continue

                            delta = choices[0].get("delta", {})
                            
                            # 1. Gestion du contenu texte
                            content = delta.get("content")
                            if content:
                                full_content += content
                                if not silent_mode:
                                    console.print(content, end="")
                            
                            # 2. Gestion des Tool Calls (streaming)
                            tc_chunk = delta.get("tool_calls")
                            if tc_chunk:
                                for tc in tc_chunk:
                                    # Nouveau tool call ou suite du précédent
                                    if tc.get("index") is not None:
                                        idx = tc["index"]
                                        
                                        # Initialisation si nouvel index
                                        if current_tool_index != idx:
                                            # Sauvegarder le précédent si existant
                                            if current_tool_index is not None:
                                                tool_calls.append({
                                                    "id": current_tool_id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": current_tool_name,
                                                        "arguments": current_tool_args
                                                    }
                                                })
                                            
                                            # Reset pour le nouveau
                                            current_tool_index = idx
                                            current_tool_id = tc.get("id", "")
                                            current_tool_name = tc.get("function", {}).get("name", "")
                                            current_tool_args = ""
                                            if not silent_mode:
                                                console.print(f"\n[cyan]🛠️  Appel outil: {current_tool_name}...[/cyan]", end="")
                                        
                                        # Accumulation des arguments
                                        args_part = tc.get("function", {}).get("arguments", "")
                                        current_tool_args += args_part

                            # 3. Métadonnées (usage, backend)
                            if chunk.get("usage"):
                                usage = chunk["usage"]
                            if chunk.get("backend"):
                                backend_details = chunk["backend"]

                        except json.JSONDecodeError:
                            continue
                
                # Fin du stream : sauvegarder le dernier tool call en cours
                if current_tool_index is not None:
                     tool_calls.append({
                        "id": current_tool_id,
                        "type": "function",
                        "function": {
                            "name": current_tool_name,
                            "arguments": current_tool_args
                        }
                    })

                if not silent_mode:
                    console.print() # Saut de ligne final

            else:
                # Mode non-streaming
                with Live(Spinner("dots", text=" Réflexion..."), transient=True, console=console):
                    response = await client.post(f"{api_url}/chat/completions", json=payload, headers=headers)
                
                if response.status_code != 200:
                    console.print(f"[bold red]Erreur API ({response.status_code}): {response.text}[/bold red]")
                    return None, None, [], None

                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]
                
                full_content = message.get("content") or ""
                tool_calls = message.get("tool_calls") or []
                usage = data.get("usage")
                backend_details = data.get("backend")

                if not silent_mode:
                    console.print(f"[bold magenta]{model}:[/bold magenta] {full_content}")

            # Estimation usage si manquant
            if not usage:
                duration = time.monotonic() - start_time
                estimated_tokens = len(full_content.split()) * 1.3 # approx
                usage = {
                    "completion_tokens": int(estimated_tokens),
                    "total_tokens": int(estimated_tokens), # approximation
                    "tokens_per_second": estimated_tokens / duration if duration > 0 else 0
                }

    except Exception as e:
        console.print(f"[bold red]Exception API: {e}[/bold red]")
        return None, None, [], None

    return full_content, usage, tool_calls, backend_details

async def get_embeddings(api_url: str, api_key: str, texts: List[str], model: str) -> Optional[List[List[float]]]:
    """Récupère les embeddings vectoriels."""
    if not api_key:
        return None
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{api_url}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"input": texts, "model": model},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
    except Exception as e:
        console.print(f"[bold red]Erreur Embeddings: {e}[/bold red]")
        return None
