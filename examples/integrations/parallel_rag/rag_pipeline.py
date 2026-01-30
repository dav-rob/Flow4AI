"""
Massive Parallel RAG Pipeline

Demonstrates Flow4AI's parallel execution at scale with 1000+ document chunks.

This example implements a production-grade RAG pipeline:
- Download corpus from Project Gutenberg
- Chunk text with overlap
- Parallel embedding using Flow4AI (1000+ concurrent tasks)
- Store in ChromaDB vector database
- Search with reranking
- Answer generation with citations

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

# Load environment variables
load_dotenv()

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# Local imports
from utils.download import download_corpus, load_corpus
from utils.chunking import chunk_corpus, Chunk
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
# Indexing Pipeline - Parallel embedding with Flow4AI
# =============================================================================

def run_indexing_pipeline(
    max_chunks: int = None,
    reset_collection: bool = True,
    books: list = None,
) -> dict:
    """
    Run the indexing pipeline.
    
    This demonstrates Flow4AI's massive parallel execution:
    - Submit 1000+ embedding tasks concurrently
    - Tasks complete while others are still being submitted
    
    Args:
        max_chunks: Limit number of chunks (for testing)
        reset_collection: Whether to clear existing collection
        books: List of book names to download
    
    Returns:
        Dict with indexing statistics
    """
    print("\n" + "="*60)
    print("INDEXING PIPELINE")
    print("="*60)
    
    # 1. Download corpus
    print("\n📥 Downloading corpus...")
    if books is None:
        books = ["alice_wonderland", "sherlock_holmes", "frankenstein"]
    
    corpus_dir = Path(__file__).parent / "corpus"
    download_corpus(corpus_dir, books)
    
    corpus = load_corpus(corpus_dir)
    print(f"   Loaded {len(corpus)} documents")
    
    # 2. Chunk text
    print("\n✂️  Chunking text...")
    chunks = chunk_corpus(corpus, chunk_size=500, overlap=100)
    print(f"   Created {len(chunks)} chunks")
    
    if max_chunks and len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        print(f"   Limited to {max_chunks} chunks for testing")
    
    # 3. Parallel embedding with Flow4AI
    print(f"\n🔄 Embedding {len(chunks)} chunks in parallel...")
    
    # Track completions
    embeddings = []
    completion_count = [0]  # Use list for mutability in closure
    
    def on_complete(result):
        embeddings.append(result)
        completion_count[0] += 1
        if completion_count[0] == 1:
            print(f"   🎯 First embedding complete")
        elif completion_count[0] % 100 == 0:
            print(f"   ⏱️  {completion_count[0]}/{len(chunks)} complete")
    
    # Create Flow4AI workflow
    workflow = job(embed=embed_chunk)
    fm = FlowManager(on_complete=on_complete)
    fq_name = fm.add_workflow(workflow, "embedding_pipeline")
    
    start_time = time.perf_counter()
    
    # Submit all tasks
    for chunk in chunks:
        task = {
            "embed.chunk_id": chunk.id,
            "embed.text": chunk.text,
        }
        fm.submit_task(task, fq_name)
    
    print(f"   📤 Submitted {len(chunks)} tasks")
    
    # Wait for completion
    success = fm.wait_for_completion(timeout=300, check_interval=0.5)
    
    embed_time = time.perf_counter() - start_time
    
    if not success:
        print("   ❌ Timeout waiting for embeddings")
        return {"status": "timeout"}
    
    print(f"   ✅ Embedded {len(embeddings)} chunks in {embed_time:.2f}s")
    print(f"   ⚡ Rate: {len(embeddings)/embed_time:.1f} chunks/sec")
    
    # 4. Index in ChromaDB
    print("\n💾 Indexing in ChromaDB...")
    
    # Convert Chunk objects to dicts for indexing
    chunk_dicts = [c.to_dict() for c in chunks]
    
    # Run indexing synchronously (ChromaDB is not async)
    index_result = asyncio.run(index_chunks(
        chunk_dicts,
        embeddings,
        reset=reset_collection,
    ))
    
    if index_result.get("status") == "error":
        print(f"   ❌ Indexing failed: {index_result.get('error')}")
        return index_result
    
    print(f"   ✅ Indexed {index_result.get('indexed_count')} chunks")
    
    return {
        "status": "success",
        "chunks_created": len(chunks),
        "embeddings_created": len(embeddings),
        "indexed_count": index_result.get("indexed_count"),
        "embed_time": embed_time,
    }


# =============================================================================
# Query Pipeline - Search and answer with citations
# =============================================================================

async def run_query_pipeline(query: str) -> dict:
    """
    Run a single query through the RAG pipeline.
    
    Args:
        query: The user's question
    
    Returns:
        Dict with answer and citations
    """
    print("\n" + "="*60)
    print("QUERY PIPELINE")
    print("="*60)
    print(f"\n❓ Query: {query}")
    
    # 1. Search with reranking
    print("\n🔍 Searching...")
    search_result = await search_and_rerank(query, top_k_initial=20, top_k_final=5)
    
    if search_result.get("status") != "success":
        print(f"   ❌ Search failed: {search_result.get('error', 'No results')}")
        return search_result
    
    print(f"   ✅ Found {len(search_result['results'])} relevant chunks")
    print(f"   📊 Mean vector score: {search_result['mean_vector_score']}")
    print(f"   📊 Mean BM25 score: {search_result['mean_bm25_score']}")
    
    # 2. Generate answer with citations
    print("\n💡 Generating answer...")
    answer_result = await generate_answer(query, search_result["results"])
    
    if answer_result.get("status") != "success":
        print(f"   ❌ Generation failed: {answer_result.get('error')}")
        return answer_result
    
    print(f"   ✅ Generated answer with {answer_result['citations']['total_cited']} citations")
    
    return {
        "status": "success",
        "query": query,
        "answer": answer_result["answer"],
        "citations": answer_result["citations"],
        "search_stats": {
            "mean_vector_score": search_result["mean_vector_score"],
            "mean_bm25_score": search_result["mean_bm25_score"],
        },
    }


# =============================================================================
# Query Pipeline - FlowManager Version with Job Chaining
# =============================================================================

def run_query_pipeline_fm(query: str) -> dict:
    """
    Run a single query using FlowManager with explicit job chaining.
    
    This demonstrates:
    - Sequential workflow with >> operator
    - j_ctx["inputs"] for accessing predecessor outputs
    - Explicit data flow between jobs
    
    Args:
        query: The user's question
    
    Returns:
        Dict with answer and citations
    """
    print("\n" + "="*60)
    print("QUERY PIPELINE (FlowManager)")
    print("="*60)
    print(f"\n❓ Query: {query}")
    
    # Reset clients for fresh connections
    reset_embed_client()
    reset_gen_client()
    
    # Define sequential workflow using >> operator
    # Each job's output becomes available to next job via j_ctx["inputs"]
    query_workflow = (
        job(embed_query=embed_query_job)
        >> job(vector_search=vector_search_job)
        >> job(bm25_rerank=bm25_rerank_job)
        >> job(generate_answer=generate_answer_job)
    )
    
    # Create FlowManager
    result_holder = {}
    
    def on_complete(result):
        result_holder["result"] = result
    
    fm = FlowManager(on_complete=on_complete)
    fq_name = fm.add_workflow(query_workflow, "query_pipeline")
    
    # Submit task: only embed_query needs params
    # Other jobs get all data from j_ctx["inputs"] (predecessor outputs)
    task = {
        "embed_query": {"text": query},
    }
    
    print("\n🔄 Running workflow: embed_query >> vector_search >> bm25_rerank >> generate_answer")
    fm.submit_task(task, fq_name)
    
    success = fm.wait_for_completion(timeout=60)
    
    if not success:
        print("   ❌ Timeout")
        return {"status": "error", "error": "Timeout"}
    
    # Extract result
    result = result_holder.get("result", {})
    
    if result.get("status") != "success":
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        return result
    
    print(f"   ✅ Generated answer with {result['citations']['total_cited']} citations")
    print(f"   📊 Mean vector score: {result['search_stats']['mean_vector_score']}")
    print(f"   📊 Mean BM25 score: {result['search_stats']['mean_bm25_score']}")
    
    return {
        "status": "success",
        "query": query,
        "answer": result["answer"],
        "citations": result["citations"],
        "search_stats": result["search_stats"],
    }


# =============================================================================
# Main - Full pipeline or individual modes
# =============================================================================

def main():
    """Run the RAG pipeline."""
    parser = argparse.ArgumentParser(description="Massive Parallel RAG Pipeline")
    parser.add_argument("--mode", choices=["full", "index", "query"], default="full",
                        help="Pipeline mode: full, index, or query")
    parser.add_argument("--chunks", type=int, default=None,
                        help="Limit number of chunks (for testing)")
    parser.add_argument("--query", type=str, default="What happens to Alice in Wonderland?",
                        help="Query for search (in query mode)")
    parser.add_argument("--books", nargs="+", default=None,
                        help="Books to download (e.g., alice_wonderland sherlock_holmes)")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 Flow4AI Massive Parallel RAG Pipeline")
    print("="*60)
    
    if args.mode in ["full", "index"]:
        index_result = run_indexing_pipeline(
            max_chunks=args.chunks,
            books=args.books,
        )
        
        if index_result.get("status") != "success":
            print("\n❌ Indexing failed")
            return False
        
        print("\n" + "-"*60)
        print("📊 INDEXING SUMMARY")
        print("-"*60)
        print(f"   Chunks created: {index_result['chunks_created']}")
        print(f"   Embeddings: {index_result['embeddings_created']}")
        print(f"   Indexed: {index_result['indexed_count']}")
        print(f"   Embed time: {index_result['embed_time']:.2f}s")
    
    if args.mode in ["full", "query"]:
        # Reset OpenAI clients before new event loop (fixes stale connection issue)
        if args.mode == "full":
            reset_embed_client()
            reset_gen_client()
        
        query_result = asyncio.run(run_query_pipeline(args.query))
        
        if query_result.get("status") != "success":
            print("\n❌ Query failed")
            return False
        
        print("\n" + "-"*60)
        print("📊 QUERY RESULT")
        print("-"*60)
        print(f"\n{query_result['answer']}")
        print("\n" + "-"*60)
        print(f"Citations: {query_result['citations']['total_cited']} of {query_result['citations']['total_shown']} chunks")
        print(f"Cited: {query_result['citations']['cited']}")
    
    print("\n" + "="*60)
    print("✅ Pipeline complete!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
