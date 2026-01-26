# -*- coding: utf-8 -*-
"""
Script de test automatisé pour le scénario RAG de Mini-Chat.

Ce script permet de valider le fonctionnement complet de la chaîne RAG :
1. Connexion à Qdrant.
2. Ingestion d'un document (embedding + upsert).
3. Activation du mode RAG.
4. Interrogation du modèle avec contexte injecté.

Usage:
    python test_rag_scenario.py
"""

import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console

# Import des composants modulaires de Mini-Chat
from mini_chat import ChatConfig, ChatService, MiniChatCLI

# Configuration pour l'affichage console
console = Console()

async def run_rag_test():
    """
    Exécute le scénario de test RAG étape par étape.
    """
    console.print("[bold blue]--- Démarrage du test RAG ---[/bold blue]")
    
    # 1. Configuration initiale
    # On force l'utilisation de gpt-oss-120b et du modèle d'embedding granite
    api_key = os.getenv("API_KEY")
    if not api_key:
        console.print("[bold red]Erreur: API_KEY non trouvée dans l'environnement.[/bold red]")
        return

    config = ChatConfig(
        model="openai/gpt-oss-120b",
        api_key=api_key,
        embedding_model="granite-embedding:278m",
        silent=False, # On veut voir les logs
        debug=False   # Mettre à True pour voir les payloads JSON
    )
    
    # Initialisation du service et de l'interface (pour utiliser ses méthodes helpers)
    service = ChatService(config)
    cli = MiniChatCLI(service)
    
    # 2. Nettoyage préventif
    # On supprime la collection pour partir d'un état propre
    console.print("\n[bold yellow]--- Nettoyage de la collection Qdrant ---[/bold yellow]")
    try:
        if service.qdrant.client and service.qdrant.check_collection_exists():
            service.qdrant.delete_collection()
            console.print("[green]Collection existante supprimée.[/green]")
        else:
            console.print("[dim]Aucune collection à supprimer.[/dim]")
    except Exception as e:
        console.print(f"[red]Erreur lors du nettoyage: {e}[/red]")
    
    # 3. Ingestion (Embedding & Indexation)
    console.print("\n[bold yellow]--- Test d'ingestion (Embedding) ---[/bold yellow]")
    file_path = "constitution.1958.txt"
    
    if not os.path.exists(file_path):
        console.print(f"[bold red]Erreur: Le fichier de test '{file_path}' est introuvable.[/bold red]")
        console.print("Veuillez vous assurer d'être dans le dossier 'mini-chat' et que le fichier existe.")
        return

    # Utilisation de la méthode helper de la CLI pour l'embedding
    # Elle gère le découpage (chunking), l'appel API d'embedding et l'upsert Qdrant
    await cli._run_embed(file_path)
    
    # 4. Activation du mode RAG
    console.print("\n[bold yellow]--- Activation RAG ---[/bold yellow]")
    # On force l'activation dans l'état du service
    service.state.is_rag_enabled = True
    
    if service.state.is_rag_enabled and service.state.qdrant_ready:
        console.print("[green]Mode RAG activé avec succès.[/green]")
    else:
        console.print("[bold red]Échec de l'activation RAG (Qdrant non prêt ?).[/bold red]")
        return
    
    # 5. Question RAG
    console.print("\n[bold yellow]--- Test de Question RAG ---[/bold yellow]")
    question = "Qui assure la présidence en cas de vacance ?"
    console.print(f"[bold]Question :[/bold] {question}")
    
    # On simule le traitement complet de l'input utilisateur par le service
    # Cela va : 
    # 1. Chercher le contexte dans Qdrant
    # 2. Construire le prompt augmenté
    # 3. Interroger le LLM en streaming
    await service.process_user_input(question)
    
    console.print("\n[bold blue]--- Fin du test ---[/bold blue]")

if __name__ == "__main__":
    # Chargement des variables d'environnement (.env)
    load_dotenv()
    
    try:
        asyncio.run(run_rag_test())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrompu par l'utilisateur.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erreur inattendue : {e}[/bold red]")
