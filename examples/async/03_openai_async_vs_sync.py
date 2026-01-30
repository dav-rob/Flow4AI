"""
Experiment: OpenAI Sync vs Async - Real API Calls

This experiment tests Flow4AI parallelism with actual OpenAI API calls:
1. openai.chat.completions.create() - SYNC (blocks event loop)
2. openai.AsyncOpenAI with await - ASYNC (true parallelism)

Expected Results:
- Sync: ~N x latency (sequential)
- Async: ~1 x latency (parallel)

Usage:
    export OPENAI_API_KEY=your_key_here
    python 03_openai_async_vs_sync.py
"""

import asyncio
import time
import os
from dotenv import load_dotenv

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

load_dotenv()

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not set. Export it first.")
    exit(1)

# Simple prompt that should take ~1s to complete
PROMPT = "What is 2+2? Answer in exactly one word."
MODEL = "gpt-4o-mini"
NUM_TASKS = 5


# =============================================================================
# Test 1: Sync OpenAI Client (BLOCKS EVENT LOOP)
# =============================================================================

def openai_sync(task_id):
    """Sync OpenAI call - blocks the event loop."""
    from openai import OpenAI
    
    client = OpenAI()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=10,
    )
    return {"task_id": task_id, "answer": response.choices[0].message.content, "type": "sync"}


def test_openai_sync():
    """Test sync OpenAI client - expected to block."""
    print("\n" + "="*60)
    print("TEST 1: OpenAI Sync Client (BLOCKING)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=openai_sync)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "openai_sync")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.task_id": f"sync_{i}"}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    results = fm.pop_results()
    errors = counts.get("errors", 0)
    
    print(f"\n{'⚠️' if elapsed > 3.0 else '✅'} Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    per_call = elapsed / NUM_TASKS
    print(f"   Avg per call: {per_call:.2f}s")
    
    return elapsed


# =============================================================================
# Test 2: Async OpenAI Client (TRUE PARALLELISM)
# =============================================================================

async def openai_async(task_id):
    """Async OpenAI call - true parallelism."""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=10,
    )
    return {"task_id": task_id, "answer": response.choices[0].message.content, "type": "async"}


def test_openai_async():
    """Test async OpenAI client - expected true parallelism."""
    print("\n" + "="*60)
    print("TEST 2: OpenAI Async Client (PARALLEL)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=openai_async)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "openai_async")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.task_id": f"async_{i}"}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    errors = counts.get("errors", 0)
    
    print(f"\n✅ Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    per_call = elapsed / NUM_TASKS
    print(f"   Avg per call: {per_call:.2f}s (but executed in parallel!)")
    
    return elapsed


# =============================================================================
# Test 3: Sync OpenAI wrapped in asyncio.to_thread (WORKAROUND)
# =============================================================================

async def openai_sync_threaded(task_id):
    """Sync OpenAI call wrapped in thread pool."""
    from openai import OpenAI
    
    def _sync_call():
        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=10,
        )
        return response.choices[0].message.content
    
    answer = await asyncio.to_thread(_sync_call)
    return {"task_id": task_id, "answer": answer, "type": "sync_threaded"}


def test_openai_sync_threaded():
    """Test sync OpenAI in thread pool - expected parallelism."""
    print("\n" + "="*60)
    print("TEST 3: OpenAI Sync + asyncio.to_thread (THREAD POOL)")
    print("="*60)
    print(f"Submitting {NUM_TASKS} tasks...")
    
    workflow = job(call=openai_sync_threaded)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "openai_threaded")
    
    start = time.perf_counter()
    
    for i in range(NUM_TASKS):
        fm.submit_task({"call.task_id": f"threaded_{i}"}, fq_name)
    
    fm.wait_for_completion(timeout=60)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    errors = counts.get("errors", 0)
    
    print(f"\n✅ Completed {counts['completed']} calls in {elapsed:.2f}s")
    if errors:
        print(f"   ❌ Errors: {errors}")
    
    return elapsed


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("🤖 Flow4AI: OpenAI Sync vs Async Experiment")
    print("="*60)
    print(f"\nModel: {MODEL}")
    print(f"Tasks: {NUM_TASKS}")
    print(f"Prompt: '{PROMPT[:40]}...'")
    
    t1 = test_openai_sync()
    t2 = test_openai_async()
    t3 = test_openai_sync_threaded()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"{'Test':<40} {'Time':<10} {'Speedup'}")
    print("-"*60)
    print(f"{'OpenAI Sync (blocking)':<40} {t1:<10.2f} 1.0x (baseline)")
    print(f"{'OpenAI Async (native)':<40} {t2:<10.2f} {t1/t2:.1f}x")
    print(f"{'OpenAI Sync + to_thread':<40} {t3:<10.2f} {t1/t3:.1f}x")
    
    print("\n" + "="*60)
    print("💡 CONCLUSION")
    print("="*60)
    if t2 < t1 * 0.6:
        print("✅ AsyncOpenAI provides SIGNIFICANT parallelism benefit!")
    if t3 < t1 * 0.6:
        print("✅ asyncio.to_thread() is a viable workaround for sync code!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
