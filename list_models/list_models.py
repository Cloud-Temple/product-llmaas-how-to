#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Exemple : Lister les Modèles Disponibles via l'API LLMaaS

Ce script se connecte à l'endpoint /v1/models de l'API LLMaaS
pour récupérer la liste des modèles disponibles et les affiche
dans un tableau formaté à l'aide de la bibliothèque Rich.

Auteur: Cloud Temple
Version: 1.0.2
Date: 25/01/2026
"""

# Importations des modules nécessaires
import os  # Pour interagir avec le système d'exploitation (variables d'environnement)
import requests  # Pour effectuer des requêtes HTTP vers l'API
from dotenv import load_dotenv  # Pour charger les variables d'environnement depuis un fichier .env
from rich.console import Console  # Pour un affichage en console amélioré (couleurs, tableaux, etc.)
from rich.table import Table  # Spécifiquement pour créer des tableaux avec Rich
from rich.panel import Panel  # Pour encadrer du texte avec Rich
from rich.text import Text  # Pour formater du texte avec Rich
from rich.progress import Progress, SpinnerColumn, TextColumn  # Pour afficher une barre de progression avec Rich

# Initialisation de la console Rich pour un affichage esthétique
console = Console()

def load_configuration():
    """
    Charge la configuration nécessaire (URL de l'API et clé API) depuis les variables d'environnement.
    Les variables attendues sont API_URL et API_KEY (conformément à .env.example de mini-chat).
    Le script s'arrête si ces variables ne sont pas trouvées.
    
    Returns:
        tuple: Un tuple contenant l'URL de l'API et la clé API.
    """
    console.print("[info]Chargement de la configuration depuis le fichier .env...[/info]")
    load_dotenv()  # Charge les variables depuis le fichier .env s'il existe
    
    # Récupération des variables d'environnement
    api_url = os.getenv("API_URL")
    api_key = os.getenv("API_KEY")

    # Vérification de la présence des variables d'environnement indispensables
    if not api_url or not api_key:
        console.print(
            Panel(
                Text(
                    "Erreur: Les variables d'environnement API_URL et API_KEY doivent être définies.\n"
                    "Veuillez créer un fichier .env (en copiant .env.example) et y renseigner ces valeurs, "
                    "ou les exporter directement dans votre session shell.",
                    style="bold red"
                ),
                title="[bold red]Configuration Manquante[/bold red]",
                border_style="red",
                expand=False  # Le panel ne s'étend pas sur toute la largeur
            )
        )
        exit(1)  # Arrête le script si la configuration est manquante
    
    console.print(f"[debug]API_URL chargée: {api_url}[/debug]")
    # Par sécurité, ne pas afficher la clé API dans les logs standards.
    # console.print(f"[debug]API_KEY chargée: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'Non définie'}[/debug]")
    
    return api_url, api_key

def fetch_models(api_url, api_key):
    """
    Récupère la liste des modèles disponibles en interrogeant l'endpoint /models de l'API LLMaaS.
    Gère les erreurs potentielles lors de l'appel API (HTTP, connexion, timeout).
    
    Args:
        api_url (str): L'URL de base de l'API LLMaaS (doit inclure /v1, ex: https://api.ai.cloud-temple.com/v1).
        api_key (str): La clé d'authentification API.
        
    Returns:
        list: Une liste de dictionnaires représentant les modèles, ou None en cas d'erreur.
    """
    # Construction de l'URL complète pour l'endpoint des modèles.
    # L'URL de base (API_URL) doit déjà contenir le segment /v1.
    # On s'assure juste qu'il n'y a pas de double slash si API_URL se termine déjà par /
    # et on ajoute /models.
    models_endpoint = f"{api_url.rstrip('/')}/models"
    
    # Préparation des en-têtes HTTP pour l'authentification et le type de contenu
    headers = {
        "Authorization": f"Bearer {api_key}", # Utilisation de la clé API comme token Bearer
        "Content-Type": "application/json"
    }

    console.print(f"[info]Appel API vers l'endpoint : [cyan]{models_endpoint}[/cyan][/info]")

    # Utilisation de Rich Progress pour afficher un spinner pendant l'appel API
    with Progress(
        SpinnerColumn(spinner_name="dots"),  # Style de spinner
        TextColumn("[progress.description]{task.description}"),  # Texte descriptif de la tâche
        transient=True,  # La barre de progression disparaît une fois terminée
    ) as progress_bar:
        # Ajout d'une tâche à la barre de progression
        progress_bar.add_task("Récupération des modèles en cours...", total=None) # total=None pour un spinner indéfini
        
        try:
            # Exécution de la requête GET vers l'API avec un timeout
            response = requests.get(models_endpoint, headers=headers, timeout=15) # Timeout de 15 secondes
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
            
            # Extraction des données des modèles depuis la réponse JSON.
            # Une API compatible OpenAI retourne typiquement les données dans une clé "data".
            models_list = response.json().get("data", [])
            console.print(f"[debug]Réponse API brute (premiers 100 caractères de la liste): {str(models_list)[:100]}...[/debug]")
            return models_list
        
        # Gestion des exceptions spécifiques à la bibliothèque requests
        except requests.exceptions.HTTPError as http_err:
            error_message = f"Erreur HTTP lors de l'appel API: {http_err.response.status_code}\n" \
                            f"Réponse du serveur: {http_err.response.text}"
            console.print(Panel(Text(error_message, style="bold red"), title="[bold red]Erreur API[/bold red]", border_style="red"))
        except requests.exceptions.ConnectionError:
            console.print(Panel(Text("Erreur de Connexion: Impossible de se connecter au serveur API. "
                                     "Vérifiez l'URL de l'API et votre connexion internet.", style="bold red"), 
                                     title="[bold red]Erreur de Connexion[/bold red]", border_style="red"))
        except requests.exceptions.Timeout:
            console.print(Panel(Text("Erreur de Timeout: La requête vers l'API a expiré. "
                                     "Le serveur n'a pas répondu dans le délai imparti (15 secondes).", style="bold red"), 
                                     title="[bold red]Timeout[/bold red]", border_style="red"))
        except requests.exceptions.RequestException as err:
            # Gestion de toute autre erreur liée à la requête (plus générique)
            console.print(Panel(Text(f"Erreur inattendue lors de la requête API: {err}", style="bold red"), 
                                     title="[bold red]Erreur Inattendue[/bold red]", border_style="red"))
        return None # Retourne None si une erreur s'est produite

def categorize_model(model_id):
    """
    Catégorise un modèle selon son ID.
    
    Args:
        model_id (str): L'ID du modèle
        
    Returns:
        str: La catégorie du modèle
    """
    model_id_lower = model_id.lower()
    
    # Modèles de langage généralistes
    if any(keyword in model_id_lower for keyword in ['gemma3', 'llama3', 'qwen3', 'mistral', 'ministral', 'gpt-oss', 'olmo', 'cogito', 'magistral']):
        return "Langage Généraliste"
    
    # Modèles d'embedding
    elif any(keyword in model_id_lower for keyword in ['embedding', 'bge']):
        return "Embedding"
    
    # Modèles multimodaux (vision)
    elif any(keyword in model_id_lower for keyword in ['vision', 'vl', 'image']):
        return "Multimodal (Vision)"
    
    # Modèles spécialisés en traduction
    elif 'translate' in model_id_lower:
        return "Traduction"
    
    # Modèles OCR
    elif 'ocr' in model_id_lower:
        return "OCR"
    
    # Modèles spécialisés en code
    elif 'coder' in model_id_lower:
        return "Code"
    
    # Modèles de sécurité/modération
    elif 'guardian' in model_id_lower:
        return "Sécurité/Modération"
    
    # Modèles médicaux
    elif 'medgemma' in model_id_lower or 'mediphi' in model_id_lower:
        return "Médical"
    
    # Modèles de raisonnement
    elif 'reasoning' in model_id_lower:
        return "Raisonnement"
    
    # Modèles de fonctions
    elif 'functiongemma' in model_id_lower:
        return "Fonctions"
    
    # Par défaut
    else:
        return "Autre"

def display_models_table(models_data):
    """
    Affiche la liste des modèles récupérés dans un tableau formaté avec Rich.
    
    Args:
        models_data (list): Une liste de dictionnaires, où chaque dictionnaire représente un modèle.
                            Chaque modèle doit avoir au moins une clé "id".
    """
    # Si aucune donnée de modèle n'est disponible (liste vide ou None après une erreur)
    if not models_data:
        console.print(Panel(Text("Aucun modèle n'a été trouvé ou une erreur est survenue lors de la récupération.", 
                               style="yellow"), 
                               title="[bold yellow]Information[/bold yellow]", border_style="yellow"))
        return

    # Création de la table Rich avec un titre, affichage des en-têtes et style pour les en-têtes
    table = Table(title=Text("Modèles LLMaaS Disponibles sur l'API", style="bold cyan"), 
                  show_header=True, header_style="bold magenta", expand=True)
    
    # Définition des colonnes du tableau avec leurs styles et largeurs
    table.add_column("ID du Modèle", style="dim cyan", width=35, overflow="fold") # ID du modèle, peut être long
    table.add_column("Possédé par", width=20) # Qui a créé/possède le modèle (ex: "openai", "cloud-temple")
    table.add_column("Type d'Objet", width=15) # Type d'objet API (généralement "model")
    table.add_column("Type de Modèle", width=20) # Catégorie fonctionnelle du modèle
    table.add_column("Créé le (UTC)", justify="right", width=20) # Timestamp de création, formaté
    table.add_column("Alias", overflow="fold") # Liste des alias éventuels du modèle

    # Tri des modèles par ID pour un affichage cohérent et prédictible
    for model in sorted(models_data, key=lambda m: m.get("id", "")):
        # Extraction des informations de chaque modèle, avec des valeurs par défaut "N/A" si une clé est manquante
        model_id = model.get("id", "N/A")
        owned_by = model.get("owned_by", "N/A")
        object_type = model.get("object", "N/A")
        
        created_timestamp = model.get("created") # Timestamp Unix (nombre de secondes depuis l'epoch)
        created_date_str = "N/A" # Valeur par défaut si la conversion échoue
        if isinstance(created_timestamp, (int, float)): # Vérifie si c'est un nombre valide
            try:
                from datetime import datetime, timezone # Importation pour la conversion de date et gestion du fuseau horaire
                # Conversion du timestamp Unix en date et heure lisibles, en spécifiant UTC
                created_date_str = datetime.fromtimestamp(created_timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                # En cas d'erreur de conversion (peu probable si le timestamp est correct), logguer et garder "N/A"
                console.print(f"[debug]Erreur de conversion de date pour le timestamp {created_timestamp}: {e}[/debug]")
                pass 

        aliases = model.get("aliases", []) # Liste des alias, peut être vide
        aliases_str = ", ".join(aliases) if aliases else "-" # Formatte la liste des alias en chaîne de caractères

        # Déterminer le type fonctionnel du modèle
        model_type = categorize_model(model_id)
        
        # Ajout d'une ligne à la table pour chaque modèle avec les informations extraites
        table.add_row(
            model_id,
            owned_by,
            object_type,
            model_type,
            created_date_str,
            aliases_str
        )

    # Affichage de la table complète dans la console
    console.print(table)

def main():
    """
    Fonction principale du script.
    Orchestre le chargement de la configuration, la récupération des modèles depuis l'API,
    et leur affichage dans un format tabulaire.
    """
    # Affichage d'un panneau de bienvenue stylisé
    console.print(Panel(Text("Client API LLMaaS - Liste des Modèles Disponibles", style="bold green"), 
                        title="[bold green]Bienvenue[/bold green]", border_style="green", expand=False))
    
    # Étape 1: Chargement de la configuration (URL de l'API et clé API)
    api_url, api_key = load_configuration()
    
    console.print("\n[info]Tentative de récupération de la liste des modèles depuis l'API...[/info]")
    # Étape 2: Récupération des données des modèles via l'API
    models_data = fetch_models(api_url, api_key)

    # Étape 3: Affichage des modèles si la récupération a réussi
    if models_data is not None: # Vérifie si des données ont été retournées (pas None, ce qui indique une erreur)
        console.print("\n[success]Liste des modèles récupérée avec succès ![/success]\n")
        display_models_table(models_data) # Appel de la fonction d'affichage
    else:
        # Message d'erreur si la récupération a échoué
        console.print("\n[error]Échec de la récupération des modèles. Veuillez vérifier les messages d'erreur ci-dessus.[/error]")

# Point d'entrée du script :
# Cette condition vérifie si le script est exécuté directement (et non importé comme module).
if __name__ == "__main__":
    main() # Appel de la fonction principale
