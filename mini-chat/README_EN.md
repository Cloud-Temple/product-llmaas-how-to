# Mini-Chat LLMaaS v3.0

A modern, robust, and modular command-line interface (CLI) chat for interacting with LLMaaS models. This v3.0 release has been completely re-architected to offer better stability, easier maintenance, and an enriched user experience.

## 🌟 What's New in v3.0

- **Modular Architecture**: Clear separation between configuration, state, business logic, and user interface.
- **Enhanced Robustness**: Centralized error management, strict typing, and input validation.
- **Simplified RAG**: Seamless integration of embedding and vector search with Qdrant.
- **Improved Tool Support**: Reliable execution of tools (calculator, time, files, etc.) even in streaming mode.
- **Default Model**: Uses `openai/gpt-oss-120b` for optimal performance.

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to the directory
cd mini-chat

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example file and configure your API key:

```bash
cp .env.example .env
# Edit .env with your LLMaaS API key
```

**Minimum Configuration (.env)**:
```env
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="your_api_key_here"
DEFAULT_MODEL="openai/gpt-oss-120b"
```

### 3. Starting Qdrant (Optional - For RAG)

To enable long-term memory and document search:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Launch

```bash
# Standard interactive mode
python mini_chat.py

# With a specific model
python mini_chat.py --model gemma3:27b

# "One-Shot" mode (single command)
python mini_chat.py --non-interactive --prompt "Explain special relativity in 3 sentences."
```

## 🎮 Interactive Commands

Once in the chat, use slash `/` commands to control the application:

| Command | Description |
|----------|-------------|
| `/rag on|off` | Enable or disable RAG (Vector Search) mode. |
| `/embed <file>` | Read, chunk, and index a text file into the vector database. |
| `/history` | Display the full history of the current session. |
| `/clear` | Clear conversation history (keeps system prompt). |
| `/quit` | Quit the application. |

## 🧠 Advanced Features (RAG)

The RAG (Retrieval-Augmented Generation) system allows the model to access your own documents.

1.  **Indexing**:
    ```text
    /embed constitution.txt
    ```
    *The system chunks the file, computes embeddings, and stores them in Qdrant.*

2.  **Activation**:
    ```text
    /rag on
    ```

3.  **Usage**:
    Simply ask your question. If RAG is active, the system will first look for relevant passages in your documents and provide them to the model as context.

## 🛠️ Integrated Tools (Tool Calling)

The model has access to several tools it can decide to use autonomously:
- **Calculator**: For precise mathematical operations.
- **Date/Time**: To know the current time.
- **File System**: Read and write files (in the current directory).
- **Shell**: Execute system commands (requires user validation).

## 🏗️ Technical Architecture

The code is organized for readability and maintainability:

- **`mini_chat.py`**: Entry point. Contains the main loop (`MiniChatCLI`) and orchestration (`ChatService`).
- **`api_client.py`**: Low-level API call management (streaming, chunk handling).
- **`qdrant_utils.py`**: Interface with the vector database.
- **`rag_core.py`**: Text chunking logic.
- **`tools_definition.py`**: JSON schema definitions for tools.

## 📞 Support

For any questions or issues, first verify that your API key is valid and that Qdrant is running (if using RAG).

You can also run the automated test script to validate your RAG configuration:
```bash
python test_rag_scenario.py
```
