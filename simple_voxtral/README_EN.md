# 🎤 Voxtral Live — Real-Time Audio Transcription + Translation

Demonstration tool for **Voxtral** (`mistralai/Voxtral-Mini-4B-Realtime-2602`), the real-time audio transcription (ASR) model on the LLMaaS platform.

**Features:**
- 📝 **Real-time transcription** via WebSocket (word-by-word streaming)
- 🌍 **Live translation** to 26 languages (via TranslateGemma, in parallel with transcription)
- 🔊 **Synchronized audio playback** (optional, audio starts at the first transcribed word)
- 📊 **Side-by-side display** with Rich panels (Transcription | Translation)

## Voxtral vs Whisper: What's the Difference?

| Feature         | Whisper (Batch)                  | Voxtral (Realtime)          |
| --------------- | -------------------------------- | --------------------------- |
| **Endpoint**    | `POST /v1/audio/transcriptions`  | WebSocket `/v1/realtime`    |
| **Protocol**    | Classic HTTP REST                | Bidirectional WebSocket     |
| **Latency**     | Response after full processing   | Word-by-word streaming      |
| **Use case**    | Complete audio files             | Live transcription          |

## Prerequisites

### System
- **Python 3.9+**
- **ffmpeg** installed on the system:
  ```bash
  # macOS
  brew install ffmpeg

  # Linux (Debian/Ubuntu)
  sudo apt install ffmpeg
  ```

### Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies include: `websockets` (WebSocket client), `pydub` (audio conversion), `httpx` (streaming translation), `rich` (console display), `python-dotenv` (configuration).

## Configuration

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API key:
   ```
   API_KEY="your_api_key_here"
   ```

## Usage

### Transcription only
```bash
python voxtral_demo.py my_file.mp3
```

### Transcription + Live translation
```bash
# Translate to English in real time
python voxtral_demo.py audio.mp3 -t en

# Translate to German
python voxtral_demo.py audio.mp3 -t de

# Translate to Spanish with a specific model
python voxtral_demo.py audio.mp3 -t es --translate-model translategemma:27b
```

### With synchronized audio playback
```bash
# Transcribe + translate + listen to audio simultaneously
python voxtral_demo.py audio.mp3 -t en --play
```

### Other options
```bash
# Save the result (transcription + translation) to a file
python voxtral_demo.py audio.mp3 -t en -o result.txt

# Debug mode
python voxtral_demo.py audio.mp3 --debug

# Specify the API key on the command line
python voxtral_demo.py audio.mp3 --api-key MY_API_KEY
```

## CLI Options

| Option                 | Description                                                | Default                                   |
| ---------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| `audio`                | Audio file to transcribe                                   | *(required)*                              |
| `-m, --model`          | Voxtral model (ASR)                                        | `mistralai/Voxtral-Mini-4B-Realtime-2602` |
| `-t, --translate LANG` | Translate to a language (e.g., `en`, `de`, `es`, `ja`...)  | *(disabled)*                              |
| `--translate-model`    | Translation model                                          | `translategemma:12b`                       |
| `--source-lang`        | Source language (auto-detected if absent)                   | *(auto)*                                  |
| `-p, --play`           | Play audio alongside the transcription                     | *(disabled)*                              |
| `-o, --output`         | Output text file                                           | *(none)*                                  |
| `--api-url`            | API URL                                                    | `https://api.ai.cloud-temple.com`         |
| `--api-key`            | API Bearer key                                             | from `.env`                               |
| `--chunk-size`         | Audio chunk size (bytes)                                   | `4096`                                    |
| `--debug`              | Display raw WebSocket messages                             | *(disabled)*                              |

### Supported Translation Languages

`en` English, `fr` French, `de` German, `es` Spanish, `it` Italian, `pt` Portuguese, `nl` Dutch, `pl` Polish, `ru` Russian, `zh` Chinese, `ja` Japanese, `ko` Korean, `ar` Arabic, `tr` Turkish, `uk` Ukrainian, `vi` Vietnamese, `th` Thai, `hi` Hindi, `sv` Swedish, `da` Danish, `no` Norwegian, `fi` Finnish, `cs` Czech, `ro` Romanian, `hu` Hungarian, `el` Greek, `he` Hebrew.

## WebSocket Protocol

The script implements the following protocol:

```
Client                              Server (Voxtral)
  │                                      │
  │──── WebSocket Connection ───────────>│
  │<──── session.created ────────────────│
  │                                      │
  │──── session.update (model) ─────────>│
  │──── input_audio_buffer.commit ──────>│
  │                                      │
  │──── input_audio_buffer.append ──────>│  ─┐
  │──── input_audio_buffer.append ──────>│   │ Sending audio
  │──── input_audio_buffer.append ──────>│   │ chunk by chunk
  │──── ...                     ────────>│  ─┘
  │                                      │
  │──── input_audio_buffer.commit ──────>│  (final=True)
  │      (final=True)                    │
  │                                      │
  │<──── transcription.delta ────────────│  ─┐
  │<──── transcription.delta ────────────│   │ Streaming
  │<──── transcription.delta ────────────│   │ word by word
  │<──── ...                 ────────────│  ─┘
  │                                      │
  │<──── transcription.done  ────────────│  (with usage)
  │                                      │
  │──── Close ──────────────────────────>│
```

In parallel, each sentence boundary detected in the transcription triggers a streaming translation (if `-t` is enabled) via the `/v1/chat/completions` API with the TranslateGemma model.

## Audio Format

Audio is automatically converted by the script to:
- **Sample rate**: 16 kHz
- **Channels**: Mono
- **Format**: PCM 16-bit (signed, little-endian)
- **Encoding**: Base64 for WebSocket transmission

Supported input formats include: MP3, WAV, OGG, FLAC, M4A, AAC, and any format supported by ffmpeg.

## 📸 Preview

![Voxtral Live Demo](../screenshoot/voxtral.png)
*Real-time transcription via WebSocket with live side-by-side translation*

## Output Example

Here is a real execution example with English translation and audio playback:

```bash
python voxtral_demo.py ../whisper/french.mp3 -t en --play
```

The interface is divided into several zones displayed in the terminal:

### 1. Header and configuration

```
╭───────────────────────────────────────────────────╮
│ Voxtral Live                                      │
│ Transcription + Traduction English en temps réel  │
╰───────────────────────────────────────────────────╯

Configuration :
 • Audio     : ../whisper/french.mp3
 • ASR       : mistralai/Voxtral-Mini-4B-Realtime-2602
 • API       : https://api.ai.cloud-temple.com
 • Traduc.   : → English via translategemma:12b
 • Lecture   : 🔊 activée
```

### 2. Connection and sending

```
Audio : ../whisper/french.mp3 (28.0s)
WebSocket : wss://api.ai.cloud-temple.com/v1/realtime
✓ Session sess-bacf3c3e05ad101c
Envoi audio (219 chunks)...
Audio envoyé. Transcription en cours...
```

### 3. Side-by-side panels (real-time)

The core of the display: two Rich panels update continuously.
- **📝 Transcription** (cyan border, left): transcribed text appears word by word
- **🌍 Translation** (green border, right): translation arrives sentence by sentence, in parallel

```
╭──────────── 📝 Transcription ──────────────────╮╭─────────────── 🌍 English ────────────────────╮
│                                                ││                                               │
│  Bonjour, je m'appelle Amélie, j'ai 36 ans.   ││  Hello, my name is Amélie, and I am 36 years  │
│  J'ai les cheveux courts, châtains, mes yeux   ││  old. I have short, brown hair, and my eyes    │
│  sont marrons. J'ai un fils de 4 ans qui a     ││  are brown. I have a 4-year-old son who has    │
│  les mêmes cheveux que moi, mais lui les a     ││  the same hair color as me, but his hair is    │
│  bouclés. Il a un petit nez épaté. Je vis en   ││  curly. He has a small, surprised-looking      │
│  région parisienne, dans le Val d'Oise.        ││  nose. I live in the Paris region, in the Val  │
│  J'apprécie vraiment cette région qui se situe ││  d'Oise department. I really appreciate this   │
│  entre nature et ville. Mes passe-temps, la    ││  region, which offers a unique blend of nature │
│  nature, me promener, la photographie, aussi   ││  and urban life. My hobbies include nature,    │
│  bien de ville que de campagne, et puis        ││  walking, and photography, both of urban and   │
│  voyager, parce que ça ouvre l'esprit et qu'on ││  rural landscapes. I also enjoy traveling, as  │
│  rencontre des gens.                           ││  it broadens the mind and allows you to meet   │
│                                                ││  new people.                                   │
│                                                ││                                               │
╰────────────────────────────────────────────────╯╰───────────────────────────────────────────────╯
```

### 4. Final result

Once transcription and all translations are complete:

```
                    Résultat Final
┌──────────────────┬───────────────────────────────────────────────────┐
│ 📝 Transcription │ Bonjour, je m'appelle Amélie, j'ai 36 ans. J'ai │
│                  │ les cheveux courts, châtains, mes yeux sont...   │
│ 🌍 Traduction    │ Hello, my name is Amélie, and I am 36 years     │
│                  │ old. I have short, brown hair, and my eyes...    │
│ ⏱ Durée          │ 14.52s                                          │
│ Tokens           │ prompt=1234 completion=56                        │
└──────────────────┴───────────────────────────────────────────────────┘
```

## Model Aliases

You can use the aliases configured on the platform:

```bash
# Full name
python voxtral_demo.py audio.mp3 -m "mistralai/Voxtral-Mini-4B-Realtime-2602"

# Aliases
python voxtral_demo.py audio.mp3 -m "voxtral"
python voxtral_demo.py audio.mp3 -m "asr-realtime"
```
