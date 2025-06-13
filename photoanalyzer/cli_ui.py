#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module CLI UI pour PhotoAnalyzer.

Fournit des fonctions d'affichage avec couleurs et formatage pour le CLI PhotoAnalyzer.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import json
from typing import Dict, Any, Optional

# Console Rich globale
console = Console()

class TermColors:
    """Couleurs ANSI pour le terminal."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DEBUG = '\033[90m'

def print_message(
    message: str, 
    style: Optional[str] = None, 
    silent: bool = False, 
    debug_mode: bool = False
) -> None:
    """
    Affiche un message formaté selon le style spécifié.
    
    Args:
        message: Message à afficher
        style: Style d'affichage ('info', 'success', 'warning', 'error', 'debug')
        silent: Si True, n'affiche rien
        debug_mode: Si False et style='debug', n'affiche rien
    """
    if silent:
        return
    
    if style == 'debug' and not debug_mode:
        return
    
    # Mappage des styles vers les couleurs Rich
    style_mapping = {
        'info': 'blue',
        'success': 'green',
        'warning': 'yellow',
        'error': 'red bold',
        'debug': 'dim cyan'
    }
    
    if style and style in style_mapping:
        console.print(f"[{style_mapping[style]}]{message}[/]")
    else:
        console.print(message)

def print_debug_data(
    title: str, 
    data: Dict[str, Any], 
    silent: bool = False, 
    debug_mode: bool = False
) -> None:
    """
    Affiche des données de debug sous forme de tableau formaté.
    
    Args:
        title: Titre du tableau
        data: Dictionnaire de données à afficher
        silent: Si True, n'affiche rien
        debug_mode: Si False, n'affiche rien
    """
    if silent or not debug_mode:
        return
    
    # Créer un tableau Rich
    table = Table(
        title=f"🔍 {title}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title_style="bold blue"
    )
    
    table.add_column("Paramètre", style="cyan", no_wrap=True)
    table.add_column("Valeur", style="white")
    
    for key, value in data.items():
        # Formater la valeur selon son type
        if isinstance(value, dict):
            formatted_value = json.dumps(value, indent=2, ensure_ascii=False)
        elif isinstance(value, (list, tuple)):
            formatted_value = str(value)
        else:
            formatted_value = str(value)
        
        table.add_row(key, formatted_value)
    
    console.print(table)
    console.print()  # Ligne vide après le tableau

def print_image_info(image_info: Dict[str, Any], silent: bool = False, debug_mode: bool = False) -> None:
    """
    Affiche les informations sur une image de manière formatée.
    
    Args:
        image_info: Dictionnaire contenant les informations de l'image
        silent: Si True, n'affiche rien
        debug_mode: Si False, n'affiche rien en mode debug
    """
    if silent:
        return
    
    panel_content = []
    
    # Informations de base
    if 'filename' in image_info:
        panel_content.append(f"📁 **Fichier**: {image_info['filename']}")
    
    if 'format' in image_info:
        panel_content.append(f"🖼️  **Format**: {image_info['format']}")
    
    if 'size' in image_info:
        width, height = image_info['size']
        panel_content.append(f"📐 **Dimensions**: {width} × {height} pixels")
    
    if 'mode' in image_info:
        panel_content.append(f"🎨 **Mode**: {image_info['mode']}")
    
    if 'file_size' in image_info:
        size_mb = image_info['file_size'] / (1024 * 1024)
        panel_content.append(f"💾 **Taille**: {size_mb:.2f} MB")
    
    # Informations supplémentaires en mode debug
    if debug_mode:
        if 'has_transparency' in image_info:
            panel_content.append(f"🔍 **Transparence**: {'Oui' if image_info['has_transparency'] else 'Non'}")
        
        if 'is_animated' in image_info:
            panel_content.append(f"🔍 **Animée**: {'Oui' if image_info['is_animated'] else 'Non'}")
    
    if panel_content:
        content = "\n".join(panel_content)
        panel = Panel(
            content,
            title="🖼️  Informations Image",
            border_style="blue",
            padding=(1, 1)
        )
        console.print(panel)

def print_analysis_result(result: str, analysis_type: str) -> None:
    """
    Affiche le résultat d'analyse de manière formatée.
    
    Args:
        result: Résultat de l'analyse
        analysis_type: Type d'analyse effectuée
    """
    # Déterminer l'icône selon le type d'analyse
    icons = {
        'general': '🔍',
        'technical': '⚙️',
        'people': '👥',
        'objects': '📦',
        'scene': '🏞️',
        'colors': '🎨',
        'composition': '📐',
        'emotions': '😊',
        'text': '📝',
        'security': '🔒',
        'medical': '⚕️',
        'count': '🔢'
    }
    
    icon = icons.get(analysis_type, '🔍')
    title = f"{icon} Analyse {analysis_type.title()}"
    
    panel = Panel(
        result,
        title=title,
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)

def print_error_panel(error_message: str, title: str = "Erreur") -> None:
    """
    Affiche un message d'erreur dans un panneau formaté.
    
    Args:
        error_message: Message d'erreur à afficher
        title: Titre du panneau d'erreur
    """
    panel = Panel(
        f"❌ {error_message}",
        title=f"🚨 {title}",
        border_style="red bold",
        padding=(1, 1)
    )
    console.print(panel)

def print_success_panel(message: str, title: str = "Succès") -> None:
    """
    Affiche un message de succès dans un panneau formaté.
    
    Args:
        message: Message de succès à afficher
        title: Titre du panneau de succès
    """
    panel = Panel(
        f"✅ {message}",
        title=f"🎉 {title}",
        border_style="green bold",
        padding=(1, 1)
    )
    console.print(panel)

def print_warning_panel(message: str, title: str = "Attention") -> None:
    """
    Affiche un message d'avertissement dans un panneau formaté.
    
    Args:
        message: Message d'avertissement à afficher
        title: Titre du panneau d'avertissement
    """
    panel = Panel(
        f"⚠️  {message}",
        title=f"🔔 {title}",
        border_style="yellow bold",
        padding=(1, 1)
    )
    console.print(panel)

def print_header(title: str) -> None:
    """
    Affiche un en-tête formaté.
    
    Args:
        title: Titre de l'en-tête
    """
    console.rule(f"[bold blue]{title}[/bold blue]", style="blue")

def print_separator() -> None:
    """Affiche une ligne de séparation."""
    console.rule(style="dim")

def print_step(step_number: int, step_description: str, total_steps: Optional[int] = None) -> None:
    """
    Affiche une étape du processus.
    
    Args:
        step_number: Numéro de l'étape
        step_description: Description de l'étape
        total_steps: Nombre total d'étapes (optionnel)
    """
    if total_steps:
        step_text = f"Étape {step_number}/{total_steps}"
    else:
        step_text = f"Étape {step_number}"
    
    console.print(f"[bold cyan]{step_text}[/bold cyan]: {step_description}")

def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Demande une confirmation à l'utilisateur.
    
    Args:
        prompt: Message de confirmation
        default: Valeur par défaut si l'utilisateur appuie sur Entrée
    
    Returns:
        True si l'utilisateur confirme, False sinon
    """
    default_text = " [O/n]" if default else " [o/N]"
    response = console.input(f"[yellow]{prompt}{default_text}[/yellow]: ").lower().strip()
    
    if not response:
        return default
    
    return response in ('o', 'oui', 'y', 'yes', '1', 'true')
