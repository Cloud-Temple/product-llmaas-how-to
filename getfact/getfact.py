# -*- coding: utf-8 -*-
"""
🔍 Script d'Extraction de Faits et Relations via l'API LLMaaS.

Ce script permet d'extraire les faits et les relations entre faits d'un fichier texte
en utilisant un modèle de langage accessible via l'API LLMaaS. Il peut optionnellement
utiliser une ontologie fournie pour améliorer la précision de l'extraction.
Le résultat est sauvegardé au format JSON ou YAML avec une structure organisée.

🎯 Fonctionnalités principales :
- Extraction de 6 types de faits (entités, événements, relations, attributs, temporel, spatial)
- Support d'ontologie optionnelle (JSON/YAML/TXT)
- Découpage intelligent en chunks
- Interface colorée avec Rich
- Mode debug détaillé
- Validation JSON robuste

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.1
Date: 2026-01-25
"""
import argparse
import os
import sys
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import httpx
import asyncio 
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text

# 🎨 Configuration des couleurs et styles
COLORS = {
    'success': 'bold green',
    'error': 'bold red', 
    'warning': 'bold yellow',
    'info': 'bold blue',
    'debug': 'dim cyan',
    'highlight': 'bold magenta',
    'entity': 'bright_green',
    'event': 'bright_blue',
    'relationship': 'bright_yellow',
    'attribute': 'bright_cyan',
    'temporal': 'bright_magenta',
    'spatial': 'bright_white'
}

# 📋 Version du script
SCRIPT_VERSION = "1.0.1"

# ⚙️ Configuration par défaut pour les paramètres du script
DEFAULT_MODEL = "qwen3:14b" 
DEFAULT_API_URL = "https://api.ai.cloud-temple.com/v1" 
DEFAULT_CHUNK_SIZE_WORDS = 500 
DEFAULT_MAX_TOKENS = 16384  # 16k par défaut pour réduire le risque de réponses tronquées (finish_reason=length)

# 🎨 Initialisation de la console Rich pour un affichage amélioré
console = Console(force_terminal=True, color_system="auto")

def debug_print(message: str, data=None):
    """
    🐛 Fonction d'affichage pour le mode debug avec couleurs.
    
    Args:
        message (str): Message à afficher
        data: Données optionnelles à afficher (dict, list, etc.)
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    debug_text = Text()
    debug_text.append(f"[{timestamp}] ", style="dim white")
    debug_text.append("DEBUG ", style=COLORS['debug'])
    debug_text.append(message, style="white")
    console.print(debug_text)
    
    if data is not None:
        if isinstance(data, (dict, list)):
            # Affichage formaté COMPLET pour les structures de données
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            console.print(Syntax(json_content, "json", theme="monokai", line_numbers=False))
        else:
            # Affichage COMPLET du contenu texte
            console.print(f"  → {str(data)}", style="dim white")

def display_version():
    """Affiche la version actuelle du script."""
    console.print(f"LLMaaS Fact Extractor v{SCRIPT_VERSION}", style="bold green")

def parse_arguments():
    """
    Analyse et valide les arguments fournis en ligne de commande.
    Charge également les valeurs par défaut à partir des variables d'environnement si elles sont définies.
    """
    parser = argparse.ArgumentParser(
        description=f"Extracteur de faits et relations utilisant l'API LLMaaS (v{SCRIPT_VERSION}).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Chemin vers le fichier texte à analyser pour extraire les faits."
    )
    parser.add_argument(
        "--ontology",
        type=str,
        help="Chemin vers un fichier d'ontologie (JSON/YAML/TXT) pour guider l'extraction des faits. Optionnel."
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "yaml"],
        default=os.getenv("LLMAAS_OUTPUT_FORMAT", "json"),
        help="Format de sortie pour les faits extraits (json ou yaml). Défaut: json. Peut être défini via LLMAAS_OUTPUT_FORMAT."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLMAAS_GETFACT_MODEL", DEFAULT_MODEL),
        help=f"Nom du modèle LLM à utiliser pour l'extraction (défaut: {DEFAULT_MODEL}). Peut être défini via LLMAAS_GETFACT_MODEL."
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
        default="LLMAAS_API_KEY",
        help="Nom de la variable d'environnement contenant la clé API LLMaaS (défaut: LLMAAS_API_KEY)."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("LLMAAS_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        help=f"Nombre maximum de tokens pour la réponse d'extraction d'un chunk (défaut: {DEFAULT_MAX_TOKENS}, peut être défini via LLMAAS_MAX_TOKENS)."
    )
    parser.add_argument(
        "--chunk-size-words",
        type=int,
        default=int(os.getenv("LLMAAS_CHUNK_SIZE_WORDS", DEFAULT_CHUNK_SIZE_WORDS)),
        help=f"Taille approximative des chunks en mots (défaut: {DEFAULT_CHUNK_SIZE_WORDS}, peut être défini via LLMAAS_CHUNK_SIZE_WORDS)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("LLMAAS_OUTPUT_DIR", "extracted_facts"),
        help="Répertoire où sauvegarder les fichiers de faits extraits (défaut: extracted_facts/). Peut être défini via LLMAAS_OUTPUT_DIR."
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Activer le mode interactif pour valider/modifier l'extraction de chaque chunk."
    )
    parser.add_argument(
        "--fact-types",
        type=str,
        nargs="+",
        default=["entities", "events", "relationships", "attributes", "temporal", "spatial"],
        help="Types de faits à extraire. Défaut: entities events relationships attributes temporal spatial."
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Afficher la version du script et quitter."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activer les logs de débogage pour le découpage et l'extraction."
    )
    parser.add_argument(
        "--custom-prompt",
        type=str,
        default=os.getenv("LLMAAS_CUSTOM_PROMPT", ""),
        help="Prompt système personnalisé à ajouter aux instructions d'extraction. Peut être défini via LLMAAS_CUSTOM_PROMPT."
    )
    
    return parser.parse_args()

def load_api_key(api_key_env_name):
    """
    Charge la clé API à partir de la variable d'environnement spécifiée.
    Quitte le script si la clé n'est pas trouvée.
    """
    api_key = os.getenv(api_key_env_name)
    if not api_key:
        console.print(f"[bold red]Erreur: La variable d'environnement {api_key_env_name} n'est pas définie.[/bold red]")
        console.print(f"Veuillez la définir ou créer un fichier .env avec {api_key_env_name}='VOTRE_CLE'.")
        sys.exit(1)
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

def load_ontology(ontology_path, debug_mode=False):
    """
    🧠 Charge et parse un fichier d'ontologie selon son extension.
    
    Cette fonction supporte plusieurs formats d'ontologie (JSON, YAML, TXT)
    et fournit des informations détaillées sur le contenu chargé.
    
    Args:
        ontology_path (str): Chemin vers le fichier d'ontologie
        debug_mode (bool): Active l'affichage de debug détaillé
        
    Returns:
        dict|None: Données de l'ontologie parsées ou None si erreur
    """
    if not ontology_path:
        if debug_mode:
            debug_print("🧠 Aucune ontologie spécifiée")
        return None
        
    try:
        path = Path(ontology_path)
        if not path.exists():
            console.print(f"[{COLORS['error']}]❌ Erreur: Le fichier d'ontologie '{ontology_path}' n'existe pas.[/{COLORS['error']}]")
            return None
            
        content = path.read_text(encoding="utf-8")
        
        if debug_mode:
            debug_print(f"🧠 Chargement ontologie détecté", {
                "format": path.suffix.lower(),
                "taille": len(content),
                "fichier": ontology_path
            })
        
        # 📄 Parsing selon le format détecté
        if path.suffix.lower() == ".json":
            ontology_data = json.loads(content)
            if debug_mode:
                debug_print("📄 Ontologie JSON parsée", {
                    "sections": list(ontology_data.keys()) if isinstance(ontology_data, dict) else "format_inattendu"
                })
            return ontology_data
            
        elif path.suffix.lower() in [".yaml", ".yml"]:
            ontology_data = yaml.safe_load(content)
            if debug_mode:
                debug_print("📄 Ontologie YAML parsée", {
                    "sections": list(ontology_data.keys()) if isinstance(ontology_data, dict) else "format_inattendu"
                })
            return ontology_data
            
        else:
            # Pour les fichiers TXT, on retourne le contenu brut
            ontology_data = {"raw_ontology": content}
            if debug_mode:
                debug_print("📄 Ontologie TXT chargée", {
                    "lignes": len(content.split('\n')),
                    "mots": len(content.split())
                })
            return ontology_data
            
    except Exception as e:
        console.print(f"[{COLORS['warning']}]⚠️ Attention: Erreur lors du chargement de l'ontologie '{ontology_path}': {e}[/{COLORS['warning']}]")
        console.print(f"[{COLORS['warning']}]🔄 Continuation sans ontologie.[/{COLORS['warning']}]")
        if debug_mode:
            debug_print("❌ Échec chargement ontologie", {"erreur": str(e)})
        return None

def split_text_into_chunks(text, chunk_size_words, debug_mode=False):
    """
    🔪 Découpe le texte en chunks logiques pour l'extraction de faits.
    
    Cette fonction analyse le texte et le divise en segments optimaux pour l'extraction,
    en préservant la cohérence sémantique et en respectant la taille maximale.
    
    Args:
        text (str): Texte à découper
        chunk_size_words (int): Taille maximale en mots par chunk
        debug_mode (bool): Active l'affichage de debug détaillé
        
    Returns:
        list: Liste des chunks de texte
    """
    final_chunks = []
    paragraphs = text.split("\n\n")
    
    current_chunk_parts = []
    current_word_count = 0
    
    if debug_mode:
        debug_print(f"🔪 Début découpage pour extraction", {
            "taille_cible": chunk_size_words,
            "paragraphes_detectes": len(paragraphs),
            "taille_totale": len(text.split())
        })
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            if debug_mode:
                debug_print(f"⏭️ Paragraphe {i+1} vide, ignoré")
            continue
            
        words = paragraph.split()
        word_count = len(words)
        
        if debug_mode:
            preview = paragraph[:50].replace('\n', ' ')
            debug_print(f"📝 Analyse paragraphe {i+1}/{len(paragraphs)}", {
                "mots": word_count,
                "apercu": f"'{preview}...'"
            })
        
        # 🚦 Si ajouter ce paragraphe dépasse la limite, finaliser le chunk actuel
        if current_chunk_parts and (current_word_count + word_count > chunk_size_words):
            chunk_to_add = "\n\n".join(current_chunk_parts)
            if chunk_to_add.strip():
                final_chunks.append(chunk_to_add)
                if debug_mode:
                    preview = chunk_to_add[:70].replace('\n', ' ')
                    debug_print(f"✅ Chunk {len(final_chunks)} finalisé", {
                        "mots": current_word_count,
                        "apercu": f"'{preview}...'"
                    })
            current_chunk_parts = []
            current_word_count = 0
        
        # 🔄 Si le paragraphe seul dépasse la limite, le diviser
        if word_count > chunk_size_words:
            if current_chunk_parts:
                chunk_to_add = "\n\n".join(current_chunk_parts)
                if chunk_to_add.strip():
                    final_chunks.append(chunk_to_add)
                current_chunk_parts = []
                current_word_count = 0
            
            # Diviser le long paragraphe en sous-chunks
            sub_chunks = []
            current_words = []
            for word in words:
                current_words.append(word)
                if len(current_words) >= chunk_size_words:
                    sub_chunks.append(" ".join(current_words))
                    current_words = []
            if current_words:
                sub_chunks.append(" ".join(current_words))
            
            final_chunks.extend(sub_chunks)
            if debug_mode:
                debug_print(f"✂️ Paragraphe long divisé", {
                    "mots_originaux": word_count,
                    "sous_chunks_crees": len(sub_chunks)
                })
        else:
            current_chunk_parts.append(paragraph)
            current_word_count += word_count
            if debug_mode:
                debug_print(f"➕ Paragraphe ajouté au chunk courant", {
                    "total_mots_chunk": current_word_count
                })
    
    # 🏁 Ajouter le dernier chunk s'il existe
    if current_chunk_parts:
        chunk_to_add = "\n\n".join(current_chunk_parts)
        if chunk_to_add.strip():
            final_chunks.append(chunk_to_add)
            if debug_mode:
                preview = chunk_to_add[:70].replace('\n', ' ')
                debug_print(f"🏁 Dernier chunk ajouté", {
                    "mots": current_word_count,
                    "apercu": f"'{preview}...'"
                })
    
    if debug_mode:
        debug_print(f"🎯 Découpage terminé", {
            "chunks_totaux": len(final_chunks),
            "repartition_mots": [len(chunk.split()) for chunk in final_chunks]
        })
    
    return final_chunks

def build_system_prompt(fact_types, ontology_data=None, custom_prompt=""):
    """
    🛠️ Construit le prompt système pour l'extraction de faits.
    
    Cette fonction génère un prompt système complet incluant les instructions
    de base, l'ontologie optionnelle et un prompt personnalisé.
    
    Args:
        fact_types (list): Types de faits à extraire
        ontology_data (dict): Données d'ontologie optionnelles
        custom_prompt (str): Prompt système personnalisé à ajouter
        
    Returns:
        str: Prompt système complet
    """
    base_prompt = """Vous êtes un expert en extraction d'informations et d'analyse de texte. 
Votre tâche est d'extraire de manière systématique et précise les faits et relations du texte fourni.

Extrayez les informations selon ces catégories :"""

    for fact_type in fact_types:
        if fact_type == "entities":
            base_prompt += "\n- ENTITÉS: Personnes, organisations, lieux, objets, concepts importants"
        elif fact_type == "events":
            base_prompt += "\n- ÉVÉNEMENTS: Actions, processus, incidents, situations"
        elif fact_type == "relationships":
            base_prompt += "\n- RELATIONS: Connexions entre entités (hiérarchie, causalité, association)"
        elif fact_type == "attributes":
            base_prompt += "\n- ATTRIBUTS: Propriétés, caractéristiques, qualités des entités"
        elif fact_type == "temporal":
            base_prompt += "\n- TEMPOREL: Dates, durées, séquences temporelles"
        elif fact_type == "spatial":
            base_prompt += "\n- SPATIAL: Localisations, positions relatives, géographie"

    base_prompt += """\n
IMPORTANT :
- Répondez UNIQUEMENT avec du JSON valide (pas de Markdown, pas de balises ```json ... ```).
- Évitez les contenus verbeux qui risquent de tronquer la réponse.
- Limitez-vous aux faits les plus importants (≈ 25 faits max). Si vous en détectez davantage, regroupez/synthétisez.
- Les champs `source_text` et `context` doivent être courts (≈ 200 caractères max chacun).

Formatez votre réponse en JSON valide avec cette structure :
{
  "facts": [
    {
      "id": "unique_id",
      "type": "entity|event|relationship|attribute|temporal|spatial",
      "content": "description du fait",
      "entities_involved": ["entité1", "entité2"],
      "confidence": 0.95,
      "source_text": "extrait du texte source",
      "context": "contexte additionnel si pertinent"
    }
  ],
  "relationships": [
    {
      "id": "rel_unique_id",
      "type": "type_de_relation",
      "source_fact_id": "id_du_fait_source",
      "target_fact_id": "id_du_fait_cible",
      "relationship_description": "description de la relation",
      "confidence": 0.90
    }
  ],
  "summary": {
    "total_facts": 0,
    "fact_types_count": {},
    "main_entities": [],
    "key_themes": []
  }
}"""

    if ontology_data:
        base_prompt += f"""\n\nONTOLOGIE FOURNIE pour guider l'extraction :
{json.dumps(ontology_data, indent=2, ensure_ascii=False)}

Utilisez cette ontologie pour :
- Identifier les types d'entités pertinents
- Respecter les relations définies
- Maintenir la cohérence terminologique"""

    # 🎯 Ajout du prompt personnalisé si fourni
    if custom_prompt and custom_prompt.strip():
        base_prompt += f"""\n\nINSTRUCTIONS PERSONNALISÉES :
{custom_prompt.strip()}"""

    base_prompt += "\n\nSoyez précis, exhaustif et maintenez une structure JSON valide."
    
    return base_prompt


def _strip_markdown_code_fences(text: str) -> str:
    """Supprime les balises de code Markdown (```json ... ```) si présentes."""
    if not text:
        return text
    # Retirer un éventuel fence d'ouverture (```json / ```)
    text = re.sub(r"^```(?:json)?\s*\n", "", text.strip(), flags=re.IGNORECASE)
    # Retirer un éventuel fence de fermeture
    text = re.sub(r"\n```\s*$", "", text.strip())
    return text.strip()


def _parse_first_json_object_from_text(content: str, chunk_index: int, debug_mode: bool = False):
    """Nettoie le contenu LLM et tente d'en extraire le premier objet JSON valide."""
    original_content = content or ""
    processed_content = re.sub(r"<think>.*?</think>", "", original_content, flags=re.DOTALL).strip()
    processed_content = _strip_markdown_code_fences(processed_content)

    json_start_index = processed_content.find('{')
    if json_start_index == -1:
        console.print(
            f"[{COLORS['warning']}]⚠️ Attention: Aucun JSON détecté après nettoyage pour le chunk {chunk_index}.[/{COLORS['warning']}]"
        )
        if debug_mode:
            debug_print(f"❌ Contenu non-JSON reçu chunk {chunk_index}", {"contenu_original": original_content})
        return None

    json_to_decode = processed_content[json_start_index:]
    decoder = json.JSONDecoder()
    facts_data, _ = decoder.raw_decode(json_to_decode)
    return facts_data

async def extract_facts_from_chunk(api_url, api_key, model, system_prompt, chunk_text, chunk_index, max_tokens_response=2048, debug_mode=False):
    """
    🔗 Appelle l'API LLMaaS pour extraire les faits d'un chunk de texte.
    
    Cette fonction construit la requête API, envoie le chunk au modèle LLM
    et parse la réponse JSON contenant les faits extraits.
    
    Args:
        api_url (str): URL de base de l'API LLMaaS
        api_key (str): Clé d'authentification API
        model (str): Nom du modèle à utiliser
        system_prompt (str): Prompt système pour guider l'extraction
        chunk_text (str): Texte du chunk à analyser
        chunk_index (int): Index du chunk (pour debug/logs)
        max_tokens_response (int): Limite de tokens pour la réponse
        debug_mode (bool): Active l'affichage de debug détaillé
        
    Returns:
        dict|None: Données d'extraction parsées ou None si erreur
    """
    if debug_mode:
        debug_print(f"🔗 Début extraction chunk {chunk_index}", {
            "taille_chunk": len(chunk_text.split()),
            "max_tokens": max_tokens_response,
            "modele": model
        })
    
    # 📝 Construction des messages pour l'API
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analysez le texte suivant et extrayez tous les faits selon les consignes :\n\n{chunk_text}"}
    ]

    # 🔧 Configuration de la requête API
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens_response,
        "stream": False,
        "temperature": 0.1  # Température basse pour plus de cohérence
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    if debug_mode:
        debug_print(f"📤 Envoi requête API chunk {chunk_index}", {
            "url": f"{api_url}/chat/completions",
            "model": model,
            "temperature": payload["temperature"]
        })
        # Affichage complet du payload pour le debug
        debug_print(f"📦 Payload complet pour chunk {chunk_index}", payload)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{api_url}/chat/completions", json=payload, headers=headers)
            
            if debug_mode:
                # Affichage de la réponse brute
                debug_print(f"📥 Réponse API brute reçue chunk {chunk_index}", {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text # Affiche le contenu brut de la réponse
                })

            response.raise_for_status()
            response_data = response.json()
            
            if response_data.get("choices") and response_data["choices"]:
                choice0 = response_data["choices"][0]
                finish_reason = choice0.get("finish_reason")
                content = choice0.get("message", {}).get("content", "")

                if debug_mode:
                    debug_print(f"ℹ️ finish_reason chunk {chunk_index}", {"finish_reason": finish_reason})
                if content:
                    if debug_mode:
                        debug_print(f"📄 Contenu brut COMPLET reçu chunk {chunk_index}", {
                            "taille_contenu": len(content),
                            "contenu_integral": content  # Contenu complet pour le debug
                        })
                    
                    # 🧹 Nettoyage et parsing du JSON
                    try:
                        facts_data = _parse_first_json_object_from_text(content, chunk_index, debug_mode)

                        if debug_mode:
                            debug_print(f"✅ JSON parsé avec succès via raw_decode pour le chunk {chunk_index}")
                        return facts_data

                    except json.JSONDecodeError as e:
                        console.print(
                            f"[{COLORS['warning']}]⚠️ Attention: Réponse JSON invalide pour le chunk {chunk_index}: {e}[/{COLORS['warning']}]"
                        )

                        # Diagnostic principal: sortie tronquée
                        if finish_reason == "length" and max_tokens_response <= 4096:
                            console.print(
                                f"[{COLORS['warning']}]⚠️ La réponse du modèle semble tronquée (finish_reason=length). "
                                f"Je vais relancer une tentative plus concise pour le chunk {chunk_index}.[/{COLORS['warning']}]"
                            )

                            retry_system_prompt = system_prompt + (
                                "\n\nRAPPEL: Réponds UNIQUEMENT avec du JSON valide, sans balises Markdown. "
                                "Sois plus concis: ~15 faits max, `source_text` <= 120 caractères, `context` optionnel et court."
                            )

                            retry_messages = [
                                {"role": "system", "content": retry_system_prompt},
                                {
                                    "role": "user",
                                    "content": (
                                        "Ta réponse précédente a été tronquée. "
                                        "Renvoie UNIQUEMENT un JSON valide et COMPLET pour le même texte, de manière plus concise :\n\n"
                                        + chunk_text
                                    ),
                                },
                            ]

                            retry_payload = {
                                "model": model,
                                "messages": retry_messages,
                                "max_tokens": max_tokens_response,
                                "stream": False,
                                "temperature": 0.0,
                            }

                            async with httpx.AsyncClient(timeout=120.0) as retry_client:
                                retry_resp = await retry_client.post(
                                    f"{api_url}/chat/completions", json=retry_payload, headers=headers
                                )
                                retry_resp.raise_for_status()
                                retry_data = retry_resp.json()
                                retry_choice0 = (retry_data.get("choices") or [{}])[0]
                                retry_content = retry_choice0.get("message", {}).get("content", "")

                                if debug_mode:
                                    debug_print(
                                        f"ℹ️ finish_reason retry chunk {chunk_index}",
                                        {"finish_reason": retry_choice0.get("finish_reason")},
                                    )

                                if retry_content:
                                    try:
                                        facts_data = _parse_first_json_object_from_text(
                                            retry_content, chunk_index, debug_mode
                                        )
                                        console.print(
                                            f"[{COLORS['success']}]✅ Chunk {chunk_index}: JSON valide obtenu après retry concis.[/{COLORS['success']}]"
                                        )
                                        return facts_data
                                    except json.JSONDecodeError as e2:
                                        console.print(
                                            f"[{COLORS['warning']}]⚠️ Retry chunk {chunk_index} encore invalide: {e2}[/{COLORS['warning']}]"
                                        )

                        if "Unterminated string" in str(e):
                            console.print(
                                f"[{COLORS['info']}]💡 Conseil: cette erreur est souvent due à une réponse tronquée. "
                                f"Essayez aussi de réduire --chunk-size-words (ex: 250) ou d'utiliser un modèle plus concis.[/{COLORS['info']}]"
                            )

                        if debug_mode:
                            debug_print(
                                f"❌ Échec parsing JSON chunk {chunk_index}",
                                {"erreur": str(e), "contenu_complet_original": content},
                            )
                        return None
            else:
                console.print(f"[{COLORS['error']}]🚫 Réponse API invalide pour le chunk {chunk_index}: 'choices' manquantes[/{COLORS['error']}]")
                if debug_mode:
                    debug_print(f"🚫 Structure API invalide chunk {chunk_index}", response_data)
                return None
                
    except Exception as e:
        console.print(f"[{COLORS['error']}]🔌 Erreur API pour le chunk {chunk_index}: {e}[/{COLORS['error']}]")
        if debug_mode:
            debug_print(f"🔌 Exception API chunk {chunk_index}", {"erreur": str(e)})
        return None

def merge_fact_extractions(chunk_extractions, debug_mode=False):
    """
    Fusionne les extractions de faits de tous les chunks en une structure cohérente.
    """
    merged_facts = []
    merged_relationships = []
    all_entities = set()
    all_themes = set()
    fact_types_count = {}
    fact_id_counter = 1
    rel_id_counter = 1

    if debug_mode:
        console.print(f"[DEBUG] Fusion de {len(chunk_extractions)} extractions de chunks")

    for chunk_idx, extraction in enumerate(chunk_extractions):
        if not extraction:
            continue

        # Map des IDs d'origine -> nouveaux IDs (pour recâbler les relations)
        id_map = {}
            
        # Traitement des faits
        facts = extraction.get("facts", [])
        for fact in facts:
            # Réassigner un ID unique
            original_id = fact.get("id", f"fact_{fact_id_counter}")
            new_id = f"fact_{fact_id_counter}"
            fact["id"] = new_id
            fact["chunk_source"] = chunk_idx + 1

            id_map[original_id] = new_id
            
            merged_facts.append(fact)
            
            # Compter les types de faits
            fact_type = fact.get("type", "unknown")
            fact_types_count[fact_type] = fact_types_count.get(fact_type, 0) + 1
            
            # Collecter les entités
            entities = fact.get("entities_involved", [])
            all_entities.update(entities)
            
            fact_id_counter += 1

        # Traitement des relations
        relationships = extraction.get("relationships", [])
        for rel in relationships:
            rel["id"] = f"rel_{rel_id_counter}"
            rel["chunk_source"] = chunk_idx + 1

            # Recâbler les IDs de faits si possible
            src = rel.get("source_fact_id")
            tgt = rel.get("target_fact_id")
            if src in id_map:
                rel["source_fact_id"] = id_map[src]
            if tgt in id_map:
                rel["target_fact_id"] = id_map[tgt]

            merged_relationships.append(rel)
            rel_id_counter += 1

        # Traitement du sommaire
        summary = extraction.get("summary", {})
        if "key_themes" in summary:
            all_themes.update(summary.get("key_themes", []))

    # Construction du sommaire global
    global_summary = {
        "total_facts": len(merged_facts),
        "total_relationships": len(merged_relationships),
        "fact_types_count": fact_types_count,
        "main_entities": list(all_entities)[:20],  # Limiter à 20 principales entités
        "key_themes": list(all_themes)[:15],  # Limiter à 15 thèmes principaux
        "chunks_processed": len([e for e in chunk_extractions if e])
    }

    return {
        "facts": merged_facts,
        "relationships": merged_relationships,
        "summary": global_summary,
        "metadata": {
            "extraction_version": SCRIPT_VERSION,
            "timestamp": "",  # Sera ajouté lors de la sauvegarde
            "source_file": ""  # Sera ajouté lors de la sauvegarde
        }
    }

def display_extraction_summary(facts_data):
    """
    Affiche un résumé formaté de l'extraction avec Rich.
    """
    summary = facts_data.get("summary", {})
    
    # Panneau principal
    summary_text = f"""
📊 **Extraction terminée avec succès !**

✅ **{summary.get('total_facts', 0)}** faits extraits
🔗 **{summary.get('total_relationships', 0)}** relations identifiées
📄 **{summary.get('chunks_processed', 0)}** chunks traités
"""
    
    console.print(Panel(summary_text, title="🎯 Résumé de l'extraction", border_style="green"))
    
    # Tableau des types de faits
    if summary.get("fact_types_count"):
        table = Table(title="📋 Répartition par type de fait")
        table.add_column("Type de fait", style="cyan")
        table.add_column("Nombre", style="magenta", justify="right")
        
        for fact_type, count in summary["fact_types_count"].items():
            table.add_row(fact_type.title(), str(count))
        
        console.print(table)
    
    # Principales entités
    if summary.get("main_entities"):
        entities_text = ", ".join(summary["main_entities"][:10])
        console.print(f"\n🏷️  **Principales entités:** {entities_text}")
    
    # Thèmes clés
    if summary.get("key_themes"):
        themes_text = ", ".join(summary["key_themes"][:8])
        console.print(f"\n🎯 **Thèmes clés:** {themes_text}")

def save_facts_data(facts_data, source_filepath, output_dir, output_format):
    """
    Sauvegarde les faits extraits dans le format spécifié.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Préparer les métadonnées
        from datetime import datetime
        facts_data["metadata"]["timestamp"] = datetime.now().isoformat()
        facts_data["metadata"]["source_file"] = os.path.basename(source_filepath)
        
        # Générer le nom de fichier de sortie
        base_name = Path(source_filepath).stem
        output_filename = f"{base_name}_facts.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Sauvegarder selon le format
        with open(output_path, "w", encoding="utf-8") as f:
            if output_format == "json":
                json.dump(facts_data, f, indent=2, ensure_ascii=False)
            elif output_format == "yaml":
                yaml.dump(facts_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        console.print(f"\n💾 [bold green]Faits sauvegardés dans : {output_path}[/bold green]")
        return output_path
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors de la sauvegarde : {e}[/bold red]")
        return None

async def main():
    """Fonction principale orchestrant l'extraction de faits."""
    load_dotenv()
    args = parse_arguments()

    if args.version:
        display_version()
        sys.exit(0)

    # Affichage des paramètres
    console.print(f"🔍 Extracteur de Faits v{SCRIPT_VERSION}", style="bold blue")
    console.print(f"📄 Fichier: [cyan]{args.file}[/cyan]")
    console.print(f"🤖 Modèle: [cyan]{args.model}[/cyan]")
    console.print(f"📋 Format de sortie: [cyan]{args.output_format}[/cyan]")
    
    if args.ontology:
        console.print(f"🧠 Ontologie: [cyan]{args.ontology}[/cyan]")

    # 🔑 Chargement des données d'entrée
    if args.debug:
        debug_print("🚀 Début du processus d'extraction")
    
    api_key = load_api_key(args.api_key_env)
    file_content = read_file_content(args.file)
    ontology_data = load_ontology(args.ontology, args.debug)
    
    if not file_content.strip():
        console.print(f"[{COLORS['error']}]📄 Erreur: Le fichier est vide.[/{COLORS['error']}]")
        return

    if args.debug:
        debug_print("📄 Fichier chargé avec succès", {
            "taille_caracteres": len(file_content),
            "taille_mots": len(file_content.split()),
            "lignes": len(file_content.split('\n'))
        })

    # 🔪 Découpage en chunks
    chunks = split_text_into_chunks(file_content, args.chunk_size_words, args.debug)
    console.print(f"📝 Texte découpé en [cyan]{len(chunks)}[/cyan] chunk(s)")

    # 🛠️ Construction du prompt système
    system_prompt = build_system_prompt(args.fact_types, ontology_data, args.custom_prompt)
    
    if args.debug:
        debug_print("🛠️ Prompt système construit", {
            "taille_prompt": len(system_prompt),
            "types_faits": args.fact_types,
            "ontologie_presente": ontology_data is not None
        })
        console.print(f"[{COLORS['debug']}]📝 Aperçu prompt système:\n{system_prompt[:300]}...[/{COLORS['debug']}]")

    # 🔍 Extraction des faits
    chunk_extractions = []
    
    console.print(f"\n🔍 [{COLORS['info']}]Extraction des faits en cours...[/{COLORS['info']}]")
    
    if args.debug:
        debug_print("🔄 Début de la boucle d'extraction", {
            "chunks_a_traiter": len(chunks),
            "mode_interactif": args.interactive
        })
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    ) as progress:
        extraction_task = progress.add_task(f"[{COLORS['success']}]Extraction...", total=len(chunks))
        
        for i, chunk in enumerate(chunks):
            chunk_preview = " ".join(chunk.split()[:8]) + ("..." if len(chunk.split()) > 8 else "")
            progress.update(extraction_task, description=f"[{COLORS['success']}]Chunk {i+1}/{len(chunks)}: \"{chunk_preview}\"")
            
            extracted_facts = await extract_facts_from_chunk(
                args.api_url, api_key, args.model, system_prompt, 
                chunk, i+1, args.max_tokens, args.debug
            )
            
            if extracted_facts:
                chunk_extractions.append(extracted_facts)
                
                if args.interactive:
                    progress.stop()
                    console.print(f"\n--- Chunk {i+1} ---", style="bold yellow")
                    console.print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
                    console.print(f"--- Faits extraits ---", style="bold green")
                    if extracted_facts.get("facts"):
                        for fact in extracted_facts["facts"][:3]:  # Montrer les 3 premiers
                            console.print(f"• {fact.get('type', 'N/A')}: {fact.get('content', 'N/A')}")
                    user_input = console.input("Entrée pour continuer, 'q' pour quitter: ").lower()
                    if user_input == 'q':
                        console.print("[yellow]Extraction interrompue.[/yellow]")
                        return
                    progress.start()
            else:
                console.print(f"[bold yellow]Échec extraction chunk {i+1}, continuation...[/bold yellow]")
                
            progress.advance(extraction_task)

    # Fusion des résultats
    console.print("\n🔄 [blue]Fusion des extractions...[/blue]")
    final_facts_data = merge_fact_extractions(chunk_extractions, args.debug)
    
    # Affichage du résumé
    display_extraction_summary(final_facts_data)
    
    # Sauvegarde
    output_path = save_facts_data(final_facts_data, args.file, args.output_dir, args.output_format)
    
    if output_path:
        console.print(f"\n✨ [bold green]Extraction terminée ![/bold green]")
        console.print(f"📁 Résultats disponibles dans : [cyan]{output_path}[/cyan]")

if __name__ == "__main__":
    asyncio.run(main())
