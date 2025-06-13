#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module utilitaires pour les images - PhotoAnalyzer.

Fournit des fonctions pour charger, valider, analyser et encoder les images
pour l'analyse avec les modèles multimodaux.
"""

import os
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageFile
from cli_ui import print_message, print_debug_data

# Permettre le chargement d'images tronquées
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Formats d'images supportés
SUPPORTED_FORMATS = {
    'JPEG', 'JPG', 'PNG', 'GIF', 'BMP', 'TIFF', 'TIF', 'WEBP'
}

# Extensions de fichiers supportées
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'
}

# Taille maximale recommandée (en pixels)
MAX_RECOMMENDED_DIMENSION = 2048
MAX_FILE_SIZE_MB = 50

def load_and_validate_image(image_path: str, silent: bool = False, debug_mode: bool = False) -> bool:
    """
    Charge et valide un fichier image.
    
    Args:
        image_path: Chemin vers le fichier image
        silent: Si True, n'affiche pas les messages
        debug_mode: Si True, affiche des informations de debug
    
    Returns:
        True si l'image est valide et peut être chargée, False sinon
    """
    try:
        # Vérifier l'existence du fichier
        if not os.path.exists(image_path):
            print_message(f"Le fichier image '{image_path}' n'existe pas.", style="error", silent=silent, debug_mode=debug_mode)
            return False
        
        # Vérifier la taille du fichier
        file_size = os.path.getsize(image_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            print_message(f"Le fichier image est trop volumineux ({file_size_mb:.2f} MB). Taille maximale: {MAX_FILE_SIZE_MB} MB.", 
                         style="error", silent=silent, debug_mode=debug_mode)
            return False
        
        # Vérifier l'extension
        file_extension = Path(image_path).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            print_message(f"Format de fichier '{file_extension}' non supporté. Formats supportés: {', '.join(SUPPORTED_EXTENSIONS)}", 
                         style="error", silent=silent, debug_mode=debug_mode)
            return False
        
        # Essayer de charger l'image avec PIL
        with Image.open(image_path) as img:
            # Vérifier le format
            if img.format not in SUPPORTED_FORMATS:
                print_message(f"Format d'image '{img.format}' non supporté. Formats supportés: {', '.join(SUPPORTED_FORMATS)}", 
                             style="error", silent=silent, debug_mode=debug_mode)
                return False
            
            # Vérifier les dimensions
            width, height = img.size
            max_dimension = max(width, height)
            
            if max_dimension > MAX_RECOMMENDED_DIMENSION:
                print_message(f"Image très grande ({width}x{height}). La dimension maximale recommandée est {MAX_RECOMMENDED_DIMENSION}px.", 
                             style="warning", silent=silent, debug_mode=debug_mode)
                print_message("L'analyse peut être plus lente et consommer plus de tokens.", 
                             style="warning", silent=silent, debug_mode=debug_mode)
            
            # Affichage des informations en mode debug
            if debug_mode and not silent:
                print_debug_data("Validation Image", {
                    "Format": img.format,
                    "Mode": img.mode,
                    "Dimensions": f"{width} × {height}",
                    "Taille fichier": f"{file_size_mb:.2f} MB",
                    "Transparence": getattr(img, 'transparency', None) is not None,
                    "Animée": getattr(img, 'is_animated', False)
                }, silent=silent, debug_mode=debug_mode)
        
        print_message("Image validée avec succès.", style="success", silent=silent, debug_mode=debug_mode)
        return True
        
    except Exception as e:
        print_message(f"Erreur lors de la validation de l'image: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return False

def get_image_info(image_path: str, silent: bool = False, debug_mode: bool = False) -> Optional[Dict[str, Any]]:
    """
    Récupère des informations détaillées sur une image.
    
    Args:
        image_path: Chemin vers le fichier image
        silent: Si True, n'affiche pas les messages
        debug_mode: Si True, affiche des informations de debug
    
    Returns:
        Dictionnaire contenant les informations de l'image, None en cas d'erreur
    """
    try:
        with Image.open(image_path) as img:
            # Informations de base
            width, height = img.size
            info = {
                'filename': os.path.basename(image_path),
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': width,  # Ajouter width explicitement
                'height': height,  # Ajouter height explicitement
                'file_size': os.path.getsize(image_path)
            }
            
            # Informations supplémentaires
            info['has_transparency'] = (
                img.mode in ('RGBA', 'LA') or 
                (img.mode == 'P' and 'transparency' in img.info) or
                'transparency' in img.info
            )
            
            info['is_animated'] = getattr(img, 'is_animated', False)
            
            # EXIF data si disponible
            try:
                exif_method = getattr(img, '_getexif', None)
                if exif_method is not None and exif_method() is not None:
                    info['has_exif'] = True
                else:
                    info['has_exif'] = False
            except (AttributeError, Exception):
                info['has_exif'] = False
            
            # Informations sur le type MIME
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type:
                info['mime_type'] = mime_type
            
            return info
            
    except Exception as e:
        print_message(f"Erreur lors de la récupération des informations de l'image: {e}", 
                     style="error", silent=silent, debug_mode=debug_mode)
        return None

def encode_image_to_base64(image_path: str, silent: bool = False, debug_mode: bool = False) -> Optional[str]:
    """
    Encode une image en chaîne base64.
    
    Args:
        image_path: Chemin vers le fichier image
        silent: Si True, n'affiche pas les messages
        debug_mode: Si True, affiche des informations de debug
    
    Returns:
        Chaîne base64 de l'image, None en cas d'erreur
    """
    try:
        with open(image_path, "rb") as image_file:
            # Lire le fichier et l'encoder en base64
            image_data = image_file.read()
            encoded_string = base64.b64encode(image_data).decode('utf-8')
            
            # Afficher des informations de debug
            if debug_mode and not silent:
                original_size_mb = len(image_data) / (1024 * 1024)
                base64_size_mb = len(encoded_string) / (1024 * 1024)
                compression_ratio = len(encoded_string) / len(image_data)
                
                print_debug_data("Encodage Base64", {
                    "Taille originale": f"{original_size_mb:.2f} MB",
                    "Taille base64": f"{base64_size_mb:.2f} MB",
                    "Ratio expansion": f"{compression_ratio:.2f}x",
                    "Longueur chaîne": f"{len(encoded_string):,} caractères"
                }, silent=silent, debug_mode=debug_mode)
            
            print_message("Image encodée en base64 avec succès.", style="success", silent=silent, debug_mode=debug_mode)
            return encoded_string
            
    except FileNotFoundError:
        print_message(f"Fichier image non trouvé: {image_path}", style="error", silent=silent, debug_mode=debug_mode)
        return None
    except Exception as e:
        print_message(f"Erreur lors de l'encodage de l'image: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None

def optimize_image_for_analysis(
    image_path: str, 
    max_dimension: int = MAX_RECOMMENDED_DIMENSION,
    quality: int = 85,
    output_path: Optional[str] = None,
    silent: bool = False,
    debug_mode: bool = False
) -> Optional[str]:
    """
    Optimise une image pour l'analyse (redimensionnement et compression).
    
    Args:
        image_path: Chemin vers le fichier image original
        max_dimension: Dimension maximale (largeur ou hauteur)
        quality: Qualité JPEG (1-100)
        output_path: Chemin de sortie (optionnel, génère automatiquement si None)
        silent: Si True, n'affiche pas les messages
        debug_mode: Si True, affiche des informations de debug
    
    Returns:
        Chemin vers le fichier optimisé, None en cas d'erreur
    """
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            original_file_size = os.path.getsize(image_path)
            
            # Calculer les nouvelles dimensions
            width, height = img.size
            if max(width, height) <= max_dimension:
                print_message("Image déjà dans les dimensions optimales.", style="info", silent=silent, debug_mode=debug_mode)
                return image_path
            
            # Calculer le ratio de redimensionnement
            ratio = max_dimension / max(width, height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Redimensionner l'image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Déterminer le chemin de sortie
            if not output_path:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_optimized{path.suffix}")
            
            # Sauvegarder l'image optimisée
            save_kwargs = {}
            if resized_img.format == 'JPEG' or image_path.lower().endswith(('.jpg', '.jpeg')):
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            resized_img.save(output_path, **save_kwargs)
            
            # Calculer les statistiques
            new_file_size = os.path.getsize(output_path)
            size_reduction = (1 - new_file_size / original_file_size) * 100
            
            if debug_mode and not silent:
                print_debug_data("Optimisation Image", {
                    "Dimensions originales": f"{original_size[0]} × {original_size[1]}",
                    "Nouvelles dimensions": f"{new_width} × {new_height}",
                    "Taille originale": f"{original_file_size / (1024 * 1024):.2f} MB",
                    "Nouvelle taille": f"{new_file_size / (1024 * 1024):.2f} MB",
                    "Réduction": f"{size_reduction:.1f}%",
                    "Fichier optimisé": output_path
                }, silent=silent, debug_mode=debug_mode)
            
            print_message(f"Image optimisée sauvegardée: {output_path}", style="success", silent=silent, debug_mode=debug_mode)
            return output_path
            
    except Exception as e:
        print_message(f"Erreur lors de l'optimisation de l'image: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None

def detect_image_content_type(image_path: str) -> Optional[str]:
    """
    Détecte le type de contenu d'une image pour optimiser le prompt d'analyse.
    
    Args:
        image_path: Chemin vers le fichier image
    
    Returns:
        Type de contenu détecté ('photo', 'screenshot', 'diagram', 'text', 'mixed')
    """
    try:
        with Image.open(image_path) as img:
            # Analyser les caractéristiques de l'image
            width, height = img.size
            aspect_ratio = width / height
            
            # Analyser les couleurs dominantes
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Réduire l'image pour l'analyse rapide
            small_img = img.resize((100, 100))
            colors = small_img.getcolors(maxcolors=256*256*256)
            
            if colors:
                # Analyser la distribution des couleurs
                total_pixels = sum(count for count, color in colors)
                dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:10]
                
                # Calculer la diversité des couleurs
                unique_colors = len(colors)
                color_diversity = unique_colors / total_pixels
                
                # Heuristiques pour déterminer le type de contenu
                if unique_colors < 20 and color_diversity < 0.1:
                    return 'diagram'  # Diagramme ou schéma (peu de couleurs)
                elif aspect_ratio > 1.5 and unique_colors < 50:
                    return 'screenshot'  # Capture d'écran (format large, couleurs limitées)
                elif color_diversity > 0.3:
                    return 'photo'  # Photo (grande diversité de couleurs)
                else:
                    return 'mixed'  # Contenu mixte
            
            return 'mixed'  # Par défaut
            
    except Exception:
        return 'mixed'  # En cas d'erreur, retourner le type par défaut

def get_optimal_analysis_prompt(image_path: str, base_prompt: str) -> str:
    """
    Génère un prompt optimisé basé sur le type de contenu détecté.
    
    Args:
        image_path: Chemin vers le fichier image
        base_prompt: Prompt de base
    
    Returns:
        Prompt optimisé pour le type de contenu
    """
    content_type = detect_image_content_type(image_path)
    
    # Préfixes spécialisés selon le type de contenu
    type_prefixes = {
        'photo': "En analysant cette photographie, ",
        'screenshot': "En analysant cette capture d'écran, ",
        'diagram': "En analysant ce diagramme ou schéma, ",
        'text': "En analysant cette image contenant du texte, ",
        'mixed': "En analysant cette image, "
    }
    
    prefix = type_prefixes.get(content_type or 'mixed', type_prefixes['mixed'])
    return prefix + base_prompt.lower()
