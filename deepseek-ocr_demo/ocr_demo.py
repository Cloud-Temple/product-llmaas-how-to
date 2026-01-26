#!/usr/bin/env python3
"""
Démonstration d'utilisation de DeepSeek-OCR via l'API LLMaaS.

Ce script permet d'extraire du texte structuré (Markdown) à partir :
- D'images (PNG, JPG, etc.)
- De fichiers PDF (multipage)
- De fichiers locaux ou d'URLs distantes

Il illustre :
1. La préparation des données (conversion PDF, optimisation image)
2. L'utilisation de l'API OpenAI-compatible avec un modèle multimodal
3. Le rendu et la présentation des résultats
"""

import os
import sys
import time
import base64
import io
import argparse
import requests
import fitz  # Bibliothèque PyMuPDF pour la manipulation de PDF
from PIL import Image  # Bibliothèque Pillow pour le traitement d'images
from openai import OpenAI  # Client API standard
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

# Initialisation de la console Rich pour un affichage coloré et structuré
console = Console()

# Image par défaut utilisée si aucun argument n'est fourni (un reçu complexe)
# Source: Wikimedia Commons (Licence libre)
DEFAULT_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/0/0b/ReceiptSwiss.jpg"


# -----------------------------------------------------------------------------
# Fonctions de Traitement d'Image
# -----------------------------------------------------------------------------

def process_pil_image(img, source_name="Image"):
    """
    Traite une image chargée en mémoire (objet PIL.Image) pour l'optimiser avant envoi.
    
    Étapes :
    1. Conversion en mode RGB (nécessaire pour les PNG avec transparence alpha).
    2. Redimensionnement préventif si l'image est très grande (> 4096px).
    3. Encodage en JPEG base64 haute qualité.

    Args:
        img (PIL.Image): L'objet image à traiter.
        source_name (str): Nom de la source pour l'affichage (ex: "Page 1").

    Returns:
        str: La chaîne base64 de l'image JPEG.
    """
    try:
        # Affichage des caractéristiques techniques pour le debug
        console.print(f"[dim]{source_name} : {img.size} mode={img.mode}[/dim]")
        
        # Conversion en RGB : supprime le canal Alpha (transparence) qui n'est pas
        # supporté par le format JPEG et peut gêner certains modèles.
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionnement : si une dimension dépasse 4096 pixels, on réduit l'image
        # en conservant le ratio. Cela évite de saturer l'API ou le modèle, tout en
        # gardant une qualité suffisante pour l'OCR.
        max_dim = 4096
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            console.print(f"[dim]Image redimensionnée à {img.size}[/dim]")

        # Sauvegarde de l'image en mémoire (buffer) au format JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)  # Qualité 95 pour minimiser les artefacts
        
        # Encodage du buffer binaire en chaîne base64 (format requis par l'API)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    except Exception as e:
        console.print(f"[bold red]Erreur lors du traitement de l'image :[/] {e}")
        sys.exit(1)

def process_local_image(image_path):
    """
    Charge une image depuis un fichier local et délègue son traitement.
    """
    try:
        with Image.open(image_path) as img:
            return process_pil_image(img, source_name=f"Fichier {os.path.basename(image_path)}")
    except Exception as e:
        console.print(f"[bold red]Erreur lors de l'ouverture de l'image locale :[/] {e}")
        sys.exit(1)


# -----------------------------------------------------------------------------
# Fonctions de Traitement PDF
# -----------------------------------------------------------------------------

def process_pdf_stream(pdf_data, source_name="PDF"):
    """
    Lit un flux de données PDF (bytes), extrait CHAQUE page, la convertit en image
    haute résolution, et retourne une liste d'images encodées en base64.

    Args:
        pdf_data (bytes): Le contenu binaire du fichier PDF.
        source_name (str): Nom du fichier pour l'affichage.

    Returns:
        list[str]: Une liste de chaînes base64 (une par page).
    """
    images_base64 = []
    try:
        # Ouverture du PDF depuis la mémoire via PyMuPDF (fitz)
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        if doc.page_count < 1:
            raise ValueError("Le PDF est vide ou ne contient aucune page.")
        
        console.print(f"[dim]PDF chargé ({doc.page_count} pages) : {source_name}[/dim]")
        
        # Itération sur toutes les pages du document
        for i in range(doc.page_count):
            page = doc.load_page(i)
            
            # Le zoom 2.0 correspond approximativement à 144 DPI (72 * 2),
            # ce qui offre une résolution suffisante pour l'OCR de petits caractères
            # sans générer des images excessivement lourdes.
            pix = page.get_pixmap(dpi=144)
            
            # Conversion du Pixmap PyMuPDF en image Pillow (PIL)
            # pix.samples contient les octets bruts RGB
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            
            # Traitement de l'image (RGB, Resize, Base64)
            b64 = process_pil_image(img, source_name=f"Page {i+1}")
            images_base64.append(b64)
            
        return images_base64
        
    except Exception as e:
        console.print(f"[bold red]Erreur lors du traitement du PDF :[/] {e}")
        sys.exit(1)


# -----------------------------------------------------------------------------
# Logique Principale de Récupération
# -----------------------------------------------------------------------------

def get_image_sources(image_source):
    """
    Détermine le type de source (URL ou Fichier, Image ou PDF) et prépare les données.
    
    Returns:
        list[dict]: Une liste de dictionnaires au format OpenAI pour l'image_url :
                    [{"url": "data:image/jpeg;base64,..."}]
    """
    
    # Cas 1 : Source distante (URL)
    if image_source.startswith(('http://', 'https://')):
        # Si l'URL pointe vers un PDF, on doit le télécharger nous-mêmes car l'API
        # vision s'attend à recevoir une image, pas un PDF.
        if image_source.lower().endswith('.pdf'):
            try:
                console.print(f"[dim]Téléchargement du PDF distant : {image_source}[/dim]")
                response = requests.get(image_source, timeout=30)
                response.raise_for_status()  # Vérifie les erreurs HTTP (404, 500...)
                
                # Conversion du PDF téléchargé (en mémoire) en images
                base64_images = process_pdf_stream(response.content, source_name="PDF Distant")
                return [{"url": f"data:image/jpeg;base64,{b64}"} for b64 in base64_images]
            except Exception as e:
                 console.print(f"[bold red]Erreur lors du téléchargement/traitement du PDF :[/] {e}")
                 sys.exit(1)
        
        # Sinon, on assume que c'est une URL d'image directe que l'API peut télécharger elle-même.
        return [{"url": image_source}]

    # Cas 2 : Fichier local
    elif os.path.exists(image_source):
        if image_source.lower().endswith('.pdf'):
            # Lecture du fichier PDF local en binaire
            with open(image_source, "rb") as f:
                base64_images = process_pdf_stream(f.read(), source_name=os.path.basename(image_source))
                return [{"url": f"data:image/jpeg;base64,{b64}"} for b64 in base64_images]
        else:
            # Image locale simple
            base64_image = process_local_image(image_source)
            return [{"url": f"data:image/jpeg;base64,{base64_image}"}]
    
    # Cas d'erreur : Fichier non trouvé
    else:
        console.print(f"[bold red]Erreur :[/] La source '{image_source}' est introuvable (ni fichier local, ni URL).")
        sys.exit(1)

def get_prompt(mode):
    """
    Sélectionne le prompt système en fonction du mode d'extraction souhaité.
    Le modèle DeepSeek-OCR (Janus) réagit différemment selon le prompt.
    """
    prompts = {
        "markdown": "Convert the document to markdown.", # Idéal pour préserver la structure (tableaux, titres)
        "text": "Free OCR.", # Extraction de texte brut, sans souci de mise en page
        "figure": "Parse the figure." # Spécialisé pour décrire des diagrammes ou graphiques
    }
    return prompts.get(mode, prompts["markdown"])

def main():
    # --- 1. Analyse des Arguments ---
    parser = argparse.ArgumentParser(description="DeepSeek-OCR Demo Client - Analyse de documents et images.")
    
    parser.add_argument("image", nargs="?", default=DEFAULT_IMAGE, 
                      help="URL ou chemin vers le fichier à analyser (Image ou PDF). Défaut: Ticket test.")
    
    parser.add_argument("--raw", action="store_true", 
                      help="Affiche le code Markdown brut à la fin (utile pour copier-coller).")
    
    parser.add_argument("--mode", choices=["markdown", "text", "figure"], default="markdown", 
                      help="Mode d'extraction : 'markdown' (structuré), 'text' (brut), 'figure' (description).")
    
    args = parser.parse_args()

    # --- 2. Configuration de l'API ---
    # Charge les variables depuis le fichier .env
    load_dotenv()

    api_key = os.getenv("API_KEY")
    api_base = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")

    if not api_key:
        console.print("[bold red]Erreur de Configuration :[/] La variable d'environnement API_KEY n'est pas définie.")
        console.print("Veuillez créer un fichier .env contenant : API_KEY='votre_clé'")
        sys.exit(1)

    # Initialisation du client OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url=api_base,
    )

    # --- 3. Préparation des Données ---
    image_source = args.image
    prompt_text = get_prompt(args.mode)

    console.print(Panel(f"[bold blue]DeepSeek-OCR Demo[/]\nAnalyse de : {image_source}\nMode : {args.mode}", border_style="blue"))
    console.print(f"[dim]Prompt système utilisé : {prompt_text}[/dim]")

    # Récupération et préparation des images (peut prendre du temps pour les gros PDF)
    image_contents = get_image_sources(image_source)
    total_pages = len(image_contents)

    if total_pages > 1:
        console.print(f"[bold yellow]Document multipage détecté ({total_pages} pages). Traitement séquentiel...[/]")

    # --- 4. Boucle de Traitement (Page par Page) ---
    full_markdown = ""
    total_duration = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    
    for idx, img_content in enumerate(image_contents):
        page_num = idx + 1
        
        # Séparateur visuel pour les documents multipages
        if total_pages > 1:
            console.rule(f"[bold]Page {page_num}/{total_pages}[/]")

        # Construction du message pour l'API
        # Note: On envoie une image à la fois pour maximiser la qualité de l'OCR
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": img_content
                    }
                ]
            }
        ]

        try:
            # Mesure du temps d'appel API
            start_time = time.time()
            
            with console.status(f"[bold green]Analyse page {page_num}/{total_pages} en cours...[/]", spinner="dots"):
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-OCR",
                    messages=messages,
                    max_tokens=4096,  # Limite de génération pour une page
                    temperature=0.0,  # Température 0 pour une extraction déterministe et fidèle
                )
            
            duration = time.time() - start_time

            # Extraction du texte généré
            result_text = response.choices[0].message.content
            
            # Accumulation pour le rapport global
            if total_pages > 1:
                full_markdown += f"\n\n<!-- Page {page_num} -->\n\n"
            full_markdown += result_text

            # Affichage du rendu Markdown dans le terminal
            console.print(Panel(Markdown(result_text), title=f"Résultat (Page {page_num})", border_style="green"))
            
            # Mise à jour des statistiques
            usage = response.usage
            total_duration += duration
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens
            
            console.print(f"[dim]Page {page_num} traitée en {duration:.2f}s | Tokens: Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}[/dim]")

        except Exception as e:
            console.print(f"[bold red]Erreur lors de l'analyse de la page {page_num} :[/] {e}")
            # On continue avec les autres pages même si une échoue

    # --- 5. Résumé et Sortie ---
    
    # Afficher un résumé global pour les documents multipages
    if total_pages > 1:
        console.rule("[bold]Résumé Global[/]")
        console.print(f"Temps total API : [bold green]{total_duration:.2f}s[/]")
        console.print(f"Moyenne par page : [bold]{total_duration/total_pages:.2f}s[/]")
        console.print(f"Tokens totaux : [bold]Prompt={total_prompt_tokens}, Completion={total_completion_tokens}[/]")
        if total_duration > 0:
            console.print(f"Vitesse de génération : [bold]{(total_completion_tokens/total_duration):.2f} tokens/s[/]")

    # Si l'option --raw est activée, afficher tout le Markdown brut
    if args.raw:
        console.print("\n[bold yellow]Code Markdown complet brut :[/]")
        console.print(Syntax(full_markdown, "markdown", theme="monokai", word_wrap=True))

if __name__ == "__main__":
    main()
