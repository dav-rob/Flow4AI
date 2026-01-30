"""
Experiment: LangChain Sync vs Async - Real API Calls

This experiment tests Flow4AI parallelism with actual LangChain calls:
1. chain.invoke() - SYNC (blocks event loop)
2. chain.ainvoke() - ASYNC (true parallelism)

Expected Results:
- Sync invoke(): ~N x latency (sequential)
- Async ainvoke(): ~1 x latency (parallel)

Usage:
    pip install langchain-openai langchain-core
    export OPENAI_API_KEY=your_key_here
    python 04_langchain_async_vs_sync.py
"""

import asyncio
import time
import os
from dotenv import load_dotenv

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p

load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not set. Export it first.")
    exit(1)

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("❌ LangChain not installed. Install with:")
    print("   pip install langchain-openai langchain-core")
    exit(1)

# Simple prompt
PROMPT = "What is {num}+{num}? Answer in exactly one word."
MODEL = "gpt-4o-mini"
NUM_TASKS = 5


# =============================================================================
# Test 1: LangChain Sync invoke() (BLOCKS EVENT LOOP)
# =============================================================================

def langchain_sync(num):
    """Sync LangChain call - blocks the event loop."""
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=10)
    prompt = ChatPromptTemplate.from_template(PROMPT)
    chain = prompt | llm
    
    # SYNC invoke - blocks!
    result = chain.invoke({"num": num})
    return {"num": num, "answer": result.content, "type": "sync"}


def test_langchain_sync():
    """Test sync LangChain invoke - expected to block."""
    print("\n" + "="*60)
    print("TEST 1: LangChain chain.invoke() (SYNC - BLOCKING)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=langchain_sync)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "langchain_sync")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.num": i + 1}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    errors = counts.get("errors", 0)
    
    print(f"\n{'⚠️' if elapsed > 3.0 else '✅'} Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    per_call = elapsed / NUM_TASKS
    print(f"   Avg per call: {per_call:.2f}s")
    
    return elapsed


# =============================================================================
# Test 2: LangChain Async ainvoke() (TRUE PARALLELISM)
# =============================================================================

async def langchain_async(num):
    """Async LangChain call - true parallelism."""
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=10)
    prompt = ChatPromptTemplate.from_template(PROMPT)
    chain = prompt | llm
    
    # ASYNC ainvoke - parallel!
    result = await chain.ainvoke({"num": num})
    return {"num": num, "answer": result.content, "type": "async"}


def test_langchain_async():
    """Test async LangChain ainvoke - expected true parallelism."""
    print("\n" + "="*60)
    print("TEST 2: LangChain chain.ainvoke() (ASYNC - PARALLEL)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=langchain_async)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "langchain_async")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.num": i + 1}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    errors = counts.get("errors", 0)
    
    print(f"\n✅ Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    return elapsed


# =============================================================================
# Test 3: LangChain Sync invoke() wrapped in asyncio.to_thread
# =============================================================================

async def langchain_sync_threaded(num):
    """Sync LangChain call wrapped in thread pool."""
    def _sync_call():
        llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=10)
        prompt = ChatPromptTemplate.from_template(PROMPT)
        chain = prompt | llm
        return chain.invoke({"num": num})
    
    result = await asyncio.to_thread(_sync_call)
    return {"num": num, "answer": result.content, "type": "sync_threaded"}


def test_langchain_sync_threaded():
    """Test sync LangChain in thread pool - expected parallelism."""
    print("\n" + "="*60)
    print("TEST 3: LangChain invoke() + asyncio.to_thread (THREAD POOL)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=langchain_sync_threaded)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "langchain_threaded")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.num": i + 1}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    errors = counts.get("errors", 0)
    
    print(f"\n✅ Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    return elapsed


# =============================================================================
# Test 4: Parallel LangChain with Flow4AI (like langchain_chains.py)
# =============================================================================

async def analyze_tech(document):
    """Technical analysis - async."""
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=50)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical analyst. Give a one-sentence analysis."),
        ("human", "{document}")
    ])
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    return {"perspective": "technical", "analysis": result.content}


async def analyze_business(document):
    """Business analysis - async."""
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=50)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a business analyst. Give a one-sentence analysis."),
        ("human", "{document}")
    ])
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    return {"perspective": "business", "analysis": result.content}


async def analyze_ux(document):
    """UX analysis - async."""
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=50)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a UX researcher. Give a one-sentence analysis."),
        ("human", "{document}")
    ])
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    return {"perspective": "ux", "analysis": result.content}


def test_parallel_langchain_flow4ai():
    """Test parallel LangChain calls orchestrated by Flow4AI (like langchain_chains.py)."""
    print("\n" + "="*60)
    print("TEST 4: Parallel LangChain Analysis (Flow4AI orchestrated)")
    print("="*60)
    print("Running 3 parallel LangChain chains (tech, business, UX)...")
    
    # Parallel LangChain workflow - like langchain_chains.py
    jobs = job({
        "tech": analyze_tech,
        "business": analyze_business,
        "ux": analyze_ux,
    })
    
    # Run all 3 in parallel
    workflow = p(jobs["tech"], jobs["business"], jobs["ux"])
    
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "parallel_analysis")
    
    document = "Flow4AI is a Python framework for orchestrating AI workflows with parallel execution."
    
    start = time.perf_counter()
    
    fm.submit_task({
        "tech.document": document,
        "business.document": document,
        "ux.document": document,
    }, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    results = fm.pop_results()
    
    print(f"\n✅ Completed 3 parallel analyses in {elapsed:.2f}s")
    print(f"   If sequential, would be ~{elapsed * 3:.1f}s")
    
    # Show results
    if results.get("completed"):
        for fq, job_results in results["completed"].items():
            for r in job_results:
                perspective = r.get("result", {}).get("perspective", "unknown")
                analysis = r.get("result", {}).get("analysis", "N/A")[:60]
                print(f"   {perspective}: {analysis}...")
    
    return elapsed


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("🔗 Flow4AI: LangChain Sync vs Async Experiment")
    print("="*60)
    print(f"\nModel: {MODEL}")
    print(f"Tasks per test: {NUM_TASKS}")
    
    t1 = test_langchain_sync()
    t2 = test_langchain_async()
    t3 = test_langchain_sync_threaded()
    t4 = test_parallel_langchain_flow4ai()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"{'Test':<45} {'Time':<10} {'Speedup'}")
    print("-"*60)
    print(f"{'LangChain invoke() (sync blocking)':<45} {t1:<10.2f} 1.0x (baseline)")
    print(f"{'LangChain ainvoke() (async native)':<45} {t2:<10.2f} {t1/t2:.1f}x")
    print(f"{'LangChain invoke() + to_thread':<45} {t3:<10.2f} {t1/t3:.1f}x")
    print(f"{'Parallel Flow4AI (3 chains)':<45} {t4:<10.2f} (parallel)")
    
    print("\n" + "="*60)
    print("💡 CONCLUSION")
    print("="*60)
    if t2 < t1 * 0.6:
        print("✅ LangChain ainvoke() provides SIGNIFICANT parallelism benefit!")
    else:
        print("⚠️  Results may vary due to API rate limiting")
    print("\nRecommendation: Always use ainvoke() with LangChain in Flow4AI")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
