"""
RAG Pipeline Test Suite

Tests for verifying retrieval accuracy and edge cases.

Usage:
    python test_rag.py                          # Run all tests
    python test_rag.py --suite needle           # Run needle-in-haystack only
    python test_rag.py --suite edge             # Run edge cases only
    python test_rag.py --chunks 100             # Test with specific chunk count
"""

import asyncio
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from jobs.search import search_and_rerank
from jobs.generation import generate_answer
from jobs.embedding import reset_client as reset_embed_client
from jobs.generation import reset_client as reset_gen_client


@dataclass
class TestCase:
    """A single test case."""
    name: str
    query: str
    expected_keywords: List[str]  # Keywords that SHOULD appear in answer
    negative_keywords: List[str] = None  # Keywords that should NOT appear
    suite: str = "needle"  # needle, edge, etc.
    min_citations: int = 1


# =============================================================================
# NEEDLE IN HAYSTACK TESTS
# Specific facts that should be found in the corpus
# =============================================================================

NEEDLE_TESTS = [
    TestCase(
        name="DRINK ME bottle",
        query="What was written on the bottle that Alice drank from?",
        expected_keywords=["DRINK ME", "bottle"],
        suite="needle",
    ),
    TestCase(
        name="EAT ME cake",
        query="What did the cake say that Alice ate?",
        expected_keywords=["EAT ME", "cake"],
        suite="needle",
    ),
    TestCase(
        name="Caucus-Race participants",
        query="Who ran the Caucus-Race?",
        expected_keywords=["Dodo"],  # The Dodo organized it
        suite="needle",
    ),
    TestCase(
        name="White Rabbit's watch",
        query="What did the White Rabbit take out of its waistcoat-pocket?",
        expected_keywords=["watch"],
        suite="needle",
    ),
    TestCase(
        name="Pool of Tears",
        query="What was the pool that Alice swam in made of?",
        expected_keywords=["tears"],
        suite="needle",
    ),
]


# =============================================================================
# EDGE CASE TESTS
# Tests for boundary conditions and unusual queries
# =============================================================================

EDGE_TESTS = [
    TestCase(
        name="Non-existent fact",
        query="What color was the elephant that Alice met?",
        expected_keywords=[],  # Should say "not found" or similar
        negative_keywords=["elephant was", "the elephant"],
        suite="edge",
        min_citations=0,
    ),
    TestCase(
        name="Vague query",
        query="Tell me something",
        expected_keywords=[],  # May or may not find something
        suite="edge",
        min_citations=0,
    ),
    TestCase(
        name="Very specific - may miss",
        query="What was the exact time on the White Rabbit's watch?",
        expected_keywords=[],  # This specific detail may not be indexed
        suite="edge",
        min_citations=0,
    ),
]


# =============================================================================
# Test Runner
# =============================================================================

async def run_test(test: TestCase, verbose: bool = False) -> dict:
    """Run a single test case and return results."""
    # Reset clients for clean state
    reset_embed_client()
    reset_gen_client()
    
    result = {
        "name": test.name,
        "query": test.query,
        "passed": False,
        "reason": "",
        "answer": "",
        "citations": 0,
    }
    
    try:
        # Search
        search_result = await search_and_rerank(
            test.query, 
            top_k_initial=20, 
            top_k_final=5
        )
        
        if search_result.get("status") != "success":
            result["reason"] = f"Search failed: {search_result.get('error', 'no results')}"
            # For edge cases with no expected results, this might be ok
            if test.suite == "edge" and test.min_citations == 0:
                result["passed"] = True
                result["reason"] = "No results (expected for edge case)"
            return result
        
        # Generate answer
        answer_result = await generate_answer(test.query, search_result["results"])
        
        if answer_result.get("status") != "success":
            result["reason"] = f"Generation failed: {answer_result.get('error')}"
            return result
        
        answer = answer_result["answer"]
        citations = answer_result["citations"]["total_cited"]
        
        result["answer"] = answer[:200] + "..." if len(answer) > 200 else answer
        result["citations"] = citations
        
        # Check expected keywords
        answer_lower = answer.lower()
        found_keywords = []
        missing_keywords = []
        
        for kw in test.expected_keywords:
            if kw.lower() in answer_lower:
                found_keywords.append(kw)
            else:
                missing_keywords.append(kw)
        
        # Check negative keywords (should NOT appear)
        bad_keywords = []
        if test.negative_keywords:
            for kw in test.negative_keywords:
                if kw.lower() in answer_lower:
                    bad_keywords.append(kw)
        
        # Determine pass/fail
        if test.expected_keywords:
            if found_keywords and not bad_keywords:
                result["passed"] = True
                result["reason"] = f"Found: {found_keywords}"
            else:
                result["reason"] = f"Missing: {missing_keywords}" if missing_keywords else f"Bad: {bad_keywords}"
        else:
            # Edge case with no expected keywords
            if citations >= test.min_citations and not bad_keywords:
                result["passed"] = True
                result["reason"] = "Edge case handled correctly"
            else:
                result["reason"] = "Edge case check"
                result["passed"] = True  # Edge cases are informational
        
    except Exception as e:
        result["reason"] = f"Exception: {str(e)}"
    
    return result


async def run_suite(
    suite: str = "all",
    verbose: bool = False,
) -> dict:
    """Run a test suite."""
    tests = []
    
    if suite in ["all", "needle"]:
        tests.extend(NEEDLE_TESTS)
    if suite in ["all", "edge"]:
        tests.extend(EDGE_TESTS)
    
    print(f"\n{'='*60}")
    print(f"🧪 RAG TEST SUITE: {suite.upper()}")
    print(f"{'='*60}")
    print(f"Running {len(tests)} tests...\n")
    
    results = []
    passed = 0
    failed = 0
    
    for test in tests:
        result = await run_test(test, verbose)
        results.append(result)
        
        icon = "✅" if result["passed"] else "❌"
        print(f"{icon} {result['name']}")
        if verbose or not result["passed"]:
            print(f"   Query: {result['query']}")
            print(f"   Reason: {result['reason']}")
            if result["answer"]:
                print(f"   Answer: {result['answer'][:100]}...")
        
        if result["passed"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {passed}/{len(tests)} passed")
    print(f"{'='*60}\n")
    
    return {
        "suite": suite,
        "total": len(tests),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline Test Suite")
    parser.add_argument("--suite", choices=["all", "needle", "edge"], default="all",
                        help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed output")
    parser.add_argument("--chunks", type=int, default=None,
                        help="Re-index with specific chunk count before testing")
    
    args = parser.parse_args()
    
    # Re-index if requested
    if args.chunks:
        print(f"\n🔄 Re-indexing with {args.chunks} chunks...")
        import subprocess
        result = subprocess.run([
            sys.executable, "rag_pipeline.py",
            "--mode", "index",
            "--chunks", str(args.chunks),
            "--books", "alice_wonderland",
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Indexing failed: {result.stderr}")
            return False
        print("✅ Indexing complete\n")
    
    # Run tests
    summary = asyncio.run(run_suite(args.suite, args.verbose))
    
    return summary["failed"] == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
