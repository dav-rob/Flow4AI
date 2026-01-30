"""
Utility to download public domain books from Project Gutenberg.
"""

import os
import urllib.request
from pathlib import Path

# Popular public domain books (short to medium length for manageable chunks)
GUTENBERG_BOOKS = {
    "alice_wonderland": "https://www.gutenberg.org/files/11/11-0.txt",
    "sherlock_holmes": "https://www.gutenberg.org/files/1661/1661-0.txt",
    "pride_prejudice": "https://www.gutenberg.org/files/1342/1342-0.txt",
    "frankenstein": "https://www.gutenberg.org/files/84/84-0.txt",
    "dracula": "https://www.gutenberg.org/files/345/345-0.txt",
}


def download_book(name: str, url: str, corpus_dir: Path) -> Path:
    """Download a book from Project Gutenberg."""
    filepath = corpus_dir / f"{name}.txt"
    
    if filepath.exists():
        print(f"  ✓ {name} already exists")
        return filepath
    
    print(f"  ⬇ Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"  ✓ Downloaded {name}")
    except Exception as e:
        print(f"  ✗ Failed to download {name}: {e}")
        return None
    
    return filepath


def download_corpus(corpus_dir: Path = None, books: list = None) -> list:
    """
    Download books from Project Gutenberg.
    
    Args:
        corpus_dir: Directory to save books (default: parallel_rag/corpus)
        books: List of book names to download (default: all)
    
    Returns:
        List of downloaded file paths
    """
    if corpus_dir is None:
        corpus_dir = Path(__file__).parent.parent / "corpus"
    
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    if books is None:
        books = list(GUTENBERG_BOOKS.keys())
    
    print(f"\nDownloading {len(books)} books to {corpus_dir}")
    
    downloaded = []
    for name in books:
        if name not in GUTENBERG_BOOKS:
            print(f"  ✗ Unknown book: {name}")
            continue
        
        filepath = download_book(name, GUTENBERG_BOOKS[name], corpus_dir)
        if filepath:
            downloaded.append(filepath)
    
    print(f"\n✅ Downloaded {len(downloaded)} books\n")
    return downloaded


def load_corpus(corpus_dir: Path = None) -> dict:
    """
    Load all books from the corpus directory.
    
    Returns:
        Dict mapping book name to text content
    """
    if corpus_dir is None:
        corpus_dir = Path(__file__).parent.parent / "corpus"
    
    corpus = {}
    for filepath in corpus_dir.glob("*.txt"):
        name = filepath.stem
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            corpus[name] = f.read()
    
    return corpus


if __name__ == "__main__":
    # Download all books when run directly
    download_corpus()
