"""
Massive Parallel RAG Pipeline

Demonstrates Flow4AI's parallel execution at scale with 1000+ document chunks.

This example shows:
- Parallel embedding: 1000+ chunks embedded concurrently (~85x faster)
- Sequential workflows: Job chaining with >> operator
- Data flow: j_ctx["inputs"] and j_ctx["saved_results"] patterns

Prerequisites:
    pip install chromadb rank-bm25
    export OPENAI_API_KEY=your_key_here

Usage:
    python rag_pipeline.py                    # Full pipeline
    python rag_pipeline.py --mode index       # Index only
    python rag_pipeline.py --mode query       # Query only
    python rag_pipeline.py --chunks 100       # Limit chunks
"""

import asyncio
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# Local imports
from utils.download import download_corpus, load_corpus
from utils.chunking import chunk_corpus, Chunk
from utils import output  # Output helpers
from jobs.embedding import embed_chunk, reset_client as reset_embed_client
from jobs.indexing import index_chunks, search_collection, get_chroma_client
from jobs.search import search_and_rerank
from jobs.generation import generate_answer, reset_client as reset_gen_client
from jobs.query_jobs import (
    embed_query_job,
    vector_search_job,
    bm25_rerank_job,
    generate_answer_job,
)


# =============================================================================
# Indexing Pipeline - Parallel Embedding with Flow4AI
# =============================================================================

def run_indexing_pipeline(
    max_chunks: int = None,
    reset_collection: bool = True,
    books: list = None,
) -> dict:
    """
    Parallel embedding pipeline demonstrating Flow4AI at scale.
    
    Flow4AI workflow:
        workflow = job(embed=embed_chunk)
        for chunk in chunks:
            fm.submit_task({...}, fq_name)  # All run in parallel!
    """
    output.section("INDEXING PIPELINE")
    
    # 1. Load corpus
    output.step("📥", "Downloading corpus...")
    if books is None:
        books = ["alice_wonderland", "sherlock_holmes", "frankenstein"]
    
    corpus_dir = Path(__file__).parent / "corpus"
    download_corpus(corpus_dir, books)
    corpus = load_corpus(corpus_dir)
    output.detail(f"Loaded {len(corpus)} documents")
    
    # 2. Chunk text
    output.step("✂️", "Chunking text...")
    chunks = chunk_corpus(corpus, chunk_size=500, overlap=100)
    output.detail(f"Created {len(chunks)} chunks")
    
    if max_chunks and len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        output.detail(f"Limited to {max_chunks} chunks for testing")
    
    # 3. Parallel embedding with Flow4AI
    output.step("🔄", f"Embedding {len(chunks)} chunks in parallel...")
    
    embeddings = []
    completion_count = [0]
    
    def on_complete(result):
        embeddings.append(result)
        completion_count[0] += 1
        output.progress(completion_count[0], len(chunks))
    
    # ----- FLOW4AI WORKFLOW (key code) -----
    workflow = job(embed=embed_chunk)
    fm = FlowManager(on_complete=on_complete)
    fq_name = fm.add_workflow(workflow, "embedding_pipeline")
    
    start_time = time.perf_counter()
    
    for chunk in chunks:
        task = {
            "embed.chunk_id": chunk.id,
            "embed.text": chunk.text,
        }
        fm.submit_task(task, fq_name)
    
    output.detail(f"Submitted {len(chunks)} tasks")
    
    success = fm.wait_for_completion(timeout=300, check_interval=0.5)
    embed_time = time.perf_counter() - start_time
    # ----- END FLOW4AI WORKFLOW -----
    
    if not success:
        output.error("Timeout waiting for embeddings")
        return {"status": "timeout"}
    
    output.stats("Embedded", len(embeddings), embed_time)
    
    # 4. Index in ChromaDB
    output.step("💾", "Indexing in ChromaDB...")
    
    chunk_dicts = [c.to_dict() for c in chunks]
    index_result = asyncio.run(index_chunks(
        chunk_dicts,
        embeddings,
        reset=reset_collection,
    ))
    
    if index_result.get("status") == "error":
        output.error(f"Indexing failed: {index_result.get('error')}")
        return index_result
    
    output.success(f"Indexed {index_result.get('indexed_count')} chunks")
    
    return {
        "status": "success",
        "chunks_created": len(chunks),
        "embeddings_created": len(embeddings),
        "indexed_count": index_result.get("indexed_count"),
        "embed_time": embed_time,
    }


# =============================================================================
# Indexing Pipeline - THROTTLED for Large Scale (3000+ chunks)
# =============================================================================

def run_indexing_pipeline_throttled(
    max_chunks: int = None,
    reset_collection: bool = True,
    books: list = None,
    max_concurrent: int = 500,
) -> dict:
    """
    Throttled embedding pipeline for large scale (3000+ chunks).
    
    Uses FlowManager's built-in max_concurrent to automatically throttle
    submission and avoid overwhelming the system.
    
    Args:
        max_concurrent: Maximum concurrent tasks (default: 500)
    """
    output.section("INDEXING PIPELINE (THROTTLED)")
    
    # 1. Load corpus
    output.step("📥", "Downloading corpus...")
    if books is None:
        books = ["alice_wonderland", "sherlock_holmes", "frankenstein"]
    
    corpus_dir = Path(__file__).parent / "corpus"
    download_corpus(corpus_dir, books)
    corpus = load_corpus(corpus_dir)
    output.detail(f"Loaded {len(corpus)} documents")
    
    # 2. Chunk text
    output.step("✂️", "Chunking text...")
    chunks = chunk_corpus(corpus, chunk_size=500, overlap=100)
    output.detail(f"Created {len(chunks)} chunks")
    
    if max_chunks and len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        output.detail(f"Limited to {max_chunks} chunks for testing")
    
    # 3. Parallel embedding with automatic throttling
    output.step("🔄", f"Embedding {len(chunks)} chunks (max_concurrent={max_concurrent})...")
    
    embeddings = []
    
    def on_complete(result):
        embeddings.append(result)
        if len(embeddings) == 1:
            output.detail("First embedding complete")
        elif len(embeddings) % 500 == 0:
            output.detail(f"Progress: {len(embeddings)}/{len(chunks)} complete")
    
    # ----- FLOW4AI THROTTLED WORKFLOW (clean API) -----
    workflow = job(embed=embed_chunk)
    fm = FlowManager(on_complete=on_complete, max_concurrent=max_concurrent)
    fq_name = fm.add_workflow(workflow, "embedding_pipeline")
    
    start_time = time.perf_counter()
    
    # Single call handles all throttling internally!
    fm.submit_batch(
        chunks,
        lambda chunk: {"embed.chunk_id": chunk.id, "embed.text": chunk.text},
        fq_name
    )
    
    success = fm.wait_for_completion(timeout=600, check_interval=0.5)
    embed_time = time.perf_counter() - start_time
    # ----- END FLOW4AI THROTTLED WORKFLOW -----
    
    if not success:
        output.error("Timeout waiting for embeddings")
        return {"status": "timeout"}
    
    output.stats("Embedded", len(embeddings), embed_time)
    
    # 4. Index in ChromaDB
    output.step("💾", "Indexing in ChromaDB...")
    
    chunk_dicts = [c.to_dict() for c in chunks]
    index_result = asyncio.run(index_chunks(
        chunk_dicts,
        embeddings,
        reset=reset_collection,
    ))
    
    if index_result.get("status") == "error":
        output.error(f"Indexing failed: {index_result.get('error')}")
        return index_result
    
    output.success(f"Indexed {index_result.get('indexed_count')} chunks")
    
    return {
        "status": "success",
        "chunks_created": len(chunks),
        "embeddings_created": len(embeddings),
        "indexed_count": index_result.get("indexed_count"),
        "embed_time": embed_time,
        "mode": "throttled",
    }


# =============================================================================
# Query Pipeline - Direct Async Version
# =============================================================================

async def run_query_pipeline(query: str) -> dict:
    """
    Direct async query pipeline (for comparison with FlowManager version).
    """
    output.section("QUERY PIPELINE (Direct Async)")
    output.detail(f"Query: {query}")
    
    reset_embed_client()
    reset_gen_client()
    
    output.step("🔍", "Embedding query...")
    from jobs.embedding import embed_text
    query_embedding = await embed_text(query)
    
    output.step("🔎", "Vector search...")
    search_result = await search_collection(query, query_embedding, top_k=10)
    
    if not search_result["results"]:
        output.error("No results found")
        return {"status": "error", "error": "No results"}
    
    output.step("📊", "Reranking with BM25...")
    rerank_result = await search_and_rerank(
        query, query_embedding, 
        chroma_results=search_result["results"],
        top_k=5,
    )
    
    output.step("🤖", "Generating answer...")
    answer_result = await generate_answer(query, rerank_result["combined_results"])
    
    output.success(f"Generated answer with {answer_result['citations']['total_cited']} citations")
    
    return {
        "status": "success",
        "query": query,
        "answer": answer_result["answer"],
        "citations": answer_result["citations"],
        "search_stats": {
            "mean_vector_score": rerank_result.get("mean_vector_score"),
            "mean_bm25_score": rerank_result.get("mean_bm25_score"),
        },
    }


# =============================================================================
# Query Pipeline - FlowManager with Job Chaining
# =============================================================================

def run_query_pipeline_fm(query: str) -> dict:
    """
    FlowManager query pipeline with explicit job chaining.
    
    Flow4AI workflow:
        embed_query >> vector_search >> bm25_rerank >> generate_answer
        
    Each job receives predecessor output via j_ctx["inputs"].
    """
    output.section("QUERY PIPELINE (FlowManager)")
    output.detail(f"Query: {query}")
    
    reset_embed_client()
    reset_gen_client()
    
    # ----- FLOW4AI WORKFLOW (key code) -----
    query_workflow = (
        job(embed_query=embed_query_job)
        >> job(vector_search=vector_search_job)
        >> job(bm25_rerank=bm25_rerank_job)
        >> job(generate_answer=generate_answer_job)
    )
    
    result_holder = {}
    fm = FlowManager(on_complete=lambda r: result_holder.update({"result": r}))
    fq_name = fm.add_workflow(query_workflow, "query_pipeline")
    
    # Only first job needs params; rest get data via j_ctx["inputs"]
    task = {"embed_query": {"text": query}}
    
    output.step("🔄", "Running: embed >> search >> rerank >> generate")
    fm.submit_task(task, fq_name)
    
    success = fm.wait_for_completion(timeout=60)
    # ----- END FLOW4AI WORKFLOW -----
    
    if not success:
        output.error("Timeout")
        return {"status": "error", "error": "Timeout"}
    
    result = result_holder.get("result", {})
    
    if result.get("status") != "success":
        output.error(f"Failed: {result.get('error', 'Unknown')}")
        return result
    
    output.success(f"Generated answer with {result['citations']['total_cited']} citations")
    output.detail(f"Mean vector score: {result['search_stats']['mean_vector_score']}")
    output.detail(f"Mean BM25 score: {result['search_stats']['mean_bm25_score']}")
    
    return {
        "status": "success",
        "query": query,
        "answer": result["answer"],
        "citations": result["citations"],
        "search_stats": result["search_stats"],
    }


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the RAG pipeline."""
    parser = argparse.ArgumentParser(description="Massive Parallel RAG Pipeline")
    parser.add_argument("--mode", choices=["full", "index", "query"], default="full")
    parser.add_argument("--chunks", type=int, default=None, help="Limit chunks")
    parser.add_argument("--query", type=str, default="What happens to Alice in Wonderland?")
    parser.add_argument("--books", nargs="+", default=None)
    parser.add_argument("--throttle", action="store_true", 
                        help="Use throttled submission for large datasets (3000+ chunks)")
    parser.add_argument("--max-concurrent", type=int, default=500,
                        help="Max concurrent tasks for throttled mode (default: 500)")
    
    args = parser.parse_args()
    
    output.section("🚀 Flow4AI Massive Parallel RAG Pipeline")
    
    if args.mode in ["full", "index"]:
        if args.throttle:
            index_result = run_indexing_pipeline_throttled(
                max_chunks=args.chunks,
                books=args.books,
                max_concurrent=args.max_concurrent,
            )
        else:
            index_result = run_indexing_pipeline(
                max_chunks=args.chunks,
                books=args.books,
            )
        
        if index_result.get("status") != "success":
            output.error("Indexing failed")
            return False
        
        output.summary_table("📊 INDEXING SUMMARY", [
            ("Chunks", str(index_result['chunks_created'])),
            ("Embeddings", str(index_result['embeddings_created'])),
            ("Indexed", str(index_result['indexed_count'])),
            ("Time", f"{index_result['embed_time']:.2f}s"),
            ("Mode", index_result.get('mode', 'parallel')),
        ])
    
    if args.mode in ["full", "query"]:
        if args.mode == "full":
            reset_embed_client()
            reset_gen_client()
        
        query_result = asyncio.run(run_query_pipeline(args.query))
        
        if query_result.get("status") != "success":
            output.error("Query failed")
            return False
        
        output.summary_table("📊 QUERY RESULT", [
            ("Citations", f"{query_result['citations']['total_cited']} sources"),
        ])
        print(f"\n{query_result['answer']}")
    
    output.section("✅ Pipeline complete!")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
