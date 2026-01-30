"""
Query Pipeline Jobs for FlowManager

Demonstrates j_ctx["inputs"] pattern for chaining job outputs.
Each job receives outputs from upstream jobs via j_ctx["inputs"].

Workflow: embed_query >> vector_search >> bm25_rerank >> generate_answer
"""

from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

from .embedding import embed_chunk, get_client
from .indexing import search_collection
from .generation import generate_answer as _generate_answer


# =============================================================================
# Job 1: Embed Query
# =============================================================================

async def embed_query_job(j_ctx, **kwargs):
    """
    Embed the query text.
    
    Inputs (from task via **kwargs):
        - text: The query string
    
    Outputs:
        - embedding: The query embedding vector
        - query: The original query text (passed through)
    """
    query = kwargs.get("text", "")
    
    if not query:
        return {"status": "error", "error": "No query text provided"}
    
    result = await embed_chunk("query", query)
    
    if result.get("status") == "error":
        return {"status": "error", "error": result.get("error")}
    
    return {
        "status": "success",
        "embedding": result["embedding"],
        "query": query,
    }


# =============================================================================
# Job 2: Vector Search
# =============================================================================

async def vector_search_job(j_ctx):
    """
    Search ChromaDB for relevant chunks.
    
    Inputs (from j_ctx["inputs"]):
        - embed_query.embedding: The query embedding
    
    Parameters (from **kwargs):
        - collection: ChromaDB collection name (default: "rag_chunks")
        - top_k: Number of results (default: 20)
    
    Outputs:
        - results: List of matching chunks with scores
    """
    inputs = j_ctx["inputs"]
    
    # Get embedding from previous job
    embed_result = inputs.get("embed_query", {})
    if embed_result.get("status") == "error":
        return embed_result  # Propagate error
    
    embedding = embed_result["embedding"]
    collection_name = "rag_chunks"  # Hardcoded default
    top_k = 20  # Hardcoded default
    
    results = await search_collection(
        embedding,
        collection_name=collection_name,
        top_k=top_k,
    )
    
    if not results:
        return {"status": "no_results", "results": []}
    
    return {
        "status": "success",
        "results": results,
        "query": embed_result["query"],  # Pass query through for downstream jobs
    }


# =============================================================================
# Job 3: BM25 Rerank
# =============================================================================

def bm25_rerank_job(j_ctx):
    """
    Rerank results using BM25 algorithm.
    
    Inputs (from j_ctx["inputs"]):
        - embed_query.query: The original query text
        - vector_search.results: The vector search results
    
    Parameters (from **kwargs):
        - top_k: Number of final results (default: 5)
    
    Outputs:
        - results: Reranked results with combined scores
    """
    inputs = j_ctx["inputs"]
    
    # Get data from immediate predecessors (vector_search)
    search_result = inputs.get("vector_search", {})
    
    if search_result.get("status") != "success":
        return search_result  # Propagate error/no_results
    
    # Query was passed through from embed_query via vector_search
    query = search_result["query"]
    results = search_result["results"]
    top_k_final = 5  # Hardcoded default
    
    if not results:
        return {"status": "no_results", "results": []}
    
    # Build BM25 index from result texts
    tokenized_docs = [r["text"].lower().split() for r in results]
    bm25 = BM25Okapi(tokenized_docs)
    
    # Score query against results
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    
    # Combine scores (normalize and weight)
    for i, result in enumerate(results):
        result["bm25_score"] = float(bm25_scores[i])
        # Combined score: 70% vector, 30% BM25 (normalized)
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        normalized_bm25 = bm25_scores[i] / max_bm25
        result["combined_score"] = 0.7 * result["score"] + 0.3 * normalized_bm25
    
    # Sort by combined score and take top_k
    reranked = sorted(results, key=lambda x: x["combined_score"], reverse=True)[:top_k_final]
    
    # Calculate stats
    mean_vector = sum(r["score"] for r in reranked) / len(reranked)
    mean_bm25 = sum(r["bm25_score"] for r in reranked) / len(reranked)
    
    return {
        "status": "success",
        "results": reranked,
        "mean_vector_score": round(mean_vector, 4),
        "mean_bm25_score": round(mean_bm25, 4),
        "query": query,  # Pass query through for generate_answer
    }


# =============================================================================
# Job 4: Generate Answer
# =============================================================================

async def generate_answer_job(j_ctx):
    """
    Generate answer from context chunks.
    
    Inputs (from j_ctx["inputs"]):
        - embed_query.query: The original query text
        - bm25_rerank.results: The reranked context chunks
    
    Outputs:
        - answer: The generated answer
        - citations: Citation information
    """
    inputs = j_ctx["inputs"]
    
    # Get data from immediate predecessors (bm25_rerank)
    rerank_result = inputs.get("bm25_rerank", {})
    
    if rerank_result.get("status") != "success":
        return rerank_result  # Propagate error
    
    # Query was passed through from embed_query via vector_search and bm25_rerank
    query = rerank_result["query"]
    results = rerank_result["results"]
    
    # Call the generation function
    answer_result = await _generate_answer(query, results)
    
    # Include search stats in final result
    answer_result["search_stats"] = {
        "mean_vector_score": rerank_result.get("mean_vector_score"),
        "mean_bm25_score": rerank_result.get("mean_bm25_score"),
    }
    
    return answer_result
