# LLMaaS TTS Demonstration (Text-to-Speech)

This folder contains a simple and elegant example of using the Text-to-Speech (TTS) API from the LLMaaS platform.

It uses the OpenAI-compatible `/v1/audio/speech` endpoint to convert text into an audio file.

## Features

*   **Rich Console Interface**: Uses the `rich` library for colored display, information panels, and progress bars.
*   **Full API Support**: Allows choosing the model, voice, output format, and text.
*   **Interactive Mode**: If no text is provided as an argument, the script will ask you to enter it.
*   **File Reading**: Can read the text to be synthesized from a local file.
*   **Direct Audio Playback**: Can automatically play the generated file with the `--play` option (supports macOS, Windows, and Linux with ffplay/mpg123/aplay).
*   **Error Handling**: Clearly displays API or connection errors.

## Prerequisites

*   Python 3.8+
*   An LLMaaS API access token (Bearer Token)

## Installation and Configuration

1.  Navigate to the example directory:
    ```bash
    cd examples/simple_tts
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure the environment:
    *   Copy the example file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file to add your API key and customize the URL if necessary.

## Usage

The script will automatically use the configuration defined in `.env`.

### Command Examples

**1. Simple synthesis (text as an argument):**

```bash
python tts_demo.py "Welcome to the Cloud Temple AI platform."
```
*Generates an mp3 file with the default voice (alloy).*

**2. Synthesis and immediate playback:**

```bash
python tts_demo.py "This is an audio test." --play
```

**3. Change voice and format:**

```bash
python tts_demo.py "This is a different voice." --voice onyx --format wav --output my_voice.wav
```

**4. Read from a text file:**

```bash
python tts_demo.py -f my_book.txt --voice shimmer
```

**5. Interactive Mode:**

```bash
python tts_demo.py
```
*The script will ask you to enter the text.*

**6. Debug Mode (to see request/response details):**

```bash
python tts_demo.py "Technical test" --debug
```

**7. Adjust Timeout (for long texts):**

```bash
python tts_demo.py "Very long text..." --timeout 600
```
*The default timeout is 300 seconds.*

## Available Voices

*   `alloy` (Female, American) - *Default*
*   `echo` (Male, American)
*   `fable` (Male, American)
*   `onyx` (Female, American)
*   `nova` (Female, American)
*   `shimmer` (Female, American)
*   `coral` (Female, American)
*   `ash` (Male, Chinese/English)
*   `ballad` (Male, Indian/English)
*   `xi` (Male, Chinese)
*   `sage` (Female, Chinese)
*   `chef` (Male, French)
