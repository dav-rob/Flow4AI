"""
Text chunking utilities with overlap for RAG processing.
"""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Chunk:
    """A text chunk with metadata."""
    id: str
    text: str
    source: str
    start_char: int
    end_char: int
    chunk_index: int
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "chunk_index": self.chunk_index,
        }


def clean_text(text: str) -> str:
    """Clean Gutenberg text by removing headers/footers and normalizing whitespace."""
    # Find start marker
    start_markers = [
        "*** START OF THIS PROJECT GUTENBERG",
        "*** START OF THE PROJECT GUTENBERG",
        "*END*THE SMALL PRINT!",
    ]
    start_idx = 0
    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            # Find next newline after marker
            newline_idx = text.find("\n", idx)
            if newline_idx != -1:
                start_idx = newline_idx + 1
                break
    
    # Find end marker
    end_markers = [
        "*** END OF THIS PROJECT GUTENBERG",
        "*** END OF THE PROJECT GUTENBERG",
        "End of the Project Gutenberg",
    ]
    end_idx = len(text)
    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            end_idx = idx
            break
    
    # Extract main content
    text = text[start_idx:end_idx]
    
    # Normalize whitespace
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[Chunk]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The text to chunk
        source: Source document name
        chunk_size: Target size of each chunk in characters
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of Chunk objects
    """
    # Clean the text first
    text = clean_text(text)
    
    if len(text) <= chunk_size:
        return [Chunk(
            id=f"{source}_0",
            text=text,
            source=source,
            start_char=0,
            end_char=len(text),
            chunk_index=0,
        )]
    
    chunks = []
    start = 0
    chunk_idx = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end within last 100 chars of chunk
            search_start = max(end - 100, start)
            for end_char in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                last_period = text.rfind(end_char, search_start, end)
                if last_period != -1:
                    end = last_period + 1
                    break
        else:
            end = len(text)
        
        chunk_text_content = text[start:end].strip()
        
        if chunk_text_content:  # Only add non-empty chunks
            chunks.append(Chunk(
                id=f"{source}_{chunk_idx}",
                text=chunk_text_content,
                source=source,
                start_char=start,
                end_char=end,
                chunk_index=chunk_idx,
            ))
            chunk_idx += 1
        
        # Move start with overlap
        start = end - overlap
        if start <= chunks[-1].start_char if chunks else 0:
            start = end  # Prevent infinite loop
    
    return chunks


def chunk_corpus(corpus: dict, chunk_size: int = 500, overlap: int = 100) -> List[Chunk]:
    """
    Chunk an entire corpus of documents.
    
    Args:
        corpus: Dict mapping source name to text
        chunk_size: Target chunk size
        overlap: Overlap between chunks
    
    Returns:
        List of all chunks across all documents
    """
    all_chunks = []
    
    for source, text in corpus.items():
        chunks = chunk_text(text, source, chunk_size, overlap)
        all_chunks.extend(chunks)
    
    return all_chunks


if __name__ == "__main__":
    # Test chunking
    from download import load_corpus, download_corpus
    
    # Ensure we have corpus
    download_corpus(books=["alice_wonderland"])
    corpus = load_corpus()
    
    if corpus:
        chunks = chunk_corpus(corpus)
        print(f"Created {len(chunks)} chunks")
        print(f"\nFirst chunk: {chunks[0].text[:200]}...")
        print(f"\nLast chunk: {chunks[-1].text[:200]}...")
