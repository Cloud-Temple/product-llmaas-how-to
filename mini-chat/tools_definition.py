# -*- coding: utf-8 -*-
"""
Définition des Outils pour Mini-Chat LLMaaS.

Ce module définit les fonctions Python qui peuvent être appelées par le LLM
en tant qu'"outils" (function calling). Il contient également la structure JSON
(`TOOLS_AVAILABLE`) qui décrit ces outils à l'API LLMaaS, ainsi qu'un mapping
(`TOOL_FUNCTIONS_MAP`) entre les noms d'outils et leurs implémentations Python.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-02
"""
import datetime
import json
import os
import subprocess # Pour l'outil execute_shell_command
from rich.prompt import Confirm # Pour la confirmation de l'outil shell

# --- Définition des Outils ---

def get_current_time(**kwargs) -> str:
    """Retourne l'heure et la date actuelles."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculator(expression: str, **kwargs) -> str:
    """
    Évalue une expression mathématique simple.
    Exemple: "2 + 2 * 10"
    """
    try:
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "Erreur: L'expression contient des caractères non autorisés."
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Erreur de calcul: {str(e)}"

def read_file_content(file_path: str, **kwargs) -> str:
    """Lit et retourne le contenu d'un fichier spécifié."""
    try:
        if ".." in file_path:
            return "Erreur: Chemin de fichier non autorisé (contient '..')."
        abs_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
        if not abs_path.startswith(os.getcwd()):
             return "Erreur: Chemin de fichier non autorisé (en dehors du répertoire de travail)."
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read(10000) 
        if len(content) == 10000:
            return content + "\n[... Contenu tronqué ...]"
        return content
    except FileNotFoundError:
        return f"Erreur: Le fichier '{file_path}' n'a pas été trouvé."
    except Exception as e:
        return f"Erreur lors de la lecture du fichier '{file_path}': {str(e)}"

def save_content_to_file(file_path: str, content: str, **kwargs) -> str:
    """Sauvegarde le contenu textuel fourni dans un fichier spécifié."""
    try:
        # Interpréter file_path comme relatif au CWD.
        # Si file_path est juste un nom de fichier, il sera créé dans CWD/mini_chat_output.
        # Si file_path contient des répertoires (ex: "data/notes.txt"), il sera relatif au CWD.
        
        # Normaliser le chemin pour supprimer les "./" et résoudre les ".."
        # mais toujours vérifier la présence de ".." pour interdire la remontée.
        if ".." in os.path.normpath(file_path): # Vérifier après normalisation aussi
            return "Erreur: Chemin de fichier non autorisé pour la sauvegarde (contient '..')."

        # Déterminer le chemin absolu final
        god_mode = kwargs.get('god_mode', False)

        if os.path.isabs(file_path):
            if not god_mode:
                return "Erreur: Les chemins absolus ne sont autorisés pour la sauvegarde qu'en mode GOD MODE. Veuillez utiliser un chemin relatif ou activer le godmode."
            # En god_mode, on accepte le chemin absolu
            final_path = os.path.abspath(file_path)
            # S'assurer que le répertoire parent existe pour le chemin absolu
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
        elif not os.path.dirname(file_path): # Si c'est un simple nom de fichier (relatif)
            target_dir = os.path.join(os.getcwd(), "mini_chat_output")
            os.makedirs(target_dir, exist_ok=True)
            final_path = os.path.abspath(os.path.join(target_dir, file_path))
        else: # Sinon, c'est un chemin relatif avec des répertoires
            final_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
            # S'assurer que le répertoire parent existe
            os.makedirs(os.path.dirname(final_path), exist_ok=True)

        # Si ce n'est pas un chemin absolu et qu'on n'est pas en god_mode, on vérifie qu'on reste dans le CWD
        if not os.path.isabs(file_path) and not god_mode:
            if not final_path.startswith(os.getcwd()):
                 return "Erreur: Chemin de fichier non autorisé pour la sauvegarde (en dehors du répertoire de travail)."
        # En god_mode avec un chemin absolu, cette vérification est implicitement bypassée.

        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Retourner le chemin absolu si c'était un chemin absolu, sinon relatif
        if os.path.isabs(file_path):
            return f"Contenu sauvegardé avec succès dans '{final_path}'."
        else:
            relative_final_path = os.path.relpath(final_path, os.getcwd())
            return f"Contenu sauvegardé avec succès dans '{relative_final_path}'."
    except Exception as e:
        return f"Erreur lors de la sauvegarde du fichier '{file_path}': {str(e)}"

def execute_shell_command(command: str, **kwargs) -> str:
    """
    Exécute une commande shell. ATTENTION: Potentiellement dangereux.
    Une confirmation utilisateur est requise sauf si le mode 'god_mode' est activé.
    """
    god_mode = kwargs.get('god_mode', False)
    
    if not god_mode:
        console_instance = kwargs.get('console_instance')
        if console_instance:
            console_instance.print(f"[bold yellow]AVERTISSEMENT : Le modèle demande à exécuter la commande shell suivante :[/bold yellow]\n`{command}`")
            if not Confirm.ask("Voulez-vous autoriser cette commande ?", default=False, console=console_instance):
                return "Exécution de la commande annulée par l'utilisateur."
        else: # Fallback si la console n'est pas passée
            print(f"AVERTISSEMENT : Le modèle demande à exécuter la commande shell suivante :\n`{command}`")
            if input("Voulez-vous autoriser cette commande ? (o/N): ").lower() != 'o':
                return "Exécution de la commande annulée par l'utilisateur."
    else: # En god_mode, on log juste l'exécution
        console_instance = kwargs.get('console_instance')
        if console_instance:
            console_instance.print(f"[bold red]GOD MODE ACTIF : Exécution automatique de la commande shell :[/bold red]\n`{command}`")
        else:
            print(f"GOD MODE ACTIF : Exécution automatique de la commande shell :\n`{command}`")


    try:
        # Pour des raisons de sécurité, il est préférable d'utiliser shell=False et de passer la commande comme une liste d'arguments.
        # Cependant, pour un outil générique appelé par un LLM, shell=True est souvent plus flexible, mais plus risqué.
        # Ici, on garde shell=True pour la flexibilité, mais avec la confirmation utilisateur comme garde-fou.
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, check=False)
        
        output = "Sortie Standard:\n" + result.stdout if result.stdout else "Aucune sortie standard."
        if result.stderr:
            output += "\n\nErreur Standard:\n" + result.stderr
        output += f"\n\nCode de retour: {result.returncode}"
        
        # Limiter la taille de la sortie retournée au modèle
        if len(output) > 2000:
            output = output[:2000] + "\n[... Sortie tronquée ...]"
        
        return output
    except subprocess.TimeoutExpired:
        return "Erreur: La commande a expiré (timeout)."
    except Exception as e:
        return f"Erreur lors de l'exécution de la commande shell: {str(e)}"


TOOLS_AVAILABLE = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Obtient l'heure et la date actuelles.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Évalue une expression mathématique. Par exemple, '2+2*10'.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "L'expression mathématique à évaluer."}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Lit le contenu d'un fichier local. Le chemin doit être relatif au répertoire d'exécution du script.",
            "parameters": {
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Le chemin relatif du fichier à lire (ex: './mon_fichier.txt')."}},
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_content_to_file",
            "description": "Sauvegarde un contenu textuel dans un fichier. Si seul un nom de fichier est fourni (ex: 'notes.txt'), il sera sauvegardé dans './mini_chat_output/'. Si un chemin relatif est fourni (ex: 'data/rapport.txt'), il sera créé par rapport au répertoire courant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Chemin relatif du fichier (ex: 'notes.txt' ou 'dossier/notes.txt')."},
                    "content": {"type": "string", "description": "Le contenu textuel à sauvegarder."},
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_shell_command",
            "description": "Exécute une commande shell sur le système où le script Python est lancé. ATTENTION: Potentiellement dangereux. Une confirmation utilisateur est requise sauf si le 'godmode' est activé via CLI.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "La commande shell à exécuter (ex: 'ls -l', 'echo Hello')."}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_vector_database",
            "description": "Recherche des informations pertinentes dans une base de connaissances interne (vectorielle) pour répondre à la question de l'utilisateur. Utilise cet outil si la question semble porter sur des documents ou des informations spécifiques qui pourraient se trouver dans la base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La question ou le sujet de recherche à utiliser pour trouver des informations pertinentes."
                    }
                },
                "required": ["query"]
            },
        },
    },
]

TOOL_FUNCTIONS_MAP = {
    "get_current_time": get_current_time,
    "calculator": calculator,
    "read_file_content": read_file_content,
    "save_content_to_file": save_content_to_file,
    "execute_shell_command": execute_shell_command,
    "search_in_vector_database": None, # La fonction réelle sera dans mini_chat.py
}
