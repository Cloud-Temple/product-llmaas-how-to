import os
import time
import json
import requests
import qdrant_client
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.prompts import PromptTemplate
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List


class LLMaaSEmbeddings(Embeddings):
    """
    Classe d'embedding personnalisée pour interagir avec l'API LLMaaS.
    Elle garantit que le texte brut est envoyé, contournant le problème
    de tokenisation du client OpenAI par défaut de LangChain.
    """

    def __init__(self, model: str, api_base: str, api_key: str):
        self.model = model
        self.api_url = f"{api_base.rstrip('/')}/embeddings"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _embed(self, text: str) -> List[float]:
        """Méthode interne pour obtenir l'embedding d'un seul texte."""
        payload = {"model": self.model, "input": text}
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'appel à l'API d'embedding: {e}")
            raise
        except (KeyError, IndexError) as e:
            print(f"Erreur dans le format de la réponse de l'API d'embedding: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeddings pour une liste de documents."""
        print(f"Génération des embeddings pour {len(texts)} documents avec le modèle '{self.model}'...")
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embedding pour une seule requête."""
        print(f"Génération de l'embedding pour la requête avec le modèle '{self.model}'...")
        return self._embed(text)


def wait_for_qdrant(qdrant_url, retries=15, delay=5):
    """Attend que le service Qdrant soit disponible."""
    print(f"En attente de Qdrant sur {qdrant_url}...")
    client = qdrant_client.QdrantClient(url=qdrant_url)
    for i in range(retries):
        try:
            client.get_collections()
            print("Qdrant est prêt.")
            return qdrant_url
        except Exception:
            print(f"Tentative {i+1}/{retries}: Qdrant n'est pas encore accessible.")
            time.sleep(delay)
    print("Erreur: Impossible de se connecter à Qdrant.")
    return None


def main():
    load_dotenv()

    # --- Configuration ---
    qdrant_url_from_env = os.getenv("QDRANT_URL")
    collection_name = os.getenv("COLLECTION_NAME")
    llmaas_api_base = os.getenv("LLMAAS_API_BASE")
    llmaas_api_key = os.getenv("LLMAAS_API_KEY")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    llm_model_name = os.getenv("LLM_MODEL_NAME")

    if not all([qdrant_url_from_env, collection_name, llmaas_api_base, llmaas_api_key, embedding_model_name, llm_model_name]):
        print("Erreur: Toutes les variables d'environnement requises ne sont pas définies dans .env")
        return

    # --- Attendre Qdrant ---
    qdrant_url = wait_for_qdrant(qdrant_url_from_env)
    if not qdrant_url:
        return

    # --- 1. Charger et segmenter le document ---
    loader = TextLoader("./source_document.txt")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    print(f"Document segmenté en {len(docs)} chunks.")

    # --- 2. Configurer le client d'embedding pour l'API LLMaaS ---
    print(f"\nUtilisation du modèle d'embedding via l'API LLMaaS: {embedding_model_name}")
    # On utilise notre classe personnalisée `LLMaaSEmbeddings`.
    # C'est la solution la plus robuste car elle gère correctement l'authentification
    # par Bearer Token requise par notre API et garantit l'envoi de texte brut,
    # assurant la compatibilité avec tous nos backends (Ollama, VLLM).
    embeddings = LLMaaSEmbeddings(
        model=embedding_model_name,
        api_key=llmaas_api_key,
        api_base=llmaas_api_base,
    )

    # --- 3. Stocker les documents dans Qdrant ---
    print(f"\nStockage des documents dans Qdrant (collection: {collection_name})...")
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    vector_store = Qdrant.from_texts(
        texts,
        embeddings,
        metadatas=metadatas,
        url=qdrant_url,
        collection_name=collection_name,
        force_recreate=True,
    )
    print("Documents stockés avec succès.")

    # --- 4. Configurer le LLM et la chaîne RAG ---
    print(f"\nUtilisation du LLM via l'API LLMaaS: {llm_model_name}")
    llm = ChatOpenAI(
        model_name=llm_model_name,
        openai_api_key=llmaas_api_key,
        openai_api_base=llmaas_api_base,
        temperature=0.2,
    )

    prompt_template = """Utilise les morceaux de contexte suivants pour répondre à la question à la fin.
Si tu ne connais pas la réponse, dis simplement que tu ne sais pas, n'essaie pas d'inventer une réponse.

{context}

Question: {question}
Réponse en français:"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    retriever = vector_store.as_retriever()

    def format_docs(docs):
        """Formate les documents récupérés en une seule chaîne."""
        return "\n\n".join(doc.page_content for doc in docs)

    # Construction de la chaîne RAG avec LCEL (LangChain Expression Language)
    rag_chain = {"context": retriever | format_docs, "question": RunnablePassthrough()} | PROMPT | llm | StrOutputParser()

    # --- 5. Poser une question et suivre le processus RAG ---
    print("\n" + "=" * 50)
    print("--- DÉBUT DU PROCESSUS RAG ---")
    print("=" * 50)

    query = "Comment fonctionne le RAG et quels sont ses composants essentiels ?"
    print("\n" + f"[ÉTAPE 1/3] Question de l'utilisateur: '{query}'")

    # --- Journalisation manuelle pour la transparence ---
    print("\n" + "[ÉTAPE 2/3] Récupération des documents et construction du prompt...")
    relevant_docs = retriever.get_relevant_documents(query)
    print(f"  - {len(relevant_docs)} documents pertinents récupérés de Qdrant.")

    context_text = format_docs(relevant_docs)
    final_prompt_str = PROMPT.format(context=context_text, question=query)
    print("  - Construction du prompt final pour le LLM de génération:")
    print("-" * 20)
    print(final_prompt_str)
    print("-" * 20)

    final_llm_payload = {"model": llm_model_name, "messages": [{"role": "user", "content": final_prompt_str}]}
    print("\n" + "[PAYLOAD LLM -> LLMAAS API]")
    print(json.dumps(final_llm_payload, indent=2, ensure_ascii=False))
    # --- Fin de la journalisation ---

    print("\n" + f"[ÉTAPE 3/3] Appel de la chaîne RAG modernisée (LCEL) avec le contexte...")
    final_result = rag_chain.invoke(query)

    print("\n" + "=" * 50)
    print("--- RÉSULTAT FINAL ---")
    print("=" * 50)
    print(final_result)


if __name__ == "__main__":
    main()
