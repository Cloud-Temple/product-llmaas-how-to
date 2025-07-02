# -*- coding: utf-8 -*-
"""
Fonctionnalités de Retrieval-Augmented Generation (RAG) pour Mini-Chat LLMaaS.

Ce module contient la logique de découpage de texte en chunks sémantiques
et la fonction de recherche dans la base de données vectorielle Qdrant.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-30
"""

import os
import re
from typing import List, Dict, Any, Optional

# Importations nécessaires pour les fonctions RAG
import tiktoken
from qdrant_utils import QdrantManager # Pour l'instanciation de QdrantManager
from api_client import get_embeddings # Pour la génération d'embeddings
from ui_utils import console # Pour les messages console

async def search_in_vector_database(query: str, **kwargs) -> str:
    """
    Effectue une recherche de similarité dans Qdrant et retourne le contexte trouvé.
    Cette fonction est conçue pour être appelée comme un outil par le LLM.

    Args:
        query: La question ou le sujet de recherche à utiliser pour trouver des informations pertinentes.
        **kwargs: Contient les dépendances nécessaires (qdrant_manager, embedding_model, api_url, api_key).

    Returns:
        Une chaîne de caractères contenant le contexte trouvé, ou un message d'erreur.
    """
    # Extraire les dépendances nécessaires passées via kwargs
    qdrant_manager = kwargs.get('qdrant_manager')
    embedding_model = kwargs.get('embedding_model')
    api_url = kwargs.get('api_url')
    api_key = kwargs.get('api_key')

    if not all([qdrant_manager, embedding_model, api_url, api_key]):
        return "Erreur: La recherche RAG n'est pas correctement configurée (dépendances manquantes)."

    try:
        console.print(f"[cyan]Outil RAG: recherche pour '{query}'...[/cyan]")
        query_vector_list = await get_embeddings(str(api_url), str(api_key), [query], str(embedding_model))
        
        if not query_vector_list:
            return "Erreur: Impossible de générer l'embedding pour la recherche."

        query_vector = query_vector_list[0]
        if qdrant_manager:
            search_results = qdrant_manager.search(vector=query_vector, limit=3)
        else:
            return "Erreur: Qdrant manager non initialisé."
        
        if not search_results:
            return "Aucun résultat pertinent trouvé dans la base de connaissances."

        context_str = "\n\n---\n\n".join([
            f"Source: {hit['payload']['source']}\n\n{hit['payload']['text']}" 
            for hit in search_results
        ])
        return f"Contexte trouvé:\n{context_str}"

    except Exception as e:
        return f"Erreur lors de la recherche dans la base de données vectorielle: {e}"

def get_text_chunks(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """
    Découpe un texte en chunks sémantiques intelligents qui respectent les frontières naturelles.
    
    Hiérarchie de découpage (par ordre de préférence) :
    1. Paragraphes (double saut de ligne)
    2. Sections/titres (lignes commençant par #, -, =, etc.)
    3. Listes (lignes commençant par -, *, 1., etc.)
    4. Phrases (points, ?, !)
    5. Découpage brutal si nécessaire

    Args:
        text: Le texte d'entrée à découper.
        chunk_size: La taille maximale souhaitée pour chaque chunk (en tokens).
        chunk_overlap: Le nombre de tokens de chevauchement entre les chunks consécutifs.

    Returns:
        Une liste de chaînes de caractères, chaque chaîne étant un chunk du texte original.
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        console.print("[yellow]Avertissement: tiktoken non disponible. Le découpage des chunks sera moins précis (basé sur les caractères).[/yellow]")
        encoding = None

    if not encoding:
        # Fallback simple si tiktoken n'est pas disponible
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

    # Fonction utilitaire pour compter les tokens
    def count_tokens(text_segment: str) -> int:
        return len(encoding.encode(text_segment))

    # Fonction utilitaire pour créer un chunk avec métadonnées
    def create_chunk(segments: List[str]) -> str:
        return "\n".join(segments).strip()

    # Étape 1: Découpage hiérarchique du texte
    text_segments = _split_text_hierarchically(text)
    
    chunks = []
    current_chunk_segments = []
    current_chunk_tokens = 0

    for segment in text_segments:
        segment_tokens = count_tokens(segment)
        
        # Si un segment unique dépasse la taille max, le découper brutalement
        if segment_tokens > chunk_size:
            # Finaliser le chunk actuel s'il existe
            if current_chunk_segments:
                chunks.append(create_chunk(current_chunk_segments))
                current_chunk_segments = []
                current_chunk_tokens = 0
            
            # Découper le segment trop long
            chunks.extend(_split_oversized_segment(segment, chunk_size, chunk_overlap, encoding))
            continue
        
        # Vérifier si on peut ajouter le segment au chunk actuel
        if current_chunk_tokens + segment_tokens <= chunk_size:
            current_chunk_segments.append(segment)
            current_chunk_tokens += segment_tokens
        else:
            # Finaliser le chunk actuel
            if current_chunk_segments:
                chunks.append(create_chunk(current_chunk_segments))
            
            # Créer le chevauchement intelligent
            overlap_segments, overlap_tokens = _create_smart_overlap(
                current_chunk_segments, chunk_overlap, encoding
            )
            
            # Commencer le nouveau chunk
            current_chunk_segments = overlap_segments + [segment]
            current_chunk_tokens = overlap_tokens + segment_tokens

    # Ajouter le dernier chunk
    if current_chunk_segments:
        chunks.append(create_chunk(current_chunk_segments))

    return [chunk for chunk in chunks if chunk.strip()]

def _split_text_hierarchically(text: str) -> List[str]:
    """
    Découpe le texte en respectant la hiérarchie sémantique naturelle.
    
    Returns:
        Liste de segments de texte respectant les frontières naturelles.
    """
    segments = []
    
    # Étape 1: Découper par paragraphes (double saut de ligne)
    paragraphs = re.split(r'\n\s*\n', text)
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Étape 2: Détecter les sections/titres
        if _is_section_header(paragraph):
            segments.append(paragraph)
            continue
        
        # Étape 3: Détecter les listes
        if _is_list_content(paragraph):
            # Découper les listes par éléments
            list_items = _split_list_items(paragraph)
            segments.extend(list_items)
            continue
        
        # Étape 4: Découper par phrases pour les paragraphes normaux
        sentences = _split_into_sentences(paragraph)
        segments.extend(sentences)
    
    return segments

def _is_section_header(text: str) -> bool:
    """Détecte si un texte est un titre/section."""
    lines = text.split('\n')
    first_line = lines[0].strip()
    
    # Titres Markdown
    if first_line.startswith('#'):
        return True
    
    # Titres soulignés
    if len(lines) >= 2:
        second_line = lines[1].strip()
        if re.match(r'^[=\-_]{3,}$', second_line):
            return True
    
    # Titres en majuscules courts
    if len(first_line) < 100 and first_line.isupper() and len(first_line.split()) <= 10:
        return True
    
    return False

def _is_list_content(text: str) -> bool:
    """Détecte si un texte contient une liste."""
    lines = text.split('\n')
    list_indicators = 0
    
    for line in lines:
        line = line.strip()
        if re.match(r'^[-*+•]\s+', line) or re.match(r'^\d+\.\s+', line) or re.match(r'^[a-zA-Z]\.\s+', line):
            list_indicators += 1
    
    # Si plus de 30% des lignes sont des éléments de liste
    return list_indicators > 0 and (list_indicators / len(lines)) > 0.3

def _split_list_items(text: str) -> List[str]:
    """Découpe une liste en éléments individuels."""
    lines = text.split('\n')
    items = []
    current_item = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Nouvelle entrée de liste
        if re.match(r'^[-*+•]\s+', line_stripped) or re.match(r'^\d+\.\s+', line_stripped) or re.match(r'^[a-zA-Z]\.\s+', line_stripped):
            if current_item:
                items.append('\n'.join(current_item))
                current_item = []
            current_item.append(line)
        else:
            # Continuation de l'élément actuel
            if current_item:
                current_item.append(line)
    
    if current_item:
        items.append('\n'.join(current_item))
    
    return items

def _split_into_sentences(text: str) -> List[str]:
    """Découpe un texte en phrases avec une regex améliorée."""
    # Regex améliorée qui gère mieux les cas complexes
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\!|\?)\s+'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]

def _create_smart_overlap(segments: List[str], overlap_tokens: int, encoding) -> tuple[List[str], int]:
    """
    Crée un chevauchement intelligent en prenant les derniers segments complets.
    
    Returns:
        Tuple (segments_overlap, tokens_count)
    """
    if not segments or overlap_tokens <= 0:
        return [], 0
    
    overlap_segments = []
    current_tokens = 0
    
    # Partir de la fin et remonter
    for segment in reversed(segments):
        segment_tokens = len(encoding.encode(segment))
        if current_tokens + segment_tokens <= overlap_tokens:
            overlap_segments.insert(0, segment)
            current_tokens += segment_tokens
        else:
            break
    
    return overlap_segments, current_tokens

def _split_oversized_segment(segment: str, chunk_size: int, chunk_overlap: int, encoding) -> List[str]:
    """
    Découpe un segment trop long en respectant les mots quand possible.
    """
    tokens = encoding.encode(segment)
    chunks = []
    
    for i in range(0, len(tokens), chunk_size - chunk_overlap):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        
        # Essayer de couper sur un espace pour éviter de couper les mots
        if i + chunk_size < len(tokens):  # Pas le dernier chunk
            last_space = chunk_text.rfind(' ')
            if last_space > len(chunk_text) * 0.8:  # Si l'espace est dans les 20% finaux
                chunk_text = chunk_text[:last_space]
        
        chunks.append(chunk_text)
    
    return chunks

__all__ = [
    "get_text_chunks",
    "search_in_vector_database",
]
