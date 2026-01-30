"""
Answer generation job with citation logging.

Uses OpenAI for generation with structured output for citations.
"""

import asyncio
from typing import List
from openai import AsyncOpenAI

# Global client
_client = None


def get_client() -> AsyncOpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


async def generate_answer(
    query: str,
    context_chunks: List[dict],
    model: str = "gpt-4o-mini",
    max_tokens: int = 500,
) -> dict:
    """
    Generate an answer with citations.
    
    This job:
    1. Formats context from retrieved chunks
    2. Generates answer with citations
    3. Logs which chunks were cited
    
    Args:
        query: The user's question
        context_chunks: List of retrieved chunk dicts
        model: OpenAI model to use
        max_tokens: Maximum tokens in response
    
    Returns:
        Dict with answer, citations, and logging data
    """
    client = get_client()
    
    if not context_chunks:
        return {
            "query": query,
            "answer": "I don't have enough information to answer this question.",
            "citations": [],
            "status": "no_context",
        }
    
    # Format context with chunk IDs
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        chunk_id = chunk.get("id", f"chunk_{i}")
        source = chunk.get("source", "unknown")
        text = chunk.get("text", "")
        context_parts.append(f"[{chunk_id}] (Source: {source})\n{text}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # System prompt for citation
    system_prompt = """You are a helpful assistant that answers questions based on provided context.
    
IMPORTANT: When answering, cite your sources using the chunk IDs in square brackets like [chunk_id].
Only use information from the provided context. If the context doesn't contain enough information,
say so clearly.

Format your response as:
ANSWER: Your answer here with [citations] inline.

SOURCES USED: List the chunk IDs you cited."""

    user_prompt = f"""Context:
{context}

Question: {query}

Please answer the question using only the provided context, and cite the relevant chunks."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        
        answer_text = response.choices[0].message.content
        
        # Parse citations from the response
        import re
        cited_ids = re.findall(r'\[([^\]]+)\]', answer_text)
        
        # Determine which chunks were shown vs cited
        shown_ids = [chunk.get("id") for chunk in context_chunks]
        cited_ids_clean = [cid for cid in cited_ids if cid in shown_ids]
        uncited_ids = [sid for sid in shown_ids if sid not in cited_ids_clean]
        
        return {
            "query": query,
            "answer": answer_text,
            "citations": {
                "cited": cited_ids_clean,
                "shown_but_not_cited": uncited_ids,
                "total_shown": len(shown_ids),
                "total_cited": len(cited_ids_clean),
            },
            "model": model,
            "status": "success",
        }
        
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "status": "error",
        }
