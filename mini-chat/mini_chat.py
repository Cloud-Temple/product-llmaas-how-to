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
import readline
from typing import List, Dict, Any, Optional, Tuple

import asyncio
import os
import time
from typing import List, Dict, Any, Optional, Tuple

import click
import httpx
from dotenv import load_dotenv
from rich.prompt import Prompt

# Importer les fonctions et la console depuis ui_utils
from ui_utils import (
    console,
    select_model_interactive,
    display_tool_call_request,
    display_tool_call_response,
    display_stats,
    clean_thinking_content,
    Panel,
    Markdown,
)

# Importer les fonctions de sauvegarde/chargement depuis session_manager
from session_manager import save_session_json, load_session_from_json, save_chat_markdown

# Importer les fonctions RAG depuis rag_core
from rag_core import get_text_chunks, search_in_vector_database


# Importer les définitions d'outils et les fonctions client API
from tools_definition import TOOL_FUNCTIONS_MAP, TOOLS_AVAILABLE
from api_client import get_available_models, stream_chat_completions, get_embeddings

# Importer le gestionnaire de commandes
from command_handler import CommandHandler

from qdrant_utils import QdrantManager # QdrantManager reste ici car il est instancié dans chat_loop

# Débogage du chargement des variables d'environnement
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print(f"Fichier .env trouvé à l'emplacement : {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Fichier .env non trouvé.")

API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
API_KEY = os.getenv("API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
MAX_TOKENS = os.getenv("MAX_TOKENS")

print(f"API_KEY après getenv: {'Clé trouvée' if API_KEY else 'Clé non trouvée'}")

class CommandCompleter:
    """
    Classe pour gérer l'autocomplétion des commandes et l'historique.
    """
    def __init__(self):
        # Liste des commandes disponibles
        self.commands = [
            "/quit", "/exit", "/help", "/history", "/clear", "/model", "/system", "/system_clear",
            "/save_session", "/load_session", "/savemd", "/tools", "/debug", "/silent", "/stream",
            "/smol", "/embed", "/rag", "/rag_threshold", "/context", "/qdrant_list", "/qdrant_info",
            "/qdrant_delete", "/qdrant_clear", "/qdrant_drop"
        ]
        
        # Configurer readline
        self._setup_readline()
    
    def _setup_readline(self):
        """Configure readline pour l'autocomplétion et l'historique."""
        try:
            # Configurer l'autocomplétion
            readline.set_completer(self._complete)
            readline.set_completer_delims(' \t\n`!@#$%^&*()=+[{]}\\|;:\'",<>?')
            
            # Configuration de l'autocomplétion - plusieurs variantes pour compatibilité
            readline.parse_and_bind("tab: complete")
            readline.parse_and_bind("set completion-ignore-case on")
            readline.parse_and_bind("set show-all-if-ambiguous on")
            
            # Configuration de l'historique
            readline.parse_and_bind("set editing-mode emacs")
            readline.parse_and_bind("\"\\e[A\": history-search-backward")
            readline.parse_and_bind("\"\\e[B\": history-search-forward")
            
            # Charger l'historique depuis un fichier si il existe
            history_file = os.path.expanduser("~/.minichat_history")
            try:
                readline.read_history_file(history_file)
            except FileNotFoundError:
                pass  # Pas d'historique existant
            
            # Limiter la taille de l'historique
            readline.set_history_length(1000)
            
            
        except ImportError:
            # readline n'est pas disponible (Windows sans pyreadline)
            pass
        except Exception as e:
            # Ignorer silencieusement les erreurs de configuration readline
            pass
    
    def _complete(self, text: str, state: int):
        """Fonction d'autocomplétion pour readline."""
        if text.startswith('/'):
            # Autocomplétion des commandes
            matches = [cmd for cmd in self.commands if cmd.startswith(text)]
        else:
            # Pas d'autocomplétion pour le texte normal
            matches = []
        
        try:
            return matches[state]
        except IndexError:
            return None
    
    def input_with_completion(self, prompt: str) -> str:
        """
        Demande une entrée utilisateur avec autocomplétion et historique.
        
        Args:
            prompt: Le prompt à afficher
            
        Returns:
            L'entrée utilisateur
        """
        try:
            user_input = input(prompt)
            
            # Ajouter à l'historique seulement si ce n'est pas vide
            if user_input.strip():
                readline.add_history(user_input)
                
                # Sauvegarder l'historique
                history_file = os.path.expanduser("~/.minichat_history")
                try:
                    readline.write_history_file(history_file)
                except:
                    pass  # Ignorer les erreurs de sauvegarde
            
            return user_input
        except (ImportError, AttributeError):
            # Fallback si readline n'est pas disponible
            return input(prompt)

class ChatClient:
    """
    Classe encapsulant la logique et l'état du client de chat interactif.
    """
    def __init__(self, **kwargs):
        """
        Initialise le client de chat avec les paramètres fournis.
        """
        # Initialisation des paramètres depuis les kwargs
        self.api_url = kwargs.get('api_url_param')
        self.api_key = kwargs.get('api_key_param')
        self.current_model = kwargs.get('initial_model')
        self.current_max_tokens = kwargs.get('initial_max_tokens')
        self.current_temperature = kwargs.get('initial_temperature')
        self.debug_active = kwargs.get('initial_debug')
        self.god_mode = kwargs.get('god_mode')
        self.silent_mode = kwargs.get('silent_mode_initial')
        self.non_interactive_mode = kwargs.get('non_interactive_initial', False)
        self.streaming_enabled = kwargs.get('stream_enabled_initial', True)
        self.embedding_model = kwargs.get('embedding_model')
        
        self.autosave_json_path = kwargs.get('autosave_json_path')
        self.autosave_md_path = kwargs.get('autosave_md_path')
        self.load_session_path = kwargs.get('load_session_path')
        self.initial_user_prompt = kwargs.get('initial_user_prompt')

        # Combinaison des prompts système et des règles
        initial_system_prompt = kwargs.get('initial_system_prompt', "")
        initial_rules_prompt = kwargs.get('initial_rules_prompt')
        combined_system_prompt = initial_system_prompt
        if initial_rules_prompt:
            if combined_system_prompt:
                combined_system_prompt += f"\n\n--- Règles Additionnelles ---\n{initial_rules_prompt}"
            else:
                combined_system_prompt = f"--- Règles Applicables ---\n{initial_rules_prompt}"
        self.current_system_prompt = combined_system_prompt if combined_system_prompt else None

        # Initialisation de l'état du chat
        self.messages: List[Dict[str, Any]] = []
        self.available_models: List[str] = []
        self.is_rag_enabled = False
        self.vector_size_initialized = False
        self.rag_similarity_threshold = 0.78  # Seuil par défaut selon les meilleures pratiques

        # Initialisation des gestionnaires
        self.qdrant_manager = QdrantManager(
            host=kwargs.get('qdrant_url', "localhost"),
            port=kwargs.get('qdrant_port', 6333),
            collection_name=kwargs.get('qdrant_collection', "minichat_rag")
        )
        self.command_handler = self._setup_command_handler()
        
        # Initialiser l'autocomplétion seulement en mode interactif
        self.completer = None
        if not self.non_interactive_mode:
            self.completer = CommandCompleter()

    async def run(self):
        """
        Lance la boucle principale du chat.
        """
        if not self.api_url or not self.api_key:
            console.print("[bold red]Erreur: URL de l'API ou clé API non configurée.[/bold red]")
            return

        if not self.non_interactive_mode:
            console.print(Panel(Markdown("# Bienvenue au Mini-Chat LLMaaS !"), title="👋", border_style="green"))
            console.print("Tapez `/help` pour voir les commandes disponibles.")

        # Initialisation du RAG
        if self.embedding_model and self.qdrant_manager.client and self.qdrant_manager.check_collection_exists():
            self.is_rag_enabled = True
            console.print("[bold green]Mode RAG activé automatiquement (connexion Qdrant OK et collection trouvée).[/bold green]")
        elif self.embedding_model:
            console.print("[yellow]Mode RAG désactivé. Pour l'activer, utilisez `/embed` pour créer la collection ou `/rag on` si elle existe déjà.[/yellow]")

        if self.non_interactive_mode or self.initial_user_prompt:
            self.streaming_enabled = False

        self.available_models = await get_available_models(self.api_url, self.api_key)
        
        if self.load_session_path:
            if not await self.command_handler.handle_command(f"/load_session {self.load_session_path}"):
                console.print(f"[red]Échec du chargement de '{self.load_session_path}'. Démarrage d'une nouvelle session.[/red]")
        
        if not self.messages and self.current_system_prompt:
            self.messages = [{"role": "system", "content": self.current_system_prompt}]
        
        if not self.silent_mode:
            await self._select_initial_model()
            self._display_initial_status()

        first_turn = True
        if self.initial_user_prompt:
            self.messages.append({"role": "user", "content": self.initial_user_prompt})
            if not self.silent_mode:
                console.print(f"\n[bold green]Vous (via --prompt):[/bold green] {self.initial_user_prompt}")
        
        await self._chat_loop_internal(first_turn)
        
        self._autosave_session()

    def _setup_command_handler(self) -> CommandHandler:
        """
        Initialise et retourne le CommandHandler avec une référence au client.
        
        Returns:
            CommandHandler: L'instance du gestionnaire de commandes.
        """
        self.command_handler = CommandHandler(self)
        return self.command_handler

    async def _select_initial_model(self):
        """
        Gère la sélection interactive du modèle au démarrage si aucun n'est
        défini ou si le modèle défini n'est pas valide.
        """
        if not self.current_model and self.available_models:
            self.current_model = select_model_interactive(self.available_models, None)
            if not self.current_model:
                console.print("[bold red]Aucun modèle sélectionné. Arrêt.[/bold red]")
                return
        elif self.current_model and self.available_models and self.current_model not in self.available_models:
            console.print(f"[yellow]Modèle '{self.current_model}' non listé. Choix manuel.[/yellow]")
            new_model = select_model_interactive(self.available_models, self.current_model)
            if not new_model:
                console.print("[bold red]Aucun modèle sélectionné. Arrêt.[/bold red]")
                return
            self.current_model = new_model
        elif not self.available_models and not self.current_model:
            console.print("[bold red]Aucun modèle disponible ou défini. Arrêt.[/bold red]")
            return
        elif not self.available_models and self.current_model:
            console.print(f"[yellow]Liste des modèles indisponible. Utilisation de '{self.current_model}'.[/yellow]")

    def _display_initial_status(self):
        """
        Affiche l'état initial de la configuration du chat (modèle,
        température, etc.) dans la console.
        """
        console.print(f"Modèle: [cyan]{self.current_model}[/cyan] | Temp: {self.current_temperature:.1f} | MaxTokens: {self.current_max_tokens} | Debug: {'On' if self.debug_active else 'Off'}")
        if self.current_system_prompt:
            console.print(f"Prompt Système: [italic yellow]'{self.current_system_prompt}'[/italic yellow]")

    async def _chat_loop_internal(self, first_turn: bool):
        """
        La boucle interne qui gère les tours de conversation, de l'entrée
        utilisateur à la réponse du modèle.

        Args:
            first_turn (bool): Indique si c'est le premier tour de la boucle
                               (utile pour le mode non interactif).
        """
        while True:
            try:
                if self.initial_user_prompt and first_turn:
                    user_input = ""
                    first_turn = False
                else:
                    # Utiliser l'autocomplétion si disponible, sinon fallback sur Prompt.ask
                    if self.completer:
                        # Utiliser un prompt simple sans Rich pour éviter les conflits d'affichage
                        print("\n\033[1;32mVous\033[0m: ", end="", flush=True)
                        user_input = self.completer.input_with_completion("")
                    else:
                        user_input = Prompt.ask("\n[bold green]Vous[/bold green]")

                # Traiter les commandes en priorité
                if user_input.startswith("/"):
                    if await self.command_handler.handle_command(user_input):
                        if user_input.lower() in ["/quit", "/exit"]:
                            break
                        continue

                # Si pas d'input et pas de prompt initial, continuer
                if not user_input and not (self.initial_user_prompt and first_turn):
                    continue

                # Ajouter le message à l'historique seulement si ce n'est pas une commande
                if user_input:
                    self.messages.append({"role": "user", "content": user_input})

                # Traiter la réponse (soit user_input soit initial_user_prompt)
                input_to_process = user_input if user_input else self.initial_user_prompt
                if input_to_process:
                    await self._process_and_respond(input_to_process)

                if self.non_interactive_mode:
                    if not self.silent_mode:
                        console.print(Markdown("--- Fin du mode non interactif ---"))
                    break
            
            except KeyboardInterrupt:
                console.print(Markdown("\n--- Chat interrompu ---"))
                break
            except Exception as e:
                console.print(f"[bold red]Erreur boucle de chat: {e}[/bold red]")
                break
            
            if self.non_interactive_mode:
                break

    async def _process_and_respond(self, user_input: str):
        """
        Orchestre un seul tour de conversation : préparation des messages
        (avec RAG), appel à l'API, et gestion de la réponse (texte ou outils).

        Args:
            user_input (str): Le message entré par l'utilisateur.
        """
        # La préparation des messages (et donc l'injection RAG) est faite ici.
        messages_for_api = await self._prepare_messages_for_api(user_input)

        while True:
            if not self.current_model:
                console.print("[red]Erreur: Modèle non sélectionné.[/red]")
                break
            
            response_content, usage, tool_calls, backend = await stream_chat_completions(
                self.api_url or "",
                self.api_key or "",
                self.current_model or "",
                messages_for_api,
                self.current_max_tokens or 1024,
                self.debug_active or False,
                self.current_temperature or 0.7,
                self.streaming_enabled
            )

            self._add_assistant_message_to_history(response_content, tool_calls)

            if tool_calls:
                await self._handle_tool_calls(tool_calls, messages_for_api)
                continue  # Continue la boucle pour renvoyer les résultats des outils au modèle

            if not self.silent_mode:
                display_stats(usage, backend)
            
            break # Sort de la boucle d'appel d'outils

    async def _prepare_messages_for_api(self, user_input: str) -> List[Dict[str, Any]]:
        """
        Prépare la liste des messages à envoyer à l'API.
        Ajoute le contexte RAG au prompt système si le mode RAG est activé.
        Cette fonction ne modifie plus self.messages directement, mais retourne une nouvelle liste.

        Args:
            user_input (str): Le dernier message de l'utilisateur.

        Returns:
            List[Dict[str, Any]]: La liste des messages prête pour l'API.
        """
        # Partir d'une copie propre de l'historique pour cette préparation
        messages_for_api = [msg for msg in self.messages if msg.get("role") != "system"]
        
        # Récupérer le prompt système de base (sans RAG)
        base_system_prompt = self.current_system_prompt or ""
        
        if self.is_rag_enabled and user_input:
            if not self.embedding_model:
                console.print("[bold red]Erreur RAG: Aucun modèle d'embedding n'est configuré. Désactivation du RAG.[/bold red]")
                self.is_rag_enabled = False
            else:
                # Effectuer la recherche RAG avec filtrage par score de similarité
                if not self.silent_mode:
                    console.print("[cyan]Recherche RAG en cours...[/cyan]")
                context_str = await self._get_rag_context(user_input)
                if context_str:
                    # Remplacer le message utilisateur par un prompt RAG structuré
                    rag_prompt = (
                        "En te basant exclusivement sur le contexte suivant, réponds à la question ci-dessous.\n\n"
                        "--- CONTEXTE ---\n"
                        f"{context_str}\n"
                        "--- FIN DU CONTEXTE ---\n\n"
                        f"Question: {user_input}"
                    )
                    # Modifier le dernier message (la question de l'utilisateur)
                    if messages_for_api and messages_for_api[-1]["role"] == "user":
                        messages_for_api[-1]["content"] = rag_prompt
                    
                    if not self.silent_mode:
                        context_panel = Panel(Markdown(context_str), title="🧠 Contexte RAG trouvé", border_style="magenta", expand=False)
                        console.print(context_panel)
                else:
                    if not self.silent_mode:
                        console.print("[yellow]Aucun contexte pertinent trouvé dans la base de données vectorielle.[/yellow]")

        # S'assurer qu'il y a un prompt système s'il est défini
        if base_system_prompt and (not messages_for_api or messages_for_api[0].get("role") != "system"):
             messages_for_api.insert(0, {"role": "system", "content": base_system_prompt})

        return messages_for_api

    async def _get_rag_context(self, user_input: str) -> Optional[str]:
        """
        Effectue la recherche vectorielle dans Qdrant et retourne le contexte
        formaté pour être injecté dans le prompt.
        Utilise un seuil de similarité pour filtrer les résultats non pertinents.

        Args:
            user_input (str): Le message de l'utilisateur à utiliser pour la recherche.

        Returns:
            Optional[str]: Le contexte formaté, ou None si aucun résultat pertinent n'est trouvé.
        """
        if not self.api_url or not self.api_key or not self.embedding_model:
            return None
        query_vector_list = await get_embeddings(self.api_url, self.api_key, [user_input], self.embedding_model)
        if not query_vector_list:
            return None
        
        query_vector = query_vector_list[0]
        search_results = self.qdrant_manager.search(vector=query_vector, limit=5) if self.qdrant_manager.client else []
        
        if not search_results:
            return None
        
        # Utiliser le seuil de similarité configurable
        similarity_threshold = self.rag_similarity_threshold
        
        # Filtrer les résultats selon le seuil de similarité
        relevant_results = [hit for hit in search_results if hit.get('score', 0) >= similarity_threshold]
        
        if not relevant_results:
            if not self.silent_mode:
                max_score = max(hit.get('score', 0) for hit in search_results) if search_results else 0
                console.print(f"[yellow]Aucun résultat suffisamment pertinent (meilleur score: {max_score:.3f}, seuil: {similarity_threshold})[/yellow]")
            return None
        
        # Afficher les scores pour information/debug
        if not self.silent_mode:
            scores_info = ", ".join([f"{hit.get('score', 0):.3f}" for hit in relevant_results])
            console.print(f"[green]Résultats pertinents trouvés (scores: {scores_info}, seuil: {similarity_threshold})[/green]")
            
        return "\n\n---\n\n".join([
            f"Source: {hit['payload']['source']} (score: {hit.get('score', 0):.3f})\n\n{hit['payload']['text']}" 
            for hit in relevant_results
        ])

    def _add_assistant_message_to_history(self, response_content: Optional[str], tool_calls: Optional[List[Dict]]):
        """
        Formate et ajoute la réponse de l'assistant (texte et/ou appels d'outils)
        à l'historique de la conversation.

        Args:
            response_content (Optional[str]): Le contenu textuel de la réponse.
            tool_calls (Optional[List[Dict]]): La liste des appels d'outils.
        """
        processed_tool_calls = []
        if tool_calls:
            for tc in tool_calls:
                processed_tc = tc.copy()
                if "function" in processed_tc and "arguments" in processed_tc["function"]:
                    args_val = processed_tc["function"]["arguments"]
                    if isinstance(args_val, dict):
                        processed_tc["function"]["arguments"] = json.dumps(args_val)
                    elif isinstance(args_val, str) and not args_val.strip():
                        processed_tc["function"]["arguments"] = "{}"
                processed_tool_calls.append(processed_tc)

        assistant_message: Dict[str, Any] = {"role": "assistant"}
        assistant_message["content"] = clean_thinking_content(response_content or "")
        if processed_tool_calls:
            assistant_message["tool_calls"] = processed_tool_calls
        
        self.messages.append(assistant_message)

    async def _handle_tool_calls(self, tool_calls: List[Dict], messages_for_api: List[Dict]):
        """
        Gère l'exécution des appels d'outils demandés par le modèle,
        appelle les fonctions correspondantes et ajoute les résultats à l'historique.

        Args:
            tool_calls (List[Dict]): La liste des appels d'outils reçus de l'API.
            messages_for_api (List[Dict]): La liste des messages à laquelle ajouter
                                           les réponses des outils.
        """
        for tool_call in tool_calls:
            if not self.silent_mode:
                display_tool_call_request(tool_call)
            
            func_name = tool_call.get("function", {}).get("name")
            func_args_raw = tool_call.get("function", {}).get("arguments", "{}")
            tool_call_id = tool_call.get("id", "N/A")

            if func_name in TOOL_FUNCTIONS_MAP:
                try:
                    # Gérer le cas où arguments est déjà un dict ou une string JSON
                    if isinstance(func_args_raw, dict):
                        func_args = func_args_raw
                    elif isinstance(func_args_raw, str) and func_args_raw.strip():
                        func_args = json.loads(func_args_raw)
                    else:
                        func_args = {}
                    
                    func_to_call = TOOL_FUNCTIONS_MAP[func_name]
                    if not func_to_call:
                        raise ValueError(f"Fonction pour '{func_name}' non implémentée.")

                    tool_kwargs = {
                        **func_args,
                        'god_mode': self.god_mode,
                        'console_instance': console,
                        'qdrant_manager': self.qdrant_manager,
                        'embedding_model': self.embedding_model,
                        'api_url': self.api_url or "",
                        'api_key': self.api_key or "",
                    }
                    
                    console.print(f"[yellow]Outil {func_name}...[/yellow]")
                    
                    tool_result = await func_to_call(**tool_kwargs) if asyncio.iscoroutinefunction(func_to_call) else func_to_call(**tool_kwargs)
                    
                    if not self.silent_mode:
                        display_tool_call_response(tool_call_id, func_name, tool_result)
                    
                    # Convertir le résultat en chaîne de caractères de manière sûre
                    if isinstance(tool_result, dict):
                        tool_content = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    elif isinstance(tool_result, (list, tuple)):
                        tool_content = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    else:
                        tool_content = str(tool_result)
                    
                    tool_response_message = {"tool_call_id": tool_call_id, "role": "tool", "content": tool_content}
                except Exception as e:
                    error_msg = f"Erreur outil {func_name}: {e}"
                    console.print(f"[red]{error_msg}[/red]")
                    tool_response_message = {"tool_call_id": tool_call_id, "role": "tool", "content": error_msg}
            else:
                error_msg = f"Outil inconnu: {func_name}"
                console.print(f"[red]{error_msg}[/red]")
                tool_response_message = {"tool_call_id": tool_call_id, "role": "tool", "content": error_msg}

            self.messages.append(tool_response_message)
            messages_for_api.append(tool_response_message)

    def _autosave_session(self):
        """
        Sauvegarde la session en cours (métadonnées et historique) dans un
        fichier JSON et/ou Markdown si les chemins sont configurés.
        """
        if not self.autosave_json_path and not self.autosave_md_path:
            return

        session_metadata = {
            "model": self.current_model, 
            "temperature": self.current_temperature, 
            "max_tokens": self.current_max_tokens,
            "system_prompt": self.current_system_prompt,
            "api_url": self.api_url, 
            "debug": self.debug_active
        }
        
        if self.autosave_json_path:
            session_data = {"metadata": session_metadata, "history": self.messages}
            save_session_json(session_data, self.autosave_json_path)
        
        if self.autosave_md_path:
            save_chat_markdown(self.messages, self.autosave_md_path, session_metadata)

@click.command()
@click.option('--model', 'cli_model', default=None, help="Modèle à utiliser (ex: gemma3:4b).")
@click.option('--max-tokens', 'cli_max_tokens', default=int(MAX_TOKENS) if MAX_TOKENS else 1024, type=int, help="Max tokens pour réponse (défaut: 1024).")
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
@click.option('--qdrant-url', 'cli_qdrant_url', default=os.getenv("QDRANT_URL", "localhost"), help="URL du serveur Qdrant.")
@click.option('--qdrant-port', 'cli_qdrant_port', default=int(os.getenv("QDRANT_PORT", 6333)), type=int, help="Port du serveur Qdrant.")
@click.option('--qdrant-collection', 'cli_qdrant_collection', default=os.getenv("QDRANT_COLLECTION", "minichat_rag"), help="Nom de la collection Qdrant.")
@click.option('--embedding-model', 'cli_embedding_model', default=os.getenv("EMBEDDING_MODEL"), help="Modèle à utiliser pour l'embedding.")
def main(**kwargs):
    """
    Point d'entrée principal du Mini-Chat LLMaaS.
    Initialise et exécute le client de chat en fonction des arguments de la ligne de commande.
    """
    global API_URL, API_KEY, DEFAULT_MODEL 

    # Écraser les configurations globales si des options CLI sont fournies
    if kwargs.get('cli_api_url'):
        API_URL = kwargs['cli_api_url']
    if kwargs.get('cli_api_key'):
        API_KEY = kwargs['cli_api_key']
    
    # Déterminer le modèle initial à utiliser
    initial_model_to_use = kwargs.get('cli_model') or DEFAULT_MODEL
    
    # Charger le contenu du fichier de règles si spécifié
    rules_prompt_content: Optional[str] = None
    if kwargs.get('cli_rules_path'):
        try:
            with open(kwargs['cli_rules_path'], 'r', encoding='utf-8') as f_rules:
                rules_prompt_content = f_rules.read()
            if not kwargs.get('cli_silent_mode'):
                console.print(f"[info]Règles chargées depuis '{kwargs['cli_rules_path']}'[/info]")
        except Exception as e:
            console.print(f"[red]Erreur lors du chargement du fichier de règles '{kwargs['cli_rules_path']}': {e}[/red]")

    # Vérifier la présence de la clé API
    if not API_KEY:
        console.print("[bold red]Erreur: Clé API (API_KEY) non configurée.[/bold red]")
        return

    # Préparer les arguments pour le constructeur de ChatClient
    client_args = {
        'api_url_param': API_URL,
        'api_key_param': API_KEY,
        'initial_model': initial_model_to_use,
        'initial_max_tokens': kwargs.get('cli_max_tokens'),
        'initial_debug': kwargs.get('cli_debug'),
        'initial_temperature': kwargs.get('cli_temperature'),
        'initial_system_prompt': kwargs.get('cli_system_prompt'),
        'initial_rules_prompt': rules_prompt_content,
        'initial_user_prompt': kwargs.get('cli_initial_user_prompt'),
        'autosave_json_path': kwargs.get('cli_autosave_json_path'),
        'autosave_md_path': kwargs.get('cli_autosave_md_path'),
        'load_session_path': kwargs.get('cli_load_session_path'),
        'god_mode': kwargs.get('cli_god_mode'),
        'silent_mode_initial': kwargs.get('cli_silent_mode'),
        'non_interactive_initial': kwargs.get('cli_non_interactive'),
        'stream_enabled_initial': not kwargs.get('cli_no_stream'),
        'qdrant_url': kwargs.get('cli_qdrant_url'),
        'qdrant_port': kwargs.get('cli_qdrant_port'),
        'qdrant_collection': kwargs.get('cli_qdrant_collection'),
        'embedding_model': kwargs.get('cli_embedding_model')
    }

    # Créer et exécuter le client de chat
    chat_client = ChatClient(**client_args)
    asyncio.run(chat_client.run())

if __name__ == "__main__":
    main()
