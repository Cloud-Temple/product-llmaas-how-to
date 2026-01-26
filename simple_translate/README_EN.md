# Translation Example with TranslateGemma

This script illustrates how to use **TranslateGemma** models (4B, 12B, 27B) available via the LLMaaS API.

Unlike standard chat models, TranslateGemma requires a **very specific prompt format** to work correctly. This script implements that format and allows you to translate text easily.

## Prerequisites

- Python 3.7+
- A Cloud Temple LLMaaS API key

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure your environment:
    Copy the `.env.example` file to `.env` and add your API key.
    ```bash
    cp .env.example .env
    # Edit .env with your favorite editor
    ```

## Usage

The script contains a simple English to French translation example.

```bash
python simple_translate.py
```

## Customization

You can modify the `simple_translate.py` script to change:
- The text to translate (`text_to_translate`).
- The source and target languages (`source_lang`, `source_code`, `target_lang`, `target_code`).
- The model used (via the `LLMAAS_MODEL` environment variable or directly in the code).

**Note on the model:** By default, the script uses `translategemma:27b`. Ensure this model is available or switch to `translategemma:4b` or `translategemma:12b` as needed.
