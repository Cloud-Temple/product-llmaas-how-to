# File Translation Script Example

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

This example provides a Python script (`translate.py`) for translating the content of a text file from a source language to a target language using the **Cloud Temple LLMaaS API**.

## Objective

The main objective is to demonstrate how to:
1.  Interact with the LLMaaS API for translation tasks.
2.  Process a text file by segments (chunks) to handle long documents.
3.  Maintain translation consistency by passing the previously translated segment as context to the model.
4.  Offer a flexible command-line interface to specify the file, target language, model, and other parameters.
5.  Provide an optional interactive mode to validate or adjust the translation as it progresses.

## Features

-   File selection for translation via the `--file` option.
-   Target language specification using ISO 639-1 codes (e.g., `en`, `fr`) via `--target-language`.
-   `--list-languages` option to display common language codes.
-   Choice of LLM model to use (`--model`).
-   Configuration of the system prompt (`--system-prompt`), maximum tokens per chunk (`--max-tokens`), chunk size in words (`--chunk-size-words`), and output directory (`--output-dir`).
-   **Default configuration via `.env` file**: Most options (model, API URL, target language, max tokens, chunk size, system prompt, output directory) can be set by default in a `.env` file. See `.env.example`.
-   Translation by "chunks" (text segments) with context passing from the previous chunk to improve consistency.
-   **Intelligent chunking**: Attempts to aggregate small paragraphs and respect natural text boundaries, while ensuring that chunks do not exceed the configured size.
-   Optional interactive mode (`--interactive`) to validate each chunk's translation (modification is not yet implemented).
-   Saving the translated text to a new file in the output directory.
-   **Improved progress display**: Uses a detailed `rich` progress bar during translation, including a preview of the current chunk.
-   Debug option (`--debug`) to visualize the chunking process.

## Installation

```bash
# Clone the repository (if you haven't already)
# git clone ...
# cd llmaas/examples/translate

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate # On Linux/macOS
# .venv\Scripts\activate # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy examples/translate/.env.example to examples/translate/.env
# and fill in at least LLMAAS_API_KEY.
# You can also set default values for the model, target language, etc.
# cp .env.example .env
# nano .env
```

## Usage

To display full help:
```bash
python translate.py --help
```

To list common language codes:
```bash
python translate.py --list-languages
```

Example of translating a file to English:
```bash
python translate.py --file path/to/my_source_file.txt --target-language en
```

Example with interactive mode and chunking debug:
```bash
python translate.py --file my_document.txt --target-language fr --interactive --debug
```

The translated file will be saved by default in the `translated_files/` subdirectory (configurable via `--output-dir` or `LLMAAS_OUTPUT_DIR` in `.env`).
