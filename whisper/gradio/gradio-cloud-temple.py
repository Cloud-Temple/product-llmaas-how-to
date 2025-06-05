"""
Script Gradio pour l'interface de transcription audio utilisant l'API Cloud Temple.
Ce script permet de transcrire de l'audio en texte via l'API api.ai.cloud-temple.com.
Il inclut un champ configurable pour le token d'authentification.
"""

import gradio as gr
import requests
import numpy as np
from pydub import AudioSegment
import io
import queue
import json
import time
import os


class AudioProcessor:
    """
    Classe pour traiter les chunks audio et les envoyer à l'API Cloud Temple.

    Exemple d'utilisation de l'API avec curl:
    curl -X 'POST' 'https://api.ai.cloud-temple.com/v1/audio/transcriptions'
    -H 'Authorization: Bearer TOKEN'
    -F 'file=@test_audio.wav;type=audio/x-wav'
    -H 'accept: application/json'
    -H 'Content-Type: multipart/form-data'
    -F 'language=fr'
    -F 'response_format=json'
    -F 'temperature=0'
    """

    def __init__(self, server_url="https://api.ai.cloud-temple.com/v1/audio/transcriptions", token=""):
        self.server_url = server_url
        self.token = token
        self.audio_queue = queue.Queue()
        self.is_processing = False
        self.current_text = ""

    def set_token(self, token):
        """Met à jour le token d'authentification."""
        self.token = token
        return f"Token mis à jour: {token[:5]}..." if token else "Token supprimé"

    def process_audio_chunk(self, audio_chunk, sample_rate, language="fr"):
        """Traite un chunk audio et l'envoie à l'API pour transcription."""
        # Préparation du fichier audio
        byte_io = io.BytesIO()
        audio_segment = AudioSegment(audio_chunk.tobytes(), frame_rate=sample_rate * 2, sample_width=2, channels=1)  # Ajustement du taux d'échantillonnage

        # Export au format WAV
        audio_segment.export(byte_io, format="wav")

        # Préparation des données pour l'API
        files = {"file": ("chunk.wav", byte_io.getvalue(), "audio/x-wav")}
        data = {"language": language, "response_format": "json", "temperature": "0"}

        # Ajout du header d'authentification si un token est fourni
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Envoi de la requête à l'API
        try:
            response = requests.post(self.server_url, files=files, data=data, headers=headers)

            # Traitement de la réponse
            if response.status_code == 200:
                result = response.json()
                if "text" in result:
                    return result["text"], 0, 0  # Retourne le texte sans les probabilités
                return result.get("text", "Aucun texte détecté"), 0, 0
            elif response.status_code == 401:
                return "Erreur d'authentification. Vérifiez votre token.", 0, 1
            else:
                return f"Erreur API (code {response.status_code}): {response.text}", 0, 1
        except Exception as e:
            return f"Erreur de connexion: {str(e)}", 0, 1


# Initialisation du processeur audio
processor = AudioProcessor()

# Variables globales pour stocker les chunks audio et l'historique des transcriptions
arrays = []
history = []


def update_token(token):
    """Met à jour le token d'authentification du processeur audio."""
    return processor.set_token(token)


def process_audio(audio, token) -> str:
    """
    Traite l'audio capturé et le transcrit via l'API.

    Args:
        audio: Tuple contenant le taux d'échantillonnage et les données audio
        token: Token d'authentification pour l'API

    Returns:
        str: Texte transcrit
    """
    global arrays
    global history

    # Mise à jour du token si nécessaire
    if token != processor.token:
        processor.set_token(token)

    # Si aucun audio n'est fourni, retourne l'état actuel
    if len(audio) == 0:
        return " ".join(history) if history else ""

    # Extraction des données audio
    sample_rate, one_chunk = audio
    arrays.append(np.array(one_chunk))

    # Mesure du temps de traitement
    t0 = time.time()

    # Concaténation de tous les chunks pour une meilleure transcription
    all_chunks = np.concatenate(arrays)

    # Envoi à l'API pour transcription
    text, _, no_speech = processor.process_audio_chunk(all_chunks, sample_rate)

    t1 = time.time()
    processing_time = t1 - t0
    print(f"Temps de traitement: {processing_time:.2f}s, Temps/échantillon: {processing_time/len(all_chunks):.6f}s")

    # Si le texte semble être une erreur d'authentification, on le signale
    if "Erreur d'authentification" in text:
        return text

    # Gestion de l'historique des transcriptions
    if "Erreur" not in text and text.strip():
        arrays = []  # Réinitialisation des chunks après une transcription réussie
        history.append(text)

    # Limitation de la taille des chunks stockés
    if len(arrays) >= 10:
        arrays.pop(0)  # Suppression du chunk le plus ancien

    # Retour de l'historique concaténé
    if len(history) > 1:
        out = " ".join(history)
        history = [out]  # Simplification de l'historique
        return out
    elif len(history) == 0:
        return ""
    else:
        return history[0]


# Interface Gradio
with gr.Blocks(title="Transcription Audio Cloud Temple") as demo:
    gr.Markdown("# Transcription Audio via Cloud Temple API")
    gr.Markdown("Cet outil permet de transcrire de l'audio en texte via l'API Cloud Temple.")

    with gr.Row():
        with gr.Column(scale=3):
            token_input = gr.Textbox(label="Token d'authentification", placeholder="Entrez votre token API Cloud Temple ici", type="password")
            token_button = gr.Button("Mettre à jour le token")
            token_status = gr.Textbox(label="Statut du token", interactive=False)

    with gr.Row():
        with gr.Column(scale=2):
            audio_input = gr.Audio(sources=["microphone"], streaming=True, label="Entrée audio")
        with gr.Column(scale=3):
            text_output = gr.Textbox(label="Texte transcrit", placeholder="La transcription apparaîtra ici...", lines=10)

    # Connexion des composants
    token_button.click(update_token, inputs=[token_input], outputs=[token_status])

    audio_input.stream(process_audio, inputs=[audio_input, token_input], outputs=[text_output])

    gr.Markdown(
        """
    ## Instructions
    1. Entrez votre token d'authentification Cloud Temple et cliquez sur "Mettre à jour le token"
    2. Cliquez sur le microphone pour commencer l'enregistrement
    3. Parlez clairement dans votre microphone
    4. La transcription apparaîtra automatiquement dans la zone de texte
    
    ## Notes
    - La transcription est optimisée pour le français
    - Pour de meilleurs résultats, parlez clairement et dans un environnement calme
    - Si vous rencontrez des erreurs d'authentification, vérifiez votre token
    """
    )


# Démarrage de l'application
if __name__ == "__main__":
    print("Démarrage de l'interface Gradio pour la transcription audio...")
    demo.queue()
    demo.launch(share=True)  # share=True permet de générer un lien public temporaire
