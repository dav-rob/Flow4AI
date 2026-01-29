"""
LlamaIndex RAG Pipeline

Demonstrates a simple Retrieval Augmented Generation (RAG) pipeline
using LlamaIndex with Flow4AI orchestration:
- Index documents in-memory with LlamaIndex
- Retrieve relevant context for queries
- Generate answers using retrieved context

Prerequisites:
    pip install llama-index-core llama-index-embeddings-openai llama-index-llms-openai
    export OPENAI_API_KEY=your_key_here
"""

import asyncio
import os
from dotenv import load_dotenv

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# Load environment variables from .env file
load_dotenv()

try:
    from llama_index.core import VectorStoreIndex, Document, Settings
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("⚠️  LlamaIndex not installed. Install with:")
    print("    pip install llama-index-core llama-index-embeddings-openai llama-index-llms-openai")


# =============================================================================
# Sample Data - Embedded documents about Flow4AI
# =============================================================================

DOCUMENTS = [
    """Flow4AI is a Python framework for orchestrating AI workflows. It provides
    a clean DSL for defining parallel and sequential job graphs, making it easy
    to coordinate multiple LLM calls efficiently.""",
    
    """The job() function wraps Python async functions as Flow4AI jobs. Jobs can
    be connected using >> for sequential execution or p() for parallel execution.
    Each job receives task input and can access upstream results via j_ctx.""",
    
    """Flow4AI integrates with LangChain by wrapping LangChain chains as async
    functions. This allows parallel execution of multiple chains with automatic
    coordination and result aggregation.""",
    
    """The FlowManager.run() method executes workflows with configurable timeouts.
    It returns (errors, results) tuple where results contains outputs from all
    leaf nodes in the workflow graph.""",
]

QUERY = "How do I connect jobs in Flow4AI?"


# =============================================================================
# RAG Jobs - Async functions for indexing, retrieval, and generation
# =============================================================================

async def create_index(docs: list) -> dict:
    """Create LlamaIndex vector store from documents."""
    if not LLAMAINDEX_AVAILABLE:
        return {"error": "LlamaIndex not installed"}
    
    # Configure LlamaIndex settings
    Settings.llm = OpenAI(model="gpt-4o-mini", max_tokens=150)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    
    # Create documents and index
    documents = [Document(text=doc) for doc in docs]
    index = VectorStoreIndex.from_documents(documents)
    
    return {
        "index": index,
        "doc_count": len(documents),
        "status": "indexed"
    }


async def query_and_generate(j_ctx, **kwargs) -> dict:
    """Query the index and generate an answer using retrieved context.
    
    Uses j_ctx["inputs"] to access the index from the previous stage.
    Query can be passed via kwargs or defaults to QUERY constant.
    """
    if not LLAMAINDEX_AVAILABLE:
        return {"error": "LlamaIndex not installed"}
    
    # Get index from previous job
    inputs = j_ctx["inputs"]
    index_result = inputs.get("index_docs", {})
    index = index_result.get("index")
    
    if not index:
        return {"error": "No index available"}
    
    # Get query from kwargs (task params) or use default
    query = kwargs.get("query", QUERY)
    
    # Create query engine and run query
    query_engine = index.as_query_engine()
    response = await asyncio.to_thread(query_engine.query, query)
    
    # Extract source nodes for attribution
    sources = []
    for node in response.source_nodes:
        sources.append({
            "text": node.text[:100] + "...",
            "score": round(node.score, 3) if node.score else None
        })
    
    return {
        "query": query,
        "answer": str(response),
        "sources": sources,
        "source_count": len(sources)
    }


# =============================================================================
# Main - Core Flow4AI + LlamaIndex integration
# =============================================================================

def main():
    """Run the LlamaIndex RAG example."""
    if not LLAMAINDEX_AVAILABLE:
        print("\n❌ LlamaIndex is not installed.")
        print("Install with:")
        print("    pip install llama-index-core llama-index-embeddings-openai llama-index-llms-openai\n")
        return False
    
    _print_header()
    
    # Create RAG pipeline jobs
    jobs = job({
        "index_docs": create_index,
        "query_generate": query_and_generate,
    })
    
    # Pattern: sequential RAG pipeline
    # index >> query+generate (retrieval and generation combined for simplicity)
    workflow = jobs["index_docs"] >> jobs["query_generate"]
    
    # Task provides documents to index and query to answer
    task = {
        "index_docs.docs": DOCUMENTS,
        "query_generate.query": QUERY,
    }
    
    # Execute the workflow
    errors, results = FlowManager.run(workflow, task, "rag_pipeline", timeout=60)
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    _print_results(results)
    return True


# =============================================================================
# Output Helpers - Terminal display formatting
# =============================================================================

def _print_header():
    """Print example header and description."""
    print("\n" + "="*60)
    print("LlamaIndex RAG Pipeline")
    print("="*60 + "\n")
    print("This example demonstrates:")
    print("- Document indexing with LlamaIndex VectorStoreIndex")
    print("- Query and retrieval with semantic search")
    print("- Answer generation using retrieved context\n")


def _print_results(results):
    """Print RAG results and source attribution."""
    print("="*60)
    print("✅ RAG Pipeline Complete")
    print("="*60 + "\n")
    
    print(f"Query: \"{results.get('query', '')}\"")
    print()
    print(f"Answer: {results.get('answer', 'N/A')}")
    print()
    
    print("-"*60)
    print(f"Sources ({results.get('source_count', 0)} retrieved):")
    print("-"*60)
    
    for i, source in enumerate(results.get("sources", []), 1):
        score = source.get("score", "N/A")
        print(f"\n  [{i}] Score: {score}")
        print(f"      {source.get('text', 'N/A')}")
    
    print("\n" + "="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ Documents indexed in-memory with LlamaIndex")
    print("✓ Semantic search retrieved relevant context")
    print("✓ LLM generated answer using retrieved sources")
    print("✓ Flow4AI orchestrated the pipeline with >>\n")
    print("="*60 + "\n")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
