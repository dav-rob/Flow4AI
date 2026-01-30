"""
Scale Test - Find optimal max_concurrent for your system

This benchmark tests different max_concurrent values to find what works
best on your hardware. Results vary by:
- CPU cores
- Available memory  
- Network latency (for API calls)
- Type of work (CPU-bound vs IO-bound)

Usage:
    python examples/benchmarks/scale_test.py                    # Quick test
    python examples/benchmarks/scale_test.py --tasks 5000       # More tasks
    python examples/benchmarks/scale_test.py --levels 100,500,1000,2000  # Custom levels
"""

import asyncio
import argparse
import time
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job


# =============================================================================
# Test Job - Simulates async work (like API call)
# =============================================================================

async def simulate_work(task_id: int, delay_ms: int = 50) -> dict:
    """
    Simulate an async task like an API call.
    
    Args:
        task_id: Unique identifier for this task
        delay_ms: Simulated work duration in milliseconds
    """
    await asyncio.sleep(delay_ms / 1000)
    return {
        "task_id": task_id,
        "status": "complete",
    }


# =============================================================================
# Benchmark Runner
# =============================================================================

def run_benchmark(num_tasks: int, max_concurrent: int = None) -> dict:
    """
    Run a benchmark with the given number of tasks and max_concurrent setting.
    
    Returns:
        Dict with timing and throughput stats
    """
    completed = [0]
    
    def on_complete(result):
        completed[0] += 1
    
    workflow = job(work=simulate_work)
    fm = FlowManager(on_complete=on_complete, max_concurrent=max_concurrent)
    fq_name = fm.add_workflow(workflow, "benchmark")
    
    start = time.perf_counter()
    
    # Use submit_batch for clean iteration
    fm.submit_batch(
        range(num_tasks),
        lambda i: {"work.task_id": i, "work.delay_ms": 50},
        fq_name
    )
    
    success = fm.wait_for_completion(timeout=300, check_interval=0.1)
    elapsed = time.perf_counter() - start
    
    return {
        "num_tasks": num_tasks,
        "max_concurrent": max_concurrent or "unlimited",
        "elapsed": elapsed,
        "throughput": num_tasks / elapsed if elapsed > 0 else 0,
        "success": success,
        "completed": completed[0],
    }


def main():
    parser = argparse.ArgumentParser(description="Scale test for FlowManager")
    parser.add_argument("--tasks", type=int, default=1000, 
                        help="Number of tasks to run per test (default: 1000)")
    parser.add_argument("--levels", type=str, default="100,500,1000,2000",
                        help="Comma-separated max_concurrent values to test")
    
    args = parser.parse_args()
    
    levels = [int(x) for x in args.levels.split(",")]
    
    print("=" * 60)
    print("Flow4AI Scale Test")
    print("=" * 60)
    print(f"\nTesting {args.tasks} tasks at max_concurrent levels: {levels}")
    print("\n" + "-" * 60)
    
    results = []
    
    # Test unlimited first (may hang if too many tasks!)
    if args.tasks <= 500:
        print(f"\n🔄 Testing unlimited (tasks={args.tasks})...")
        result = run_benchmark(args.tasks, max_concurrent=None)
        results.append(result)
        print(f"   ✅ {result['elapsed']:.2f}s ({result['throughput']:.0f} tasks/sec)")
    else:
        print(f"\n⚠️  Skipping unlimited test (tasks > 500 may hang)")
    
    # Test each level
    for level in levels:
        print(f"\n🔄 Testing max_concurrent={level}...")
        result = run_benchmark(args.tasks, max_concurrent=level)
        results.append(result)
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {result['elapsed']:.2f}s ({result['throughput']:.0f} tasks/sec)")
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n{'max_concurrent':<15} {'Time (s)':<12} {'Throughput':<15} {'Status'}")
    print("-" * 55)
    
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        mc = str(r["max_concurrent"])
        print(f"{mc:<15} {r['elapsed']:<12.2f} {r['throughput']:<15.0f} {status}")
    
    # Recommendation
    best = max([r for r in results if r["success"]], key=lambda x: x["throughput"])
    print(f"\n💡 Recommendation: max_concurrent={best['max_concurrent']}")
    print(f"   Achieved {best['throughput']:.0f} tasks/sec")


if __name__ == "__main__":
    main()
