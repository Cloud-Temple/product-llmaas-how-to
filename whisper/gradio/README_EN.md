# Audio Transcription Test Scripts

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

This directory contains various scripts for testing and interacting with audio transcription services, including the **Cloud Temple LLMaaS Audio Transcription API**.

## Files

- `gradio-cloud-temple.py`: Gradio-based user interface for interacting with the Cloud Temple audio transcription API. Allows token authentication.
- `run_cloud_temple_interface.sh`: Shell script to install necessary dependencies and launch the `gradio-cloud-temple.py` interface.
- `gradio-client.py`: A similar Gradio user interface, potentially an older or generic version, which does not include token authentication management and uses a default server URL.
- `whisper-api.py`: A local implementation of an audio transcription API using OpenAI's `whisper` library. Provides `/transcribe` and `/translate` endpoints via FastAPI.
- `vllm-whisper-api.py`: A performance test script that uses vLLM to load the Whisper "large-v3" model and perform transcriptions on predefined audio examples. This is not an API implementation.
- `qwen_audio_test.py`: A test script using the `transformers` library to interact with the "Qwen/Qwen2-Audio-7B-Instruct" multimodal model for audio-related tasks.
- `requirements-cloud-temple.txt`: List of Python dependencies required to run `gradio-cloud-temple.py`.
- `requirements.txt`: List of Python dependencies required to run local APIs (`whisper-api.py`, `vllm-whisper-api.py`) and potentially other scripts.
- `test_audio.wav`: A test audio file.

## Using the Cloud Temple Interface

The `gradio-cloud-temple.py` interface allows easy testing of the Cloud Temple audio transcription API via an interactive web interface.

### How to Test the Cloud Temple API

The simplest way to get started is to use the `run_cloud_temple_interface.sh` shell script. This script automatically handles dependency installation and launching the Gradio interface.

#### Prerequisites

Ensure you have Python 3 installed on your system.

#### Launching the Test Script

Execute the shell script from the `scripts/test_whisper/` directory:

```bash
./run_cloud_temple_interface.sh
```

This script will perform the following actions:

1. Check for Python 3 installation.
2. Create a Python virtual environment (`venv`) if it doesn't exist.
3. Activate the virtual environment.
4. Install required dependencies listed in `requirements-cloud-temple.txt`.
5. Launch the Gradio interface (`gradio-cloud-temple.py`).

The web interface will automatically open in your default browser.

#### Using the Web Interface

Once the Gradio interface is launched:

1. **Enter your authentication token** for the Cloud Temple API in the "Authentication Token" field.
2. Click the **"Update Token"** button. The token status will be displayed.
3. Click the microphone button in the "Audio Input" section to **start recording**.
4. **Speak clearly** into your microphone.
5. The transcription of your speech will appear in real-time in the "Transcribed Text" text area.

You can also use the `test_audio.wav` file to test transcription without using the microphone.

#### Cloud Temple Interface Features

- **Configurable authentication**: Enter your API token in the interface.
- **Real-time transcription**: Speak into your microphone and see the transcription appear.
- **Optimized for French**: The API is configured by default for the French language.
- **Intuitive user interface**: Simple design and clear instructions.

#### Usage example (via the web interface)

1. Launch the interface by following the steps above.
2. In the web interface that opens, enter your authentication token.
3. Click "Update Token".
4. Click the microphone button to start recording.
5. Speak clearly into your microphone.
6. The transcription will automatically appear in the text area.

## Local APIs and Other Test Scripts

This directory also contains scripts for running audio transcription APIs locally or testing other models:

- `whisper-api.py`: A local implementation of an audio transcription API using OpenAI's `whisper` library. Provides `/transcribe` and `/translate` endpoints via FastAPI. You can run it with `uvicorn whisper-api:app --reload` or `gunicorn --timeout 60 -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3000 whisper-api:app`.
- `vllm-whisper-api.py`: A performance test script that uses vLLM to load the Whisper "large-v3" model and perform transcriptions on predefined audio examples. This is not an API implementation per se.
- `qwen_audio_test.py`: Specific script using the `transformers` library to interact with the "Qwen/Qwen2-Audio-7B-Instruct" multimodal model for audio-related tasks.

To run these scripts, you may need to install the dependencies listed in `requirements.txt`.

## Troubleshooting

- **Authentication error**: Check that your token is valid and correctly entered in the Cloud Temple interface.
- **Connection issues**: Ensure that the Cloud Temple API URL (`https://api.ai.cloud-temple.com/v1/audio/transcriptions`) is accessible from your network. For local APIs, ensure the server is properly launched and accessible.
- **Transcription quality**: For best results, speak clearly and in a quiet environment.

## Customization (Cloud Temple Interface)

You can modify the `gradio-cloud-temple.py` script to adjust:

- The API URL (`server_url` in the `AudioProcessor` class).
- The transcription language (`language` parameter in `process_audio_chunk`).
- Audio processing parameters (sample rate, format, etc.).

## Comparison of Interface/API Scripts

- `gradio-cloud-temple.py`: Uses the Cloud Temple API with token authentication.
- `gradio-client.py`: Original version using another API.
- `whisper-api.py`: Local API using the standard Whisper model.
- `vllm-whisper-api.py`: Performance test script for Whisper with vLLM.

## Technical Notes (Cloud Temple Interface)

- The `gradio-cloud-temple.py` script uses the Gradio library for the user interface.
- Audio chunks are processed and sent to the API via HTTP requests.
- Transcription history is managed to improve user experience.
