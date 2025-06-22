# Advanced Text Summarization Tool

This Python tool generates accurate summaries of text or Markdown files of any size, using a Large Language Model (LLM) via the LLMaaS API. It handles intelligent text chunking, parallel batch processing, and contextual continuity between sections.

## Features

*   **Token-based Chunking**: Uses `tiktoken` for precise token-based chunking, ensuring chunks respect model limits.
*   **Parallel Batch Processing**: Chunks are grouped into batches, and LLM requests for chunks in the same batch are executed in parallel to optimize speed.
*   **Contextual Continuity**: Option (enabled by default) to include the previous batch summary in the LLM prompt for the current batch, ensuring coherent synthesis across very long documents.
*   **Unified Final Summary**: By default, the script performs a final summary pass on all chunk summaries. This step is particularly useful for long documents (generating many chunks) to create a unified and coherent summary. Can be disabled with the `--no-final-summary` option.
*   **Configurable Prompts**: Uses a `prompts.yaml` file to define different types of summary prompts (e.g., concise, detailed, action items, Q&A), including the prompt for final summary.
*   **Visual Progress Bars**: Displays aesthetic progress bars with `rich.progress` for clear progress tracking.
*   **Debug Mode**: A debug mode configurable via environment variable allows displaying LLM request and response payloads for easier debugging.
*   **Flexible Configuration**: LLMaaS API parameters and default model are configurable via a `.env` file. Chunking, batch processing, and LLM generation parameters are configurable via command-line arguments.
*   **Response Cleaning**: Automatically handles removal of `<think>...</think>` tags from reasoning LLM responses.

## Prerequisites

*   Python 3.8+
*   `pip` (Python package manager)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone [REPOSITORY_URL]
    cd [REPOSITORY_NAME]/examples/summarizer
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate # On Linux/macOS
    # venv\Scripts\activate # On Windows
    ```
3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **`.env` File**:
    Create a file named `.env` in the `examples/summarizer/` directory based on the `examples/summarizer/.env.example` file.

    ```bash
    cp .env.example .env
    ```
    Modify the `.env` file to configure your LLMaaS API URL and API key:
    ```dotenv
    LLMAAS_API_BASE_URL=http://localhost:8000/v1
    LLMAAS_API_KEY=your_api_key_here
    LLMAAS_DEFAULT_MODEL=gemma3:8b
    DEBUG_MODE=false
    ```

2.  **`prompts.yaml` File**:
    This file contains summary prompt definitions. You can add or modify prompts according to your needs.
    Example structure:
    ```yaml
    concise_summary:
      system_prompt: |
        You are an expert summarization assistant. Your task is to provide a concise and accurate summary of the provided text.
        Focus on key points and essential information.
      user_template: |
        Please summarize the following text concisely:
        ---
        {text}
        ---
    ```
    The `{text}` in `user_template` is a placeholder that will be replaced by the chunk content.

## Usage

Run the `summarizer.py` script directly from the `examples/summarizer/` directory:

```bash
python3 summarizer.py --input path/to/your_file.md --output my_summary.md --prompt concise_summary --model gemma3:8b
```

### Command Line Arguments

*   `--input`, `-i` (required): Path to the input text/Markdown file to summarize.
*   `--output`, `-o` (optional): Path to the output file where the summary will be written. Default: `summary.md`.
*   `--model`, `-m` (optional): Name of the LLM model to use. Default uses the value of `LLMAAS_DEFAULT_MODEL` in `.env`.
*   `--prompt`, `-p` (required): Name of the summary prompt to use, as defined in `prompts.yaml` (e.g., `concise_summary`, `detailed_summary`).
*   `--chunk_size`, `-cs` (optional): Maximum size of a chunk in tokens. Default: `2000`.
*   `--chunk_overlap`, `-co` (optional): Number of overlapping tokens between chunks. Default: `200`.
*   `--max_tokens_per_chunk`, `-mt` (optional): Maximum number of tokens the LLM should generate for each chunk. Default: `500`.
*   `--batch_size`, `-bs` (optional): Number of chunks to process in parallel per batch. Default: `5`.
*   `--no_previous_summary_context`, `-npc` (flag): If present, disables inclusion of the previous batch summary in the LLM context. Default: context is included.
*   `--no-final-summary` (flag): Disables the final unified summary pass.

### Usage Examples

```bash
# For a concise summary of an example file
python3 summarizer.py -i ../../README.md -o readme_summary.md -p concise_summary -m gemma3:8b

# For a detailed summary without previous context, with larger batch_size
python3 summarizer.py -i long_document.txt -o detailed_report.md -p detailed_summary -m deepseek-r1:32b -bs 10 --no_previous_summary_context

# To extract action items from meeting notes
python3 summarizer.py -i meeting_notes.md -o action_items.txt -p action_items -m cogito:14b
```

## Debugging

Enable debug mode by setting `DEBUG_MODE=true` in your `.env` file. This will display JSON payloads sent to and received from the LLMaaS API in the console, which is useful for debugging.

```dotenv
DEBUG_MODE=true
```

## Project Structure

```
examples/
└── summarizer/
    ├── summarizer.py           # Main script containing all logic
    ├── .env.example            # Example environment file
    ├── prompts.yaml            # Summary prompt definitions
    ├── requirements.txt        # Python dependencies
    ├── README.md               # French documentation
    └── README_EN.md            # English documentation (this file)
```

## Available Prompt Types

The `prompts.yaml` file includes several predefined prompt types:

*   **`concise_summary`**: Generates brief, essential summaries
*   **`detailed_summary`**: Creates comprehensive, detailed summaries
*   **`action_items`**: Extracts action points and tasks
*   **`qa_summary`**: Formats content as questions and answers

You can customize these prompts or add new ones according to your specific needs.

## Performance Tips

*   **Chunk Size**: Adjust `--chunk_size` based on your model's context window
*   **Batch Size**: Increase `--batch_size` for faster processing if your API can handle concurrent requests
*   **Model Selection**: Choose models appropriate for your content complexity
*   **Context**: Use `--no_previous_summary_context` for independent chunk processing

## Troubleshooting

### Common Issues

**API Connection Error**
```
Error: Unable to connect to LLMaaS API
```
→ Check your `LLMAAS_API_BASE_URL` and `LLMAAS_API_KEY` in the `.env` file.

**Token Limit Exceeded**
```
Error: Token limit exceeded for chunk
```
→ Reduce `--chunk_size` or `--max_tokens_per_chunk` values.

**Invalid Prompt Name**
```
Error: Prompt 'xyz' not found in prompts.yaml
```
→ Check available prompts in `prompts.yaml` and use the correct name.

### Debug Mode
Use `DEBUG_MODE=true` in your `.env` file to see detailed API requests and responses:

```bash
DEBUG_MODE=true python3 summarizer.py -i document.txt -p concise_summary
```

## Contributing

This example is part of the Cloud Temple LLMaaS project. For improvement suggestions:

1. Open an issue to discuss proposed changes
2. Respect existing code style and conventions
3. Test your changes with different document types
4. Document new features

## License

This script is distributed under the same license as the main LLMaaS project.

---

**Cloud Temple - LLMaaS Team**  
*Sovereign and Secure Artificial Intelligence*
