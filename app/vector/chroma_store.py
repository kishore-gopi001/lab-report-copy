# app/vector/chroma_store.py

import uuid
import chromadb
from chromadb.config import Settings
from ai.embedding_service import embed_text, embed_texts

# Persistent Chroma DB
client = chromadb.PersistentClient(
    path="data/chroma",
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_or_create_collection(
    name="lab_rag_knowledge"
)

def add_documents(texts: list[str], metadatas: list[dict]):
    """Add documents with embeddings and metadata"""
    if not texts:
        return
    
    embeddings = embed_texts(texts)
    ids = [str(uuid.uuid4()) for _ in texts]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

def search_documents(query: str, k: int = 1, where: dict = None):
    """Semantic Search using ChromaDB with optional filtering"""
    query_embedding = embed_text(query)

    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"]
    }
    
    if where:
        query_params["where"] = where

    results = collection.query(**query_params)

    docs = []
    if results["documents"]:
        for i in range(len(results["documents"][0])):
            docs.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # cosine similarity approximation
            })

    return docs
