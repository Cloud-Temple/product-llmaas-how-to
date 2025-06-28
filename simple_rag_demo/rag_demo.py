# -*- coding: utf-8 -*-
"""
Ce script est un démonstrateur minimaliste de RAG (Retrieval-Augmented Generation)
utilisant l'API LLMaaS de Cloud Temple. Il est conçu pour être un outil pédagogique
mettant en évidence les étapes clés du processus RAG de manière claire et visuelle.
"""

import os
import httpx
import numpy as np
import argparse
import json
from dotenv import load_dotenv
from typing import List, Dict, Any

# Import des composants de la bibliothèque 'rich' pour une sortie console améliorée
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.table import Table
from rich.markup import escape

# ==============================================================================
# 1. CONFIGURATION INITIALE
# ==============================================================================

# Initialisation de la console 'rich' pour de belles impressions
console = Console()

# Charger les variables d'environnement à partir d'un fichier .env.
# C'est une bonne pratique pour ne pas coder en dur les informations sensibles.
load_dotenv()
API_KEY = os.getenv("LLMAAS_API_KEY")
BASE_URL = os.getenv("LLMAAS_BASE_URL", "https://api.ai.cloud-temple.com/v1")

# Vérification critique que la configuration est bien présente.
if not API_KEY or not BASE_URL:
    console.print(Panel("[bold red]Erreur de Configuration[/bold red]\nVeuillez définir les variables [cyan]LLMAAS_API_KEY[/cyan] et [cyan]LLMAAS_BASE_URL[/cyan] dans un fichier .env.", title="Erreur", border_style="red"))
    exit()

# Préparation des headers HTTP qui seront utilisés pour toutes les requêtes API.
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Définition des modèles spécifiques qui seront utilisés pour chaque étape du RAG.
# Il est crucial d'utiliser un modèle spécialisé pour l'embedding et un autre pour la génération.
EMBEDDING_MODEL = "granite-embedding:278m"
GENERATION_MODEL = "mistral-small3.2:24b"

# ==============================================================================
# 2. CORPUS DE DOCUMENTS
# ==============================================================================

# Notre base de connaissances. Dans une application réelle, cela proviendrait
# d'une base de données, de fichiers, d'un site web, etc.
# Ici, nous utilisons des articles clés de la Constitution française.
CORPUS = [
    "Article 1: La France est une République indivisible, laïque, démocratique et sociale. Elle assure l'égalité devant la loi de tous les citoyens sans distinction d'origine, de race ou de religion. Elle respecte toutes les croyances. Son organisation est décentralisée.",
    "Article 2: La langue de la République est le français. L'emblème national est le drapeau tricolore, bleu, blanc, rouge. L'hymne national est 'La Marseillaise'. La devise de la République est 'Liberté, Égalité, Fraternité'. Son principe est : gouvernement du peuple, par le peuple et pour le peuple.",
    "Article 3: La souveraineté nationale appartient au peuple qui l'exerce par ses représentants et par la voie du référendum. Le suffrage est toujours universel, égal et secret.",
    "Article 4: Les partis et groupements politiques concourent à l'expression du suffrage. Ils se forment et exercent leur activité librement. Ils doivent respecter les principes de la souveraineté nationale et de la démocratie.",
    "Article 5: Le Président de la République veille au respect de la Constitution. Il assure, par son arbitrage, le fonctionnement régulier des pouvoirs publics ainsi que la continuité de l'État. Il est le garant de l'indépendance nationale, de l'intégrité du territoire et du respect des traités.",
    "Article 6: Le Président de la République est élu pour cinq ans au suffrage universel direct. Nul ne peut exercer plus de deux mandats consécutifs.",
    "Article 8: Le Président de la République nomme le Premier ministre. Il met fin à ses fonctions sur la présentation par celui-ci de la démission du Gouvernement.",
    "Article 20: Le Gouvernement détermine et conduit la politique de la Nation. Il dispose de l'administration et de la force armée.",
    "Article 21: Le Premier ministre dirige l'action du Gouvernement. Il est responsable de la Défense Nationale. Il assure l'exécution des lois.",
    "Article 24: Le Parlement vote la loi. Il contrôle l'action du Gouvernement. Il évalue les politiques publiques. Il comprend l'Assemblée nationale et le Sénat.",
    "Article 89: L'initiative de la révision de la Constitution appartient concurremment au Président de la République sur proposition du Premier ministre et aux membres du Parlement. Le projet ou la proposition de révision doit être examiné dans les conditions de délai fixées au troisième alinéa de l'article 42 et voté par les deux assemblées en termes identiques. La révision est définitive après avoir été approuvée par référendum."
]

# ==============================================================================
# 3. FONCTIONS D'INTERACTION AVEC L'API LLMAAS
# ==============================================================================

def get_embedding(text: str, debug: bool = False) -> np.ndarray:
    """
    Appelle l'endpoint /embeddings de l'API LLMaaS pour convertir un texte en vecteur numérique (embedding).
    
    Args:
        text (str): Le texte à vectoriser.
        debug (bool): Si True, affiche les payloads de la requête et de la réponse.

    Returns:
        np.ndarray: Le vecteur numpy représentant le texte. Retourne un tableau vide en cas d'erreur.
    """
    payload = {"input": [text], "model": EMBEDDING_MODEL}
    if debug:
        console.print(Panel(Syntax(json.dumps(payload, indent=2), "json", theme="solarized-dark", line_numbers=True), title="[blue]Payload de la Requête Embedding[/blue]", border_style="blue"))

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{BASE_URL}/embeddings", headers=HEADERS, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            if debug:
                display_json = json.loads(json.dumps(response_json))
                if 'data' in display_json and display_json['data']:
                    display_json['data'][0]['embedding'] = display_json['data'][0]['embedding'][:5] + ['...']
                console.print(Panel(Syntax(json.dumps(display_json, indent=2), "json", theme="solarized-dark", line_numbers=True), title="[blue]Réponse de l'API Embedding[/blue]", border_style="blue"))

            embedding_data = response_json['data'][0]['embedding']
            return np.array(embedding_data)
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Erreur HTTP (Embedding)[/bold red]: {e.response.status_code}\n{e.response.text}")
        return np.array([])
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue (Embedding)[/bold red]: {e}")
        return np.array([])

def generate_answer(prompt: str, debug: bool = False) -> str:
    """
    Appelle l'endpoint /chat/completions de l'API LLMaaS pour générer une réponse textuelle à partir d'un prompt.

    Args:
        prompt (str): Le prompt complet (contexte + question) à envoyer au modèle de génération.
        debug (bool): Si True, affiche les payloads de la requête et de la réponse.

    Returns:
        str: La réponse textuelle générée par le modèle.
    """
    payload = {
        "model": GENERATION_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.2,
    }
    if debug:
        display_payload = payload.copy()
        display_payload["messages"][0]["content"] = display_payload["messages"][0]["content"][:200] + "..."
        console.print(Panel(Syntax(json.dumps(display_payload, indent=2), "json", theme="solarized-dark", line_numbers=True), title="[blue]Payload de la Requête Génération[/blue]", border_style="blue"))

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload)
            response.raise_for_status()
            
            response_json = response.json()
            if debug:
                console.print(Panel(Syntax(json.dumps(response_json, indent=2), "json", theme="solarized-dark", line_numbers=True), title="[blue]Réponse de l'API Génération[/blue]", border_style="blue"))

            return response_json["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Erreur HTTP (Génération)[/bold red]: {e.response.status_code}\n{e.response.text}")
        return "Désolé, je n'ai pas pu générer de réponse."
    except Exception as e:
        console.print(f"[bold red]Erreur inattendue (Génération)[/bold red]: {e}")
        return "Désolé, une erreur est survenue."

# ==============================================================================
# 4. LOGIQUE FONDAMENTALE DU RAG
# ==============================================================================

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcule la similarité cosinus. Score de -1 à 1. Plus haut = mieux.
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcule la distance euclidienne. Score >= 0. Plus bas = mieux.
    """
    return float(np.linalg.norm(vec1 - vec2))

def find_most_relevant_document(query_embedding: np.ndarray, corpus_embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Compare le vecteur de la question à tous les vecteurs du corpus.
    Le choix du document pertinent se base sur la similarité cosinus (standard de l'industrie).
    """
    if not corpus_embeddings:
        return {"winner": "Aucun document.", "details": []}

    winner = ""
    best_similarity = -1
    details = []

    for doc, doc_embedding in corpus_embeddings.items():
        similarity = cosine_similarity(query_embedding, doc_embedding)
        distance = euclidean_distance(query_embedding, doc_embedding)
        details.append({"doc": doc, "similarity": similarity, "distance": distance})
        
        if similarity > best_similarity:
            best_similarity = similarity
            winner = doc
    
    details.sort(key=lambda x: x['similarity'], reverse=True)
            
    return {"winner": winner, "details": details}

# ==============================================================================
# 5. ORCHESTRATION PRINCIPALE DU SCRIPT
# ==============================================================================

def main(args):
    """
    Fonction principale qui orchestre toutes les étapes du processus RAG.
    """
    console.print(Panel("[bold cyan]Démonstrateur RAG (Retrieval-Augmented Generation)[/bold cyan]\nUtilisation de la Constitution Française comme base de connaissances", title="Bienvenue", border_style="green"))

    # --- ÉTAPE 1: Vectorisation du Corpus ---
    console.print(Panel("[bold]ÉTAPE 1: Vectorisation du Corpus[/bold]\nChaque article est converti en vecteur numérique (embedding).", title_align="left", border_style="magenta"))
    corpus_embeddings = {}
    with console.status("[bold yellow]Vectorisation en cours...[/bold yellow]") as status:
        for doc in CORPUS:
            status.update(f"Vectorisation: \"{doc[:40]}...\"")
            embedding = get_embedding(doc, debug=args.payload)
            if embedding.size > 0:
                corpus_embeddings[doc] = embedding
    console.print(f"[green]   => {len(corpus_embeddings)} documents vectorisés avec succès.[/green]\n")

    if not corpus_embeddings:
        console.print("[bold red]Erreur: Impossible de vectoriser le corpus.[/bold red]")
        return

    # --- ÉTAPE 2: Question de l'Utilisateur ---
    console.print(Panel("[bold]ÉTAPE 2: Question de l'Utilisateur[/bold]\nPosez une question sur la Constitution.", title_align="left", border_style="magenta"))
    user_query = console.input("[bold yellow]Votre question > [/bold yellow]")
    console.print("")

    # --- ÉTAPE 3: Vectorisation de la Question ---
    console.print(Panel("[bold]ÉTAPE 3: Vectorisation de la Question[/bold]\nLa question est convertie en vecteur pour la comparer au corpus.", title_align="left", border_style="magenta"))
    with console.status("[bold yellow]Vectorisation de la question...[/bold yellow]"):
        query_embedding = get_embedding(user_query, debug=args.payload)
    
    if query_embedding.size == 0:
        console.print("[bold red]Erreur: Impossible de vectoriser la question.[/bold red]")
        return
    console.print("[green]   => Question vectorisée avec succès.[/green]\n")

    # --- ÉTAPE 4: Recherche du Document Pertinent (Retrieval) ---
    console.print(Panel("[bold]ÉTAPE 4: Recherche par Similarité (Retrieval)[/bold]\nLe vecteur de la question est comparé à tous les vecteurs du corpus.", title_align="left", border_style="magenta"))
    
    search_results = find_most_relevant_document(query_embedding, corpus_embeddings)
    relevant_document = search_results["winner"]
    details = search_results["details"]

    table = Table(title="[bold]Calcul de Proximité[/bold]", show_header=True, header_style="bold cyan")
    table.add_column("Article (extrait)", style="dim", width=60)
    table.add_column("Similarité Cosinus ↑", justify="right", style="green")
    table.add_column("Distance Euclidienne ↓", justify="right", style="red")
    table.add_column("Choix (par Cosinus)", justify="center")

    for item in details:
        is_winner = (item["doc"] == relevant_document)
        winner_emoji = "✅" if is_winner else ""
        similarity_cell = f"[bold]{item['similarity']:.4f}[/bold]" if is_winner else f"{item['similarity']:.4f}"
        distance_cell = f"{item['distance']:.4f}"
        doc_text = escape(item["doc"][:70] + "...")
        table.add_row(doc_text, similarity_cell, distance_cell, winner_emoji)
    
    console.print(table)
    console.print("[green]   => Le document avec le score de similarité cosinus le plus élevé est choisi comme contexte.[/green]\n")
    console.print("[bold green]   => Document pertinent trouvé :[/bold green]")
    console.print(Panel(relevant_document, style="cyan", border_style="cyan"))

    # --- ÉTAPE 5: Génération de la Réponse (Augmented Generation) ---
    console.print(Panel("[bold]ÉTAPE 5: Génération Augmentée (Generation)[/bold]\nConstruction d'un prompt enrichi et envoi au modèle de génération.", title_align="left", border_style="magenta"))
    
    prompt = f"""Réponds en français à la question : "{user_query}", en t'aidant du texte suivant : "{relevant_document}" """
    console.print("[bold green]   => Prompt final envoyé au modèle de génération :[/bold green]")
    console.print(Syntax(prompt, "markdown", theme="solarized-dark", line_numbers=True))

    with console.status("[bold yellow]Génération de la réponse finale...[/bold yellow]"):
        answer = generate_answer(prompt, debug=args.payload)

    # --- ÉTAPE 6: Affichage de la Réponse Finale ---
    console.print(Panel(Markdown(answer), title="[bold green]Réponse Finale du Modèle[/bold green]", border_style="green", title_align="left"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Démonstrateur RAG avec l'API LLMaaS.")
    parser.add_argument(
        "--payload",
        action="store_true",
        help="Affiche les payloads détaillés des requêtes et réponses API."
    )
    args = parser.parse_args()
    main(args)
