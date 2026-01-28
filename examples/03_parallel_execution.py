"""
Example 3: Parallel Execution with FlowManager

Demonstrates FlowManager's multi-threaded parallel execution:
- Submit 1000 tasks concurrently
- All tasks execute in parallel using async/await
- Proof of parallelism via execution time
"""

import asyncio
import time
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap


async def simulate_work(task_id, duration=0.5):
    """Simulate work with an async delay."""
    await asyncio.sleep(duration)
    return {"task_id": task_id, "status": "completed", "duration": duration}


def main():
    """Run the parallel execution example."""
    print("\n" + "="*60)
    print("Example 3: Parallel Execution (FlowManager)")
    print("="*60 + "\n")
    
    # Wrap the async function as a job
    dsl = wrap(worker=simulate_work)
    
    # Create FlowManager instance
    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "parallel_workers")
    
    # Test with increasing task counts
    task_counts = [100, 500, 1000]
    
    for count in task_counts:
        print(f"\nSubmitting {count} tasks with 0.5s delay each...")
        
        start_time = time.perf_counter()
        
        # Submit all tasks
        for i in range(count):
            task = {"worker.task_id": f"task_{i}", "worker.duration": 0.5}
            fm.submit_task(task, fq_name)
        
        # Wait for completion
        success = fm.wait_for_completion(timeout=10, check_interval=0.1)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        if not success:
            print(f"❌ Timeout waiting for {count} tasks to complete")
            continue
        
        # Get results
        results = fm.pop_results()
        
        if results["errors"]:
            print(f"❌ Errors in {count} task execution: {results['errors']}")
            continue
        
        # Calculate metrics
        completed_count = fm.get_counts()["completed"]
        
        print(f"✅ Completed {completed_count} tasks in {execution_time:.2f}s")
        print(f"   Sequential would take: {count * 0.5:.2f}s")
        print(f"   Speedup: {(count * 0.5) / execution_time:.1f}x")
        
        # Verify true parallelism
        if execution_time < count * 0.5 * 0.1:  # Should be at least 10x faster
            print(f"   ✨ Confirmed parallel execution!")
        else:
            print(f"   ⚠️  Execution slower than expected")
    
    print("\nKey Points:")
    print("  - FlowManager uses asyncio for concurrent execution")
    print("  - Tasks execute in parallel, not sequentially")
    print("  - Execution time proves parallelism (not sequential)")
    print("  - Ideal for I/O-bound tasks (API calls, database queries)")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
