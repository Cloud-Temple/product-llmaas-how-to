# -*- coding: utf-8 -*-
"""
Mini-Chat LLMaaS v3.0 - Architecture Refondue.

Ce module implémente une architecture robuste et modulaire pour le client de chat.
Il sépare la gestion de l'état (Session), la logique métier (Service) et l'interface (UI).

Auteur: Cloud Temple - LLMaaS Team
Date: 2026-01-25
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import readline

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

# Imports internes
from api_client import stream_chat_completions, get_available_models, get_embeddings
from qdrant_utils import QdrantManager
from tools_definition import TOOL_FUNCTIONS_MAP
from session_manager import save_session_json, save_chat_markdown
from rag_core import get_text_chunks
from ui_utils import display_tool_call_request, display_tool_call_response, display_stats

# Configuration
load_dotenv()
console = Console()

# --- Modèles de Données ---

@dataclass
class ChatConfig:
    """
    Configuration de la session de chat.
    Regroupe tous les paramètres statiques (URL, clés, modèle) et les préférences utilisateur.
    """
    api_url: str = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
    api_key: str = os.getenv("API_KEY", "")
    model: str = "openai/gpt-oss-120b"
    max_tokens: int = int(os.getenv("MAX_TOKENS", 8192))
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    
    # Options RAG
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "granite-embedding:278m")
    qdrant_url: str = os.getenv("QDRANT_URL", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "minichat_rag")
    rag_threshold: float = 0.75
    
    # Flags de fonctionnement
    debug: bool = False
    silent: bool = False
    stream: bool = True
    god_mode: bool = False

@dataclass
class ChatState:
    """
    État mutable de la session en cours.
    Contient l'historique des messages et l'état des connexions externes.
    """
    messages: List[Dict[str, Any]] = field(default_factory=list)
    is_rag_enabled: bool = False
    qdrant_ready: bool = False

# --- Service Métier ---

class ChatService:
    """
    Orchestrateur principal de la logique chat.
    Fait le lien entre l'état, la configuration et les services externes (API LLM, Qdrant).
    """
    
    def __init__(self, config: ChatConfig):
        self.config = config
        self.state = ChatState()
        self.qdrant = QdrantManager(
            host=config.qdrant_url, 
            port=config.qdrant_port, 
            collection_name=config.qdrant_collection
        )
        self._init_session()

    def _init_session(self):
        """
        Initialise l'historique avec le prompt système et vérifie la connexion Qdrant.
        Active automatiquement le RAG si la collection existe.
        """
        if self.config.system_prompt:
            self.state.messages.append({"role": "system", "content": self.config.system_prompt})
        
        # Vérification Qdrant
        try:
            if self.qdrant.client and self.qdrant.check_collection_exists():
                self.state.qdrant_ready = True
                # Activation auto si collection existe
                self.state.is_rag_enabled = True 
        except Exception:
            self.state.qdrant_ready = False

    async def process_user_input(self, user_input: str):
        """
        Traite une entrée utilisateur de bout en bout :
        1. Recherche RAG (si activé)
        2. Appel LLM (streaming)
        3. Exécution d'outils (si demandé par le LLM)
        4. Mise à jour de l'historique
        
        Args:
            user_input: Le texte saisi par l'utilisateur.
        """
        # 1. Gestion RAG
        context_msg = None
        if self.state.is_rag_enabled and self.state.qdrant_ready:
            context = await self._retrieve_context(user_input)
            if context:
                if not self.config.silent:
                    console.print(Panel(Markdown(context), title="🧠 Contexte RAG", border_style="magenta", expand=False))
                # On formate le message avec le contexte injecté
                context_msg = (
                    f"Utilise le contexte suivant pour répondre à la question.\n"
                    f"---\n{context}\n---\n"
                    f"Question: {user_input}"
                )

        # 2. Ajout message utilisateur à l'historique
        self.state.messages.append({"role": "user", "content": context_msg or user_input})
        
        # 3. Boucle d'interaction LLM (pour gérer les tool calls en chaîne)
        while True:
            # Préparation des messages pour l'API (filtrage éventuel)
            api_messages = self.state.messages
            
            content, usage, tool_calls, backend = await stream_chat_completions(
                self.config.api_url,
                self.config.api_key,
                self.config.model,
                api_messages,
                self.config.max_tokens,
                self.config.debug,
                self.config.temperature,
                self.config.stream,
                self.config.silent
            )

            # Ajout réponse assistant
            self.state.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls if tool_calls else None
            })

            if not self.config.silent and usage:
                display_stats(usage, backend)

            # 4. Exécution des outils si nécessaire
            if tool_calls:
                for tc in tool_calls:
                    await self._execute_tool(tc)
                continue # Reboucle pour envoyer les résultats au LLM
            
            break # Fin du tour de conversation

    async def _retrieve_context(self, query: str) -> Optional[str]:
        """
        Récupère le contexte pertinent depuis la base vectorielle.
        
        Args:
            query: La question de l'utilisateur.
            
        Returns:
            Une chaîne formatée contenant les extraits pertinents, ou None.
        """
        if not self.config.embedding_model: return None
        
        vectors = await get_embeddings(self.config.api_url, self.config.api_key, [query], self.config.embedding_model)
        if not vectors: return None
        
        results = self.qdrant_manager.search(vectors[0], limit=3)
        relevant = [r for r in results if r['score'] >= self.config.rag_threshold]
        
        if not relevant: return None
        return "\n\n".join([f"Source: {r['payload'].get('source','?')}\n{r['payload'].get('text','')}" for r in relevant])

    async def _execute_tool(self, tool_call: Dict):
        """
        Exécute un outil demandé par le modèle et ajoute le résultat à l'historique.
        
        Args:
            tool_call: Le dictionnaire décrivant l'appel d'outil (nom, arguments, id).
        """
        func_name = tool_call.get("function", {}).get("name")
        args_str = tool_call.get("function", {}).get("arguments", "{}")
        call_id = tool_call.get("id")

        if not self.config.silent:
            display_tool_call_request(tool_call)

        result_content = "Error: Tool not found"
        
        # Gestion des ID manquants (parfois le cas avec certains modèles)
        if call_id is None: call_id = "unknown"
        
        if func_name in TOOL_FUNCTIONS_MAP:
            try:
                args = json.loads(args_str) if args_str else {}
                func = TOOL_FUNCTIONS_MAP[func_name]
                
                # Injection de dépendances dynamique via kwargs
                kwargs = {**args}
                kwargs.update({
                    'god_mode': self.config.god_mode,
                    'api_url': self.config.api_url,
                    'api_key': self.config.api_key,
                    'qdrant_manager': self.qdrant,
                    'embedding_model': self.config.embedding_model
                })

                # Support des fonctions synchrones et asynchrones
                if asyncio.iscoroutinefunction(func):
                    res = await func(**kwargs)
                else:
                    res = func(**kwargs)
                
                # Formatage du résultat pour l'historique
                if isinstance(res, (dict, list)):
                    result_content = json.dumps(res, ensure_ascii=False)
                else:
                    result_content = str(res)

                if not self.config.silent:
                    display_tool_call_response(call_id, func_name, result_content)

            except Exception as e:
                result_content = f"Error: {str(e)}"
                if not self.config.silent:
                    console.print(f"[red]Erreur exécution outil: {e}[/red]")

        # Ajout du message de résultat d'outil à l'historique
        self.state.messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": result_content
        })

    # --- Propriétés helper ---
    @property
    def qdrant_manager(self): return self.qdrant

# --- Interface Utilisateur (CLI) ---

class MiniChatCLI:
    """
    Interface en ligne de commande (CLI).
    Gère l'affichage, la saisie utilisateur et le dispatching des commandes slash.
    """
    
    def __init__(self, service: ChatService):
        self.service = service
        self.setup_readline()

    def setup_readline(self):
        """Configure l'historique des commandes (flèches haut/bas)."""
        try:
            hist_file = os.path.expanduser("~/.minichat_history")
            if os.path.exists(hist_file):
                readline.read_history_file(hist_file)
            readline.set_history_length(1000)
        except: pass

    async def loop(self):
        """Boucle principale d'interaction (REPL)."""
        console.print(Panel(
            f"Modèle: [cyan]{self.service.config.model}[/cyan]\n"
            f"RAG: {'✅' if self.service.state.is_rag_enabled else '❌'}",
            title="🤖 Mini-Chat v3.0", border_style="blue"
        ))

        while True:
            try:
                user_input = Prompt.ask("\n[bold green]Vous[/bold green]")
                if not user_input.strip(): continue

                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                else:
                    await self.service.process_user_input(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Au revoir ![/yellow]")
                try: readline.write_history_file(os.path.expanduser("~/.minichat_history"))
                except: pass
                break
            except Exception as e:
                console.print(f"[bold red]Erreur critique: {e}[/bold red]")

    async def handle_command(self, cmd_str: str):
        """
        Traite les commandes internes (commençant par /).
        
        Args:
            cmd_str: La commande complète (ex: "/rag on").
        """
        parts = cmd_str.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["/quit", "/exit"]:
            raise KeyboardInterrupt
        
        elif cmd == "/clear":
            self.service.state.messages = []
            if self.service.config.system_prompt:
                self.service.state.messages.append({"role": "system", "content": self.service.config.system_prompt})
            console.print("[yellow]Historique effacé.[/yellow]")

        elif cmd == "/rag":
            if arg == "on":
                if self.service.state.qdrant_ready:
                    self.service.state.is_rag_enabled = True
                    console.print("[green]RAG activé.[/green]")
                else:
                    console.print("[red]Qdrant non prêt ou non connecté.[/red]")
            elif arg == "off":
                self.service.state.is_rag_enabled = False
                console.print("[yellow]RAG désactivé.[/yellow]")
            else:
                console.print(f"RAG est {'activé' if self.service.state.is_rag_enabled else 'désactivé'}.")

        elif cmd == "/embed":
            if not arg:
                console.print("[red]Usage: /embed <fichier>[/red]")
                return
            await self._run_embed(arg)

        elif cmd == "/history":
            for msg in self.service.state.messages:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content') or "[Tool Calls]"
                console.print(f"[bold]{role}[/bold]: {content[:100]}...")

        else:
            console.print(f"[red]Commande inconnue: {cmd}[/red]")

    async def _run_embed(self, path):
        """
        Logique d'embedding simplifiée et robuste.
        Lit un fichier, le découpe, génère les embeddings et les stocke dans Qdrant.
        """
        if not os.path.exists(path):
            console.print(f"[red]Fichier introuvable: {path}[/red]")
            return
        
        with open(path, 'r') as f: text = f.read()
        # Valeurs par défaut raisonnables pour le RAG : chunks de 512 tokens avec overlap de 50
        chunks = get_text_chunks(text, chunk_size=512, chunk_overlap=50)
        console.print(f"[dim]Génération de {len(chunks)} embeddings...[/dim]")
        
        vectors = await get_embeddings(self.service.config.api_url, self.service.config.api_key, chunks, self.service.config.embedding_model)
        if vectors:
            # S'assurer que la collection existe avec la bonne taille de vecteur avant l'upsert
            vector_size = len(vectors[0])
            self.service.qdrant.create_collection_if_not_exists(vector_size)
            
            self.service.qdrant.upsert_points(vectors, [{"text": c, "source": path} for c in chunks])
            console.print("[green]Indexation terminée.[/green]")
            self.service.state.qdrant_ready = True

# --- Point d'entrée ---

@click.command()
@click.option('--model', default="openai/gpt-oss-120b", help="Modèle à utiliser")
@click.option('--non-interactive', is_flag=True, help="Mode exécution unique sans prompt")
@click.option('--prompt', help="Prompt initial pour mode non-interactif")
def main(model, non_interactive, prompt):
    """
    Mini-Chat LLMaaS v3 - Point d'entrée.
    Initialise la configuration et lance la boucle principale.
    """
    config = ChatConfig(model=model)
    if not config.api_key:
        console.print("[red]API_KEY manquante dans .env[/red]")
        return

    service = ChatService(config)
    cli = MiniChatCLI(service)

    if non_interactive and prompt:
        asyncio.run(service.process_user_input(prompt))
    else:
        asyncio.run(cli.loop())

if __name__ == "__main__":
    main()
