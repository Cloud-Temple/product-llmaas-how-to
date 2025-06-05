#!/bin/bash

# Script pour installer les dépendances et lancer l'interface de transcription Cloud Temple
# Auteur: Cloud Temple
# Date: 02/05/2025

set -e  # Arrête le script en cas d'erreur

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Vérification de Python
print_message "Vérification de l'installation Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Création d'un environnement virtuel (optionnel)
if [ ! -d "venv" ]; then
    print_message "Création d'un environnement virtuel Python..."
    python3 -m venv venv
    print_message "Environnement virtuel créé avec succès."
else
    print_message "Environnement virtuel existant détecté."
fi

# Activation de l'environnement virtuel
print_message "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installation des dépendances
print_message "Installation des dépendances requises..."
pip install -r requirements-cloud-temple.txt

# Vérification de l'existence du fichier audio de test
if [ ! -f "test_audio.wav" ]; then
    print_warning "Aucun fichier audio de test (test_audio.wav) n'a été trouvé."
    print_warning "Vous pouvez utiliser votre microphone pour les tests."
else
    print_message "Fichier audio de test détecté: test_audio.wav"
fi

# Lancement de l'interface
print_message "Lancement de l'interface de transcription Cloud Temple..."
print_message "Appuyez sur Ctrl+C pour arrêter l'application."
print_warning "N'oubliez pas d'entrer votre token d'authentification dans l'interface."

# Exécution du script Python
python3 gradio-cloud-temple.py

# Désactivation de l'environnement virtuel (ne sera jamais exécuté si le script Python est en cours d'exécution)
deactivate
