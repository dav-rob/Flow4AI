"""
Output helpers for the RAG pipeline demo.

Extracts verbose print statements to keep main pipeline code succinct.
"""


def section(title: str) -> None:
    """Print a section header."""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def step(emoji: str, message: str) -> None:
    """Print a step with emoji prefix."""
    print(f"\n{emoji} {message}")


def detail(message: str) -> None:
    """Print an indented detail line."""
    print(f"   {message}")


def success(message: str) -> None:
    """Print a success message."""
    print(f"   ✅ {message}")


def error(message: str) -> None:
    """Print an error message."""
    print(f"   ❌ {message}")


def progress(current: int, total: int, interval: int = 100) -> None:
    """Print progress at specified intervals."""
    if current == 1:
        print("   🎯 First item complete")
    elif current % interval == 0:
        print(f"   ⏱️  {current}/{total} complete")


def stats(label: str, count: int, time_sec: float) -> None:
    """Print performance statistics."""
    rate = count / time_sec if time_sec > 0 else 0
    print(f"   ✅ {label}: {count} in {time_sec:.2f}s")
    print(f"   ⚡ Rate: {rate:.1f}/sec")


def query_result(answer: str, citations: list) -> None:
    """Print formatted query result."""
    print(f"\n📝 Answer:\n{answer}")
    if citations:
        print(f"\n📚 Citations: {len(citations)} sources")
        for i, cite in enumerate(citations[:3], 1):
            source = cite.get("source", "Unknown")
            print(f"   {i}. {source}")


def summary_table(title: str, rows: list[tuple[str, str]]) -> None:
    """Print a simple summary table."""
    print(f"\n{title}:")
    for label, value in rows:
        print(f"   {label}: {value}")
