#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple pour redimensionner une image en utilisant les utilitaires existants.
"""

import sys
import argparse
from image_utils import optimize_image_for_analysis, get_image_info, MAX_RECOMMENDED_DIMENSION

def main():
    """
    Fonction principale du script.
    """
    parser = argparse.ArgumentParser(description="Optimise une image pour l'analyse.")
    parser.add_argument("image_path", help="Chemin vers le fichier image à optimiser.")
    parser.add_argument("--max-dim", type=int, default=MAX_RECOMMENDED_DIMENSION,
                        help=f"Dimension maximale (largeur ou hauteur) pour le redimensionnement. Défaut: {MAX_RECOMMENDED_DIMENSION}px.")
    parser.add_argument("--quality", type=int, default=85,
                        help="Qualité de compression JPEG (1-100). Défaut: 85.")

    args = parser.parse_args()

    print("--- Informations sur l'image originale ---")
    info = get_image_info(args.image_path)
    if not info:
        sys.exit(1)
    
    file_size_mb = info.get('file_size', 0) / (1024 * 1024)
    print(f"Chemin: {info.get('filename')}")
    print(f"Dimensions: {info.get('width')}x{info.get('height')}")
    print(f"Taille du fichier: {file_size_mb:.2f} MB")
    print("----------------------------------------\n")

    print(f"Tentative d'optimisation de l'image avec une dimension maximale de {args.max_dim}px et une qualité de {args.quality}...")
    
    optimized_path = optimize_image_for_analysis(
        image_path=args.image_path,
        max_dimension=args.max_dim,
        quality=args.quality
    )
    
    if optimized_path:
        print("\nOpération terminée.")
        if optimized_path != args.image_path:
            print(f"L'image optimisée a été sauvegardée ici : {optimized_path}")
        else:
            print("L'image n'a pas nécessité d'optimisation (elle respectait déjà les critères).")
    else:
        print("\nL'optimisation a échoué. Veuillez vérifier les messages d'erreur ci-dessus.")

if __name__ == '__main__':
    main()
