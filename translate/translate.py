# -*- coding: utf-8 -*-
"""
Script de Traduction de Fichiers via l'API LLMaaS.

Ce script permet de traduire le contenu d'un fichier texte d'une langue source
vers une langue cible en utilisant un modèle de langage accessible via l'API LLMaaS.
Il découpe le texte en segments (chunks) pour gérer les documents longs,
maintient un contexte de traduction entre les chunks, et offre diverses options
de configuration via la ligne de commande et un fichier .env.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-02
"""
import argparse
import os
import sys
from dotenv import load_dotenv
import httpx
import json
import asyncio 
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# Version du script
SCRIPT_VERSION = "1.0.0" # Mise à jour de la version

# Configuration par défaut pour les paramètres du script
DEFAULT_MODEL = "qwen3:14b" 
DEFAULT_API_URL = "https://api.ai.cloud-temple.com/v1" 
DEFAULT_CHUNK_SIZE_WORDS = 300 
DEFAULT_MAX_TOKENS = 2048 

# Initialisation de la console Rich pour un affichage amélioré
console = Console()

def display_version():
    """Affiche la version actuelle du script."""
    console.print(f"LLMaaS File Translator v{SCRIPT_VERSION}", style="bold green")

def parse_arguments():
    """
    Analyse et valide les arguments fournis en ligne de commande.
    Charge également les valeurs par défaut à partir des variables d'environnement si elles sont définies.
    """
    parser = argparse.ArgumentParser(
        description=f"Traducteur de fichiers utilisant l'API LLMaaS (v{SCRIPT_VERSION}).",
        formatter_class=argparse.RawTextHelpFormatter # Permet un formatage personnalisé de l'aide
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True, # Le fichier source est toujours requis
        help="Chemin vers le fichier texte à traduire."
    )
    parser.add_argument(
        "--target-language",
        type=str,
        default=os.getenv("LLMAAS_TARGET_LANGUAGE"), # Priorité à la variable d'environnement
        help="Code ISO 639-1 de la langue cible (ex: 'en' pour Anglais, 'fr' pour Français). Peut être défini via LLMAAS_TARGET_LANGUAGE."
    )
    parser.add_argument(
        "--list-languages",
        action="store_true", # Argument de type booléen (flag)
        help="Afficher une liste des codes de langues courants et quitter."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLMAAS_TRANSLATE_MODEL", DEFAULT_MODEL), # Variable d'env ou défaut du script
        help=f"Nom du modèle LLM à utiliser pour la traduction (défaut: {DEFAULT_MODEL}). Peut être défini via LLMAAS_TRANSLATE_MODEL."
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("LLMAAS_API_URL", DEFAULT_API_URL),
        help=f"URL de base de l'API LLMaaS (défaut: {DEFAULT_API_URL}). Peut être défini via LLMAAS_API_URL."
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="LLMAAS_API_KEY", # Nom de la variable d'environnement pour la clé API
        help="Nom de la variable d'environnement contenant la clé API LLMaaS (défaut: LLMAAS_API_KEY)."
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        default=os.getenv("LLMAAS_SYSTEM_PROMPT", "Vous êtes un traducteur expert. Traduisez le texte fourni dans la langue cible demandée en conservant le ton et le style. Si un contexte de traduction précédente est fourni, utilisez-le pour assurer la cohérence."),
        help="Prompt système à utiliser pour guider le modèle de traduction. Peut être défini via LLMAAS_SYSTEM_PROMPT."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("LLMAAS_MAX_TOKENS", DEFAULT_MAX_TOKENS)), # Conversion en int pour la variable d'env
        help=f"Nombre maximum de tokens pour la réponse de traduction d'un chunk (défaut: {DEFAULT_MAX_TOKENS}, peut être défini via LLMAAS_MAX_TOKENS)."
    )
    parser.add_argument(
        "--chunk-size-words",
        type=int,
        default=int(os.getenv("LLMAAS_CHUNK_SIZE_WORDS", DEFAULT_CHUNK_SIZE_WORDS)),
        help=f"Taille approximative des chunks en mots (défaut: {DEFAULT_CHUNK_SIZE_WORDS}, peut être défini via LLMAAS_CHUNK_SIZE_WORDS)."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Activer le mode interactif pour valider/modifier la traduction de chaque chunk."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("LLMAAS_OUTPUT_DIR", "translated_files"),
        help="Répertoire où sauvegarder les fichiers traduits (défaut: translated_files/). Peut être défini via LLMAAS_OUTPUT_DIR."
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Afficher la version du script et quitter."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activer les logs de débogage pour le découpage des chunks."
    )
    
    args = parser.parse_args()

    # Validation spécifique : --file et --target-language sont requis sauf si --list-languages est utilisé.
    if args.list_languages:
        # Si --list-languages est présent, les autres arguments ne sont pas nécessaires pour cette action.
        pass
    elif not args.file or not args.target_language:
        # Si --list-languages n'est pas utilisé, alors --file et --target-language (s'il n'a pas de défaut via .env) deviennent requis.
        # argparse gère la vérification de --file (required=True).
        # Nous vérifions --target-language ici car sa valeur par défaut peut être None si non fournie par CLI ou .env.
        if not args.target_language:
             parser.error("l'argument --target-language est requis (ou doit être défini via la variable d'environnement LLMAAS_TARGET_LANGUAGE) sauf si --list-languages est utilisé.")
    return args

# Dictionnaire des codes de langues supportés et leurs noms en français pour l'affichage.
SUPPORTED_LANGUAGES = {
    "en": "Anglais", "fr": "Français", "es": "Espagnol", "de": "Allemand",
    "it": "Italien", "pt": "Portugais", "ru": "Russe", "zh": "Chinois (simplifié)",
    "ja": "Japonais", "ko": "Coréen", "ar": "Arabe", "hi": "Hindi",
}

def display_supported_languages():
    """Affiche une liste formatée des codes de langues courants."""
    console.print("\n[bold blue]Codes de langues courants (ISO 639-1) et leurs noms en français:[/bold blue]")
    for code, name in SUPPORTED_LANGUAGES.items():
        console.print(f"  [cyan]{code}[/cyan] : {name}")
    console.print("\nUtilisez le code (ex: 'en') avec l'option --target-language.")

def load_api_key(api_key_env_name):
    """
    Charge la clé API à partir de la variable d'environnement spécifiée.
    Quitte le script si la clé n'est pas trouvée.
    """
    api_key = os.getenv(api_key_env_name)
    if not api_key:
        console.print(f"[bold red]Erreur: La variable d'environnement {api_key_env_name} n'est pas définie.[/bold red]")
        console.print(f"Veuillez la définir ou créer un fichier .env avec {api_key_env_name}='VOTRE_CLE'.")
        sys.exit(1) # Arrêt du script si la clé API est manquante
    return api_key

def read_file_content(filepath):
    """
    Lit et retourne le contenu d'un fichier texte.
    Gère les erreurs de fichier non trouvé ou de lecture.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        console.print(f"[bold red]Erreur: Le fichier '{filepath}' n'a pas été trouvé.[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la lecture du fichier '{filepath}': {e}[/bold red]")
        sys.exit(1)

def _split_single_long_paragraph(paragraph_text, chunk_size_words, debug_mode=False):
    """
    Fonction d'aide pour découper un unique "paragraphe" (segment de texte)
    qui dépasse `chunk_size_words`. Actuellement, effectue une découpe simple
    basée sur le nombre de mots.
    """
    words = paragraph_text.split()
    sub_chunks = []
    current_sub_chunk_words = []
    for word in words:
        current_sub_chunk_words.append(word)
        if len(current_sub_chunk_words) >= chunk_size_words:
            sub_chunks.append(" ".join(current_sub_chunk_words))
            if debug_mode:
                preview = sub_chunks[-1][:70].replace('\n', ' ') # Aperçu pour le log
                console.print(f"[DEBUG]     Sub-chunk (découpe mots): '{preview}...'")
            current_sub_chunk_words = []
    if current_sub_chunk_words: # Ajouter les mots restants
        sub_chunks.append(" ".join(current_sub_chunk_words))
        if debug_mode:
            preview = sub_chunks[-1][:70].replace('\n', ' ')
            console.print(f"[DEBUG]     Sub-chunk (reste découpe mots): '{preview}...'")
    return sub_chunks

def split_text_into_chunks(text, chunk_size_words, debug_mode=False):
    """
    Découpe le texte en chunks avec une logique améliorée pour agréger les petits "paragraphes".
    1. Sépare le texte initial par double saut de ligne ("\\n\\n") pour obtenir des "paragraphes bruts".
    2. Itère sur ces paragraphes bruts et les accumule dans un chunk courant tant que
       `chunk_size_words` n'est pas dépassé.
    3. Si un paragraphe brut est lui-même plus grand que `chunk_size_words`, il est
       isolé et potentiellement sous-découpé par `_split_single_long_paragraph`.
    4. Gère la préservation des doubles sauts de ligne intentionnels (paragraphes vides).
    """
    final_chunks = [] # Liste pour stocker les chunks finaux
    raw_paragraphs = text.split("\n\n") # Découpage initial par double saut de ligne
    
    current_chunk_accumulator_parts = [] # Accumulateur pour les parties du chunk en cours de construction
    current_chunk_accumulator_word_count = 0 # Compteur de mots pour le chunk en cours

    if debug_mode: console.print(f"[DEBUG] Début découpage intelligent. Taille de chunk cible: {chunk_size_words} mots.")

    for i, p_text in enumerate(raw_paragraphs):
        is_last_raw_paragraph = (i == len(raw_paragraphs) - 1) # Indicateur si c'est le dernier paragraphe brut
        
        # Gestion des paragraphes vides (provenant de multiples \n\n)
        if not p_text.strip(): 
            if current_chunk_accumulator_parts: # Si un chunk est en cours, le finaliser
                chunk_to_add = "".join(current_chunk_accumulator_parts)
                if chunk_to_add.endswith("\n\n"): 
                    chunk_to_add = chunk_to_add[:-2] # Retirer le dernier \n\n si on ajoute un para vide ensuite
                if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
                if debug_mode and chunk_to_add.strip():
                    preview = chunk_to_add[:70].replace('\n', ' ')
                    console.print(f"[DEBUG] Chunk {len(final_chunks)} (Finalisé avant para. vide, {current_chunk_accumulator_word_count} mots): '{preview}...'")
                current_chunk_accumulator_parts = []
                current_chunk_accumulator_word_count = 0
            
            final_chunks.append("\n\n") # Ajouter le paragraphe vide comme un chunk distinct
            if debug_mode: console.print(f"[DEBUG] Chunk {len(final_chunks)} (Paragraphe vide)")
            continue

        p_words = p_text.split()
        p_word_count = len(p_words)
        
        if debug_mode:
            preview_p_text = p_text[:50].replace('\n',' ')
            console.print(f"[DEBUG]   Traitement 'paragraphe' brut {i+1}/{len(raw_paragraphs)} ({p_word_count} mots): '{preview_p_text}...'")

        # Cas 1: Le paragraphe brut actuel est lui-même plus grand que chunk_size_words
        if p_word_count > chunk_size_words:
            if current_chunk_accumulator_parts: # Finaliser le chunk accumulé précédemment
                chunk_to_add = "".join(current_chunk_accumulator_parts)
                if chunk_to_add.endswith("\n\n"): chunk_to_add = chunk_to_add[:-2]
                if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
                if debug_mode and chunk_to_add.strip():
                    preview = chunk_to_add[:70].replace('\n', ' ')
                    console.print(f"[DEBUG] Chunk {len(final_chunks)} (Finalisé avant gros para., {current_chunk_accumulator_word_count} mots): '{preview}...'")
                current_chunk_accumulator_parts = []
                current_chunk_accumulator_word_count = 0
            
            # Scinder ce gros paragraphe
            if debug_mode: console.print(f"[DEBUG]     'Paragraphe' trop long ({p_word_count} mots), découpage interne...")
            sub_split_chunks = _split_single_long_paragraph(p_text, chunk_size_words, debug_mode)
            for sub_idx, sub_chunk in enumerate(sub_split_chunks):
                chunk_to_add_sub = sub_chunk
                # Ajouter le séparateur \n\n au dernier sous-chunk si ce n'est pas le dernier paragraphe brut global
                if not is_last_raw_paragraph and sub_idx == len(sub_split_chunks) -1:
                     chunk_to_add_sub += "\n\n"
                # Ajouter un espace entre les sous-chunks d'un même paragraphe (pourrait être \n)
                elif sub_idx < len(sub_split_chunks) -1 : 
                    chunk_to_add_sub += " " 
                final_chunks.append(chunk_to_add_sub)
                if debug_mode:
                    preview = chunk_to_add_sub[:70].replace('\n', ' ')
                    console.print(f"[DEBUG] Chunk {len(final_chunks)} (Sous-chunk de gros para., {len(sub_chunk.split())} mots): '{preview}...'")
            continue # Passer au prochain paragraphe brut

        # Cas 2: L'ajout de ce paragraphe ferait déborder le chunk accumulé
        if current_chunk_accumulator_parts and (current_chunk_accumulator_word_count + p_word_count > chunk_size_words):
            chunk_to_add = "".join(current_chunk_accumulator_parts)
            if chunk_to_add.endswith("\n\n"): chunk_to_add = chunk_to_add[:-2] 
            if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
            if debug_mode and chunk_to_add.strip():
                preview = chunk_to_add[:70].replace('\n', ' ')
                console.print(f"[DEBUG] Chunk {len(final_chunks)} (Agrégé, limite atteinte, {current_chunk_accumulator_word_count} mots): '{preview}...'")
            current_chunk_accumulator_parts = [] # Réinitialiser pour le nouveau chunk
            current_chunk_accumulator_word_count = 0
        
        # Cas 3: Ajouter le paragraphe (et son séparateur potentiel) au chunk en cours d'accumulation
        current_chunk_accumulator_parts.append(p_text)
        current_chunk_accumulator_word_count += p_word_count
        if not is_last_raw_paragraph: # Préparer le séparateur pour le prochain paragraphe brut
            current_chunk_accumulator_parts.append("\n\n")
        
        if debug_mode: console.print(f"[DEBUG]     'Paragraphe' ajouté à l'accumulateur. Mots accumulés: {current_chunk_accumulator_word_count}")

    # Ajouter le dernier chunk accumulé s'il reste des éléments
    if current_chunk_accumulator_parts:
        chunk_to_add = "".join(current_chunk_accumulator_parts)
        if chunk_to_add.endswith("\n\n") and is_last_raw_paragraph:
             chunk_to_add = chunk_to_add[:-2] # Retirer le dernier \n\n si c'est la fin du texte
        if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
        if debug_mode and chunk_to_add.strip():
            preview = chunk_to_add[:70].replace('\n', ' ')
            console.print(f"[DEBUG] Chunk {len(final_chunks)} (Dernier chunk agrégé, {current_chunk_accumulator_word_count} mots): '{preview}...'")
    
    # Nettoyage final : retirer les chunks complètement vides (sauf ceux qui sont "\n\n")
    # et s'assurer qu'on ne termine pas par un \n\n si le texte original ne le faisait pas.
    cleaned_chunks = []
    for chunk_text in final_chunks:
        if chunk_text.strip() or chunk_text == "\n\n": # Conserver les chunks non vides ou les paragraphes vides explicites
            cleaned_chunks.append(chunk_text)
    
    # Cas particulier: si le texte original ne se terminait pas par \n\n,
    # mais que notre dernier chunk est \n\n (et qu'il y a d'autres chunks avant), on l'ajuste.
    if not text.endswith("\n\n") and cleaned_chunks and cleaned_chunks[-1] == "\n\n":
        if len(cleaned_chunks) > 1: # S'il y a d'autres chunks avant ce \n\n final
            cleaned_chunks[-1] = cleaned_chunks[-1].rstrip('\n') # Enlever les sauts de ligne du dernier élément
            if not cleaned_chunks[-1].strip(): # S'il est devenu vide après rstrip
                 cleaned_chunks.pop() # Le supprimer
        elif not text.strip() and cleaned_chunks[0] == "\n\n": 
            # Si le texte original était juste "\n\n", on garde le chunk "\n\n"
            pass
        elif text.strip(): 
            # Si le texte original n'était pas vide, mais le seul chunk est "\n\n" et le texte ne finissait pas par \n\n
            cleaned_chunks = [] # Alors on ne devrait pas avoir de chunk

    if debug_mode:
        console.print(f"[DEBUG] Total chunks finaux (après nettoyage): {len(cleaned_chunks)}")
        for i, fc in enumerate(cleaned_chunks):
            preview = fc[:100].replace('\n', ' ')
            console.print(f"[DEBUG] Final Chunk {i+1} (len: {len(fc.split())} mots): '{preview}...'")
    return cleaned_chunks

async def translate_chunk(api_url, api_key, model, system_prompt, chunk_to_translate, target_language, previous_chunk_context=None, max_tokens_response=1024):
    """
    Appelle l'API LLMaaS pour traduire un unique chunk de texte.
    Construit le message pour l'API et gère la réponse.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Construction du prompt utilisateur incluant le contexte précédent si disponible
    user_content = f"Traduisez le texte suivant en {target_language}."
    if previous_chunk_context:
        user_content += f"\n\nVoici le contexte de la traduction précédente pour assurer la cohérence : \"{previous_chunk_context}\""
    user_content += f"\n\nTexte à traduire : \"{chunk_to_translate}\""
    
    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens_response,
        "stream": False, # La traduction par chunk ne bénéficie pas forcément du streaming
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Timeout de 60 secondes pour l'appel API
            response = await client.post(f"{api_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status() # Lève une exception pour les codes HTTP 4xx/5xx
            response_data = response.json()
            
            # Extraction de la traduction de la réponse JSON
            if response_data.get("choices") and response_data["choices"]:
                translation = response_data["choices"][0].get("message", {}).get("content", "")
                return translation.strip() if translation else None # Retourne la traduction nettoyée ou None
            else:
                console.print(f"[bold red]Réponse API invalide: 'choices' manquantes ou vides. {response_data}[/bold red]")
                return None
    except Exception as e: # Gestion générique des erreurs (HTTP, réseau, JSON decode, etc.)
        console.print(f"[bold red]Erreur API: {e}[/bold red]")
        return None

def save_translated_content(filepath, content, output_dir, target_language):
    """
    Sauvegarde le contenu traduit dans un nouveau fichier.
    Le nom du fichier de sortie inclut la langue cible.
    """
    try:
        os.makedirs(output_dir, exist_ok=True) # Crée le répertoire de sortie s'il n'existe pas
        base, ext = os.path.splitext(os.path.basename(filepath)) # Sépare le nom de fichier et l'extension
        safe_target_language = "".join(c if c.isalnum() else "_" for c in target_language) # Nettoie le code langue pour le nom de fichier
        translated_filename = f"{base}.translated_to_{safe_target_language}{ext}"
        output_path = os.path.join(output_dir, translated_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"\n[bold green]Fichier traduit sauvegardé sous : {output_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Erreur sauvegarde fichier: {e}[/bold red]")

async def main():
    """Fonction principale orchestrant la traduction."""
    load_dotenv() # Charge les variables d'environnement depuis un fichier .env (si présent)
    args = parse_arguments() # Récupère et valide les arguments de la ligne de commande

    if args.version: display_version(); sys.exit(0)
    if args.list_languages: display_supported_languages(); sys.exit(0)

    # Affichage des paramètres de traduction utilisés
    console.print(f"Script de traduction v{SCRIPT_VERSION}", style="bold blue")
    console.print(f"Fichier: [cyan]{args.file}[/cyan], Langue cible: [cyan]{SUPPORTED_LANGUAGES.get(args.target_language, args.target_language)} ({args.target_language})[/cyan], Modèle: [cyan]{args.model}[/cyan]")

    api_key = load_api_key(args.api_key_env)
    original_content = read_file_content(args.file)
    if not original_content: return # Quitte si le fichier est vide ou illisible

    # Découpage du contenu original en chunks
    chunks = split_text_into_chunks(original_content, args.chunk_size_words, args.debug)
    console.print(f"Texte découpé en {len(chunks)} chunk(s).")

    translated_chunks = [] # Liste pour stocker les traductions de chaque chunk
    previous_context = None # Contexte de la traduction précédente pour la cohérence

    console.print("\n[blue]Traduction en cours...[/blue]")
    # Utilisation de Rich Progress pour une barre de progression
    with Progress(
        SpinnerColumn(), 
        TextColumn("[progress.description]{task.description}"), 
        BarColumn(), 
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), 
        TimeRemainingColumn(), 
        console=console, 
        transient=False # Garder la barre visible après la fin
    ) as progress:
        translation_task = progress.add_task("[green]Traduction...", total=len(chunks))
        
        for i, chunk in enumerate(chunks):
            chunk_preview = " ".join(chunk.split()[:10]) + ("..." if len(chunk.split()) > 10 else "")
            progress.update(translation_task, description=f"[green]Chunk {i+1}/{len(chunks)}: \"{chunk_preview}\"")
            
            # Si le chunk est juste un paragraphe vide, on le conserve tel quel sans le traduire
            if chunk == "\n\n" and not chunk.strip(): 
                translated_chunks.append("\n\n")
                progress.advance(translation_task)
                if args.debug: console.print(f"[DEBUG] Chunk {i+1} est un paragraphe vide, conservé tel quel.")
                continue

            # Appel à l'API pour traduire le chunk
            translated_chunk = await translate_chunk(
                args.api_url, api_key, args.model, args.system_prompt, 
                chunk, args.target_language, previous_context, args.max_tokens
            )
            
            if translated_chunk:
                translated_chunks.append(translated_chunk)
                previous_context = translated_chunk # Mettre à jour le contexte pour le prochain chunk
                
                # Gestion du mode interactif
                if args.interactive:
                    progress.stop() # Pause de la barre de progression pour l'interaction
                    console.print(f"\n--- Chunk Original {i+1} ---", style="bold yellow"); console.print(chunk)
                    console.print(f"--- Traduction Proposée (Chunk {i+1}) ---", style="bold green"); console.print(Markdown(translated_chunk))
                    user_input = console.input("Entrée pour continuer, 'm' pour modifier, 'q' pour quitter: ").lower()
                    if user_input == 'q': console.print("[yellow]Traduction interrompue.[/yellow]"); progress.start(); return
                    if user_input == 'm': console.print("[yellow]Modification non implémentée.[/yellow]") # TODO
                    progress.start() # Reprise de la barre de progression
            else:
                # Arrêt en cas d'échec de traduction d'un chunk
                console.print(f"[bold red]Échec traduction chunk {i+1}. Arrêt.[/bold red]"); progress.stop(); return
            progress.advance(translation_task) # Avancer la barre de progression
            
    # Concaténation des chunks traduits (join simple car les \n\n sont déjà dans les chunks)
    final_translation = "".join(translated_chunks) 
    console.print("\n[bold green]Traduction terminée ![/bold green]")
    save_translated_content(args.file, final_translation, args.output_dir, args.target_language)

if __name__ == "__main__":
    asyncio.run(main())
