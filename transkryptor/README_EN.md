# Transkryptor Python CLI - Advanced Audio Transcription Example

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

This Python script, `transkryptor.py`, is an advanced command-line tool designed to transcribe audio files, even very large ones, using the **Cloud Temple LLMaaS Transcription API** (Whisper compatible). It implements intelligent audio file chunking with overlap, processes these chunks in parallel batches to optimize speed, and offers a polished user interface with debug and silent modes.

## ✨ Key Features

-   **🎤 Large Audio File Support**: Designed to transcribe long audio files without being limited by maximum API request size.
-   **🧩 Intelligent Chunking**: Divides audio into chunks with configurable duration and overlap to ensure continuous and accurate transcription.
-   **⚡ Parallel Batch Processing**: Sends multiple chunks simultaneously to the API to accelerate the overall transcription process.
-   **📝 Real-time Writing**: **NEW FEATURE** - Writes the transcription progressively to the output file, allowing results to be seen gradually without waiting for full completion.
-   **🖥️ Real-time Preview**: **NEW FEATURE** - `--preview` option that displays the transcription in real-time directly in the terminal with an organized interface, visual progress bar, and live status.
-   **🎨 Polished User Interface**: Uses the `rich` library for a clear and colorful display, including:
    -   Progress bars for global and batch processing.
    -   Informative and well-formatted logs.
-   **🐛 Debug Mode (`--debug`)**: Displays detailed information about each step of the process, including chunk metadata, API request parameters (without the key), and API responses.
-   **🔇 Silent Mode (`--silent`)**:
    -   Suppresses all progress displays and informative logs.
    -   Displays the transcription of each batch to `stdout` as soon as it is completed.
    -   Ideal for redirecting output to a file or for use in script pipelines.
-   **⚙️ Flexible Configuration**: Parameters configurable via a `config.json` file and/or command-line arguments (API URL, API key, language, prompt, chunking parameters, batch size).
-   **📝 Prompt Management**: Allows providing an initial prompt to guide the Whisper model and improve transcription relevance for specific contexts.
-   **🗣️ Multilingual Support**: Specify the audio language for better accuracy.
-   **📄 Verbatim Output**: Generates a complete transcription of the audio file.

## 🆕 New Features

### 📝 Real-time Writing
The script now writes the transcription directly to the output file as each chunk is transcribed, instead of waiting for full completion. This allows:
- Seeing results progressively
- Retrieving a partial transcription even if the process is interrupted
- Better memory usage for very large files

### 🖥️ Preview Mode (`--preview`)
A new `--preview` option displays the transcription in real-time directly in the terminal with a modern interface:
- **Real-time transcription**: Text appears gradually in the terminal
- **Visual progress bar**: Graphical progress with percentage and number of chunks
- **Organized interface**: Separate panels for header, progress, transcription, and instructions
- **Live status**: Information on transcription status
- **Optimized display**: Automatic truncation for very long texts
- **Terminal compatible**: Works in any modern terminal

**Note**: The `--preview` option uses Rich (already included in dependencies) and requires no additional installation.

## 📁 Directory Structure

```
examples/transkryptor/
├── transkryptor.py         # Main script
├── audio_utils.py          # Utilities for audio manipulation
├── api_utils.py            # Utilities for API calls
├── cli_ui.py               # Utilities for CLI interface (colors, etc.)
├── requirements.txt        # Python dependencies
├── config.json             # Your configuration file (created from example)
├── config.example.json     # Template for the configuration file
└── README.md               # This file
```

## 🚀 Prerequisites

-   Python 3.8+
-   **`ffmpeg`**: For `pydub` to process a wide range of audio formats (like MP3, M4A, etc.), `ffmpeg` must be installed on your system and accessible in the PATH.
    -   On macOS: `brew install ffmpeg`
    -   On Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`
    -   On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
-   Python libraries listed in `requirements.txt` (will be installed in the next step).
-   Access to the LLMaaS Transcription API and a valid API key.

## ⚙️ Installation and Configuration

1.  **Clone the repository** (if you haven't already) and navigate to the `examples/transkryptor/` directory.

2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv_transkryptor
    source venv_transkryptor/bin/activate  # On macOS/Linux
    # .\venv_transkryptor\Scripts\activate  # On Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `httpx`, `pydub`, `rich`, `python-dotenv`, `soundfile`, and `numpy`.

4.  **Configure the application**:
    *   Copy `config.example.json` to `config.json`.
        ```bash
        cp config.example.json config.json
        ```
    *   Modify `config.json` to add your LLMaaS API key (`api_token`) and adjust other parameters if necessary:
        ```json
        {
          "api_url": "https://api.ai.cloud-temple.com/v1/audio/transcriptions",
          "api_token": "YOUR_REAL_LLMAAS_API_KEY_HERE",
          "default_language": "fr",
          "default_prompt": "This is a transcription about...",
          "chunk_duration_ms": 30000,
          "chunk_overlap_ms": 2000,
          "batch_size": 1,
          "sample_rate_hz": 24000,
          "output_directory": "./transkryptor_outputs"
        }
        ```
    *   Alternatively, you can pass the API key and other parameters directly via the command line.

## 🎮 Usage

The script is used from the command line. Here's the basic help:

```bash
python transkryptor.py --help
```

### Usage Examples

**Simple file transcription:**
```bash
python transkryptor.py path/to/your/audio_file.mp3
```
The transcription will be saved in the directory specified by `output_directory` in `config.json` (default `./transkryptor_outputs/`) with a name based on the input file.

**Specify an output file:**
```bash
python transkryptor.py my_audio.wav -o complete_transcription.txt
```

**🆕 Use real-time preview mode:**
```bash
python transkryptor.py conference.mp3 --preview -o transcript.txt
```
This command opens a window to see the transcription live while saving to a file.

**Use a specific language and prompt:**
```bash
python transkryptor.py expert_interview.m4a -l en -p "Interview with Dr. Expert about AI ethics."
```

**Debug mode to see details:**
```bash
python transkryptor.py short_excerpt.flac --debug
```

**Silent mode for raw batch output to stdout:**
```bash
python transkryptor.py long_podcast.ogg --silent
```
If you want to capture this output to a file:
```bash
python transkryptor.py long_podcast.ogg --silent > podcast_transcription.txt
```

**🆕 Use preview with real-time writing:**
```bash
python transkryptor.py presentation.m4a --preview -o presentation_transcript.txt
```
This example shows real-time transcription in the terminal and progressively writes it to a file.

**Debug mode (incompatible with preview):**
```bash
python transkryptor.py presentation.m4a -o presentation_transcript.txt --debug
```
To see debug details, use this command without the --preview option.

**Change chunk and batch sizes:**
```bash
python transkryptor.py very_long_file.mp3 --chunk-duration 600000 --chunk-overlap 60000 --batch-size 3
```
(10-minute chunk, 1-minute overlap, 3 chunks per batch)

## 📋 Command Line Options

| Option | Description |
|---|---|
| `AUDIO_FILE_PATH` | Path to the audio file to transcribe (required) |
| `-o, --output-file` | File to save the final transcription to |
| `-c, --config-file` | Path to the JSON configuration file |
| `--api-url` | LLMaaS Transcription API URL |
| `--api-key` | API key for LLMaaS |
| `-l, --language` | Audio language code (e.g., fr, en) |
| `-p, --prompt` | Prompt to guide transcription |
| `--chunk-duration` | Duration of each chunk in milliseconds |
| `--chunk-overlap` | Overlap between chunks in milliseconds |
| `--batch-size` | Number of chunks to process in parallel per batch |
| `--sample-rate` | Sample rate in Hz (e.g., 16000, 22050, 44100) |
| `--output-dir` | Directory to save transcriptions to |
| `--preview` | 🆕 Open a real-time preview window |
| `--debug` | Enable verbose debug mode |
| `--silent` | Silent mode: displays batch transcription to stdout |

## 🛠️ Supported Audio Formats

Thanks to `pydub`, a wide range of audio formats should be supported, including:
`mp3`, `wav`, `flac`, `ogg`, `m4a`, `aac`, etc.
The script will convert the audio to a mono 16-bit PCM WAV format before sending it to the API, if necessary.

## 💡 Usage Tips

### 🆕 Real-time Writing
- Transcription is progressively written to the file as it's generated.
- You can follow progress by opening the output file in an auto-refreshing editor.
- In case of interruption, you retain the partial transcription.

### 🆕 Preview Mode
- Ideal for long transcriptions where you want to see progress.
- The window can be resized to your preference.
- Use "Copy All" to quickly get the transcribed text.
- The window remains open even after transcription is complete.

### Performance Optimization
- For very long files, increase `chunk_duration` (e.g., 600000ms = 10min).
- Increase `batch_size` if your internet connection is stable.
- Use `--silent` mode for automated pipelines.

## 📝 Technical Notes

-   **`ffmpeg` is crucial** for `pydub`'s extended audio format support. If you encounter decoding errors, check your `ffmpeg` installation.
-   **Real-time writing**: The file is written with line buffering for immediate display of results.
-   **Preview mode**: Uses Rich to display a real-time interface directly in the terminal without blocking the transcription process.
-   Performance will depend on your file size, internet connection speed, and load on the LLMaaS API.
-   Debug mode can generate a large amount of logs.

## 🔧 Troubleshooting

### Common Issues

1. **`--preview` option issues**:
    The `--preview` option uses Rich for terminal display and should not cause issues on most systems. If you encounter difficulties:
    - Check that Rich is installed: `pip show rich`
    - Ensure you are using a modern terminal that supports colors and Unicode characters.
    - If the display is corrupted, you can still use real-time writing without preview: `python transkryptor.py audio.mp3 -o transcript.txt`
    - To diagnose: use debug mode to see details: `python transkryptor.py audio.mp3 -o transcript.txt --debug`

### Audio Format Issues
If an audio format is not recognized:
1. Check that `ffmpeg` is installed and in the PATH.
2. Try converting the file to WAV with `ffmpeg` first.
3. Consult logs in `--debug` mode for more details.

This script is an advanced example and can be extended or modified according to your specific needs.
