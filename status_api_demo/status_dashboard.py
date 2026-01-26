#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démonstration de l'API publique de statut LLMaaS.
Ce script récupère l'état global de la plateforme et les métriques de performance
pour une liste de modèles, en affichant également les données de consommation énergétique.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.1.0
Date: 26/01/2026
"""

import argparse
import requests
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import track

# Initialisation de la console Rich
console = Console()

# URL de base de l'API de statut publique
STATUS_API_URL = "https://llmaas.status.cloud-temple.app"

# Dictionnaire de consommation énergétique (kWh par million de tokens)
# Mis à jour le 26/01/2026 selon la configuration officielle des serveurs.
MODEL_ENERGY_MAP = {
    "bge-m3:567m": 0.36,
    "cogito:32b": 6.67,
    "deepseek-ocr": 1.01,
    "devstral-small-2:24b": 5.80,
    "devstral:24b": 3.28,
    "embeddinggemma:300m": 0.35,
    "functiongemma:270m": 1.17,
    "gemma3:1b": 1.15,
    "gemma3:27b": 6.35,
    "glm-4.7-flash:30b": 2.38,
    "glm-4.7:358b": 7.41,
    "gpt-oss:120b": 2.19,
    "gpt-oss:20b": 14.81,
    "granite-embedding:278m": 0.31,
    "granite3.1-moe:2b": 0.60,
    "granite3.2-vision:2b": 1.05,
    "granite4-small-h:32b": 4.04,
    "granite4-tiny-h:7b": 1.05,
    "llama3.3:70b": 7.85,
    "magistral:24b": 5.80,
    "medgemma:27b": 6.56,
    "ministral-3:14b": 4.30,
    "ministral-3:3b": 1.22,
    "ministral-3:8b": 2.42,
    "mistral-small3.2:24b": 5.35,
    "nemotron3-nano:30b": 1.62,
    "olmo-3:32b": 7.02,
    "olmo-3:7b": 1.65,
    "qwen2.5:0.5b": 1.03,
    "qwen3-coder:30b": 1.39,
    "qwen3-2507-gptq:235b": 3.93,
    "qwen3-2507-think:4b": 2.56,
    "qwen3-2507:4b": 4.44,
    "qwen3:30b-a3b": 1.39,
    "qwen3-next:80b": 1.54,
    "qwen3-omni:30b": 2.65,
    "qwen3-vl:2b": 0.95,
    "qwen3-vl:30b": 3.10,
    "qwen3-vl:32b": 7.84,
    "qwen3-vl:4b": 2.34,
    "qwen3-vl:8b": 2.05,
    "qwen3-vl:235b": 7.35,
    "qwen3:0.6b": 1.33,
    "rnj-1:8b": 1.97,
    "translategemma:12b": 4.44,
    "translategemma:27b": 6.35,
    "translategemma:4b": 1.27
}

def get_global_status() -> Optional[Dict[str, Any]]:
    """
    Récupère l'état global de la plateforme.
    Endpoint: GET /api/platform-status
    """
    try:
        response = requests.get(f"{STATUS_API_URL}/api/platform-status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Erreur lors de la récupération du statut global :[/] {e}")
        return None

def get_model_status(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère les métriques détaillées pour un modèle spécifique.
    Endpoint: GET /api/platform-status?model=<model_id>
    """
    try:
        response = requests.get(f"{STATUS_API_URL}/api/platform-status", params={"model": model_id}, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # En cas d'erreur sur un modèle spécifique, on retourne None sans bloquer le script
        return None

def calculate_request_energy(total_tokens: int, energy_per_m: Optional[float]) -> str:
    """
    Calcule l'énergie estimée pour une requête en Wh.
    """
    if energy_per_m is None or total_tokens is None:
        return "N/A"
    
    # Énergie (kWh) = (Tokens / 1,000,000) * Energy_per_M
    # Énergie (Wh) = Énergie (kWh) * 1000
    energy_wh = (total_tokens / 1_000_000) * energy_per_m * 1000
    return f"{energy_wh:.4f} Wh"

def main():
    parser = argparse.ArgumentParser(description="LLMaaS Status Dashboard")
    parser.add_argument("--models", type=str, help="Liste de modèles séparés par des virgules (optionnel)")
    args = parser.parse_args()

    console.print("[bold blue]LLMaaS - Tableau de Bord de Statut et Performance[/]")
    console.print(f"API URL: {STATUS_API_URL}\n")

    # 1. Récupération du statut global
    with console.status("[bold green]Récupération du statut global...[/]"):
        global_status = get_global_status()

    if not global_status:
        sys.exit(1)

    # Affichage du statut global
    status_color = "green" if global_status.get("status") == "operational" else "red"
    stats = global_status.get("stats", {})
    
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column(justify="right")
    grid.add_row(f"[bold]Statut:[/]", f"[{status_color}]{global_status.get('message', 'Inconnu')}[/]")
    grid.add_row(f"[bold]Dernière mise à jour:[/]", f"{global_status.get('updated_at', 'N/A')}")
    grid.add_row(f"[bold]Modèles opérationnels:[/]", f"{stats.get('operational_models', 0)} / {stats.get('total_models', 0)}")
    
    panel = Panel(grid, title=f"[{status_color}]Statut de la Plateforme[/]", border_style=status_color)
    console.print(panel)

    failed_models = global_status.get("failed_models", [])
    if failed_models:
        console.print(f"[bold red]Modèles en échec :[/] {', '.join(failed_models)}")

    # 2. Préparation de la liste des modèles à vérifier
    if args.models:
        models_to_check = [m.strip() for m in args.models.split(",")]
    else:
        # Par défaut, on utilise la liste connue dans notre map d'énergie
        # On trie pour un affichage cohérent
        models_to_check = sorted(list(MODEL_ENERGY_MAP.keys()))

    console.print("\n[bold]Analyse détaillée des modèles...[/]")

    # Création du tableau de résultats
    table = Table(title="Performance et Consommation Énergétique des Modèles")
    table.add_column("Modèle", style="cyan", no_wrap=True)
    table.add_column("État", justify="center")
    table.add_column("TTFB (ms)", justify="right")
    table.add_column("Vitesse (tok/s)", justify="right")
    table.add_column("Conso. (kWh/M)", justify="right") # Donnée statique
    table.add_column("Conso. Req. Test (Wh)", justify="right") # Donnée calculée

    # Itération sur les modèles avec barre de progression
    for model_id in track(models_to_check, description="Vérification des modèles..."):
        status_data = get_model_status(model_id)
        
        energy_per_m = MODEL_ENERGY_MAP.get(model_id)
        energy_str = f"{energy_per_m:.2f}" if energy_per_m is not None else "N/A"

        if status_data and status_data.get("ok"):
            # Modèle OK
            ok_symbol = "[green]✔[/]"
            ttfb = f"{status_data.get('ttfb_ms', 0)} ms"
            speed = f"{status_data.get('tokens_per_sec', 0):.1f}"
            
            # Calcul de l'énergie pour la requête de test effectuée par la sonde de statut
            usage = status_data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            req_energy = calculate_request_energy(total_tokens, energy_per_m)
            
            table.add_row(
                model_id,
                ok_symbol,
                ttfb,
                speed,
                energy_str,
                req_energy
            )
        else:
            # Modèle KO ou non trouvé
            err_msg = "[red]✖[/]"
            if status_data and not status_data.get("ok"):
                 err_msg += f" (HTTP {status_data.get('http_status')})"
            
            table.add_row(
                model_id,
                err_msg,
                "-",
                "-",
                energy_str,
                "-"
            )

    console.print(table)
    console.print("\n[italic dim]Note : La colonne 'Conso. (kWh/M)' indique la consommation énergétique estimée en kWh par million de tokens traités.[/]")
    console.print("[italic dim]La colonne 'Conso. Req. Test (Wh)' est une estimation basée sur la requête de sonde effectuée par l'API de statut.[/]")

if __name__ == "__main__":
    main()
