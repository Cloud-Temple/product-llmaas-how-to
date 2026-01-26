# Vision API Example

This directory contains a simple example showing how to use the vision (multimodal) capabilities of the LLMaaS API.

## How it Works

The `test_vision.py` script:
1.  Generates a sample image (`image_example.png`) if it doesn't already exist.
2.  Encodes this image in base64.
3.  Constructs a request in the standard OpenAI multimodal format, including a text prompt and the encoded image.
4.  Sends the request to the `/v1/chat/completions` endpoint.
5.  Displays the model's generated description of the image.

## Prerequisites

- Python 3.8+
- Dependencies listed in `requirements.txt`.

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure your credentials:
    -   Copy `.env.example` to a new file named `.env`.
    -   Edit the `.env` file and add your `API_KEY` and the API URL if it's different from the default.

    ```dotenv
    # .env
    API_URL="https://api.ai.cloud-temple.com/v1"
    API_KEY="YOUR_BEARER_TOKEN_HERE"
    DEFAULT_MODEL="granite3.2-vision:2b"
    ```

## Usage

### Simple Execution

To run the test in standard mode (non-streaming):
```bash
python3 test_vision.py
```

### Streaming Execution

To test the response in streaming mode, use the `--stream` option:
```bash
python3 test_vision.py --stream
```
