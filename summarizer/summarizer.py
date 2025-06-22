import argparse
import asyncio
import os
import json
import yaml
import httpx
import re
import tiktoken
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Pour le chunking avancé
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Pour une sortie console améliorée
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

console = Console()

# --- Configuration et chargement des prompts ---

class Config:
    """
    Gère la configuration de l'application de synthèse.
    Charge les variables d'environnement et les prompts depuis un fichier YAML.
    """
    def __init__(self):
        # Charge les variables d'environnement depuis un fichier .env
        load_dotenv()

        # Configuration de l'API LLMaaS
        self.api_base_url: str = os.getenv("LLMAAS_API_BASE_URL", "http://localhost:8000/v1")
        self.api_key: Optional[str] = os.getenv("LLMAAS_API_KEY")
        self.default_model: str = os.getenv("LLMAAS_DEFAULT_MODEL", "granite3.3:8b")
        self.final_model: str = os.getenv("LLMAAS_FINAL_MODEL", "granite3.3:8b")
        self.final_max_tokens: int = int(os.getenv("LLMAAS_FINAL_MAX_TOKENS", 30000))
        self.max_tokens_per_chunk: int = int(os.getenv("LLMAAS_MAX_TOKENS_PER_CHUNK", 4096))
        
        # Charge les prompts de synthèse depuis le fichier prompts.yaml
        self.prompts: Dict = self._load_prompts("prompts.yaml")
        self.debug_mode: bool = False # Sera défini par un argument de ligne de commande

    def _load_prompts(self, filename: str) -> Dict:
        """
        Charge les définitions de prompts depuis un fichier YAML.
        Le fichier doit se trouver dans le même répertoire que ce script.
        """
        # Construit le chemin absolu du fichier de prompts
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        # Vérifie si le fichier existe
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Le fichier de prompts '{filepath}' est introuvable. Veuillez le créer.")
        
        # Lit et parse le fichier YAML
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

config = Config()

# --- Fonctions utilitaires ---

def print_debug(message: str, is_json: bool = False):
    """
    Affiche un message uniquement si le mode debug est activé.
    """
    if config.debug_mode:
        if is_json:
            # Affiche le JSON complet sans le tronquer
            console.print(json.loads(message))
        else:
            console.print(f"[bold yellow]DEBUG:[/bold yellow] {message}")

async def call_llm_api(
    messages: List[Dict],
    model: str,
    max_tokens: int,
    client: httpx.AsyncClient,
    temperature: float = 0.7,
    stream: bool = False,
    retries: int = 3
) -> Optional[str]:
    """
    Appelle l'API LLMaaS pour obtenir une complétion de chat, avec un mécanisme de retry.
    """
    headers = {
        "Content-Type": "application/json",
    }
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }

    print_debug(f"\n--- Requête LLM (Modèle: {model}) ---")
    print_debug(json.dumps(payload, indent=2, ensure_ascii=False), is_json=True)

    for attempt in range(retries):
        try:
            response = await client.post(f"{config.api_base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()

            print_debug(f"--- Réponse LLM (Statut: {response.status_code}) ---")
            print_debug(json.dumps(response.json(), indent=2, ensure_ascii=False), is_json=True)

            response_data = response.json()
            
            content = response_data["choices"][0]["message"]["content"]
            if "reasoning_content" not in response_data["choices"][0]["message"]:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                content = content.strip()

            return content

        except httpx.HTTPStatusError as e:
            console.print(f"[bold red]Erreur HTTP lors de l'appel API (tentative {attempt + 1}/{retries}):[/bold red] {e.response.status_code} - {e.response.text}")
            if config.debug_mode:
                print_debug(f"Requête échouée: {json.dumps(payload, indent=2, ensure_ascii=False)}", is_json=True)
                print_debug(f"Réponse reçue: {e.response.text}")
        except httpx.RequestError as e:
            console.print(f"[bold red]Erreur réseau ou de requête (tentative {attempt + 1}/{retries}):[/bold red] {e}")
            if config.debug_mode:
                console.print(e.request)
        except KeyError as e:
            console.print(f"[bold red]Erreur de structure de réponse de l'API (tentative {attempt + 1}/{retries}):[/bold red] Clé manquante {e}. Réponse: {response.json()}")
        except Exception as e:
            console.print(f"[bold red]Une erreur inattendue est survenue (tentative {attempt + 1}/{retries}):[/bold red] {e}")
        
        if attempt < retries - 1:
            await asyncio.sleep(2) # Attend 2 secondes avant de réessayer

    return None

# --- Logique de Chunking ---

def get_text_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[Document]:
    """
    Découpe le texte en chunks en utilisant RecursiveCharacterTextSplitter de Langchain.
    """
    # Utilise tiktoken pour compter les tokens, ce qui est plus précis pour les LLM
    encoding = tiktoken.get_encoding("cl100k_base")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda text: len(encoding.encode(text)),
        add_start_index=True,
    )
    return text_splitter.create_documents([text])

# --- Logique de Traitement par Lots et Parallèle ---

async def process_batch(
    batch_chunks: List[Document],
    model: str,
    prompt_name: str,
    max_tokens_per_chunk: int,
    previous_summary: Optional[str],
    include_previous_summary: bool,
    client: httpx.AsyncClient,
    progress: Progress,
    task_id
) -> str:
    """
    Traite un lot de chunks en parallèle et retourne une synthèse combinée.
    """
    tasks = []
    for chunk_doc in batch_chunks:
        chunk_text = chunk_doc.page_content
        
        messages = []
        system_prompt = config.prompts[prompt_name]["system_prompt"]
        messages.append({"role": "system", "content": system_prompt})
        
        if include_previous_summary and previous_summary:
            messages.append({"role": "user", "content": f"Résumé du contexte précédent: {previous_summary}"})
            messages.append({"role": "user", "content": f"Texte à synthétiser: {chunk_text}"})
        else:
            user_template = config.prompts[prompt_name]["user_template"]
            messages.append({"role": "user", "content": user_template.format(text=chunk_text)})
            
        tasks.append(call_llm_api(messages, model, max_tokens_per_chunk, client=client))

    chunk_summaries = []
    for future in asyncio.as_completed(tasks):
        result = await future
        chunk_summaries.append(result)
        progress.update(task_id, advance=1)
    
    chunk_summaries = [s for s in chunk_summaries if s is not None]

    if not chunk_summaries:
        return "" 

    return "\n\n".join(chunk_summaries)

async def summarize_text(
    input_file: str,
    output_file: str,
    model: str,
    prompt_name: str,
    chunk_size: int,
    chunk_overlap: int,
    max_tokens_per_chunk: int,
    batch_size: int,
    include_previous_summary: bool,
    final_model: str,
    final_max_tokens: int,
    no_final_summary: bool
):
    """
    Orchestre le processus de synthèse d'un fichier texte ou Markdown.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        console.print(f"[bold red]Erreur:[/bold red] Le fichier d'entrée '{input_file}' est introuvable.")
        return
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la lecture du fichier d'entrée:[/bold red] {e}")
        return

    console.print(f"[cyan]Découpage du texte en chunks (taille: {chunk_size}, chevauchement: {chunk_overlap})...[/cyan]")
    all_chunks = get_text_chunks(text, chunk_size, chunk_overlap)
    console.print(f"[cyan]Nombre total de chunks:[/cyan] {len(all_chunks)}")

    final_summary_parts = []
    previous_summary_for_context: Optional[str] = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("[green]Synthèse des chunks...", total=len(all_chunks))

        async with httpx.AsyncClient(timeout=300.0) as client:
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                
                batch_combined_summary = await process_batch(
                    batch_chunks,
                    model,
                    prompt_name,
                    max_tokens_per_chunk,
                    previous_summary_for_context,
                    include_previous_summary,
                    client,
                    progress,
                    task_id
                )
                
                if batch_combined_summary:
                    final_summary_parts.append(batch_combined_summary)
                    if include_previous_summary:
                        previous_summary_for_context = batch_combined_summary
                else:
                    console.print(f"[yellow]Avertissement:[/yellow] Le lot {i // batch_size + 1} n'a généré aucune synthèse.")

            combined_summaries = "\n\n".join(final_summary_parts)

            if no_final_summary:
                final_summary = combined_summaries
            elif combined_summaries.strip():
                console.print("\n[bold blue]Génération de la synthèse finale...[/bold blue]")
                
                final_system_prompt = config.prompts["final_summary"]["system_prompt"]
                final_user_template = config.prompts["final_summary"]["user_template"]
                
                final_messages = [
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": final_user_template.format(text=combined_summaries)}
                ]
                
                final_summary = await call_llm_api(
                    messages=final_messages,
                    model=final_model,
                    max_tokens=final_max_tokens,
                    client=client
                )
            else:
                final_summary = ""

            if final_summary and final_summary.strip():
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(final_summary)
                    console.print(Panel(f"[bold green]Synthèse complète écrite dans '{output_file}'[/bold green]", title="Succès", border_style="green"))
                except Exception as e:
                    console.print(f"[bold red]Erreur lors de l'écriture du fichier de sortie:[/bold red] {e}")
            else:
                console.print(Panel("[bold yellow]Aucune synthèse n'a été générée. Le fichier de sortie n'a pas été créé.[/bold yellow]", title="Avertissement", border_style="yellow"))

# --- Point d'entrée principal ---

def main():
    """
    Fonction principale pour l'exécution du script de synthèse.
    """
    # Vérification de la clé d'API
    if not config.api_key or config.api_key == "votre_cle_api_ici":
        console.print(Panel("[bold red]Erreur: Clé d'API manquante ou non configurée.[/bold red]\nVeuillez définir la variable d'environnement `LLMAAS_API_KEY` dans votre fichier `.env`.", title="Erreur de Configuration", border_style="red"))
        return

    parser = argparse.ArgumentParser(
        description="Génère une synthèse d'un fichier texte ou Markdown en utilisant un LLM.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Chemin vers le fichier texte/Markdown d'entrée.")
    parser.add_argument("--output", "-o", type=str, default="summary.md",
                        help="Chemin vers le fichier de sortie pour la synthèse (par défaut: summary.md).")
    parser.add_argument("--model", "-m", type=str, default=config.default_model,
                        help=f"Nom du modèle LLM à utiliser (par défaut: {config.default_model}).")
    parser.add_argument("--prompt", "-p", type=str, required=True,
                        help="Nom du prompt de synthèse à utiliser (défini dans prompts.yaml).")
    parser.add_argument("--chunk_size", "-cs", type=int, default=2000,
                        help="Taille maximale d'un chunk en tokens (par défaut: 2000).")
    parser.add_argument("--chunk_overlap", "-co", type=int, default=200,
                        help="Nombre de tokens de chevauchement entre les chunks (par défaut: 200).")
    parser.add_argument("--max_tokens_per_chunk", "-mt", type=int, default=config.max_tokens_per_chunk,
                        help=f"Nombre maximal de tokens à générer par le LLM pour chaque chunk (par défaut: {config.max_tokens_per_chunk}).")
    parser.add_argument("--batch_size", "-bs", type=int, default=5,
                        help="Nombre de chunks à traiter en parallèle par lot (par défaut: 5).")
    parser.add_argument("--no_previous_summary_context", "-npc", action="store_true",
                        help="Désactive l'inclusion du résumé du lot précédent dans le contexte du LLM.")
    parser.add_argument("--final_model", "-fm", type=str, default=config.final_model,
                        help=f"Modèle LLM à utiliser pour la synthèse finale (par défaut: {config.final_model}).")
    parser.add_argument("--final_max_tokens", "-fmt", type=int, default=config.final_max_tokens,
                        help=f"Nombre maximal de tokens pour la synthèse finale (par défaut: {config.final_max_tokens}).")
    parser.add_argument("--no-final-summary", action="store_true",
                        help="Désactive la synthèse finale et retourne l'agrégat des synthèses de chunks.")
    parser.add_argument("--debug", action="store_true",
                        help="Active le mode debug pour afficher les payloads des requêtes et réponses.")
    
    args = parser.parse_args()

    if args.debug:
        config.debug_mode = True

    if args.prompt not in config.prompts:
        console.print(f"[bold red]Erreur:[/bold red] Le prompt '{args.prompt}' n'est pas défini dans prompts.yaml.")
        console.print(f"Prompts disponibles: {', '.join(config.prompts.keys())}")
        return

    include_previous_summary = not args.no_previous_summary_context

    final_model = args.final_model if args.final_model else args.model

    asyncio.run(summarize_text(
        input_file=args.input,
        output_file=args.output,
        model=args.model,
        prompt_name=args.prompt,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        max_tokens_per_chunk=args.max_tokens_per_chunk,
        batch_size=args.batch_size,
        include_previous_summary=include_previous_summary,
        final_model=final_model,
        final_max_tokens=args.final_max_tokens,
        no_final_summary=args.no_final_summary
    ))

if __name__ == "__main__":
    main()
