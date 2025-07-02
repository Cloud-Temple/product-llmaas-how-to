# -*- coding: utf-8 -*-
"""
Client API pour Mini-Chat LLMaaS.

Ce module fournit les fonctions nécessaires pour interagir avec l'API LLMaaS,
notamment pour récupérer la liste des modèles disponibles et pour envoyer
des requêtes de complétion de chat, en gérant le streaming et les appels d'outils.

Auteur: Cloud Temple - LLMaaS Team 
Version: 1.0.0
Date: 2025-06-02
"""
import asyncio # Ajout de l'import
import json
import os # Ajout de l'import pour os.urandom
import time
from typing import List, Dict, Any, Optional, Tuple

import httpx
from rich.console import Console
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from tools_definition import TOOLS_AVAILABLE # Importer pour l'utiliser dans le payload

console = Console() # Chaque module peut avoir sa propre console si besoin, ou on peut la passer

async def get_available_models(api_url: str, api_key: str) -> List[str]:
    """Récupère la liste des modèles disponibles depuis l'API LLMaaS."""
    if not api_key:
        console.print("[bold red]Erreur: Clé API non configurée. Veuillez la définir dans .env ou via --api-key.[/bold red]")
        return []
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(f"{api_url}/models", headers=headers, timeout=10)
            response.raise_for_status()
            models_data = response.json()
            return sorted([model["id"] for model in models_data.get("data", [])])
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Erreur API ({e.response.status_code}) lors de la récupération des modèles: {e.response.text}[/bold red]")
    except httpx.RequestError as e:
        console.print(f"[bold red]Erreur de connexion à l'API pour lister les modèles: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue lors de la récupération des modèles: {e}[/bold red]")
    return []

async def stream_chat_completions(
    api_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, Any]],
    max_tokens: int,
    debug_mode: bool,
    temperature: float = 0.7,
    stream_enabled: bool = True,  # Nouveau paramètre
    silent_mode: bool = False # Nouveau paramètre pour le mode silencieux
) -> Tuple[Optional[str], Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Envoie une requête de chat à l'API et gère la réponse.
    Supporte le mode streaming et non-streaming.
    Gère également les appels d'outils.
    Retourne le contenu complet de la réponse, les informations d'usage, les appels d'outils et les informations backend.
    """
    if not api_key:
        console.print("[bold red]Erreur: Clé API non configurée.[/bold red]")
        return None, None, [], None

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream_enabled, # Utilise le nouveau paramètre
        "max_tokens": max_tokens,
        "temperature": temperature,
        "tools": TOOLS_AVAILABLE,
        "tool_choice": "auto",
    }

    if debug_mode:
        console.print("\n[bold blue]--- Payload API (Envoi) ---[/bold blue]")
        # Log spécifique si des messages de rôle 'tool' sont présents pour inspection
        if any(msg.get("role") == "tool" for msg in messages):
            console.print("[bold yellow]Messages avec rôle 'tool' avant envoi:[/bold yellow]")
            console.print(Syntax(json.dumps(messages, indent=2), "json", theme="dracula", line_numbers=True))
        else:
            console.print(Syntax(json.dumps(payload, indent=2), "json", theme="dracula", line_numbers=True))

    full_response_content = ""
    tool_calls: List[Dict[str, Any]] = []
    usage_info: Optional[Dict[str, Any]] = None
    backend_info: Optional[Dict[str, Any]] = None
    
    async def process_request():
        nonlocal full_response_content, tool_calls, usage_info, backend_info # Permet de modifier les variables externes
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            if stream_enabled:
                headers["Accept"] = "text/event-stream"
            
            start_time = time.monotonic()
            
            if stream_enabled:
                async with client.stream("POST", f"{api_url}/chat/completions", json=payload, headers=headers, timeout=120) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        console.print(f"[bold red]Erreur API ({response.status_code}):[/bold red]")
                        try:
                            console.print(Syntax(json.dumps(json.loads(error_content.decode()), indent=2), "json", theme="dracula"))
                        except json.JSONDecodeError:
                            console.print(error_content.decode())
                        response.raise_for_status()
                    
                    # Si le statut est OK, on procède au streaming
                    if not silent_mode: # N'affiche pas le nom du modèle si en mode silencieux
                        console.print(f"[bold magenta]{model}:[/bold magenta] ", end="")
                    
                    buffer = ""
                    json_payload_buffer = ""
                    async for raw_chunk in response.aiter_raw():
                        buffer += raw_chunk.decode('utf-8')
                        
                        # On ne traite que les événements complets
                        while "\n\n" in buffer:
                            event_string, buffer = buffer.split("\n\n", 1)
                            
                            for line in event_string.splitlines():
                                if line.startswith("data:"):
                                    content = line[len("data: "):].strip()
                                    if content == "[DONE]":
                                        json_payload_buffer = "[DONE]"
                                        break
                                    # On ajoute le contenu au buffer JSON
                                    json_payload_buffer += content
                            
                            if json_payload_buffer == "[DONE]":
                                break

                            # On essaie de parser le buffer JSON accumulé
                            try:
                                # On ne traite que si le buffer n'est pas vide
                                if json_payload_buffer:
                                    chunk = json.loads(json_payload_buffer)
                                    
                                    # Si le parsing réussit, on a un objet JSON complet.
                                    # On le traite et on réinitialise le buffer pour le prochain objet.
                                    if debug_mode:
                                        console.print("\n[bold blue]--- Chunk API (Reçu & Décodé) ---[/bold blue]")
                                        console.print(Syntax(json.dumps(chunk, indent=2), "json", theme="dracula"))

                                    # ... (La logique de traitement du chunk reste identique)
                                    content_part = None
                                    tool_calls_in_chunk = None
                                    if chunk.get("message", {}).get("tool_calls"):
                                        message_field = chunk.get("message", {})
                                        content_part = message_field.get("content")
                                        tool_calls_in_chunk = message_field.get("tool_calls")
                                    elif chunk.get("choices") and chunk["choices"][0].get("delta"):
                                        delta = chunk["choices"][0].get("delta", {})
                                        content_part = delta.get("content")
                                        tool_calls_in_chunk = delta.get("tool_calls")
                                    elif chunk.get("done") and chunk.get("message"):
                                        message_field = chunk.get("message", {})
                                        content_part = message_field.get("content")

                                    # Découpler l'affichage du traitement
                                    # 1. Affichage en temps réel
                                    if not silent_mode:
                                        if content_part:
                                            # Convertir en chaîne de manière sûre
                                            if isinstance(content_part, dict):
                                                content_display = json.dumps(content_part, ensure_ascii=False)
                                            else:
                                                content_display = str(content_part)
                                            console.print(content_display, end="")
                                        
                                    if tool_calls_in_chunk:
                                        for tc in tool_calls_in_chunk:
                                            if tc.get("function", {}).get("arguments"):
                                                args_part = tc["function"]["arguments"]
                                                # Convertir en chaîne de manière sûre
                                                if isinstance(args_part, dict):
                                                    args_display = json.dumps(args_part, ensure_ascii=False)
                                                else:
                                                    args_display = str(args_part)
                                                console.print(f"[dim cyan]{args_display}[/dim cyan]", end="")

                                    # 2. Accumulation des données pour l'état final
                                    if content_part:
                                        # Convertir en chaîne de manière sûre pour l'accumulation
                                        if isinstance(content_part, dict):
                                            full_response_content += json.dumps(content_part, ensure_ascii=False)
                                        else:
                                            full_response_content += str(content_part)
                                
                                    if tool_calls_in_chunk:
                                        for tc_from_chunk in tool_calls_in_chunk:
                                            if tc_from_chunk.get("index") is not None:
                                                idx = tc_from_chunk["index"]
                                                while idx >= len(tool_calls): 
                                                    tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                                
                                                if tc_from_chunk.get("id"): 
                                                    tool_calls[idx]["id"] = tc_from_chunk["id"]
                                                
                                                current_function = tool_calls[idx].get("function", {"name": "", "arguments": ""})
                                                chunk_function = tc_from_chunk.get("function", {})

                                                if chunk_function.get("name"):
                                                    current_function["name"] = chunk_function["name"]
                                                if chunk_function.get("arguments"):
                                                    # Convertir en chaîne de manière sûre pour la concaténation
                                                    args_to_add = chunk_function["arguments"]
                                                    if isinstance(args_to_add, dict):
                                                        current_function["arguments"] += json.dumps(args_to_add, ensure_ascii=False)
                                                    else:
                                                        current_function["arguments"] += str(args_to_add)
                                                
                                                if not current_function["arguments"].strip() and tc_from_chunk.get("done", False):
                                                    current_function["arguments"] = "{}"
                                                tool_calls[idx]["function"] = current_function
                                            else:
                                                func_details = tc_from_chunk.get("function")
                                                if func_details:
                                                    if "arguments" not in func_details or not func_details["arguments"]:
                                                        func_details["arguments"] = "{}"
                                                    elif isinstance(func_details["arguments"], dict):
                                                        func_details["arguments"] = json.dumps(func_details["arguments"])
                                                    tool_call_to_add = {
                                                        "id": tc_from_chunk.get("id", f"call_{os.urandom(4).hex()}"),
                                                        "type": tc_from_chunk.get("type", "function"),
                                                        "function": func_details
                                                    }
                                                    tool_calls.append(tool_call_to_add)
                                                elif tc_from_chunk.get("id"):
                                                    if debug_mode:
                                                        console.print(f"[bold yellow]Avertissement: tool_call partiel sans index reçu: {tc_from_chunk}[/bold yellow]")

                                    if chunk.get("usage"): usage_info = chunk["usage"]
                                    if chunk.get("backend"): backend_info = chunk["backend"]
                                    
                                    # Réinitialiser le buffer JSON après un succès
                                    json_payload_buffer = ""

                            except json.JSONDecodeError:
                                # Le JSON est incomplet, on attend le prochain événement pour le compléter.
                                # On ne fait rien et on continue d'accumuler.
                                pass
                        
                        if json_payload_buffer == "[DONE]":
                            break

                    if not silent_mode : console.print() # Newline after streaming, sauf si silencieux
            else: # Not streaming (stream_enabled is False)
                response = await client.post(f"{api_url}/chat/completions", json=payload, headers=headers, timeout=120)
                # Le spinner (si actif) sera arrêté à la sortie du contexte Live dans la fonction appelante
                if response.status_code != 200:
                    console.print(f"[bold red]Erreur API ({response.status_code}):[/bold red]")
                    try: console.print(Syntax(json.dumps(response.json(), indent=2), "json", theme="dracula"))
                    except json.JSONDecodeError: console.print(response.text)
                    response.raise_for_status() # Lever une exception
                
                data = response.json()
                if debug_mode:
                    console.print("\n[bold blue]--- Réponse API (Non-Stream) ---[/bold blue]")
                    console.print(Syntax(json.dumps(data, indent=2), "json", theme="dracula"))
                
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                full_response_content = message.get("content", "")
                if message.get("tool_calls"):
                    tool_calls = message["tool_calls"]
                
                if not silent_mode: # N'affiche la réponse complète que si pas en mode silencieux
                    console.print(f"[bold magenta]{model}:[/bold magenta] {full_response_content}")
                usage_info = data.get("usage")
                backend_info = data.get("backend")

                end_time = time.monotonic()
                duration = end_time - start_time

                if usage_info and duration > 0:
                    completion_tokens = usage_info.get("completion_tokens", 0)
                    if completion_tokens > 0:
                         usage_info["tokens_per_second"] = completion_tokens / duration
                elif full_response_content and not usage_info: # Estimate if no usage info
                    estimated_completion_tokens = len(full_response_content.split()) 
                    if estimated_completion_tokens > 0 and duration > 0:
                        usage_info = {"completion_tokens": estimated_completion_tokens, "tokens_per_second": estimated_completion_tokens / duration, "estimated": True}

    # Gestion de l'affichage du spinner et de l'appel à process_request
    if not silent_mode and not stream_enabled:
        # CAS A: Non silencieux ET Non-stream => Utiliser le spinner
        live_spinner_display = Spinner("dots", text=Text(" Le modèle réfléchit...", style="green"))
        with Live(live_spinner_display, refresh_per_second=10, transient=True, console=console) as live_spinner_obj:
            try:
                await process_request()
            except httpx.HTTPStatusError as e:
                console.print(f"[bold red]Erreur API ({e.response.status_code}) lors du chat: {e.response.text}[/bold red]")
                return None, None, [], None
            except httpx.RequestError as e:
                console.print(f"[bold red]Erreur de connexion à l'API lors du chat: {e}[/bold red]")
                return None, None, [], None
            except Exception as e:
                console.print(f"[bold red]Erreur inattendue lors du chat: {e}[/bold red]")
                return None, None, [], None
    else:
        # CAS B: Silencieux OU Stream (ou les deux) => Pas de spinner, appel direct
        try:
            await process_request()
        except httpx.HTTPStatusError as e:
            console.print(f"[bold red]Erreur API ({e.response.status_code}) lors du chat: {e.response.text}[/bold red]")
            return None, None, [], None
        except httpx.RequestError as e:
            console.print(f"[bold red]Erreur de connexion à l'API lors du chat: {e}[/bold red]")
            return None, None, [], None
        except Exception as e: # Correction de l'indentation ici
            console.print(f"[bold red]Erreur inattendue lors du chat: {e}[/bold red]")
            return None, None, [], None
        
    return full_response_content, usage_info, tool_calls, backend_info

async def get_embeddings(
    api_url: str, 
    api_key: str, 
    texts: List[str], 
    model: str
) -> Optional[List[List[float]]]:
    """
    Récupère les embeddings pour une liste de textes via l'API LLMaaS.

    Args:
        api_url: URL de l'API.
        api_key: Clé d'API.
        texts: Liste de chaînes de caractères à embedder.
        model: Le nom du modèle d'embedding à utiliser.

    Returns:
        Une liste de vecteurs (embeddings), ou None en cas d'erreur.
    """
    if not api_key:
        console.print("[bold red]Erreur: Clé API non configurée.[/bold red]")
        return None
    
    payload = {
        "input": texts,
        "model": model,
    }

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            response = await client.post(f"{api_url}/embeddings", json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Extraire les embeddings de la réponse
            embeddings = [item["embedding"] for item in result.get("data", [])]
            return embeddings
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Erreur API ({e.response.status_code}) lors de la récupération des embeddings: {e.response.text}[/bold red]")
    except httpx.RequestError as e:
        console.print(f"[bold red]Erreur de connexion à l'API pour les embeddings: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue lors de la récupération des embeddings: {e}[/bold red]")
    
    return None
