"""
Experiment: Async vs Sync Blocking Code in Flow4AI

This experiment tests how Flow4AI handles:
1. Async functions with asyncio.sleep() - TRUE parallelism expected
2. Sync functions with time.sleep() - BLOCKS the event loop (no parallelism!)
3. Sync functions wrapped in asyncio.to_thread() - TRUE parallelism expected

Key Insight:
- Flow4AI uses asyncio for concurrency
- Async functions yield control during await, enabling parallelism
- Sync blocking functions (time.sleep, requests.get) block the event loop
- To use sync blocking code, wrap in asyncio.to_thread()

Usage:
    python 01_async_vs_sync_blocking.py
"""

import asyncio
import time
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job


# =============================================================================
# Test 1: Async function with asyncio.sleep (TRUE PARALLELISM)
# =============================================================================

async def async_work(task_id, delay=0.5):
    """Async function that yields control during sleep."""
    await asyncio.sleep(delay)  # Yields to event loop - other tasks can run
    return {"task_id": task_id, "type": "async", "delay": delay}


def test_async_parallelism():
    """Test that async functions run in parallel."""
    print("\n" + "="*60)
    print("TEST 1: Async Functions (asyncio.sleep)")
    print("="*60)
    print("Expected: ~0.5s for 10 tasks (TRUE parallel)")
    
    workflow = job(worker=async_work)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "async_test")
    
    start = time.perf_counter()
    
    for i in range(10):
        task = {"worker.task_id": f"async_{i}", "worker.delay": 0.5}
        fm.submit_task(task, fq_name)
    
    fm.wait_for_completion(timeout=10)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n✅ Completed {counts['completed']} tasks in {elapsed:.2f}s")
    print(f"   Sequential time would be: {10 * 0.5:.1f}s")
    print(f"   Speedup: {(10 * 0.5) / elapsed:.1f}x")
    
    if elapsed < 1.0:
        print("   ✨ CONFIRMED: True parallel execution!")
    else:
        print("   ⚠️  Slower than expected, may indicate issues")
    
    return elapsed


# =============================================================================
# Test 2: Sync function with time.sleep (BLOCKS EVENT LOOP!)
# =============================================================================

def sync_blocking_work(task_id, delay=0.5):
    """Sync function that BLOCKS the event loop during sleep."""
    time.sleep(delay)  # BLOCKS - no other tasks can run!
    return {"task_id": task_id, "type": "sync_blocking", "delay": delay}


def test_sync_blocking():
    """Test that sync blocking functions block the event loop."""
    print("\n" + "="*60)
    print("TEST 2: Sync Blocking Functions (time.sleep)")
    print("="*60)
    print("Expected: ~5s for 10 tasks (SEQUENTIAL - event loop blocked)")
    
    workflow = job(worker=sync_blocking_work)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "sync_blocking_test")
    
    start = time.perf_counter()
    
    for i in range(10):
        task = {"worker.task_id": f"sync_{i}", "worker.delay": 0.5}
        fm.submit_task(task, fq_name)
    
    fm.wait_for_completion(timeout=30)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n{'✅' if elapsed > 4.0 else '⚠️'} Completed {counts['completed']} tasks in {elapsed:.2f}s")
    print(f"   Sequential time should be: {10 * 0.5:.1f}s")
    
    if elapsed > 4.0:
        print("   ⚠️  CONFIRMED: Event loop was blocked (sequential execution)")
    else:
        print("   ✨ Surprisingly parallel! May indicate unexpected behavior")
    
    return elapsed


# =============================================================================
# Test 3: Sync function wrapped in asyncio.to_thread (TRUE PARALLELISM)
# =============================================================================

async def sync_in_thread(task_id, delay=0.5):
    """Async function that runs sync code in a thread pool."""
    # Wrap blocking sync code in a thread
    result = await asyncio.to_thread(time.sleep, delay)
    return {"task_id": task_id, "type": "sync_in_thread", "delay": delay}


def test_sync_in_thread():
    """Test that sync code wrapped in asyncio.to_thread runs in parallel."""
    print("\n" + "="*60)
    print("TEST 3: Sync Code in Thread Pool (asyncio.to_thread)")
    print("="*60)
    print("Expected: ~0.5s for 10 tasks (parallel via thread pool)")
    
    workflow = job(worker=sync_in_thread)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "sync_thread_test")
    
    start = time.perf_counter()
    
    for i in range(10):
        task = {"worker.task_id": f"thread_{i}", "worker.delay": 0.5}
        fm.submit_task(task, fq_name)
    
    fm.wait_for_completion(timeout=10)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n✅ Completed {counts['completed']} tasks in {elapsed:.2f}s")
    print(f"   Sequential time would be: {10 * 0.5:.1f}s")
    print(f"   Speedup: {(10 * 0.5) / elapsed:.1f}x")
    
    if elapsed < 1.5:
        print("   ✨ CONFIRMED: Thread pool enables parallelism for sync code!")
    else:
        print("   ⚠️  Slower than expected")
    
    return elapsed


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("🧪 Flow4AI: Async vs Sync Blocking Experiment")
    print("="*60)
    print("\nThis experiment demonstrates:")
    print("1. Async code with await = TRUE parallelism")
    print("2. Sync blocking code = BLOCKS event loop")
    print("3. Sync code in thread pool = TRUE parallelism")
    
    t1 = test_async_parallelism()
    t2 = test_sync_blocking()
    t3 = test_sync_in_thread()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"{'Test':<35} {'Time':<10} {'Result'}")
    print("-"*60)
    print(f"{'Async (asyncio.sleep)':<35} {t1:<10.2f} {'✅ Parallel' if t1 < 1.5 else '❌ Serial'}")
    print(f"{'Sync blocking (time.sleep)':<35} {t2:<10.2f} {'⚠️ Blocked' if t2 > 4.0 else '✅ Parallel'}")
    print(f"{'Sync in thread pool':<35} {t3:<10.2f} {'✅ Parallel' if t3 < 1.5 else '❌ Serial'}")
    
    print("\n" + "="*60)
    print("💡 KEY TAKEAWAY")
    print("="*60)
    print("When using Flow4AI with blocking sync code (HTTP requests, DB queries),")
    print("wrap them in asyncio.to_thread() to enable true parallel execution:")
    print()
    print("  # WRONG - blocks event loop")
    print("  def my_job(url):")
    print("      return requests.get(url).text")
    print()
    print("  # CORRECT - runs in thread pool")
    print("  async def my_job(url):")
    print("      return await asyncio.to_thread(requests.get, url)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
