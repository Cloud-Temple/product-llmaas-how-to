# Example: MCP HTTP/SSE Demo

**An ultra-pedagogical example of using the Model Context Protocol (MCP) in HTTP/SSE with the LLMaaS API**

---

## 📚 Table of Contents

1. [Introduction](#introduction)
2. [HTTP/SSE Architecture](#httpsse-architecture)
3. [Security and Authentication](#security-and-authentication)
4. [Project Files](#project-files)
5. [Detailed Operation](#detailed-operation)
6. [Prerequisites](#prerequisites)
7. [Installation](#installation)
8. [Usage](#usage)
9. [Advantages of HTTP Architecture](#advantages-of-http-architecture)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

This example demonstrates how to use the **Model Context Protocol (MCP)** with Cloud Temple's LLMaaS API in a **Web Client-Server** architecture.

Unlike basic implementations that launch subprocesses (stdio), this example shows a **distributed** and **realistic** architecture where the MCP server is an **independent and secure web service**.

The use case remains simple: **asking the model for the current time**, which will use a remote MCP tool to obtain this information.

---

## HTTP/SSE Architecture

The **Model Context Protocol (MCP)** defines how a model interacts with tools. In this HTTP/SSE version:

- **HTTP (Hypertext Transfer Protocol)**: Used by the client to send JSON-RPC requests to the server (e.g., list tools, execute a tool).
- **SSE (Server-Sent Events)**: Used by the server to send notifications or events to the client in real-time.

```
┌─────────────────────────────────────────────────┐
│  MCP Client (mcp_client_demo.py)                │
│  • Connects via HTTP to MCP server              │
│  • Sends Authorization: Bearer header...        │
│  • Talks to LLMaaS API                          │
└───────────────────────┬─────────────────────────┘
                        │
           HTTP Requests│(JSON-RPC) + Auth
                        ▼
┌─────────────────────────────────────────────────┐
│  MCP Server (mcp_server.py)                     │
│  • Web Service on http://localhost:8000         │
│  • Protected by API Key                         │
│  • Exposes "get_current_time" tool              │
└─────────────────────────────────────────────────┘
```

---

## Security and Authentication

This example shows how to secure access to an MCP server.

### Server Side
The server is protected by a middleware that checks the `Authorization` header.
The key is defined at startup:
```bash
python3 mcp_server.py --auth-key my_super_secret_key
```

### Client Side
The client must provide this key to connect. The key is read from the `.env` file:
```env
MCP_SERVER_AUTH_KEY=my_super_secret_key
```

If the key does not match, the server rejects the connection (403 Forbidden).

---

## Project Files

| File | Description | Role |
|------|-------------|------|
| `mcp_server.py` | **Secure Web Service** | Autonomous HTTP server exposing tools with authentication. |
| `mcp_client_demo.py` | **HTTP Client** | Client using the standard `mcp` SDK and handling auth. |
| `docker-compose.yml` | **Docker Deployment** | Configuration to run the server via Docker Compose. |
| `Dockerfile` | **Docker Image** | MCP server image definition. |
| `requirements.txt` | Dependencies | Contains `mcp`, `httpx`, `fastapi`, `uvicorn`, `python-dotenv`. |
| `.env.example` | Configuration | URL for LLMaaS API and MCP server. |
| `README.md` | Documentation | This file (in French). |

---

## Detailed Operation

### 1. The Server (`mcp_server.py`)

It's a web service based on **FastAPI** (via FastMCP).
- It uses a **security middleware** to check the Bearer token.
- It listens on `0.0.0.0:8000`.
- It automatically exposes MCP endpoints (`/sse`, `/message`).

### 2. The SSE Session Flow (Session ID)

A key point to understand MCP over HTTP: **Who gives the session ID?**

1.  The Client connects via `GET /sse`.
2.  The Server generates a unique **Session ID**.
3.  The Server sends an `endpoint` event to the client in the SSE stream.
    - Content: `/messages/?session_id=...`
4.  The Client then uses this URL (with the session_id) for all its `POST` requests.

### 3. The Client (`mcp_client_demo.py`)

It's an asynchronous script that:
1. Reads configuration and auth key from `.env`.
2. Connects to `http://localhost:8000/sse` passing the `Authorization` header.
3. Initializes the MCP session.
4. Retrieves available tools.
5. Orchestrates the discussion with the LLM.

---

## Prerequisites

- **Python 3.8+**
- A valid **LLMaaS API Key**
- Internet connection (for LLMaaS API)
- Port 8000 free (for MCP server)

---

## Installation

### 1. Navigate to directory

```bash
cd simple_mcp_demo/
```

### 2. Create .env file

```bash
cp .env.example .env
```
Edit `.env` with your LLMaaS API key and define an MCP server key if you wish.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

This architecture requires **two terminals**.

### Option A: Manual Launch (Without Docker)

**Terminal 1: Start the Server**
```bash
python3 mcp_server.py --auth-key my_secret_key
```

**Terminal 2: Run the Client**
Make sure `MCP_SERVER_AUTH_KEY=my_secret_key` is in your `.env`.
```bash
python3 mcp_client_demo.py --debug
```

### Option B: Launch via Docker 🐳

If you prefer not to install server dependencies on your machine:

1.  **Start the server**:
    ```bash
    docker compose up -d
    ```
    The server will be accessible at `http://localhost:8000` with the default key `ma_cle_docker_secrete` (modifiable in `docker-compose.yml`).

2.  **Configure the client**:
    Update your local `.env`:
    ```env
    MCP_SERVER_AUTH_KEY=ma_cle_docker_secrete
    ```

3.  **Run the client** (from your machine):
    ```bash
    python3 mcp_client_demo.py --debug
    ```

4.  **Stop the server**:
    ```bash
    docker compose down
    ```

---

### Terminal 2: Run the Client (Option A Continued)

Make sure `MCP_SERVER_AUTH_KEY=my_secret_key` is in your `.env`.

```bash
python3 mcp_client_demo.py --debug
```

*The client will:*
1. Read the auth key
2. Connect to the server (Auth OK)
3. Execute the full scenario

---

## Advantages of HTTP Architecture

Why use HTTP/SSE instead of the simple approach (stdio)?

1.  **Independence**: The server can be restarted without stopping the client.
2.  **Security**: Access control via token, essential for distributed architecture.
3.  **Sharing**: A single MCP server can serve multiple clients.
4.  **Deployment**: The server can be hosted on a different machine.

---

## Troubleshooting

### "403 Forbidden" or "Unauthorized"
- Check that the key passed with `--auth-key` to the server is IDENTICAL to the one in the client's `.env`.

### "Connection refused" or "Unable to connect"
- Check that `mcp_server.py` is running.
- Check the URL in `.env`.

### "Module not found: mcp"
- `pip install -r requirements.txt`.
