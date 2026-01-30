"""
ChromaDB indexing job for storing embeddings.

Uses ChromaDB for persistent vector storage.
"""

import os
from typing import List, Optional
from pathlib import Path

# Try to import chromadb
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def get_chroma_client(persist_dir: Path = None) -> 'chromadb.Client':
    """Get ChromaDB client with persistence."""
    if not CHROMADB_AVAILABLE:
        raise ImportError("chromadb not installed. Install with: pip install chromadb")
    
    if persist_dir is None:
        persist_dir = Path(__file__).parent.parent / "chroma_db"
    
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    return chromadb.PersistentClient(path=str(persist_dir))


def get_or_create_collection(
    client: 'chromadb.Client',
    name: str = "rag_chunks",
    reset: bool = False,
) -> 'chromadb.Collection':
    """Get or create a ChromaDB collection."""
    if reset:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


async def index_chunks(
    chunks: List[dict],
    embeddings: List[dict],
    collection_name: str = "rag_chunks",
    reset: bool = False,
) -> dict:
    """
    Index chunks with their embeddings in ChromaDB.
    
    Args:
        chunks: List of chunk dicts from chunking
        embeddings: List of embedding dicts from embed_chunk
        collection_name: Name of ChromaDB collection
        reset: Whether to delete existing collection
    
    Returns:
        Dict with indexing statistics
    """
    if not CHROMADB_AVAILABLE:
        return {"error": "chromadb not installed", "status": "error"}
    
    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name, reset)
    
    # Build data for ChromaDB
    ids = []
    documents = []
    metadatas = []
    embedding_vectors = []
    
    # Create a mapping of chunk_id to embedding
    embed_map = {e["chunk_id"]: e for e in embeddings if e.get("status") == "success"}
    
    for chunk in chunks:
        chunk_id = chunk["id"] if isinstance(chunk, dict) else chunk.id
        
        if chunk_id not in embed_map:
            continue
        
        embed_result = embed_map[chunk_id]
        chunk_data = chunk if isinstance(chunk, dict) else chunk.to_dict()
        
        ids.append(chunk_id)
        documents.append(chunk_data["text"])
        metadatas.append({
            "source": chunk_data.get("source", "unknown"),
            "start_char": chunk_data.get("start_char", 0),
            "end_char": chunk_data.get("end_char", 0),
            "chunk_index": chunk_data.get("chunk_index", 0),
        })
        embedding_vectors.append(embed_result["embedding"])
    
    if not ids:
        return {"error": "No valid embeddings to index", "status": "error"}
    
    # Add to collection in batches (ChromaDB has limits)
    batch_size = 100
    indexed_count = 0
    
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_embeds = embedding_vectors[i:i+batch_size]
        
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_embeds,
        )
        indexed_count += len(batch_ids)
    
    return {
        "indexed_count": indexed_count,
        "collection_name": collection_name,
        "status": "success",
    }


def search_collection(
    query_embedding: List[float],
    collection_name: str = "rag_chunks",
    top_k: int = 20,
) -> List[dict]:
    """
    Search the collection using a query embedding.
    
    Args:
        query_embedding: The query vector
        collection_name: Name of ChromaDB collection
        top_k: Number of results to return
    
    Returns:
        List of results with text, metadata, and distance
    """
    if not CHROMADB_AVAILABLE:
        return []
    
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    
    # Format results
    formatted = []
    for i in range(len(results["ids"][0])):
        formatted.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
            "score": 1 - results["distances"][0][i],  # Convert distance to similarity
        })
    
    return formatted
