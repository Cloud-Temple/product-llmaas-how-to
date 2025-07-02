# Mini-Chat LLMaaS

An elegant command-line interface to interact with the LLMaaS platform's language models, with full support for RAG (Retrieval-Augmented Generation).

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

```bash
# Copy the configuration file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Minimum configuration**:
```env
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="your_api_key_here"
DEFAULT_MODEL="qwen3:30b-a3b"
```

### 3. Starting Qdrant (for RAG)

**Option A: Docker (recommended)**
```bash
# Simple start
docker run -p 6333:6333 qdrant/qdrant

# Or with data persistence
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Option B: Docker Compose**
```bash
# Use the provided file
docker-compose up -d
```

**Option C: Local Installation**
```bash
# Follow the instructions at https://qdrant.tech/documentation/quick-start/
```

### 4. First Launch

```bash
# Simple launch
python mini_chat.py

# With a specific model
python mini_chat.py --model qwen3:4b

# Debug mode to see details
python mini_chat.py --debug
```

## 🎯 Main Features

### 💬 Smart Chat
- **Real-time streaming**: Responses are displayed as they are generated
- **Persistent history**: Navigate with ↑/↓ arrows
- **Autocompletion**: 23 commands with Tab
- **Flexible modes**: Debug, silent, non-interactive

### 🛠️ Integrated Tools
- **🕒 Clock**: Current time
- **🧮 Calculator**: Mathematical expressions
- **📁 Files**: Read and save
- **⚡ Shell**: Execute commands (with confirmation)
- **🔍 RAG**: Search in a vector knowledge base

### 🧠 RAG (Retrieval-Augmented Generation)
- **Automatic ingestion**: `/embed` command to add documents
- **Intelligent search**: Configurable similarity thresholds
- **Flexible activation**: Automatic or manual mode
- **Complete diagnostics**: Management and monitoring of the Qdrant database

## 📋 User Guide

### RAG Configuration

1. **Start Qdrant** (see Quick Start section)

2. **Configure .env**:
```env
# Qdrant settings
QDRANT_URL="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION="minichat_rag"
EMBEDDING_MODEL="granite-embedding:278m"

# Chunking settings (in tokens)
RAG_CHUNK_SIZE=256
RAG_CHUNK_OVERLAP=50
```

3. **Ingest documents**:
```bash
# In the chat
/embed constitution.txt
```

4. **Activate RAG**:
```bash
/rag on
```

### Essential Commands

#### Session Management
```bash
/model                    # Change model
/system <prompt>          # Set a system prompt
/clear                    # Clear history
/save_session chat.json   # Save the session
/load_session chat.json   # Load a session
```

#### RAG and Documents
```bash
/embed <file>             # Ingest a document
/rag on|off               # Enable/disable RAG
/rag_threshold 0.8        # Configure similarity threshold
/qdrant_info              # Information about the database
/qdrant_list              # List documents
```

#### Diagnostics and Debug
```bash
/context                  # Application state
/context all              # Full context + JSON
/debug                    # Debug mode on/off
/tools                    # List of available tools
```

## ⚙️ Command-Line Options

### Main Options
```bash
python mini_chat.py [OPTIONS]

--model TEXT              # Model to use
--max-tokens INTEGER      # Token limit (default: 8192)
--temperature FLOAT       # Temperature (default: 0.7)
--system-prompt TEXT      # Initial system prompt
--debug / --no-debug      # Debug mode
```

### Advanced Options
```bash
--api-url TEXT            # API URL (overrides .env)
--api-key TEXT            # API key (overrides .env)
--non-interactive         # Non-interactive mode
--no-stream               # Disable streaming
--silent                  # Silent mode
--godmode                 # No confirmation for shell commands
```

### RAG Options
```bash
--qdrant-url TEXT         # Qdrant URL (default: localhost)
--qdrant-port INTEGER     # Qdrant port (default: 6333)
--qdrant-collection TEXT  # Collection (default: minichat_rag)
--embedding-model TEXT    # Embedding model
```

### Session Options
```bash
--load-session FILE       # Load a session
--autosave-json FILE      # Auto-save in JSON
--autosave-md FILE        # Auto-save in Markdown
--rules FILE              # Markdown rules file
--prompt TEXT             # Initial prompt
```

## 🔧 Advanced Configuration

### Complete .env File
```env
# LLMaaS API
API_URL="https://api.ai.cloud-temple.com/v1"
API_KEY="your_api_key_here"
DEFAULT_MODEL="qwen3:30b-a3b"
MAX_TOKENS=8192

# Qdrant for RAG
QDRANT_URL="localhost"
QDRANT_PORT=6333
QDRANT_COLLECTION="minichat_rag"
EMBEDDING_MODEL="granite-embedding:278m"

# Chunking settings (in tokens)
RAG_CHUNK_SIZE=256
RAG_CHUNK_OVERLAP=50
```

### Docker Compose for Qdrant
```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
```

## 🧪 Tests and Validation

### RAG Tool Test
```bash
# Unit test of the search tool
python test_rag_tool.py

# Test with a constitutional question
echo "Who can dismiss the Prime Minister?" | python mini_chat.py --model qwen3:4b --non-interactive
```

### Installation Diagnostics
```bash
# Check the configuration
python mini_chat.py --debug
/context all

# Test the Qdrant connection
/qdrant_info
```

## 🛠️ Troubleshooting

### Common Issues

**Qdrant not accessible**
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart <container_id>
```

**RAG not working**
```bash
# In the chat
/qdrant_info              # Check the connection
/rag_threshold 0.7        # Lower the threshold
/context                  # Full diagnostics
```

**Context limit exceeded**
```bash
/context                  # See automatic diagnostics
/smol                     # Condense history
/clear                    # Clear history
```

**Model issues**
```bash
# List available models
python mini_chat.py --model ""

# Test with a smaller model
python mini_chat.py --model qwen3:4b
```

## 📁 Project Structure

```
exemples/mini-chat/
├── mini_chat.py              # Main entry point
├── api_client.py             # LLMaaS API client
├── qdrant_utils.py           # Qdrant utilities
├── tools_definition.py       # Tool definitions
├── ui_utils.py               # User interface
├── session_manager.py        # Session management
├── rag_core.py               # RAG functions
├── command_handler.py        # Command handler
├── requirements.txt          # Python dependencies
├── .env.example              # Example configuration
├── docker-compose.yml        # Qdrant configuration
└── test_rag_tool.py          # Unit tests
```

## 🎯 Usage Examples

### Simple Chat
```bash
python mini_chat.py --model qwen3:4b
> Hello! How are you?
```

### RAG with Constitution
```bash
# 1. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 2. Launch mini-chat
python mini_chat.py --model qwen3:30b-a3b

# 3. Ingest the constitution
/embed constitution.txt

# 4. Activate RAG
/rag on

# 5. Ask a question
> Who can dissolve the National Assembly according to the Constitution?
```

### Non-Interactive Mode
```bash
echo "Summarize articles 1 to 5 of the Constitution for me" | \
python mini_chat.py --model qwen3:4b --non-interactive --no-stream
```

### Persistent Session
```bash
# Save
python mini_chat.py --autosave-json my_session.json

# Resume later
python mini_chat.py --load-session my_session.json
```

## 🔄 Updates

### Version 1.3.1 (Current)
- ✅ **Critical bug fixed**: Vector search tool fully functional
- ✅ **Robust type handling**: Universal support for JSON formats
- ✅ **Validated tests**: 4/4 requests processed without error
- ✅ **Complete documentation**: User guide and troubleshooting

### Previous Features
- 🎯 **Intelligent RAG** with configurable thresholds
- 🔧 **Advanced diagnostics** for context issues
- 🛠️ **23 commands** with autocompletion
- 📊 **Complete Qdrant management** (listing, deletion, information)

## 📞 Support

To report a bug or ask for help:
1. Use `/context all` to get full diagnostics
2. Consult the Troubleshooting section above
3. Check the logs in `--debug` mode

---

**Mini-Chat LLMaaS** - Intelligent chat interface with RAG for the LLMaaS platform
