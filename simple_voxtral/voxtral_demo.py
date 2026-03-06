#!/usr/bin/env python3
"""
Voxtral Live — Transcription + Traduction audio en temps réel.
===============================================================

Transcrit un fichier audio via WebSocket (Voxtral) et traduit en direct,
avec affichage côte à côte et lecture audio optionnelle.

Usage :
    python voxtral_demo.py audio.mp3                          # Transcription seule
    python voxtral_demo.py audio.mp3 -t en                    # + Traduction live EN
    python voxtral_demo.py audio.mp3 -t en --play             # + Lecture audio en //
    python voxtral_demo.py audio.mp3 -t de --translate-model translategemma:12b
"""

import os
import sys
import time
import argparse
import asyncio
import base64
import json
import ssl
import subprocess
import platform
import re

# --- Dépendances ---
try:
    import websockets
    import httpx
    from pydub import AudioSegment
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.columns import Columns
    from rich.live import Live
    from rich.text import Text
    from rich import print as rprint
except ImportError as e:
    print(f"Erreur : Dépendance manquante ({e}).")
    print("Installez avec : pip install -r requirements.txt")
    sys.exit(1)

load_dotenv()

# --- Configuration ---
DEFAULT_API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com")
DEFAULT_API_KEY = os.getenv("API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "mistralai/Voxtral-Mini-4B-Realtime-2602")
DEFAULT_TRANSLATE_MODEL = os.getenv("TRANSLATE_MODEL", "translategemma:12b")

console = Console()

LANGUAGE_MAP = {
    "en": ("English", "en"), "fr": ("French", "fr"), "de": ("German", "de"),
    "es": ("Spanish", "es"), "it": ("Italian", "it"), "pt": ("Portuguese", "pt"),
    "nl": ("Dutch", "nl"), "pl": ("Polish", "pl"), "ru": ("Russian", "ru"),
    "zh": ("Chinese", "zh"), "ja": ("Japanese", "ja"), "ko": ("Korean", "ko"),
    "ar": ("Arabic", "ar"), "tr": ("Turkish", "tr"), "uk": ("Ukrainian", "uk"),
    "vi": ("Vietnamese", "vi"), "th": ("Thai", "th"), "hi": ("Hindi", "hi"),
    "sv": ("Swedish", "sv"), "da": ("Danish", "da"), "no": ("Norwegian", "no"),
    "fi": ("Finnish", "fi"), "cs": ("Czech", "cs"), "ro": ("Romanian", "ro"),
    "hu": ("Hungarian", "hu"), "el": ("Greek", "el"), "he": ("Hebrew", "he"),
}


# =============================================================================
# UTILITAIRES
# =============================================================================

def audio_to_pcm16_bytes(audio_path: str) -> bytes:
    """Charge et convertit un fichier audio en PCM16 16kHz mono."""
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    return audio.raw_data


def get_audio_duration(audio_path: str) -> float:
    """Retourne la durée d'un fichier audio en secondes."""
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0


def play_audio_background(audio_path: str) -> subprocess.Popen:
    """Lance la lecture audio en arrière-plan. Retourne le processus."""
    system = platform.system()
    if system == "Darwin":
        return subprocess.Popen(["afplay", audio_path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif system == "Linux":
        for player in ["ffplay", "mpg123", "aplay"]:
            try:
                args = [player, audio_path]
                if player == "ffplay":
                    args.extend(["-nodisp", "-autoexit", "-loglevel", "quiet"])
                return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                continue
    return None


def detect_source_language(text: str) -> tuple:
    """Détecte la langue source (heuristique)."""
    if any(c in text.lower() for c in ["é", "è", "ê", "à", "ù", "ç", "œ", "î", "ô"]):
        return ("French", "fr")
    return ("French", "fr")


def build_translate_prompt(text, src_lang, src_code, tgt_lang, tgt_code):
    """Prompt TranslateGemma."""
    return f"""You are a professional {src_lang} ({src_code}) to {tgt_lang} ({tgt_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {src_lang} text while adhering to {tgt_lang} grammar, vocabulary, and cultural sensitivities.
Produce only the {tgt_lang} translation, without any additional explanations or commentary. Please translate the following {src_lang} text into {tgt_lang}:


{text}"""


def is_sentence_boundary(text: str) -> bool:
    """Détecte si le texte se termine par une fin de phrase."""
    stripped = text.rstrip()
    return bool(stripped) and stripped[-1] in ".!?;:"


def build_display(transcription_text: str, translation_text: str,
                  target_lang: str = None, status: str = "") -> Columns:
    """Construit l'affichage côte à côte avec deux panneaux Rich."""
    left_content = Text(transcription_text if transcription_text else "En attente...",
                        style="white" if transcription_text else "dim")
    left_panel = Panel(left_content, title="📝 Transcription", border_style="cyan",
                       width=console.width // 2 - 1, height=min(20, console.height - 6))

    if target_lang:
        tgt_name = LANGUAGE_MAP.get(target_lang, (target_lang,))[0]
        right_content = Text(translation_text if translation_text else "En attente...",
                             style="white" if translation_text else "dim")
        right_panel = Panel(right_content, title=f"🌍 {tgt_name}", border_style="green",
                            width=console.width // 2 - 1, height=min(20, console.height - 6))
    else:
        right_panel = Panel(Text("Mode traduction désactivé\nUtilisez --translate <lang>", style="dim"),
                            title="🌍 Traduction", border_style="dim",
                            width=console.width // 2 - 1, height=min(20, console.height - 6))

    return Columns([left_panel, right_panel], expand=True)


def parse_args():
    """Arguments CLI."""
    p = argparse.ArgumentParser(
        description="Voxtral Live — Transcription + Traduction temps réel",
        epilog="Exemples :\n"
               "  python voxtral_demo.py audio.mp3 -t en\n"
               "  python voxtral_demo.py audio.mp3 -t en --play\n"
               "  python voxtral_demo.py audio.mp3 -t de --translate-model translategemma:12b",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("audio", nargs="?", help="Fichier audio à transcrire")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Modèle Voxtral")
    p.add_argument("-o", "--output", help="Fichier de sortie")
    p.add_argument("--api-url", default=DEFAULT_API_URL, help="URL API")
    p.add_argument("--api-key", default=DEFAULT_API_KEY, help="Clé API")
    p.add_argument("--chunk-size", type=int, default=4096, help="Taille chunks audio")
    p.add_argument("--debug", action="store_true", help="Mode debug")
    p.add_argument("-t", "--translate", metavar="LANG", help="Traduire vers (en, de, es...)")
    p.add_argument("--translate-model", default=DEFAULT_TRANSLATE_MODEL, help="Modèle traduction")
    p.add_argument("--source-lang", default=None, help="Langue source (auto si absent)")
    p.add_argument("-p", "--play", action="store_true", help="Jouer l'audio en parallèle")
    return p.parse_args()


# =============================================================================
# TRADUCTION STREAMING (chunk par chunk)
# =============================================================================

async def translate_chunk_streaming(
    text: str,
    api_url: str,
    api_key: str,
    model: str,
    source_lang: tuple,
    target_lang: tuple,
) -> str:
    """Traduit un chunk de texte via streaming et retourne le résultat."""
    base = api_url.rstrip("/")
    url = f"{base}/v1/chat/completions" if not base.endswith("/v1") else f"{base}/chat/completions"

    prompt = build_translate_prompt(text, source_lang[0], source_lang[1],
                                    target_lang[0], target_lang[1])
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 2048,
        "stream": True,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    parts = []
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                return f"[Erreur {resp.status_code}]"
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        parts.append(delta)
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass
    return "".join(parts).strip()


# =============================================================================
# PIPELINE PRINCIPAL : TRANSCRIPTION + TRADUCTION LIVE
# =============================================================================

async def run_live_pipeline(
    audio_path: str,
    api_url: str,
    api_key: str,
    model: str,
    chunk_size: int = 4096,
    debug: bool = False,
    translate_to: str = None,
    translate_model: str = None,
    source_lang_override: str = None,
    play_audio: bool = False,
) -> dict:
    """Pipeline complet : transcription WebSocket + traduction chunk par chunk + affichage live."""

    # --- URL WebSocket ---
    base = api_url.rstrip("/")
    if base.startswith("https://"):
        ws_url = base.replace("https://", "wss://", 1) + "/v1/realtime"
    elif base.startswith("http://"):
        ws_url = base.replace("http://", "ws://", 1) + "/v1/realtime"
    else:
        ws_url = f"wss://{base}/v1/realtime"

    # --- Audio ---
    duration_audio = get_audio_duration(audio_path)
    console.print(f"[dim]Audio : {audio_path} ({duration_audio:.1f}s)[/]")
    pcm_bytes = audio_to_pcm16_bytes(audio_path)
    total_chunks = (len(pcm_bytes) + chunk_size - 1) // chunk_size
    console.print(f"[dim]WebSocket : {ws_url}[/]")

    # --- SSL ---
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    # --- Résolution langues pour traduction ---
    src_lang = None
    tgt_lang = None
    if translate_to:
        tgt_lang = LANGUAGE_MAP.get(translate_to, (translate_to.capitalize(), translate_to))
        if source_lang_override and source_lang_override in LANGUAGE_MAP:
            src_lang = LANGUAGE_MAP[source_lang_override]

    # --- Connexion WebSocket ---
    ws_headers = {}
    if api_key:
        ws_headers["Authorization"] = f"Bearer {api_key}"

    try:
        ws = await websockets.connect(ws_url, additional_headers=ws_headers, ssl=ssl_ctx)
    except websockets.exceptions.InvalidStatus as e:
        if "404" in str(e):
            console.print("[bold red]Erreur 404[/] — Endpoint /v1/realtime non disponible.")
            console.print("[dim]Essayez : --api-url https://preprod.api.ai.cloud-temple.com[/]")
        elif "401" in str(e) or "403" in str(e):
            console.print("[bold red]Erreur 401[/] — Clé API invalide pour cet environnement.")
        else:
            console.print(f"[bold red]Erreur WebSocket : {e}[/]")
        return {"text": "", "translation": "", "duration_sec": 0}
    except Exception as e:
        console.print(f"[bold red]Erreur connexion : {e}[/]")
        return {"text": "", "translation": "", "duration_sec": 0}

    # --- État mutable pour le Live display ---
    transcription_buf = []  # Liste de mots/fragments reçus
    translation_buf = []    # Liste de phrases traduites
    pending_chunk = []       # Mots en attente de traduction
    translation_tasks = []   # Tâches async en cours

    start_time = time.time()
    usage_info = None
    audio_process = None
    audio_started = False  # Flag pour lancer l'audio au 1er delta non-vide

    async with ws:
        # Handshake
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("type") != "session.created":
            console.print(f"[red]Réponse inattendue : {msg}[/]")
            return {"text": "", "translation": "", "duration_sec": 0}

        console.print(f"[green]✓ Session {msg.get('id', '?')}[/]")

        await ws.send(json.dumps({"type": "session.update", "model": model}))
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

        # Envoi audio
        console.print(f"[cyan]Envoi audio ({total_chunks} chunks)...[/]")
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i : i + chunk_size]
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode("utf-8"),
            }))

        await ws.send(json.dumps({"type": "input_audio_buffer.commit", "final": True}))
        console.print("[cyan]Audio envoyé. Transcription en cours...[/]\n")

        # --- Boucle de réception avec Live display ---
        with Live(build_display("", "", translate_to), console=console, refresh_per_second=8) as live:

            async def fire_translation(text_to_translate: str):
                """Lance une traduction async et ajoute le résultat au buffer."""
                nonlocal src_lang
                if not src_lang:
                    src_lang = detect_source_language(text_to_translate)
                translated = await translate_chunk_streaming(
                    text_to_translate, api_url, api_key,
                    translate_model, src_lang, tgt_lang,
                )
                if translated:
                    translation_buf.append(translated)
                    live.update(build_display(
                        "".join(transcription_buf),
                        " ".join(translation_buf),
                        translate_to,
                    ))

            try:
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    msg_type = msg.get("type", "")

                    if msg_type == "transcription.delta":
                        delta = msg.get("delta", "")
                        if delta:
                            # Lancer l'audio au premier mot transcrit (meilleure sync)
                            if play_audio and not audio_started and delta.strip():
                                audio_process = play_audio_background(audio_path)
                                audio_started = True

                            transcription_buf.append(delta)
                            pending_chunk.append(delta)

                            # Mise à jour du panneau gauche
                            live.update(build_display(
                                "".join(transcription_buf),
                                " ".join(translation_buf),
                                translate_to,
                            ))

                            # Déclenchement traduction sur fin de phrase
                            if translate_to and is_sentence_boundary("".join(pending_chunk)):
                                chunk_text = "".join(pending_chunk).strip()
                                pending_chunk.clear()
                                if chunk_text:
                                    task = asyncio.create_task(fire_translation(chunk_text))
                                    translation_tasks.append(task)

                    elif msg_type == "transcription.done":
                        if msg.get("usage"):
                            usage_info = msg["usage"]

                            # Traduire le reste en attente
                            if translate_to and pending_chunk:
                                chunk_text = "".join(pending_chunk).strip()
                                pending_chunk.clear()
                                if chunk_text:
                                    task = asyncio.create_task(fire_translation(chunk_text))
                                    translation_tasks.append(task)

                            # Attendre toutes les traductions en cours
                            if translation_tasks:
                                await asyncio.gather(*translation_tasks, return_exceptions=True)
                                live.update(build_display(
                                    "".join(transcription_buf),
                                    " ".join(translation_buf),
                                    translate_to,
                                ))
                            break

                    elif msg_type == "error":
                        console.print(f"\n[red]Erreur : {msg.get('error', msg)}[/]")
                        break

            except websockets.exceptions.ConnectionClosed:
                pass

    # Attendre la fin de la lecture audio (ne pas couper le son)
    if audio_process:
        console.print("[dim]🔊 En attente de la fin de la lecture audio...[/]")
        audio_process.wait()

    duration_sec = time.time() - start_time
    full_text = "".join(transcription_buf).strip()
    full_translation = " ".join(translation_buf).strip()

    return {
        "text": full_text,
        "translation": full_translation,
        "usage": usage_info,
        "duration_sec": duration_sec,
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = parse_args()

    # Titre
    title = "[bold cyan]Voxtral Live[/bold cyan]\n"
    if args.translate:
        tgt = LANGUAGE_MAP.get(args.translate, (args.translate,))[0]
        title += f"[italic]Transcription + Traduction {tgt} en temps réel[/italic]"
    else:
        title += "[italic]Transcription audio temps réel via WebSocket[/italic]"
    rprint(Panel.fit(title))

    # Validations
    if not args.api_key:
        console.print("[bold red]Erreur :[/] Clé API manquante (--api-key ou .env)")
        sys.exit(1)
    if not args.audio:
        console.print("[bold red]Erreur :[/] Aucun fichier audio.")
        console.print("Usage : python voxtral_demo.py [bold]audio.mp3[/] [-t en] [--play]")
        sys.exit(1)
    if not os.path.isfile(args.audio):
        console.print(f"[bold red]Erreur :[/] Fichier introuvable : {args.audio}")
        sys.exit(1)

    # Résumé
    console.print(f"\n[bold]Configuration :[/]")
    console.print(f" • [cyan]Audio     :[/] {args.audio}")
    console.print(f" • [cyan]ASR       :[/] {args.model}")
    console.print(f" • [cyan]API       :[/] {args.api_url}")
    if args.translate:
        tgt = LANGUAGE_MAP.get(args.translate, (args.translate, args.translate))
        console.print(f" • [cyan]Traduc.   :[/] → {tgt[0]} via {args.translate_model}")
    if args.play:
        console.print(f" • [cyan]Lecture   :[/] 🔊 activée")
    console.print()

    # Lancement pipeline
    result = asyncio.run(run_live_pipeline(
        audio_path=args.audio,
        api_url=args.api_url,
        api_key=args.api_key,
        model=args.model,
        chunk_size=args.chunk_size,
        debug=args.debug,
        translate_to=args.translate,
        translate_model=args.translate_model,
        source_lang_override=args.source_lang,
        play_audio=args.play,
    ))

    # Résultat final
    if result["text"]:
        console.print()
        table = Table(title="Résultat Final", show_header=False, border_style="green")
        table.add_column("", style="cyan", width=18)
        table.add_column("", style="white")
        table.add_row("📝 Transcription", result["text"][:500] + ("..." if len(result["text"]) > 500 else ""))
        if result.get("translation"):
            table.add_row("🌍 Traduction", result["translation"][:500] + ("..." if len(result["translation"]) > 500 else ""))
        table.add_row("⏱ Durée", f"{result['duration_sec']:.2f}s")
        if result.get("usage"):
            u = result["usage"]
            table.add_row("Tokens", f"prompt={u.get('prompt_tokens','?')} completion={u.get('completion_tokens','?')}")
        console.print(table)

        # Sauvegarde
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("=== TRANSCRIPTION ===\n" + result["text"] + "\n")
                if result.get("translation"):
                    f.write(f"\n=== TRADUCTION ({args.translate}) ===\n" + result["translation"] + "\n")
            console.print(f"\n[green]✓ Sauvegardé : {args.output}[/]")
    else:
        console.print("[yellow]Aucune transcription reçue.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
