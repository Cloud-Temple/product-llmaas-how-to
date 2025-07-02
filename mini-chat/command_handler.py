# -*- coding: utf-8 -*-
"""
Gestionnaire de Commandes pour Mini-Chat LLMaaS.

Ce module contient la logique pour parser et exécuter les commandes internes
du client de chat (ex: /help, /model, /save_session, /embed, etc.).

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-30
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import asyncio

# Importations des modules nécessaires
from ui_utils import console, Panel, Markdown, select_model_interactive
from session_manager import save_session_json, load_session_from_json, save_chat_markdown
from rag_core import get_text_chunks, search_in_vector_database
from api_client import get_available_models, stream_chat_completions, get_embeddings
from tools_definition import TOOL_FUNCTIONS_MAP, TOOLS_AVAILABLE
from rich.status import Status
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.console import Console

if TYPE_CHECKING:
    from mini_chat import ChatClient


class CommandHandler:
    """
    Gère l'exécution des commandes internes du chat.
    """
    def __init__(self, client: 'ChatClient'):
        """
        Initialise le gestionnaire de commandes avec une référence au client de chat.

        Args:
            client: Une référence à l'instance ChatClient pour accéder et modifier son état.
        """
        self.client = client
        # Mettre à jour le mapping des outils ici pour inclure les dépendances
        # search_in_vector_database est une fonction asynchrone qui a besoin de dépendances
        TOOL_FUNCTIONS_MAP['search_in_vector_database'] = search_in_vector_database

    async def handle_command(self, user_input: str) -> bool:
        """
        Traite une commande utilisateur.

        Args:
            user_input: La chaîne de caractères entrée par l'utilisateur.

        Returns:
            True si la commande a été traitée, False sinon.
        """
        command_parts = user_input.split(maxsplit=1)
        command = command_parts[0].lower()
        # L'argument conserve sa casse originale, ce qui est crucial pour les chemins de fichiers.
        arg = command_parts[1] if len(command_parts) > 1 else ""

        if command == "/quit" or command == "/exit":
            console.print(Markdown("--- Au revoir ! ---"))
            return True # Indique que le chat doit se terminer
        
        elif command == "/help":
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
                "- `/embed <chemin_fichier>`: Lire un fichier, le découper, et l'intégrer dans la base de données vectorielle Qdrant.\n"
                "- `/rag on|off`: Activer ou désactiver la recherche RAG pour les prochains messages.\n"
                "- `/rag_threshold [valeur]`: Afficher ou modifier le seuil de similarité RAG (défaut: 0.78, plage: 0.0-1.0).\n"
                "- `/qdrant_list [limit]`: Lister les éléments stockés dans la collection Qdrant (défaut: 10 éléments).\n"
                "- `/qdrant_info`: Afficher les informations sur la collection Qdrant.\n"
                "- `/qdrant_delete <point_id>`: Supprimer un point spécifique de la collection Qdrant.\n"
                "- `/qdrant_clear`: Vider complètement la collection Qdrant (supprime tous les points).\n"
                "- `/qdrant_drop`: Supprimer complètement la collection Qdrant.\n"
                "- `/context [all]`: Afficher le contexte actuel de l'application (configuration, état, etc.). Utilisez `all` pour voir le JSON complet.\n"
                "- `/help`: Afficher cette aide.\n\n"
                "Pour les options de lancement du script, utilisez `python mini_chat.py --help`."
            ), title=" Aide Mini-Chat ", border_style="blue", expand=False))
            return True

        elif command == "/smol":
            await self._handle_smol_command()
            return True

        elif command == "/stream":
            self.client.streaming_enabled = not self.client.streaming_enabled
            console.print(f"Mode streaming {'[bold green]activé[/bold green]' if self.client.streaming_enabled else '[bold red]désactivé[/bold red]'}.")
            return True

        elif command == "/tools":
            self._handle_tools_command()
            return True

        elif command == "/silent":
            self.client.silent_mode = not self.client.silent_mode
            console.print(f"Mode silencieux {'[bold green]activé[/bold green]' if self.client.silent_mode else '[bold red]désactivé[/bold red]'}.")
            return True

        elif command.startswith("/system "):
            self._handle_system_command(arg)
            return True

        elif command == "/system_clear":
            self.client.current_system_prompt = None
            self.client.messages = []
            console.print("Prompt système supprimé. Historique réinitialisé.")
            return True

        elif command.startswith("/save_session "):
            self._handle_save_session_command(arg)
            return True

        elif command.startswith("/load_session "):
            await self._handle_load_session_command(arg)
            return True

        elif command.startswith("/savemd "):
            self._handle_save_md_command(arg)
            return True

        elif command == "/embed":
            await self._handle_embed_command(arg)
            return True

        elif command == "/rag":
            self._handle_rag_command(arg)
            return True

        elif command == "/rag_threshold":
            self._handle_rag_threshold_command(arg)
            return True

        elif command == "/context":
            self._handle_context_command(arg)
            return True

        elif command == "/debug":
            self.client.debug_active = not self.client.debug_active
            console.print(f"Mode debug {'[bold green]activé[/bold green]' if self.client.debug_active else '[bold red]désactivé[/bold red]'}.")
            return True

        elif command == "/history":
            self._handle_history_command()
            return True

        elif command == "/clear":
            self.client.messages = [{"role": "system", "content": self.client.current_system_prompt}] if self.client.current_system_prompt else []
            console.print("[yellow]Historique effacé.[/yellow]")
            return True

        elif command == "/model":
            await self._handle_model_command()
            return True

        elif command == "/qdrant_list":
            self._handle_qdrant_list_command(arg)
            return True

        elif command == "/qdrant_info":
            self._handle_qdrant_info_command()
            return True

        elif command.startswith("/qdrant_delete "):
            self._handle_qdrant_delete_command(arg)
            return True

        elif command == "/qdrant_clear":
            self._handle_qdrant_clear_command()
            return True

        elif command == "/qdrant_drop":
            self._handle_qdrant_drop_command()
            return True

        return False # La commande n'a pas été reconnue ou traitée

    async def _handle_smol_command(self):
        """Gère la commande /smol pour condenser l'historique."""
        if not self.client.messages or all(m.get("role") == "system" for m in self.client.messages):
            console.print("[yellow]Historique vide ou ne contient que des messages système. Rien à condenser.[/yellow]")
            return

        console.print("[cyan]Demande de condensation du contexte au LLM...[/cyan]")

        if not self.client.current_model:
            console.print("[red]Erreur: Aucun modèle n'est actuellement sélectionné pour la condensation.[/red]")
            return
        
        history_to_condense = [msg for msg in self.client.messages if msg.get("role") != "system"]
        history_str = "\n".join([f"{m['role']}: {m.get('content', '') or m.get('tool_calls', '')}" for m in history_to_condense])
        
        condensation_prompt_messages = [
            {"role": "system", "content": "Tu es un assistant expert en résumé et en formulation de prompts efficaces. Ta tâche est de condenser l'historique de conversation suivant en un unique prompt utilisateur concis. Ce prompt doit préserver l'intention principale de la conversation, la tâche en cours, et toutes les informations cruciales nécessaires pour que je (un autre LLM) puisse continuer la conversation ou achever la tâche sans perdre de contexte. Le résultat doit être SEULEMENT le prompt condensé, sans aucune phrase d'introduction ou de conclusion de ta part."},
            {"role": "user", "content": f"Voici l'historique à condenser :\n\n---\n{history_str}\n---\n\nProduis maintenant le prompt utilisateur condensé et efficace."}
        ]
        
        condensed_context, _, _, _ = await stream_chat_completions(
            self.client.api_url, self.client.api_key, self.client.current_model, 
            condensation_prompt_messages, 
            max_tokens=self.client.current_max_tokens,
            debug_mode=self.client.debug_active, 
            temperature=0.1,
            stream_enabled=False,
            silent_mode=True
        )

        if condensed_context:
            self.client.messages.clear()
            if self.client.current_system_prompt:
                self.client.messages.append({"role": "system", "content": self.client.current_system_prompt})
            self.client.messages.append({"role": "user", "content": condensed_context.strip()})
            console.print("[green]Contexte condensé par le LLM et appliqué.[/green]")
            console.print(f"[italic]Nouveau contexte utilisateur (condensé) :[/italic]\n{condensed_context.strip()}")
        else:
            console.print("[red]Échec de la condensation du contexte par le LLM.[/red]")

    def _handle_tools_command(self):
        """Affiche la liste des outils disponibles."""
        if not self.client.silent_mode:
            console.print("\n[bold blue]Outils disponibles:[/bold blue]")
            if TOOLS_AVAILABLE:
                for tool_spec in TOOLS_AVAILABLE:
                    f_def = tool_spec.get("function",{})
                    console.print(f"- [cyan]{f_def.get('name','N/A')}[/cyan]: {f_def.get('description','N/A')}")
            else:
                console.print("[yellow]Aucun outil configuré.[/yellow]")
        else:
            console.print("[italic dim]Mode silencieux actif. Commande /tools ignorée pour l'affichage.[/italic dim]")

    def _handle_system_command(self, new_prompt: str):
        """Définit ou modifie le prompt système."""
        self.client.current_system_prompt = new_prompt if new_prompt else self.client.current_system_prompt
        self.client.messages = [{"role": "system", "content": self.client.current_system_prompt}] if self.client.current_system_prompt else []
        console.print(f"Prompt système {'mis à jour' if new_prompt else 'conservé'}. Historique réinitialisé.")

    def _handle_save_session_command(self, filename: str):
        """Sauvegarde la session actuelle."""
        if filename:
            session_data = {
                "metadata": {
                    "model": self.client.current_model,
                    "temperature": self.client.current_temperature, 
                    "max_tokens": self.client.current_max_tokens,
                    "system_prompt": self.client.current_system_prompt,
                    "api_url": self.client.api_url,
                    "debug": self.client.debug_active
                }, 
                "history": self.client.messages
            }
            save_session_json(session_data, filename)
        else:
            console.print("[yellow]Nom de fichier manquant.[/yellow]")

    async def _handle_load_session_command(self, filename: str):
        """Charge une session depuis un fichier JSON."""
        if filename:
            loaded_s = load_session_from_json(filename)
            if loaded_s:
                meta = loaded_s.get("metadata",{})
                self.client.current_model = meta.get("model", self.client.current_model)
                self.client.current_temperature = meta.get("temperature", self.client.current_temperature)
                self.client.current_max_tokens = meta.get("max_tokens", self.client.current_max_tokens)
                self.client.current_system_prompt = meta.get("system_prompt", self.client.current_system_prompt)
                self.client.debug_active = meta.get("debug", self.client.debug_active) 
                self.client.messages = loaded_s.get("history",[])
                console.print(f"[green]Session chargée depuis '{filename}'.[/green]")
                console.print(f"Modèle: [cyan]{self.client.current_model}[/cyan] | Temp: {self.client.current_temperature:.1f} | MaxTokens: {self.client.current_max_tokens} | Debug: {'On' if self.client.debug_active else 'Off'}")
                if self.client.current_system_prompt:
                    console.print(f"Prompt Système: [italic yellow]'{self.client.current_system_prompt}'[/italic yellow]")
                else:
                    console.print(f"Prompt Système: [italic]Aucun[/italic]")
                
                # Re-vérifier l'état RAG après chargement de session
                if self.client.embedding_model and self.client.qdrant_manager.client and self.client.qdrant_manager.check_collection_exists():
                    self.client.is_rag_enabled = True
                    console.print("[bold green]Mode RAG activé automatiquement (connexion Qdrant OK et collection trouvée).[/bold green]")
                elif self.client.embedding_model:
                    self.client.is_rag_enabled = False
                    console.print("[yellow]Mode RAG désactivé. Pour l'activer, utilisez `/embed` pour créer la collection ou `/rag on` si elle existe déjà.[/yellow]")

            else:
                console.print("[yellow]Nom de fichier manquant.[/yellow]")

    def _handle_save_md_command(self, filename: str):
        """Sauvegarde l'historique en Markdown."""
        if filename: 
            md_meta = {
                "model": self.client.current_model,
                "temperature": self.client.current_temperature, 
                "max_tokens": self.client.current_max_tokens,
                "system_prompt": self.client.current_system_prompt,
                "api_url": self.client.api_url,
                "debug": self.client.debug_active
            }
            save_chat_markdown(self.client.messages, filename, md_meta)
        else:
            console.print("[yellow]Nom de fichier manquant.[/yellow]")

    async def _handle_embed_command(self, file_path: str):
        """Gère la commande /embed pour l'ingestion de documents."""
        if not self.client.embedding_model:
            console.print("[bold red]Erreur: Aucun modèle d'embedding n'est configuré. Veuillez définir EMBEDDING_MODEL dans .env ou utiliser --embedding-model.[/bold red]")
            return
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            console.print(f"[bold red]Erreur: Le fichier '{file_path}' n'existe pas.[/bold red]")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            console.print(f"[info]Fichier '{file_path}' lu. Découpage en chunks...[/info]")
            rag_chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "256"))
            rag_chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
            chunks = get_text_chunks(text_content, chunk_size=rag_chunk_size, chunk_overlap=rag_chunk_overlap)
            console.print(f"[info]{len(chunks)} chunks créés. Tentative de récupération des embeddings...[/info]")

            batch_size = 16
            all_vectors = []
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                console.print(f"[yellow]Appel API pour embedding du lot {i//batch_size + 1} ({len(batch_chunks)} chunks)...[/yellow]")
                with console.status(f"[yellow]Embedding du lot {i//batch_size + 1}...[/yellow]", spinner="earth"):
                    batch_vectors = await get_embeddings(self.client.api_url, self.client.api_key, batch_chunks, self.client.embedding_model)
                
                if not batch_vectors:
                    console.print(f"[bold red]Échec de l'embedding pour le lot {i//batch_size + 1}. Annulation de l'upsert.[/bold red]")
                    all_vectors = []
                    break
                console.print(f"[green]Embeddings reçus pour le lot {i//batch_size + 1}.[/green]")
                all_vectors.extend(batch_vectors)
            
            if all_vectors:
                if not self.client.vector_size_initialized:
                    vector_size = len(all_vectors[0])
                    console.print(f"[info]Taille de vecteur détectée: {vector_size}.[/info]")
                    self.client.qdrant_manager.create_collection_if_not_exists(vector_size)
                    self.client.vector_size_initialized = True
                
                payloads = [{"text": chunk, "source": os.path.basename(file_path)} for chunk in chunks]
                console.print(f"[info]Upsert de {len(all_vectors)} vecteurs dans Qdrant...[/info]")
                self.client.qdrant_manager.upsert_points(all_vectors, payloads)
                console.print("[bold green]Processus d'embedding et d'upsert terminé avec succès.[/bold green]")
                
                # Proposer d'activer le RAG si il est désactivé
                if not self.client.is_rag_enabled:
                    console.print("[yellow]Le mode RAG est actuellement désactivé.[/yellow]")
                    if Confirm.ask("Voulez-vous activer le mode RAG pour utiliser les données que vous venez d'intégrer ?", default=True):
                        self.client.is_rag_enabled = True
                        console.print("[bold green]Mode RAG activé ! Vous pouvez maintenant poser des questions sur le contenu intégré.[/bold green]")
                    else:
                        console.print("[yellow]Mode RAG laissé désactivé. Utilisez `/rag on` pour l'activer plus tard.[/yellow]")
                else:
                    console.print("[info]Mode RAG déjà activé. Les nouvelles données sont immédiatement disponibles.[/info]")
            else:
                console.print("[bold red]Aucun vecteur n'a pu être généré. L'upsert dans Qdrant a été ignoré.[/bold red]")

        except Exception as e:
            console.print(f"[bold red]Erreur lors du traitement du fichier pour embedding: {e}[/bold red]")

    def _handle_rag_command(self, toggle: str):
        """Active ou désactive le mode RAG."""
        toggle = toggle.lower()
        
        if toggle == "on":
            if not self.client.embedding_model:
                console.print("[bold red]Impossible d'activer le RAG: Aucun modèle d'embedding n'est configuré. Utilisez --embedding-model.[/bold red]")
            else:
                self.client.is_rag_enabled = True
                console.print("[green]Mode RAG activé.[/green]")
        elif toggle == "off":
            self.client.is_rag_enabled = False
            console.print("[yellow]Mode RAG désactivé.[/yellow]")
        else:
            console.print(f"[yellow]Usage: /rag on|off. Le mode RAG est actuellement {'activé' if self.client.is_rag_enabled else 'désactivé'}.[/yellow]")

    def _handle_rag_threshold_command(self, threshold_str: str):
        """Affiche ou modifie le seuil de similarité RAG."""
        if not threshold_str:
            # Afficher le seuil actuel
            console.print(f"[cyan]Seuil de similarité RAG actuel: {self.client.rag_similarity_threshold:.3f}[/cyan]")
            console.print("[info]Usage: /rag_threshold <valeur> pour modifier (plage: 0.0-1.0)[/info]")
            console.print("[info]Valeurs recommandées: 0.75-0.85 selon les meilleures pratiques[/info]")
            return
        
        try:
            new_threshold = float(threshold_str)
            
            # Valider la plage
            if not (0.0 <= new_threshold <= 1.0):
                console.print("[bold red]Erreur: Le seuil doit être entre 0.0 et 1.0[/bold red]")
                return
            
            old_threshold = self.client.rag_similarity_threshold
            self.client.rag_similarity_threshold = new_threshold
            
            console.print(f"[green]✅ Seuil de similarité RAG modifié: {old_threshold:.3f} → {new_threshold:.3f}[/green]")
            
            # Donner des conseils selon la valeur
            if new_threshold < 0.5:
                console.print("[yellow]⚠️  Seuil très bas: Risque de résultats non pertinents[/yellow]")
            elif new_threshold < 0.7:
                console.print("[yellow]Seuil bas: Plus de résultats mais qualité variable[/yellow]")
            elif new_threshold > 0.9:
                console.print("[yellow]Seuil très élevé: Risque de manquer des résultats pertinents[/yellow]")
            else:
                console.print("[info]Seuil dans la plage recommandée (0.7-0.9)[/info]")
                
        except ValueError as e:
            console.print(f"[bold red]Erreur: '{threshold_str}' n'est pas un nombre valide[/bold red]")
            console.print("[info]Usage: /rag_threshold <valeur> (ex: /rag_threshold 0.8)[/info]")

    def _handle_history_command(self):
        """Affiche l'historique de la conversation."""
        if not self.client.messages:
            console.print("[yellow]Historique vide.[/yellow]")
            return
        console.print(Panel(Markdown("### Historique"), title="📜",border_style="blue"))
        for msg in self.client.messages:
            role = msg.get('role','?').capitalize()
            style = "green" if role=="User" else "magenta" if role=="Assistant" else "yellow"
            content_to_display = msg.get('content')
            if content_to_display is None: # Si content est None, afficher tool_calls
                content_to_display = json.dumps(msg.get('tool_calls',''), indent=2)
            console.print(f"[bold {style}]{role}:[/bold {style}] {content_to_display}")

    async def _handle_model_command(self):
        """Permet de changer de modèle."""
        if self.client.silent_mode:
            console.print("[italic dim]Mode silencieux actif. Commande /model ignorée.[/italic dim]")
            return
        
        available_models = await get_available_models(self.client.api_url, self.client.api_key)
        if not available_models:
            console.print("[yellow]Liste des modèles indisponible.[/yellow]")
            return

        new_model = select_model_interactive(available_models, self.client.current_model)
        if new_model and new_model != self.client.current_model:
            self.client.current_model = new_model
            self.client.messages = [{"role": "system", "content": self.client.current_system_prompt}] if self.client.current_system_prompt else []
            console.print(f"Modèle: [cyan]{self.client.current_model}[/cyan]. Historique réinitialisé.")

    def _handle_context_command(self, arg: str = ""):
        """Affiche le contexte actuel de l'application de manière élégante."""
        show_all = arg.lower() == "all"
        
        # Calculer le nombre de tokens dans le contexte
        total_tokens = self._count_tokens_in_messages()
        
        # Informations sur la configuration API
        api_info = f"**API Configuration:**\n"
        api_info += f"- URL: `{self.client.api_url or 'Non configurée'}`\n"
        api_info += f"- Clé API: `{'✓ Configurée' if self.client.api_key else '✗ Non configurée'}`\n\n"
        
        # Informations sur le modèle actuel
        model_info = f"**Modèle et Paramètres:**\n"
        model_info += f"- Modèle: `{self.client.current_model or 'Aucun sélectionné'}`\n"
        model_info += f"- Température: `{self.client.current_temperature:.1f}`\n"
        model_info += f"- Max Tokens: `{self.client.current_max_tokens}`\n"
        
        model_info += "\n"
        
        # Informations sur les modes actifs
        modes_info = f"**Modes Actifs:**\n"
        modes_info += f"- Debug: `{'✓ Activé' if self.client.debug_active else '✗ Désactivé'}`\n"
        modes_info += f"- Silencieux: `{'✓ Activé' if self.client.silent_mode else '✗ Désactivé'}`\n"
        modes_info += f"- Streaming: `{'✓ Activé' if self.client.streaming_enabled else '✗ Désactivé'}`\n"
        modes_info += f"- God Mode: `{'✓ Activé' if self.client.god_mode else '✗ Désactivé'}`\n"
        modes_info += f"- Non-interactif: `{'✓ Activé' if self.client.non_interactive_mode else '✗ Désactivé'}`\n\n"
        
        # Informations sur le RAG
        rag_info = f"**Configuration RAG:**\n"
        rag_info += f"- Mode RAG: `{'✓ Activé' if self.client.is_rag_enabled else '✗ Désactivé'}`\n"
        rag_info += f"- Modèle d'embedding: `{self.client.embedding_model or 'Non configuré'}`\n"
        
        # Vérifier la connexion Qdrant
        qdrant_status = "✗ Déconnecté"
        collection_status = "✗ Inexistante"
        if self.client.qdrant_manager.client:
            qdrant_status = "✓ Connecté"
            if self.client.qdrant_manager.check_collection_exists():
                collection_status = "✓ Existante"
        
        rag_info += f"- Qdrant: `{qdrant_status}` (localhost:6333)\n"
        rag_info += f"- Collection: `{collection_status}` ({self.client.qdrant_manager.collection_name})\n"
        rag_info += f"- Vecteurs initialisés: `{'✓ Oui' if self.client.vector_size_initialized else '✗ Non'}`\n"
        rag_info += f"- Seuil de similarité: `{self.client.rag_similarity_threshold:.3f}`\n\n"
        
        # Informations sur la session
        session_info = f"**Session Actuelle:**\n"
        system_prompt_preview = ""
        if self.client.current_system_prompt:
            preview = self.client.current_system_prompt[:100]
            if len(self.client.current_system_prompt) > 100:
                preview += "..."
            system_prompt_preview = f"`{preview}`"
        else:
            system_prompt_preview = "`Aucun`"
        
        session_info += f"- Prompt système: {system_prompt_preview}\n"
        
        # Compter les messages par type
        user_msgs = len([m for m in self.client.messages if m.get('role') == 'user'])
        assistant_msgs = len([m for m in self.client.messages if m.get('role') == 'assistant'])
        system_msgs = len([m for m in self.client.messages if m.get('role') == 'system'])
        tool_msgs = len([m for m in self.client.messages if m.get('role') == 'tool'])
        
        session_info += f"- Messages: `{len(self.client.messages)} total` (👤 {user_msgs} | 🤖 {assistant_msgs} | ⚙️ {system_msgs} | 🔧 {tool_msgs})\n"
        session_info += f"- Tokens estimés: `~{total_tokens} tokens`\n"
        
        # Vérification de problème de limite de contexte
        max_tokens = self.client.current_max_tokens or 1024
        if total_tokens + max_tokens > 32768:
            session_info += f"- ⚠️  **PROBLÈME DÉTECTÉ**: `{total_tokens} tokens (messages) + {max_tokens} tokens (completion) = {total_tokens + max_tokens} tokens > 32768 (limite du modèle)`\n"
            session_info += f"- 💡 **Solution**: Réduire `max_tokens` à `{32768 - total_tokens - 100}` ou désactiver le RAG temporairement\n"
        
        session_info += "\n"
        
        # Informations sur les outils
        tools_info = f"**Outils Disponibles:**\n"
        if TOOLS_AVAILABLE:
            tools_info += f"- Nombre d'outils: `{len(TOOLS_AVAILABLE)}`\n"
            tool_names = [tool.get("function", {}).get("name", "N/A") for tool in TOOLS_AVAILABLE]
            tools_info += f"- Outils: `{', '.join(tool_names[:5])}`"
            if len(tool_names) > 5:
                tools_info += f" et {len(tool_names) - 5} autres"
            tools_info += "\n"
        else:
            tools_info += "- Aucun outil configuré\n"
        
        # Assembler le contenu complet
        full_content = api_info + model_info + modes_info + rag_info + session_info + tools_info
        
        # Afficher dans un panel élégant
        title = "🔍 Contexte Actuel" if not show_all else "🔍 Contexte Complet"
        console.print(Panel(
            Markdown(full_content),
            title=title,
            border_style="cyan",
            expand=False
        ))
        
        # Si mode "all", afficher aussi le JSON complet
        if show_all:
            self._display_full_context_json()

    def _count_tokens_in_messages(self) -> int:
        """
        Compte approximativement le nombre de tokens dans les messages.
        Inclut le contexte RAG si activé pour donner une estimation réaliste.
        Utilise une estimation simple : 1 token ≈ 4 caractères.
        """
        total_chars = 0
        
        # Compter les messages de base
        for message in self.client.messages:
            content = message.get('content', '')
            if content:
                total_chars += len(str(content))
            
            # Compter aussi les tool_calls si présents
            tool_calls = message.get('tool_calls')
            if tool_calls:
                total_chars += len(json.dumps(tool_calls))
        
        # Si RAG activé, estimer le contexte supplémentaire qui sera ajouté
        if self.client.is_rag_enabled and self.client.qdrant_manager.client:
            # Estimation du contexte RAG basée sur la taille typique des chunks
            # 5 chunks × ~256 caractères par chunk + formatage
            estimated_rag_context = 5 * 256 + 200  # ~1500 caractères
            total_chars += estimated_rag_context
        
        # Estimation : 1 token ≈ 4 caractères (approximation pour l'anglais/français)
        estimated_tokens = total_chars // 4
        return estimated_tokens

    def _display_full_context_json(self):
        """Affiche le contexte complet au format JSON."""
        context_data = {
            "api_configuration": {
                "url": self.client.api_url,
                "api_key_configured": bool(self.client.api_key)
            },
            "model_parameters": {
                "current_model": self.client.current_model,
                "temperature": self.client.current_temperature,
                "max_tokens": self.client.current_max_tokens
            },
            "active_modes": {
                "debug": self.client.debug_active,
                "silent": self.client.silent_mode,
                "streaming": self.client.streaming_enabled,
                "god_mode": self.client.god_mode,
                "non_interactive": self.client.non_interactive_mode
            },
            "rag_configuration": {
                "rag_enabled": self.client.is_rag_enabled,
                "embedding_model": self.client.embedding_model,
                "qdrant_connected": bool(self.client.qdrant_manager.client),
                "collection_exists": self.client.qdrant_manager.check_collection_exists() if self.client.qdrant_manager.client else False,
                "collection_name": self.client.qdrant_manager.collection_name,
                "vectors_initialized": self.client.vector_size_initialized
            },
            "session": {
                "system_prompt": self.client.current_system_prompt,
                "messages_count": len(self.client.messages),
                "messages": self.client.messages
            },
            "tools": {
                "available_tools_count": len(TOOLS_AVAILABLE) if TOOLS_AVAILABLE else 0,
                "tools": TOOLS_AVAILABLE
            }
        }
        
        json_content = json.dumps(context_data, indent=2, ensure_ascii=False)
        console.print(Panel(
            json_content,
            title="📋 Contexte JSON Complet",
            border_style="yellow",
            expand=False
        ))

    def _handle_qdrant_list_command(self, arg: str = ""):
        """Liste les éléments stockés dans la collection Qdrant."""
        if not self.client.qdrant_manager.client:
            console.print("[bold red]Erreur: Qdrant n'est pas connecté.[/bold red]")
            return
        
        if not self.client.qdrant_manager.check_collection_exists():
            console.print(f"[yellow]La collection '{self.client.qdrant_manager.collection_name}' n'existe pas.[/yellow]")
            return
        
        # Déterminer la limite
        try:
            limit = int(arg) if arg else 10
            limit = max(1, min(limit, 100))  # Limiter entre 1 et 100
        except ValueError:
            limit = 10
            console.print(f"[yellow]Limite invalide '{arg}', utilisation de la valeur par défaut: {limit}[/yellow]")
        
        points = self.client.qdrant_manager.list_points(limit=limit)
        
        if not points:
            console.print("[yellow]Aucun point trouvé dans la collection.[/yellow]")
            return
        
        # Afficher les points dans un tableau élégant
        content = f"**Collection:** `{self.client.qdrant_manager.collection_name}`\n\n"
        content += f"**Points trouvés:** {len(points)} (limite: {limit})\n\n"
        
        for i, point in enumerate(points, 1):
            point_id = point.get('id', 'N/A')
            payload = point.get('payload', {})
            source = payload.get('source', 'N/A')
            text_preview = payload.get('text', '')[:100]
            if len(payload.get('text', '')) > 100:
                text_preview += "..."
            
            content += f"**{i}.** ID: `{point_id}`\n"
            content += f"   - Source: `{source}`\n"
            content += f"   - Texte: `{text_preview}`\n\n"
        
        console.print(Panel(
            Markdown(content),
            title="📋 Éléments Qdrant",
            border_style="cyan",
            expand=False
        ))

    def _handle_qdrant_info_command(self):
        """Affiche les informations sur la collection Qdrant."""
        if not self.client.qdrant_manager.client:
            console.print("[bold red]Erreur: Qdrant n'est pas connecté.[/bold red]")
            return
        
        if not self.client.qdrant_manager.check_collection_exists():
            console.print(f"[yellow]La collection '{self.client.qdrant_manager.collection_name}' n'existe pas.[/yellow]")
            return
        
        collection_info = self.client.qdrant_manager.get_collection_info()
        
        if not collection_info:
            console.print("[bold red]Impossible de récupérer les informations de la collection.[/bold red]")
            return
        
        # Extraire les informations importantes
        config = collection_info.get('config', {})
        vectors_config = config.get('params', {}).get('vectors', {})
        points_count = collection_info.get('points_count', 0)
        segments_count = collection_info.get('segments_count', 0)
        
        content = f"**Collection:** `{self.client.qdrant_manager.collection_name}`\n\n"
        content += f"**Statistiques:**\n"
        content += f"- Points: `{points_count}`\n"
        content += f"- Segments: `{segments_count}`\n\n"
        
        if vectors_config:
            vector_size = vectors_config.get('size', 'N/A')
            distance = vectors_config.get('distance', 'N/A')
            content += f"**Configuration des Vecteurs:**\n"
            content += f"- Taille: `{vector_size}`\n"
            content += f"- Distance: `{distance}`\n\n"
        
        # Afficher le JSON complet si demandé
        content += f"**Informations Complètes:**\n```json\n{json.dumps(collection_info, indent=2, ensure_ascii=False)}\n```"
        
        console.print(Panel(
            Markdown(content),
            title="ℹ️ Informations Collection Qdrant",
            border_style="blue",
            expand=False
        ))

    def _handle_qdrant_delete_command(self, point_id: str):
        """Supprime un point spécifique de la collection Qdrant."""
        if not point_id:
            console.print("[yellow]Usage: /qdrant_delete <point_id>[/yellow]")
            return
        
        if not self.client.qdrant_manager.client:
            console.print("[bold red]Erreur: Qdrant n'est pas connecté.[/bold red]")
            return
        
        if not self.client.qdrant_manager.check_collection_exists():
            console.print(f"[yellow]La collection '{self.client.qdrant_manager.collection_name}' n'existe pas.[/yellow]")
            return
        
        # Demander confirmation
        if not Confirm.ask(f"Êtes-vous sûr de vouloir supprimer le point '{point_id}' ?"):
            console.print("[yellow]Suppression annulée.[/yellow]")
            return
        
        success = self.client.qdrant_manager.delete_point(point_id)
        if success:
            console.print(f"[green]Point '{point_id}' supprimé avec succès.[/green]")
        else:
            console.print(f"[bold red]Échec de la suppression du point '{point_id}'.[/bold red]")

    def _handle_qdrant_clear_command(self):
        """Vide complètement la collection Qdrant."""
        if not self.client.qdrant_manager.client:
            console.print("[bold red]Erreur: Qdrant n'est pas connecté.[/bold red]")
            return
        
        if not self.client.qdrant_manager.check_collection_exists():
            console.print(f"[yellow]La collection '{self.client.qdrant_manager.collection_name}' n'existe pas.[/yellow]")
            return
        
        # Demander confirmation avec avertissement
        console.print(f"[bold red]⚠️  ATTENTION: Cette action va supprimer TOUS les points de la collection '{self.client.qdrant_manager.collection_name}'![/bold red]")
        if not Confirm.ask("Êtes-vous absolument sûr de vouloir continuer ?"):
            console.print("[yellow]Opération annulée.[/yellow]")
            return
        
        success = self.client.qdrant_manager.clear_collection()
        if success:
            console.print(f"[green]Collection '{self.client.qdrant_manager.collection_name}' vidée avec succès.[/green]")
            # Désactiver le RAG car la collection est maintenant vide
            self.client.is_rag_enabled = False
            console.print("[yellow]Mode RAG désactivé (collection vide).[/yellow]")
        else:
            console.print(f"[bold red]Échec du vidage de la collection '{self.client.qdrant_manager.collection_name}'.[/bold red]")

    def _handle_qdrant_drop_command(self):
        """Supprime complètement la collection Qdrant."""
        if not self.client.qdrant_manager.client:
            console.print("[bold red]Erreur: Qdrant n'est pas connecté.[/bold red]")
            return
        
        if not self.client.qdrant_manager.check_collection_exists():
            console.print(f"[yellow]La collection '{self.client.qdrant_manager.collection_name}' n'existe pas déjà.[/yellow]")
            return
        
        # Demander confirmation avec double avertissement
        console.print(f"[bold red]⚠️  DANGER: Cette action va SUPPRIMER DÉFINITIVEMENT la collection '{self.client.qdrant_manager.collection_name}'![/bold red]")
        console.print("[bold red]Cette action est IRRÉVERSIBLE et supprimera toutes les données et la structure de la collection![/bold red]")
        
        if not Confirm.ask("Tapez 'oui' pour confirmer la suppression définitive", default=False):
            console.print("[yellow]Suppression annulée.[/yellow]")
            return
        
        success = self.client.qdrant_manager.delete_collection()
        if success:
            console.print(f"[green]Collection '{self.client.qdrant_manager.collection_name}' supprimée définitivement.[/green]")
            # Désactiver le RAG et réinitialiser l'état
            self.client.is_rag_enabled = False
            self.client.vector_size_initialized = False
            console.print("[yellow]Mode RAG désactivé et état vectoriel réinitialisé.[/yellow]")
        else:
            console.print(f"[bold red]Échec de la suppression de la collection '{self.client.qdrant_manager.collection_name}'.[/bold red]")

__all__ = ["CommandHandler"]
