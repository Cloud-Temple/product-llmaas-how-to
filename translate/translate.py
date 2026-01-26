# -*- coding: utf-8 -*-
"""
Script de Traduction de Fichiers via l'API LLMaaS.

Ce script permet de traduire le contenu d'un fichier texte d'une langue source
vers une langue cible en utilisant un modèle de langage accessible via l'API LLMaaS.

Fonctionnalités principales :
- Découpage intelligent du texte (Chunking) : Gère les documents plus longs que la fenêtre de contexte du modèle.
  Le découpage respecte les paragraphes pour ne pas couper les phrases au milieu.
- Support multi-modèles : Compatible avec les modèles généralistes (Qwen, Mistral) et spécialisés (TranslateGemma).
- Mode TranslateGemma : Détection automatique ou forcée pour utiliser le format de prompt spécifique requis par ces modèles.
- Reprise sur erreur : Gestion basique des erreurs API.
- Mode interactif : Permet de valider chaque segment traduit.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.2.1
Date: 2026-01-25
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
SCRIPT_VERSION = "1.2.0" 

# Configuration par défaut pour les paramètres du script
DEFAULT_MODEL = "qwen3:14b" 
DEFAULT_API_URL = "https://api.ai.cloud-temple.com/v1" 
# Taille par défaut des segments de texte (en mots). 
# Une valeur plus petite augmente le nombre d'appels API mais réduit le risque de dépasser la fenêtre de contexte.
DEFAULT_CHUNK_SIZE_WORDS = 300 
# Nombre maximum de tokens pour la réponse (traduction). Doit être suffisant pour contenir le texte traduit du chunk.
DEFAULT_MAX_TOKENS = 2048 

# Initialisation de la console Rich pour un affichage amélioré dans le terminal
console = Console()

# Dictionnaire complet des codes de langues ISO 639-1 vers noms en Anglais.
# Ce mapping est CRUCIAL pour TranslateGemma qui attend le nom complet de la langue dans le prompt.
ISO_TO_ENGLISH_NAME = {
    "aa": "Afar", "ab": "Abkhazian", "af": "Afrikaans", "ak": "Akan", "am": "Amharic",
    "an": "Aragonese", "ar": "Arabic", "as": "Assamese", "az": "Azerbaijani", "ba": "Bashkir",
    "be": "Belarusian", "bg": "Bulgarian", "bm": "Bambara", "bn": "Bengali", "bo": "Tibetan",
    "br": "Breton", "bs": "Bosnian", "ca": "Catalan", "ce": "Chechen", "co": "Corsican",
    "cs": "Czech", "cv": "Chuvash", "cy": "Welsh", "da": "Danish", "de": "German",
    "dv": "Divehi", "dz": "Dzongkha", "ee": "Ewe", "el": "Greek", "en": "English",
    "eo": "Esperanto", "es": "Spanish", "et": "Estonian", "eu": "Basque", "fa": "Persian",
    "ff": "Fulah", "fi": "Finnish", "fil": "Filipino", "fo": "Faroese", "fr": "French",
    "fy": "Western Frisian", "ga": "Irish", "gd": "Scottish Gaelic", "gl": "Galician", "gn": "Guarani",
    "gu": "Gujarati", "gv": "Manx", "ha": "Hausa", "he": "Hebrew", "hi": "Hindi",
    "hr": "Croatian", "ht": "Haitian", "hu": "Hungarian", "hy": "Armenian", "ia": "Interlingua",
    "id": "Indonesian", "ie": "Interlingue", "ig": "Igbo", "ii": "Sichuan Yi", "ik": "Inupiaq",
    "io": "Ido", "is": "Icelandic", "it": "Italian", "iu": "Inuktitut", "ja": "Japanese",
    "jv": "Javanese", "ka": "Georgian", "ki": "Kikuyu", "kk": "Kazakh", "kl": "Kalaallisut",
    "km": "Central Khmer", "kn": "Kannada", "ko": "Korean", "ks": "Kashmiri", "ku": "Kurdish",
    "kw": "Cornish", "ky": "Kyrgyz", "la": "Latin", "lb": "Luxembourgish", "lg": "Ganda",
    "ln": "Lingala", "lo": "Lao", "lt": "Lithuanian", "lu": "Luba-Katanga", "lv": "Latvian",
    "mg": "Malagasy", "mi": "Maori", "mk": "Macedonian", "ml": "Malayalam", "mn": "Mongolian",
    "mr": "Marathi", "ms": "Malay", "mt": "Maltese", "my": "Burmese", "nb": "Norwegian Bokmål",
    "nd": "North Ndebele", "ne": "Nepali", "nl": "Dutch", "nn": "Norwegian Nynorsk", "no": "Norwegian",
    "nr": "South Ndebele", "nv": "Navajo", "ny": "Chichewa", "oc": "Occitan", "om": "Oromo",
    "or": "Oriya", "os": "Ossetian", "pa": "Punjabi", "pl": "Polish", "ps": "Pashto",
    "pt": "Portuguese", "qu": "Quechua", "rm": "Romansh", "rn": "Rundi", "ro": "Romanian",
    "ru": "Russian", "rw": "Kinyarwanda", "sa": "Sanskrit", "sc": "Sardinian", "sd": "Sindhi",
    "se": "Northern Sami", "sg": "Sango", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian",
    "sn": "Shona", "so": "Somali", "sq": "Albanian", "sr": "Serbian", "ss": "Swati",
    "st": "Southern Sotho", "su": "Sundanese", "sv": "Swedish", "sw": "Swahili", "ta": "Tamil",
    "te": "Telugu", "tg": "Tajik", "th": "Thai", "ti": "Tigrinya", "tk": "Turkmen",
    "tl": "Tagalog", "tn": "Tswana", "to": "Tonga", "tr": "Turkish", "ts": "Tsonga",
    "tt": "Tatar", "ug": "Uyghur", "uk": "Ukrainian", "ur": "Urdu", "uz": "Uzbek",
    "ve": "Venda", "vi": "Vietnamese", "vo": "Volapük", "wa": "Walloon", "wo": "Wolof",
    "xh": "Xhosa", "yi": "Yiddish", "yo": "Yoruba", "za": "Zhuang", "zh": "Chinese",
    "zu": "Zulu"
}

def display_version():
    """Affiche la version actuelle du script."""
    console.print(f"LLMaaS File Translator v{SCRIPT_VERSION}", style="bold green")

def parse_arguments():
    """
    Analyse et valide les arguments fournis en ligne de commande.
    """
    parser = argparse.ArgumentParser(
        description=f"Traducteur de fichiers utilisant l'API LLMaaS (v{SCRIPT_VERSION}).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Chemin vers le fichier texte à traduire."
    )
    parser.add_argument(
        "--target-language",
        type=str,
        default=os.getenv("LLMAAS_TARGET_LANGUAGE"),
        help="Code ISO 639-1 de la langue cible (ex: 'en', 'fr')."
    )
    parser.add_argument(
        "--source-language",
        type=str,
        default=os.getenv("LLMAAS_SOURCE_LANGUAGE", "en"),
        help="Code ISO 639-1 de la langue source (ex: 'en', 'fr'). Requis pour le mode TranslateGemma."
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="Afficher la liste complète des 55+ langues supportées et quitter."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLMAAS_TRANSLATE_MODEL", DEFAULT_MODEL),
        help=f"Nom du modèle LLM (défaut: {DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--prompt-format",
        type=str,
        choices=['auto', 'standard', 'translategemma'],
        default="auto",
        help="Format du prompt à utiliser.\n'auto' : Détecte selon le nom du modèle.\n'translategemma' : Utilise le format rigide Google (sans system prompt, temp=0).\n'standard' : Utilise un prompt système classique (pour Qwen, Mistral, etc.)."
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("LLMAAS_API_URL", DEFAULT_API_URL),
        help=f"URL de l'API (défaut: {DEFAULT_API_URL})."
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="LLMAAS_API_KEY",
        help="Nom de la variable d'environnement pour la clé API."
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        default=os.getenv("LLMAAS_SYSTEM_PROMPT", "Vous êtes un traducteur expert. Traduisez le texte fourni dans la langue cible demandée en conservant le ton et le style. Si un contexte de traduction précédente est fourni, utilisez-le pour assurer la cohérence."),
        help="Prompt système (uniquement pour le mode 'standard')."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("LLMAAS_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        help=f"Max tokens par chunk pour la réponse (défaut: {DEFAULT_MAX_TOKENS})."
    )
    parser.add_argument(
        "--chunk-size-words",
        type=int,
        default=int(os.getenv("LLMAAS_CHUNK_SIZE_WORDS", DEFAULT_CHUNK_SIZE_WORDS)),
        help=f"Taille cible des chunks en mots (défaut: {DEFAULT_CHUNK_SIZE_WORDS}). Le script tentera de couper aux paragraphes."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Mode interactif : demande validation avant de passer au chunk suivant."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("LLMAAS_OUTPUT_DIR", "translated_files"),
        help="Répertoire de sortie."
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Afficher la version."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Mode debug : affiche les détails du découpage (chunking)."
    )
    
    args = parser.parse_args()

    if args.list_languages:
        pass
    elif not args.file or not args.target_language:
        if not args.target_language:
             parser.error("l'argument --target-language est requis.")
        if not args.file:
             parser.error("l'argument --file est requis.")
    return args

def display_supported_languages():
    """Affiche une liste formatée des codes de langues."""
    console.print("\n[bold blue]Codes de langues supportés (ISO 639-1) :[/bold blue]")
    
    # Affichage en colonnes pour une meilleure lisibilité
    sorted_langs = sorted(ISO_TO_ENGLISH_NAME.items())
    col_count = 3
    rows = (len(sorted_langs) + col_count - 1) // col_count
    
    for r in range(rows):
        line = ""
        for c in range(col_count):
            idx = r + c * rows
            if idx < len(sorted_langs):
                code, name = sorted_langs[idx]
                line += f"  [cyan]{code:<5}[/cyan] : {name:<20}"
        console.print(line)
    console.print("\nUtilisez le code (ex: 'en') avec l'option --target-language.")

def load_api_key(api_key_env_name):
    api_key = os.getenv(api_key_env_name)
    if not api_key:
        console.print(f"[bold red]Erreur: La variable d'environnement {api_key_env_name} n'est pas définie.[/bold red]")
        sys.exit(1)
    return api_key

def read_file_content(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        console.print(f"[bold red]Erreur lecture fichier '{filepath}': {e}[/bold red]")
        sys.exit(1)

def _split_single_long_paragraph(paragraph_text, chunk_size_words, debug_mode=False):
    """
    Découpe un paragraphe unique qui dépasse la taille limite.
    Essaie de respecter les frontières de phrases (. ! ?).
    Si une phrase est elle-même trop longue, elle sera coupée par mots (fallback).
    """
    import re
    # Découpage basique par phrases (ponctuation suivie d'espace ou fin de ligne)
    # On garde la ponctuation avec la phrase
    sentences = re.split(r'(?<=[.!?])\s+', paragraph_text)
    
    sub_chunks = []
    current_chunk_sentences = []
    current_chunk_word_count = 0
    
    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        
        # Cas 1 : La phrase elle-même est plus grande que la taille limite -> Découpage forcé par mots
        if sentence_word_count > chunk_size_words:
            # D'abord, on sauve ce qu'on a accumulé
            if current_chunk_sentences:
                sub_chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_chunk_word_count = 0
            
            # Ensuite on découpe la longue phrase mot par mot (fallback)
            words = sentence.split()
            current_sub_chunk_words = []
            for word in words:
                current_sub_chunk_words.append(word)
                if len(current_sub_chunk_words) >= chunk_size_words:
                    sub_chunks.append(" ".join(current_sub_chunk_words))
                    current_sub_chunk_words = []
            if current_sub_chunk_words:
                # Ce qui reste de la phrase longue démarre le prochain chunk "normal"
                partial_sentence = " ".join(current_sub_chunk_words)
                current_chunk_sentences.append(partial_sentence)
                current_chunk_word_count = len(current_sub_chunk_words)
            continue

        # Cas 2 : Ajouter la phrase ferait déborder le chunk
        if current_chunk_word_count + sentence_word_count > chunk_size_words:
            sub_chunks.append(" ".join(current_chunk_sentences))
            current_chunk_sentences = []
            current_chunk_word_count = 0
        
        # Cas 3 : Ajouter la phrase
        current_chunk_sentences.append(sentence)
        current_chunk_word_count += sentence_word_count
        
    # Ajouter le reste
    if current_chunk_sentences:
        sub_chunks.append(" ".join(current_chunk_sentences))
        
    return sub_chunks

def split_text_into_chunks(text, chunk_size_words, debug_mode=False):
    """
    Algorithme de Chunking Intelligent :
    1. Divise le texte par paragraphes (doubles sauts de ligne).
    2. Agrège les paragraphes tant que la taille < chunk_size_words.
    3. Si un paragraphe est trop gros, il est découpé (fallback).
    4. Préserve la structure (sauts de ligne) pour la reconstruction.
    """
    final_chunks = []
    raw_paragraphs = text.split("\n\n")
    
    current_chunk_accumulator_parts = []
    current_chunk_accumulator_word_count = 0

    if debug_mode: console.print(f"[DEBUG] Découpage. Cible: {chunk_size_words} mots.")

    for i, p_text in enumerate(raw_paragraphs):
        is_last_raw_paragraph = (i == len(raw_paragraphs) - 1)
        
        # Gestion des paragraphes vides (structurels)
        if not p_text.strip(): 
            if current_chunk_accumulator_parts:
                # Finaliser le chunk en cours avant d'ajouter le vide
                chunk_to_add = "".join(current_chunk_accumulator_parts)
                if chunk_to_add.endswith("\n\n"): chunk_to_add = chunk_to_add[:-2]
                if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
                current_chunk_accumulator_parts = []
                current_chunk_accumulator_word_count = 0
            final_chunks.append("\n\n")
            continue

        p_words = p_text.split()
        p_word_count = len(p_words)
        
        # Cas : Paragraphe unique trop gros -> on le découpe de force
        if p_word_count > chunk_size_words:
            if current_chunk_accumulator_parts:
                chunk_to_add = "".join(current_chunk_accumulator_parts)
                if chunk_to_add.endswith("\n\n"): chunk_to_add = chunk_to_add[:-2]
                if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
                current_chunk_accumulator_parts = []
                current_chunk_accumulator_word_count = 0
            
            sub_split_chunks = _split_single_long_paragraph(p_text, chunk_size_words, debug_mode)
            for sub_idx, sub_chunk in enumerate(sub_split_chunks):
                chunk_to_add_sub = sub_chunk
                if not is_last_raw_paragraph and sub_idx == len(sub_split_chunks) -1:
                     chunk_to_add_sub += "\n\n"
                elif sub_idx < len(sub_split_chunks) -1 : 
                    chunk_to_add_sub += " " 
                final_chunks.append(chunk_to_add_sub)
            continue

        # Cas : Ajouter ce paragraphe ferait déborder le chunk -> on finalise le courant
        if current_chunk_accumulator_parts and (current_chunk_accumulator_word_count + p_word_count > chunk_size_words):
            chunk_to_add = "".join(current_chunk_accumulator_parts)
            if chunk_to_add.endswith("\n\n"): chunk_to_add = chunk_to_add[:-2] 
            if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
            current_chunk_accumulator_parts = []
            current_chunk_accumulator_word_count = 0
        
        # Ajout du paragraphe au chunk courant
        current_chunk_accumulator_parts.append(p_text)
        current_chunk_accumulator_word_count += p_word_count
        if not is_last_raw_paragraph:
            current_chunk_accumulator_parts.append("\n\n")
        
    # Ajouter le reste
    if current_chunk_accumulator_parts:
        chunk_to_add = "".join(current_chunk_accumulator_parts)
        if chunk_to_add.endswith("\n\n") and is_last_raw_paragraph:
             chunk_to_add = chunk_to_add[:-2]
        if chunk_to_add.strip(): final_chunks.append(chunk_to_add)
    
    # Nettoyage
    cleaned_chunks = []
    for chunk_text in final_chunks:
        if chunk_text.strip() or chunk_text == "\n\n":
            cleaned_chunks.append(chunk_text)
            
    # Ajustement fin de fichier
    if not text.endswith("\n\n") and cleaned_chunks and cleaned_chunks[-1] == "\n\n":
        if len(cleaned_chunks) > 1:
            cleaned_chunks[-1] = cleaned_chunks[-1].rstrip('\n')
            if not cleaned_chunks[-1].strip(): cleaned_chunks.pop()
        elif text.strip(): 
            cleaned_chunks = []

    if debug_mode: console.print(f"[DEBUG] {len(cleaned_chunks)} chunks générés.")
    return cleaned_chunks

async def translate_chunk(api_url, api_key, model, system_prompt, chunk_to_translate, target_language, previous_chunk_context=None, max_tokens_response=1024, source_language="en", prompt_format="auto"):
    """
    Traduit un chunk individuel. 
    Cette fonction adapte dynamiquement le prompt en fonction du mode (standard ou translategemma).
    """
    messages = []
    
    # Détermination du mode de prompt
    use_translategemma_mode = False
    if prompt_format == "translategemma":
        use_translategemma_mode = True
    elif prompt_format == "auto" and "translategemma" in model.lower():
        use_translategemma_mode = True

    if use_translategemma_mode:
        # --- Mode TranslateGemma ---
        # Nécessite les noms complets des langues en Anglais (ex: "French" et non "fr")
        source_full = ISO_TO_ENGLISH_NAME.get(source_language, "English")
        target_full = ISO_TO_ENGLISH_NAME.get(target_language, "French")
        
        # Construction du prompt spécifique selon la documentation Google
        # Note: Les deux sauts de ligne avant {chunk_to_translate} sont importants.
        prompt_template = f"""You are a professional {source_full} ({source_language}) to {target_full} ({target_language}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_full} text while adhering to {target_full} grammar, vocabulary, and cultural sensitivities.
Produce only the {target_full} translation, without any additional explanations or commentary. Please translate the following {source_full} text into {target_full}:


{chunk_to_translate}"""
        
        # TranslateGemma utilise un message utilisateur unique avec le prompt complet
        messages.append({"role": "user", "content": prompt_template})
        
    else:
        # --- Mode Standard (Qwen, Mistral, Llama...) ---
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content = f"Traduisez le texte suivant en {target_language}."
        # Le contexte glissant aide à maintenir la cohérence (ex: genre, style) entre les chunks
        if previous_chunk_context:
            user_content += f"\n\nVoici le contexte de la traduction précédente pour assurer la cohérence : \"{previous_chunk_context}\""
        user_content += f"\n\nTexte à traduire : \"{chunk_to_translate}\""
        
        messages.append({"role": "user", "content": user_content})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens_response,
        "stream": False,
    }
    
    # Pour TranslateGemma, temperature à 0 est recommandée pour une traduction fidèle
    if use_translategemma_mode:
        payload["temperature"] = 0.0

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{api_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("choices") and response_data["choices"]:
                translation = response_data["choices"][0].get("message", {}).get("content", "")
                
                if not translation: return None
                
                cleaned_translation = translation.strip()
                
                # Réinjection des séparateurs structurels présents dans le chunk original
                if chunk_to_translate.endswith("\n\n"):
                    cleaned_translation += "\n\n"
                elif chunk_to_translate.endswith("\n"):
                    cleaned_translation += "\n"
                elif chunk_to_translate.endswith(" "):
                    cleaned_translation += " "
                    
                return cleaned_translation
            else:
                console.print(f"[bold red]Réponse API invalide: {response_data}[/bold red]")
                return None
    except Exception as e:
        console.print(f"[bold red]Erreur API: {e}[/bold red]")
        return None

def save_translated_content(filepath, content, output_dir, target_language):
    try:
        os.makedirs(output_dir, exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(filepath))
        safe_target_language = "".join(c if c.isalnum() else "_" for c in target_language)
        translated_filename = f"{base}.translated_to_{safe_target_language}{ext}"
        output_path = os.path.join(output_dir, translated_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"\n[bold green]Fichier traduit sauvegardé sous : {output_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Erreur sauvegarde fichier: {e}[/bold red]")

async def main():
    load_dotenv()
    args = parse_arguments()

    if args.version: display_version(); sys.exit(0)
    if args.list_languages: display_supported_languages(); sys.exit(0)

    console.print(f"Script de traduction v{SCRIPT_VERSION}", style="bold blue")
    
    # Récupération du nom complet de la langue pour l'affichage (si dispo)
    lang_name = ISO_TO_ENGLISH_NAME.get(args.target_language, args.target_language)
    console.print(f"Fichier: [cyan]{args.file}[/cyan], Cible: [cyan]{lang_name} ({args.target_language})[/cyan], Modèle: [cyan]{args.model}[/cyan]")
    console.print(f"Mode prompt: [cyan]{args.prompt_format}[/cyan]")

    api_key = load_api_key(args.api_key_env)
    original_content = read_file_content(args.file)
    if not original_content: return

    # Découpage du texte en chunks
    chunks = split_text_into_chunks(original_content, args.chunk_size_words, args.debug)
    console.print(f"Texte découpé en {len(chunks)} chunk(s).")

    translated_chunks = []
    previous_context = None

    console.print("\n[blue]Traduction en cours...[/blue]")
    with Progress(
        SpinnerColumn(), 
        TextColumn("[progress.description]{task.description}"), 
        BarColumn(), 
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), 
        TimeRemainingColumn(), 
        console=console, 
        transient=False
    ) as progress:
        translation_task = progress.add_task("[green]Traduction...", total=len(chunks))
        
        for i, chunk in enumerate(chunks):
            chunk_preview = " ".join(chunk.split()[:10]) + ("..." if len(chunk.split()) > 10 else "")
            progress.update(translation_task, description=f"[green]Chunk {i+1}/{len(chunks)}: \"{chunk_preview}\"")
            
            # Gestion des chunks vides (sauts de ligne)
            if chunk == "\n\n" and not chunk.strip(): 
                translated_chunks.append("\n\n")
                progress.advance(translation_task)
                continue

            translated_chunk = await translate_chunk(
                args.api_url, api_key, args.model, args.system_prompt, 
                chunk, args.target_language, previous_context, args.max_tokens, 
                args.source_language, args.prompt_format
            )
            
            if translated_chunk:
                translated_chunks.append(translated_chunk)
                previous_context = translated_chunk # Met à jour le contexte glissant
                
                if args.interactive:
                    progress.stop()
                    console.print(f"\n--- Chunk Original {i+1} ---", style="bold yellow"); console.print(chunk)
                    console.print(f"--- Traduction Proposée (Chunk {i+1}) ---", style="bold green"); console.print(Markdown(translated_chunk))
                    user_input = console.input("Entrée pour continuer, 'm' pour modifier, 'q' pour quitter: ").lower()
                    if user_input == 'q': console.print("[yellow]Traduction interrompue.[/yellow]"); progress.start(); return
                    if user_input == 'm': console.print("[yellow]Modification non implémentée.[/yellow]")
                    progress.start()
            else:
                console.print(f"[bold red]Échec traduction chunk {i+1}. Arrêt.[/bold red]"); progress.stop(); return
            progress.advance(translation_task)
            
    final_translation = "".join(translated_chunks) 
    console.print("\n[bold green]Traduction terminée ![/bold green]")
    save_translated_content(args.file, final_translation, args.output_dir, args.target_language)

if __name__ == "__main__":
    asyncio.run(main())
