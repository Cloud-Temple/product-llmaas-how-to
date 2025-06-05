# Advanced Audio Transcription Example with Cloud Temple LLMaaS API

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

This directory contains an advanced Python script (`transcribe_audio.py`) for transcribing audio files using the **Cloud Temple LLMaaS Transcription API**. It includes many advanced features and example audio files in different languages.

## ✨ New Features v2.0

- **🐛 Debug mode**: Detailed display of payloads, requests, and responses with colored JSON formatting
- **💡 Prompt support**: Ability to provide a prompt to guide Whisper transcription
- **🔍 Wildcard support**: Processing of multiple files with patterns (e.g., `*.mp3`, `audio/*.m4a`)
- **🎵 M4A support**: Added support for M4A and other popular audio formats
- **📊 Statistics**: Detailed summary of successes/errors for batch processing
- **🎨 Improved interface**: Colored and formatted display with progress indicators

## 📁 Included Files

- `transcribe_audio.py`: The main Python script (v2.0) with all new features
- `config.json`: Configuration file for API URL, token, and default language
- `french.mp3`: An example audio file in French
- `english.mp3`: An example audio file in English
- `deutch.mp3`: An example audio file in German
- `spanish.mp3`: An example audio file in Spanish

## 🎯 Supported Audio Formats

The script now supports several audio formats:

| Format | Extension | MIME Type     |
| ------ | --------- | ------------- |
| WAV    | `.wav`    | `audio/x-wav` |
| MP3    | `.mp3`    | `audio/mpeg`  |
| M4A    | `.m4a`    | `audio/mp4`   |
| FLAC   | `.flac`   | `audio/flac`  |
| OGG    | `.ogg`    | `audio/ogg`   |
| WebM   | `.webm`   | `audio/webm`  |

## 🚀 Prerequisites

- Python 3.7+
- The `requests` library

## ⚙️ Initial Configuration

1.  **Copy example audio files** to this directory if you haven't already.

2.  **Configure your API token**:
    Open the `config.json` file and replace `"YOUR_BEARER_TOKEN_HERE"` with your actual Cloud Temple authentication token.
    ```json
    {
      "api_url": "https://api.ai.cloud-temple.com/v1/audio/transcriptions",
      "api_token": "YOUR_REAL_TOKEN_HERE",
      "default_language": "fr"
    }
    ```

## 📦 Installing Dependencies

```bash
# Navigate to the directory
cd examples/whisper/

# Create a virtual environment (recommended)
python3 -m venv venv_whisper_example

# Activate the virtual environment
# On macOS/Linux:
source venv_whisper_example/bin/activate
# On Windows:
# .\venv_whisper_example\Scripts\activate

# Install dependencies
pip install requests
```

## 🎮 Using Script v2.0

### Available Arguments

```bash
python transcribe_audio.py -h
```

**Main arguments:**

- `file_patterns` (required): File(s) or pattern(s) to transcribe (supports wildcards)
- `-l, --language`: Language code (e.g., `fr`, `en`, `de`, `es`)
- `-t, --token`: Bearer authentication token
- `--api-url`: Transcription API URL
- `-p, --prompt`: Prompt to guide transcription
- `--debug`: Activates debug mode with payload display

### 📝 Usage Examples

#### Basic Examples

```bash
# Transcribe a single file
python transcribe_audio.py french.mp3

# Transcribe with a specific language
python transcribe_audio.py english.mp3 -l en

# Transcribe with a custom token
python transcribe_audio.py deutch.mp3 -l de -t YOUR_PERSONAL_TOKEN
```

#### Examples with Wildcards

```bash
# Transcribe all MP3 files in the current directory
python transcribe_audio.py *.mp3 -l en

# Transcribe all audio files in a specific folder
python transcribe_audio.py audio/*.m4a

# Transcribe files with a specific pattern
python transcribe_audio.py "recording_*.wav" -l fr
```

#### Examples with Prompt

```bash
# Medical conference transcription
python transcribe_audio.py conference.mp3 --prompt "Medical conference on cardiology"

# Music file transcription
python transcribe_audio.py concert.m4a --prompt "Classical music concert"

# Technical transcription
python transcribe_audio.py meeting.wav --prompt "Technical meeting on artificial intelligence"
```

#### Examples with Debug Mode

```bash
# Debug on a single file
python transcribe_audio.py french.mp3 --debug

# Debug with prompt and wildcards
python transcribe_audio.py *.mp3 -l en --prompt "Interview" --debug

# Full debug
python transcribe_audio.py audio/*.m4a -l fr --prompt "Podcast" --debug -t MY_TOKEN
```

### 🎨 Expected Output

#### Normal Mode
```
[INFO] Using API URL: https://api.ai.cloud-temple.com/v1/audio/transcriptions
[INFO] Processing 1 audio file(s)...
[INFO] Sending file 'french.mp3' (245.6 KB) for transcription in language 'fr'...

============================================================
📄 Transcription [1/1] - 'french.mp3' (fr)
============================================================
Hello, this is a test of the audio transcription API.
============================================================

📊 FINAL SUMMARY
✅ Success: 1
📁 Total processed: 1 file(s)
```

#### Debug Mode
```
[DEBUG] Debug mode activated
[DEBUG] Configuration loaded from: /path/to/config.json
[DEBUG] API URL: https://api.ai.cloud-temple.com/v1/audio/transcriptions
[DEBUG] Language: fr
[DEBUG] Prompt: None

========== Headers ==========
{
  "Authorization": "Bearer G3H4I5J6K7L8M9N0O1P2...",
  "Accept": "application/json"
}
=============================

========== Request Data ==========
{
  "language": "fr",
  "response_format": "json",
  "temperature": "0"
}
===================================

[DEBUG] HTTP response code: 200
[DEBUG] Response headers: {'content-type': 'application/json', ...}

========== Response JSON ==========
{
  "text": "Hello, this is a test of the audio transcription API."
}
====================================
```

## 💡 Usage Tips

### Optimization with Prompts

The prompt helps guide Whisper to improve accuracy:

- **Specific context**: `"Team meeting on the LLMaaS project"`
- **Technical vocabulary**: `"Technical discussion on artificial intelligence"`
- **Proper nouns**: `"Interview with John Doe, Cloud Temple director"`
- **Medical domain**: `"Medical consultation in cardiology"`
- **Musical content**: `"Classical music concert, composer Mozart"`

### Using Wildcards

```bash
# All audio files in the directory
python transcribe_audio.py *.{mp3,wav,m4a}

# Files with a specific prefix
python transcribe_audio.py "meeting_*.mp3"

# In a subdirectory
python transcribe_audio.py "recordings/2025/*.wav"

# Multiple patterns
python transcribe_audio.py *.mp3 *.wav *.m4a
```

### Debug Mode

Debug mode displays:
- 📋 Loaded configuration
- 📤 Request payloads (headers, data, file info)
- 📥 Full API responses
- 🔧 Technical information (HTTP codes, MIME types, sizes)
- 🐛 Detailed error messages

## ⚠️ Important Notes

- **Token required**: A valid authentication token is mandatory.
- **Supported formats**: The script automatically detects the format and applies the correct MIME type.
- **File size**: The API may have size limits (generally up to 25MB).
- **Wildcards**: Use quotes for complex patterns: `"*.{mp3,wav}"`
- **Optimal prompt**: A short and descriptive prompt yields better results.

## 🔧 Troubleshooting

### Common Errors

1. **Invalid token (401)**: Check your token in `config.json`.
2. **File not found**: Check paths and patterns.
3. **Unsupported format**: The script will display a warning but will attempt transcription.
4. **No files found**: Check your wildcard patterns.

### Debug Mode for Diagnosis

Always use `--debug` to diagnose issues:

```bash
python transcribe_audio.py problematic_file.mp3 --debug
```

This will display all request and response details to identify the problem.

## 🔄 Version Comparison

| Feature | v1.0 | v2.0 |
|---|---|---|
| Single file | ✅ | ✅ |
| Wildcards | ❌ | ✅ |
| M4A, FLAC, etc. formats | ❌ | ✅ |
| Whisper prompt | ❌ | ✅ |
| Debug mode | ❌ | ✅ |
| Statistics | ❌ | ✅ |
| Colored interface | ✅ | ✅ Improved |

Version 2.0 is 100% compatible with v1.0 while adding many advanced features!
