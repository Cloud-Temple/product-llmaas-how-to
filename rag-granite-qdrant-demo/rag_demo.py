# -*- coding: utf-8 -*-
"""
Ce script est un démonstrateur d'une architecture RAG (Retrieval-Augmented Generation)
complète, utilisant Qdrant comme base de données vectorielle et l'API LLMaaS pour
l'embedding et la génération.

Il est conçu pour être exécuté dans un environnement Docker Compose, où les services
(cette application et Qdrant) sont orchestrés.

Le processus est le suivant :
1.  Attendre que le service Qdrant soit disponible.
2.  Charger un document source depuis un fichier texte.
3.  Segmenter (chunk) le document en plus petits morceaux.
4.  Vectoriser (embed) chaque morceau à l'aide d'un modèle d'embedding via l'API LLMaaS.
5.  Stocker ces vecteurs dans une collection Qdrant.
6.  Définir une chaîne RAG (pipeline) à l'aide de LangChain Expression Language (LCEL).
7.  Poser une question, qui déclenche la chaîne :
    a. La question est vectorisée.
    b. Qdrant est interrogé pour trouver les documents les plus similaires.
    c. Un prompt est construit avec la question et les documents récupérés.
    d. Le LLM de génération est appelé via l'API LLMaaS pour répondre à la question.
8.  Afficher le résultat final.
"""

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

# ==============================================================================
# CLASSE D'EMBEDDING PERSONNALISÉE
# ==============================================================================

class LLMaaSEmbeddings(Embeddings):
    """
    Classe d'embedding personnalisée pour interagir avec l'API LLMaaS.
    
    Cette classe est une solution de contournement robuste aux problèmes d'incompatibilité
    des clients LangChain standards (`OpenAIEmbeddings`, `OllamaEmbeddings`) avec notre API.
    Elle garantit que :
    1. Le texte brut est envoyé à l'API (et non des tokens pré-calculés).
    2. L'authentification par Bearer Token est correctement gérée.
    """

    def __init__(self, model: str, api_base: str, api_key: str):
        """
        Initialise le client d'embedding.
        
        Args:
            model (str): Le nom du modèle d'embedding à utiliser (ex: "granite-embedding:278m").
            api_base (str): L'URL de base de l'API LLMaaS (ex: "https://api.ai.cloud-temple.com/v1").
            api_key (str): La clé d'API pour l'authentification.
        """
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
            response.raise_for_status()  # Lève une exception pour les erreurs HTTP.
            result = response.json()
            return result["data"][0]["embedding"]
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'appel à l'API d'embedding: {e}")
            raise
        except (KeyError, IndexError) as e:
            print(f"Erreur dans le format de la réponse de l'API d'embedding: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Génère les embeddings pour une liste de documents."""
        print(f"Génération des embeddings pour {len(texts)} documents avec le modèle '{self.model}'...")
        # Note : Pour une meilleure performance en production, on pourrait envoyer les textes par lots (batch).
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Génère l'embedding pour une seule requête (question)."""
        print(f"Génération de l'embedding pour la requête avec le modèle '{self.model}'...")
        return self._embed(text)

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def wait_for_qdrant(qdrant_url, retries=15, delay=5):
    """
    Attend que le service Qdrant soit disponible.
    C'est essentiel dans un environnement Docker Compose où les conteneurs
    peuvent démarrer à des moments différents.
    """
    print(f"En attente de Qdrant sur {qdrant_url}...")
    client = qdrant_client.QdrantClient(url=qdrant_url)
    for i in range(retries):
        try:
            # Tente une opération simple pour vérifier si le service est prêt.
            client.get_collections()
            print("Qdrant est prêt.")
            return qdrant_url
        except Exception:
            print(f"Tentative {i+1}/{retries}: Qdrant n'est pas encore accessible.")
            time.sleep(delay)
    print("Erreur: Impossible de se connecter à Qdrant après plusieurs tentatives.")
    return None

# ==============================================================================
# ORCHESTRATION PRINCIPALE
# ==============================================================================

def main():
    """
    Fonction principale qui orchestre le pipeline RAG.
    """
    load_dotenv()

    # --- Configuration ---
    # Chargement de toutes les configurations depuis les variables d'environnement (fichier .env).
    qdrant_url_from_env = os.getenv("QDRANT_URL")
    collection_name = os.getenv("COLLECTION_NAME")
    llmaas_api_base = os.getenv("LLMAAS_API_BASE")
    llmaas_api_key = os.getenv("LLMAAS_API_KEY")
    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
    llm_model_name = os.getenv("LLM_MODEL_NAME")

    # Vérification que toutes les variables nécessaires sont définies.
    if not all([qdrant_url_from_env, collection_name, llmaas_api_base, llmaas_api_key, embedding_model_name, llm_model_name]):
        print("Erreur: Toutes les variables d'environnement requises ne sont pas définies dans .env")
        return

    # Assertions pour satisfaire l'analyseur de type statique (Pylance)
    assert qdrant_url_from_env is not None
    assert collection_name is not None
    assert llmaas_api_base is not None
    assert llmaas_api_key is not None
    assert embedding_model_name is not None
    assert llm_model_name is not None

    # --- Attendre Qdrant ---
    qdrant_url = wait_for_qdrant(qdrant_url_from_env)
    if not qdrant_url:
        return

    # --- 1. Charger et Segmenter le Document ---
    print("\n--- [ÉTAPE 1/5] Chargement et Segmentation du Document ---")
    # Charge le contenu du fichier source.
    loader = TextLoader("./source_document.txt")
    documents = loader.load()
    # Découpe le document en plus petits morceaux (chunks) pour une meilleure pertinence de recherche.
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    print(f"Document segmenté en {len(docs)} chunks.")

    # --- 2. Configurer le Client d'Embedding ---
    print(f"\n--- [ÉTAPE 2/5] Configuration du Client d'Embedding ---")
    print(f"Modèle utilisé : {embedding_model_name}")
    embeddings = LLMaaSEmbeddings(
        model=embedding_model_name,
        api_key=llmaas_api_key,
        api_base=llmaas_api_base,
    )

    # --- 3. Stocker les Documents dans Qdrant (Ingestion) ---
    print(f"\n--- [ÉTAPE 3/5] Ingestion des Données dans Qdrant ---")
    print(f"Collection cible : {collection_name}")
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    # Cette fonction de LangChain gère automatiquement la vectorisation des textes
    # via notre classe `embeddings` et les stocke dans la base de données vectorielle Qdrant.
    vector_store = Qdrant.from_texts(
        texts,
        embeddings,
        metadatas=metadatas,
        url=qdrant_url,
        collection_name=collection_name,
        force_recreate=True,  # Supprime et recrée la collection à chaque exécution.
    )
    print("Documents stockés avec succès.")

    # --- 4. Configurer le LLM et la Chaîne RAG ---
    print(f"\n--- [ÉTAPE 4/5] Configuration de la Chaîne RAG ---")
    print(f"Modèle de génération utilisé : {llm_model_name}")
    # Configure le client pour le LLM de génération.
    llm = ChatOpenAI(
        model_name=llm_model_name,
        openai_api_key=llmaas_api_key,
        openai_api_base=llmaas_api_base,
        temperature=0.2, # Température basse pour des réponses factuelles.
    )

    # Template du prompt qui sera envoyé au LLM de génération.
    # Il contient des placeholders pour le contexte (récupéré de Qdrant) et la question.
    prompt_template = """Utilise les morceaux de contexte suivants pour répondre à la question à la fin.
Si tu ne connais pas la réponse, dis simplement que tu ne sais pas, n'essaie pas d'inventer une réponse.

{context}

Question: {question}
Réponse en français:"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # Le "retriever" est l'objet qui sait comment interroger la base de données vectorielle.
    retriever = vector_store.as_retriever()

    def format_docs(docs):
        """Fonction simple pour concaténer le contenu des documents récupérés."""
        return "\n\n".join(doc.page_content for doc in docs)

    # Construction de la chaîne RAG avec LangChain Expression Language (LCEL).
    # C'est une manière moderne et déclarative de définir des pipelines de traitement.
    # Le `|` (pipe) enchaîne les étapes.
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )

    # --- 5. Exécuter la Chaîne RAG ---
    print("\n" + "="*50)
    print("--- [ÉTAPE 5/5] Exécution du Pipeline RAG ---")
    print("="*50)

    query = "Comment fonctionne le RAG et quels sont ses composants essentiels ?"
    print(f"\nQuestion de l'utilisateur: '{query}'")

    # --- Journalisation manuelle pour la transparence du processus ---
    print("\n[Détails du processus de récupération...]")
    relevant_docs = retriever.get_relevant_documents(query)
    print(f"  - {len(relevant_docs)} documents pertinents récupérés de Qdrant.")
    context_text = format_docs(relevant_docs)
    final_prompt_str = PROMPT.format(context=context_text, question=query)
    print("  - Construction du prompt final pour le LLM de génération:")
    print("-" * 20)
    print(final_prompt_str)
    print("-" * 20)
    # --- Fin de la journalisation ---

    print(f"\nAppel de la chaîne RAG avec le contexte...")
    final_result = rag_chain.invoke(query)

    print("\n" + "="*50)
    print("--- RÉSULTAT FINAL ---")
    print("="*50)
    print(final_result)


if __name__ == "__main__":
    main()
