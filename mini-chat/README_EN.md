# Mini-Chat LLMaaS Cloud Temple

This Python script allows interaction with language models from the **Cloud Temple LLMaaS platform** via a "nice and pleasant" command-line interface.

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Features

- Interactive model selection.
- Streaming chat mode.
- Tool support:
    - Clock: Provides the current time.
    - Calculator: Evaluates mathematical expressions.
    - File reading: Reads the content of a local file.
    - Content saving: Saves text to a file.
    - Shell command execution: Executes shell commands (with confirmation).
- Enhanced user interface with the `rich` library.
- Integrated help and `/tools` command to list tools.
- Option to set the maximum number of tokens for the response.
- Ability to define a **system prompt**.
- Debug mode to display API payloads.
- Display of request statistics (tokens, speed).
- **Saving and loading** chat sessions (parameters + history) in JSON.
- Saving history in Markdown.

## Prerequisites

- Python 3.8+
- A valid LLMaaS API key.

## Installation

1.  Clone this repository (if you haven't already).
2.  Navigate to the `examples/mini-chat/` directory.
3.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate    # On Windows
    ```
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5.  Configure your API credentials:
    - Copy `.env.example` to `.env`.
    - Edit `.env` and fill in your `API_URL` and `API_KEY`.

        ```env
        API_URL="https://api.ai.cloud-temple.com/v1"
        API_KEY="your_api_key_here"
        ```

## Usage

```bash
python mini_chat.py [OPTIONS]
```

**Main options:**

- `--model TEXT`: Name of the model to use (e.g., `gemma3:4b`).
- `--max-tokens INTEGER`: Max tokens for the response (default: 1024).
- `--temperature FLOAT`: Temperature for generation (default: 0.7).
- `--system-prompt TEXT` or `-sp TEXT`: Initial system prompt.
- `--debug / --no-debug`: Activates/deactivates display of API payloads.
- `--api-url TEXT`: LLMaaS API URL (overrides `.env`).
- `--api-key TEXT`: LLMaaS API key (overrides `.env`).
- `--load-session FILE_PATH_JSON`: Loads a saved chat session.
- `--autosave-json FILE_PATH_JSON`: Automatically saves the session in JSON at the end.
- `--autosave-md FILE_PATH_MD`: Automatically saves history in Markdown at the end.
- `--godmode`: Activates GOD MODE (no confirmation for shell commands).
- `--silent`: Silent mode (less output, does not display tools or statistics).
- `--rules FILE_PATH_MD`: Markdown file of rules to add to the system prompt.
- `--prompt TEXT`: Initial prompt to send to the LLM at startup.
- `--non-interactive`: Non-interactive mode (exits after the first complete LLM response). Does not display the welcome message.
- `--no-stream`: Disables AI response streaming.
- `--help`: Displays help.

**In-chat commands:**

- `/quit` or `/exit`: Quits the chat.
- `/history`: Displays conversation history.
- `/clear`: Clears history (retains session parameters like system prompt).
- `/model`: Changes model (resets history, retains system prompt).
- `/system <prompt>`: Sets or modifies the system prompt (resets history).
- `/system_clear`: Removes the system prompt (resets history).
- `/save_session <file.json>`: Saves the current session (parameters and history).
- `/load_session <file.json>`: Loads a session (overwrites current session).
- `/savemd <file.md>`: Saves current history in Markdown.
- `/tools`: Lists available tools and their descriptions (not displayed in silent mode).
- `/smol`: Asks the model to condense current history into an effective prompt.
- `/debug`: Activates/deactivates debug mode.
- `/silent`: Activates/deactivates silent mode.
- `/stream`: Activates/deactivates AI response streaming.
- `/help`: Displays detailed command help.
