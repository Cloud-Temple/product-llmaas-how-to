# Medical Image Analysis Example with MedGemma

This directory contains an example of using the **MedGemma** model (based on Gemma 3) for medical image analysis via the LLMaaS API.

## Contents

- `analyze_medical_image.py`: The main Python script.
- `radio.png`: A sample X-ray image (provided).
- `requirements.txt`: Necessary Python dependencies.

## Prerequisites

1.  Python 3.8+ installed.
2.  A valid LLMaaS API key.

## Installation

1.  Create a virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure your API key:
    Create a `.env` file in the root of this directory (or export environment variables):
    ```bash
    API_KEY=your_api_key_here
    API_URL=https://api.ai.cloud-temple.com/v1
    ```
    *(You can copy `.env.example` if it exists)*

## Usage

To analyze the sample image `radio.png`:

```bash
python analyze_medical_image.py radio.png
```

To add specific medical context (e.g., age, symptoms):

```bash
python analyze_medical_image.py radio.png --context "45-year-old patient, smoker, complaining of persistent cough."
```

To enable streaming mode (progressive display of the response):

```bash
python analyze_medical_image.py radio.png --stream
```

## How it works

The script:
1.  Encodes the provided image in Base64.
2.  Constructs a multimodal request (Text + Image) for the API.
3.  Uses the `medgemma:27b` model.
4.  Sends a specific prompt requesting a detailed analysis of anatomical structures and potential abnormalities.
5.  Displays the model's response formatted in Markdown in the console.
