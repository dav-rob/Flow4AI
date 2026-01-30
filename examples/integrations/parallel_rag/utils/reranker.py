"""
BM25 reranking for search results.

Uses rank_bm25 library for lightweight, pure-Python reranking.
"""

from typing import List, Tuple
import re


class BM25Reranker:
    """Simple BM25-based reranker for search results."""
    
    def __init__(self):
        self.bm25 = None
        self.documents = None
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenizer with lowercasing."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return text.split()
    
    def rerank(
        self,
        query: str,
        documents: List[dict],
        text_key: str = "text",
        top_k: int = 5,
    ) -> List[Tuple[dict, float]]:
        """
        Rerank documents using BM25 scoring.
        
        Args:
            query: The search query
            documents: List of document dicts
            text_key: Key to access text in document dict
            top_k: Number of top results to return
        
        Returns:
            List of (document, score) tuples, sorted by score descending
        """
        if not documents:
            return []
        
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            # Fallback: just return documents in original order
            print("⚠️ rank_bm25 not installed, skipping reranking")
            return [(doc, 1.0) for doc in documents[:top_k]]
        
        # Tokenize documents
        tokenized_docs = [self._tokenize(doc[text_key]) for doc in documents]
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_docs)
        
        # Score query
        tokenized_query = self._tokenize(query)
        scores = bm25.get_scores(tokenized_query)
        
        # Sort by score
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return doc_scores[:top_k]


# Global reranker instance
_reranker = BM25Reranker()


def rerank(query: str, documents: List[dict], top_k: int = 5) -> List[Tuple[dict, float]]:
    """Convenience function for reranking."""
    return _reranker.rerank(query, documents, top_k=top_k)
