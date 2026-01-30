"""
Embedding job for parallel chunk processing.

Uses OpenAI embeddings via the openai library directly.
"""

import os
import asyncio
from typing import List
from openai import AsyncOpenAI

# Global client (initialized once per event loop)
_client = None


def get_client() -> AsyncOpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def reset_client():
    """Reset the client (needed when switching event loops via asyncio.run)."""
    global _client
    _client = None


async def embed_chunk(chunk_id: str, text: str, model: str = "text-embedding-3-small") -> dict:
    """
    Embed a single chunk of text.
    
    This is the core job function that Flow4AI will parallelize.
    
    Args:
        chunk_id: Unique identifier for the chunk
        text: The text content to embed
        model: OpenAI embedding model to use
    
    Returns:
        Dict with chunk_id, embedding, and metadata
    """
    client = get_client()
    
    try:
        response = await client.embeddings.create(
            input=text,
            model=model,
        )
        embedding = response.data[0].embedding
        
        return {
            "chunk_id": chunk_id,
            "embedding": embedding,
            "text": text,
            "model": model,
            "dimensions": len(embedding),
            "status": "success",
        }
    except Exception as e:
        return {
            "chunk_id": chunk_id,
            "error": str(e),
            "status": "error",
        }


async def embed_batch(chunks: List[dict], model: str = "text-embedding-3-small") -> List[dict]:
    """
    Embed a batch of chunks in parallel.
    
    This is a convenience function for testing, the actual parallel execution
    should use Flow4AI's submit_task pattern.
    
    Args:
        chunks: List of chunk dicts with 'id' and 'text' keys
        model: OpenAI embedding model
    
    Returns:
        List of embedding results
    """
    tasks = [
        embed_chunk(chunk["id"], chunk["text"], model)
        for chunk in chunks
    ]
    return await asyncio.gather(*tasks)
