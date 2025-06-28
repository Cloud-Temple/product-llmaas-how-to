# RAG Demonstrator with Qdrant and the LLMaaS API

This project is a demonstrator of a complete and containerized RAG (Retrieval-Augmented Generation) architecture.

The architecture uses the LLMaaS API for the two key steps of the RAG process:
1.  **Embedding via LLMaaS**: The API is used to generate embeddings (vectors) for documents and questions with the `granite-embedding:278m` model.
2.  **Generation via LLMaaS**: The API is also used for generating the final response with the `granite3.3:8b` model, based on the context provided by the vector search.
3.  **Vector Database**: Qdrant is used to store the vectors and perform similarity searches.

## Prerequisites

- Docker and Docker Compose
- Access to the LLMaaS API.

## Configuration

Before launching, ensure that the `.env` file is correctly configured from the `.env.example` file:

- `QDRANT_URL`: Must point to the Qdrant service. The default value `http://qdrant:6333` is correct for `docker-compose`.
- `LLMAAS_API_BASE`: The base URL of your LLMaaS API (e.g., `https://api.ai.cloud-temple.com/v1`).
- `LLMAAS_API_KEY`: Your access key for the LLMaaS API.
- `EMBEDDING_MODEL_NAME`: The name of the embedding model available on the LLMaaS API (e.g., `granite-embedding:278m`).
- `LLM_MODEL_NAME`: The name of the generation model available on the LLMaaS API (e.g., `granite3.3:8b`).

## Execution Instructions

### 1. Launch the application

Navigate to the root of this folder (`examples/rag-granite-qdrant-demo`) and run the following command:

```bash
docker-compose up --build
```

This command will:
1.  **Build the Docker image** for the Python application (`rag-app`).
2.  **Start the containers** for the application and the Qdrant database.
3.  The `rag_demo.py` script will run and display each step of the RAG process in detail.

### 2. Stop the application

To stop the services, press `Ctrl+C` in the terminal where `docker-compose` is running, then execute:

```bash
docker-compose down
