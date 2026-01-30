"""
Search job for RAG queries with reranking.
"""

import asyncio
from typing import List, Tuple
from .embedding import embed_chunk
from .indexing import search_collection

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.reranker import rerank


async def search_and_rerank(
    query: str,
    collection_name: str = "rag_chunks",
    top_k_initial: int = 20,
    top_k_final: int = 5,
) -> dict:
    """
    Search for relevant chunks and rerank results.
    
    This job:
    1. Embeds the query
    2. Does vector similarity search
    3. Reranks with BM25
    
    Args:
        query: The search query
        collection_name: ChromaDB collection name
        top_k_initial: Initial number of results from vector search
        top_k_final: Final number after reranking
    
    Returns:
        Dict with search results and scores
    """
    # Embed the query
    query_result = await embed_chunk("query", query)
    
    if query_result.get("status") == "error":
        return {
            "error": query_result.get("error"),
            "status": "error",
        }
    
    query_embedding = query_result["embedding"]
    
    # Vector search
    vector_results = await search_collection(
        query_embedding,
        collection_name=collection_name,
        top_k=top_k_initial,
    )
    
    if not vector_results:
        return {
            "query": query,
            "results": [],
            "status": "no_results",
        }
    
    # Calculate mean cosine score (for logging/observability)
    mean_vector_score = sum(r["score"] for r in vector_results) / len(vector_results)
    
    # Rerank with BM25
    reranked = rerank(query, vector_results, top_k=top_k_final)
    
    # Format final results
    final_results = []
    for doc, bm25_score in reranked:
        final_results.append({
            "id": doc["id"],
            "text": doc["text"],
            "source": doc["metadata"]["source"],
            "vector_score": doc["score"],
            "bm25_score": float(bm25_score),
            "chunk_index": doc["metadata"]["chunk_index"],
        })
    
    # Calculate mean reranker score
    mean_bm25_score = sum(r["bm25_score"] for r in final_results) / len(final_results) if final_results else 0
    
    return {
        "query": query,
        "results": final_results,
        "mean_vector_score": round(mean_vector_score, 4),
        "mean_bm25_score": round(mean_bm25_score, 4),
        "total_retrieved": len(vector_results),
        "total_reranked": len(final_results),
        "status": "success",
    }
