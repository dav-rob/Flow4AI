"""
RAG Pipeline Test Suite

Tests for verifying retrieval accuracy and edge cases.

Usage:
    python test_rag.py                          # Run all tests (sequential)
    python test_rag.py --suite needle           # Run needle-in-haystack only
    python test_rag.py --suite edge             # Run edge cases only
    python test_rag.py --parallel               # Run tests in parallel with FlowManager
    python test_rag.py --chunks 100             # Test with specific chunk count
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

from jobs.search import search_and_rerank
from jobs.generation import generate_answer
from jobs.embedding import reset_client as reset_embed_client
from jobs.generation import reset_client as reset_gen_client
from jobs.query_jobs import (
    embed_query_job,
    vector_search_job,
    bm25_rerank_job,
    generate_answer_job,
)


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
        expected_keywords=["Dodo"],
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
# =============================================================================

EDGE_TESTS = [
    TestCase(
        name="Non-existent fact",
        query="What color was the elephant that Alice met?",
        expected_keywords=[],
        negative_keywords=["elephant was", "the elephant"],
        suite="edge",
        min_citations=0,
    ),
    TestCase(
        name="Vague query",
        query="Tell me something",
        expected_keywords=[],
        suite="edge",
        min_citations=0,
    ),
    TestCase(
        name="Very specific - may miss",
        query="What was the exact time on the White Rabbit's watch?",
        expected_keywords=[],
        suite="edge",
        min_citations=0,
    ),
]


# =============================================================================
# Sequential Test Runner (Original)
# =============================================================================

async def run_test(test: TestCase, verbose: bool = False) -> dict:
    """Run a single test case sequentially."""
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
        search_result = await search_and_rerank(test.query, top_k_initial=20, top_k_final=5)
        
        if search_result.get("status") != "success":
            if test.suite == "edge" and test.min_citations == 0:
                result["passed"] = True
                result["reason"] = "No results (expected for edge case)"
            else:
                result["reason"] = f"Search failed: {search_result.get('error', 'no results')}"
            return result
        
        answer_result = await generate_answer(test.query, search_result["results"])
        
        if answer_result.get("status") != "success":
            result["reason"] = f"Generation failed: {answer_result.get('error')}"
            return result
        
        result["answer"] = answer_result["answer"][:200] + "..." if len(answer_result["answer"]) > 200 else answer_result["answer"]
        result["citations"] = answer_result["citations"]["total_cited"]
        
        # Check keywords
        answer_lower = answer_result["answer"].lower()
        found_keywords = [kw for kw in test.expected_keywords if kw.lower() in answer_lower]
        missing_keywords = [kw for kw in test.expected_keywords if kw.lower() not in answer_lower]
        bad_keywords = [kw for kw in (test.negative_keywords or []) if kw.lower() in answer_lower]
        
        if test.expected_keywords:
            if found_keywords and not bad_keywords:
                result["passed"] = True
                result["reason"] = f"Found: {found_keywords}"
            else:
                result["reason"] = f"Missing: {missing_keywords}" if missing_keywords else f"Bad: {bad_keywords}"
        else:
            result["passed"] = True
            result["reason"] = "Edge case handled"
        
    except Exception as e:
        result["reason"] = f"Exception: {str(e)}"
    
    return result


# =============================================================================
# Parallel Test Runner (FlowManager)
# =============================================================================

def run_suite_parallel(tests: List[TestCase], verbose: bool = False) -> dict:
    """Run all tests in parallel using FlowManager."""
    print("\n🚀 Running tests in PARALLEL with FlowManager...")
    
    reset_embed_client()
    reset_gen_client()
    
    # Define the query workflow
    query_workflow = (
        job(embed_query=embed_query_job)
        >> job(vector_search=vector_search_job)
        >> job(bm25_rerank=bm25_rerank_job)
        >> job(generate_answer=generate_answer_job)
    )
    
    # Collect results
    results_by_query = {}
    
    def on_complete(result):
        # Get query from task_pass_through - it contains the original task params
        pass_through = result.get("task_pass_through", {})
        if hasattr(pass_through, "data"):
            query = pass_through.data.get("embed_query", {}).get("text", "unknown")
        else:
            query = pass_through.get("embed_query", {}).get("text", "unknown")
        results_by_query[query] = result
    
    fm = FlowManager(on_complete=on_complete)
    fq_name = fm.add_workflow(query_workflow, "parallel_tests")
    
    start_time = time.time()
    
    # Submit all tests at once
    for test in tests:
        task = {"embed_query": {"text": test.query}}
        fm.submit_task(task, fq_name)
    
    # Wait for all to complete
    fm.wait_for_completion(timeout=120)
    
    elapsed = time.time() - start_time
    
    # Process results
    test_results = []
    passed = 0
    
    for test in tests:
        result_data = results_by_query.get(test.query, {})
        
        result = {
            "name": test.name,
            "query": test.query,
            "passed": False,
            "reason": "",
            "answer": "",
            "citations": 0,
        }
        
        if result_data.get("status") == "success":
            answer = result_data.get("answer", "")
            result["answer"] = answer[:200] + "..." if len(answer) > 200 else answer
            result["citations"] = result_data.get("citations", {}).get("total_cited", 0)
            
            # Check keywords
            answer_lower = answer.lower()
            found = [kw for kw in test.expected_keywords if kw.lower() in answer_lower]
            
            if test.expected_keywords:
                if found:
                    result["passed"] = True
                    result["reason"] = f"Found: {found}"
                else:
                    result["reason"] = f"Missing expected keywords"
            else:
                result["passed"] = True
                result["reason"] = "Edge case"
        else:
            result["reason"] = f"Failed: {result_data.get('status', 'no result')}"
            if test.suite == "edge":
                result["passed"] = True
                result["reason"] = "Edge case - no result ok"
        
        test_results.append(result)
        if result["passed"]:
            passed += 1
        
        icon = "✅" if result["passed"] else "❌"
        print(f"{icon} {result['name']}")
        if verbose:
            print(f"   Reason: {result['reason']}")
    
    return {
        "total": len(tests),
        "passed": passed,
        "failed": len(tests) - passed,
        "elapsed": elapsed,
        "results": test_results,
    }


# =============================================================================
# Main Suite Runner
# =============================================================================

async def run_suite(suite: str = "all", verbose: bool = False) -> dict:
    """Run test suite sequentially."""
    tests = []
    if suite in ["all", "needle"]:
        tests.extend(NEEDLE_TESTS)
    if suite in ["all", "edge"]:
        tests.extend(EDGE_TESTS)
    
    print(f"\n{'='*60}")
    print(f"🧪 RAG TEST SUITE: {suite.upper()} (Sequential)")
    print(f"{'='*60}")
    print(f"Running {len(tests)} tests...\n")
    
    start_time = time.time()
    results = []
    passed = 0
    
    for test in tests:
        result = await run_test(test, verbose)
        results.append(result)
        
        icon = "✅" if result["passed"] else "❌"
        print(f"{icon} {result['name']}")
        if verbose or not result["passed"]:
            print(f"   Reason: {result['reason']}")
        
        if result["passed"]:
            passed += 1
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {passed}/{len(tests)} passed in {elapsed:.2f}s")
    print(f"{'='*60}\n")
    
    return {
        "total": len(tests),
        "passed": passed,
        "failed": len(tests) - passed,
        "elapsed": elapsed,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline Test Suite")
    parser.add_argument("--suite", choices=["all", "needle", "edge"], default="all")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel with FlowManager")
    parser.add_argument("--chunks", type=int, default=None)
    
    args = parser.parse_args()
    
    # Re-index if requested
    if args.chunks:
        print(f"\n🔄 Re-indexing with {args.chunks} chunks...")
        import subprocess
        result = subprocess.run([
            sys.executable, "rag_pipeline.py",
            "--mode", "index", "--chunks", str(args.chunks),
            "--books", "alice_wonderland",
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Indexing failed: {result.stderr}")
            return False
        print("✅ Indexing complete\n")
    
    # Get tests
    tests = []
    if args.suite in ["all", "needle"]:
        tests.extend(NEEDLE_TESTS)
    if args.suite in ["all", "edge"]:
        tests.extend(EDGE_TESTS)
    
    # Run tests
    if args.parallel:
        print(f"\n{'='*60}")
        print(f"🧪 RAG TEST SUITE: {args.suite.upper()} (Parallel FlowManager)")
        print(f"{'='*60}")
        summary = run_suite_parallel(tests, args.verbose)
    else:
        summary = asyncio.run(run_suite(args.suite, args.verbose))
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL: {summary['passed']}/{summary['total']} passed in {summary['elapsed']:.2f}s")
    print(f"{'='*60}\n")
    
    return summary["failed"] == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

