"""
Experiment: HTTP Requests - Sync vs Async Libraries

This experiment tests Flow4AI parallelism with real HTTP calls:
1. requests (sync library) - blocks the event loop
2. requests in asyncio.to_thread() - parallel via thread pool
3. aiohttp (async library) - TRUE native parallelism

Key Insight:
- Sync HTTP libraries (requests, urllib) block the event loop
- To use sync libraries, wrap calls in asyncio.to_thread()
- Async HTTP libraries (aiohttp, httpx with async) give best performance

Usage:
    pip install aiohttp
    python 02_http_async_vs_sync.py
"""

import asyncio
import time

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# A simple public API endpoint for testing
TEST_URL = "https://httpbin.org/delay/0.5"  # Returns after 0.5s delay


# =============================================================================
# Test 1: Sync requests library (BLOCKS)
# =============================================================================

def fetch_sync_blocking(url):
    """Fetch URL using sync requests - BLOCKS the event loop."""
    import requests
    response = requests.get(url, timeout=10)
    return {"status": response.status_code, "type": "sync_blocking"}


def test_sync_requests():
    """Test sync requests library - expected to block."""
    print("\n" + "="*60)
    print("TEST 1: Sync requests Library (BLOCKING)")
    print("="*60)
    print("Expected: ~2.5s for 5 requests (sequential - blocked)")
    
    workflow = job(fetch=fetch_sync_blocking)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "sync_requests")
    
    start = time.perf_counter()
    
    for i in range(5):
        fm.submit_task({"fetch.url": TEST_URL}, fq_name)
    
    fm.wait_for_completion(timeout=30)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n{'⚠️' if elapsed > 2.0 else '✅'} Completed {counts['completed']} requests in {elapsed:.2f}s")
    
    if elapsed > 2.0:
        print("   ⚠️  CONFIRMED: Event loop blocked (sequential)")
    else:
        print("   ✨ Parallel! May indicate thread pool was used")
    
    return elapsed


# =============================================================================
# Test 2: Sync requests in thread pool (PARALLEL)
# =============================================================================

async def fetch_in_thread(url):
    """Fetch URL using sync requests in thread pool."""
    import requests
    response = await asyncio.to_thread(requests.get, url, timeout=10)
    return {"status": response.status_code, "type": "sync_in_thread"}


def test_sync_in_thread():
    """Test sync requests in thread pool - expected to be parallel."""
    print("\n" + "="*60)
    print("TEST 2: Sync requests in Thread Pool")
    print("="*60)
    print("Expected: ~0.5-1s for 5 requests (parallel via threads)")
    
    workflow = job(fetch=fetch_in_thread)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "sync_thread")
    
    start = time.perf_counter()
    
    for i in range(5):
        fm.submit_task({"fetch.url": TEST_URL}, fq_name)
    
    fm.wait_for_completion(timeout=30)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n✅ Completed {counts['completed']} requests in {elapsed:.2f}s")
    
    if elapsed < 2.0:
        print("   ✨ CONFIRMED: Thread pool enables parallelism!")
    else:
        print("   ⚠️  Slower than expected")
    
    return elapsed


# =============================================================================
# Test 3: Async aiohttp library (TRUE NATIVE PARALLEL)
# =============================================================================

async def fetch_async(url):
    """Fetch URL using async aiohttp - TRUE native parallelism."""
    try:
        import aiohttp
    except ImportError:
        return {"error": "aiohttp not installed", "type": "async"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            return {"status": response.status, "type": "async_native"}


def test_async_aiohttp():
    """Test async aiohttp library - expected true parallelism."""
    try:
        import aiohttp
    except ImportError:
        print("\n" + "="*60)
        print("TEST 3: Async aiohttp Library (SKIPPED)")
        print("="*60)
        print("⚠️  aiohttp not installed. Install with: pip install aiohttp")
        return None
    
    print("\n" + "="*60)
    print("TEST 3: Async aiohttp Library (NATIVE ASYNC)")
    print("="*60)
    print("Expected: ~0.5-1s for 5 requests (TRUE parallel)")
    
    workflow = job(fetch=fetch_async)
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "async_aiohttp")
    
    start = time.perf_counter()
    
    for i in range(5):
        fm.submit_task({"fetch.url": TEST_URL}, fq_name)
    
    fm.wait_for_completion(timeout=30)
    elapsed = time.perf_counter() - start
    
    counts = fm.get_counts()
    print(f"\n✅ Completed {counts['completed']} requests in {elapsed:.2f}s")
    
    if elapsed < 2.0:
        print("   ✨ CONFIRMED: Native async = TRUE parallelism!")
    else:
        print("   ⚠️  Slower than expected")
    
    return elapsed


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "="*60)
    print("🌐 Flow4AI: HTTP Async vs Sync Experiment")
    print("="*60)
    print(f"\nTest URL: {TEST_URL}")
    print("(Each request has ~0.5s server-side delay)")
    
    try:
        import requests
    except ImportError:
        print("\n❌ 'requests' library not installed. Install with: pip install requests")
        return
    
    t1 = test_sync_requests()
    t2 = test_sync_in_thread()
    t3 = test_async_aiohttp()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"{'Test':<35} {'Time':<10} {'Result'}")
    print("-"*60)
    print(f"{'Sync requests (blocking)':<35} {t1:<10.2f} {'⚠️ Blocked' if t1 > 2.0 else '✅ Parallel'}")
    print(f"{'Sync in thread pool':<35} {t2:<10.2f} {'✅ Parallel' if t2 < 2.0 else '❌ Serial'}")
    if t3:
        print(f"{'Async aiohttp':<35} {t3:<10.2f} {'✅ Parallel' if t3 < 2.0 else '❌ Serial'}")
    else:
        print(f"{'Async aiohttp':<35} {'N/A':<10} {'⚠️ Not installed'}")
    
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS FOR INTEGRATION EXAMPLES")
    print("="*60)
    print("1. Use async libraries when available (aiohttp, httpx async)")
    print("2. If using sync libraries (requests), wrap in asyncio.to_thread()")
    print("3. Document this requirement in README.md")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
