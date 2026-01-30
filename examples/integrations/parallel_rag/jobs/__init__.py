"""Jobs package for parallel RAG pipeline."""
from .embedding import embed_chunk, embed_batch
from .indexing import index_chunks, search_collection, get_chroma_client
from .search import search_and_rerank
from .generation import generate_answer

__all__ = [
    "embed_chunk",
    "embed_batch",
    "index_chunks",
    "search_collection",
    "get_chroma_client",
    "search_and_rerank",
    "generate_answer",
]
