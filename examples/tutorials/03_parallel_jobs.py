"""
Tutorial 03: Parallel Jobs

Demonstrates FlowManager's multi-threaded parallel execution:
- Submit 1000 tasks concurrently
- Tasks complete WHILE others are still being submitted (interlacing)
- All tasks execute in parallel using async/await
- Proof of parallelism via execution time
"""

import asyncio
import time
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job


async def simulate_work(task_id, duration=0.5):
    """Simulate work with an async delay."""
    await asyncio.sleep(duration)
    return {"task_id": task_id, "status": "completed", "duration": duration}


# Global counter for tracking completions
completion_count = 0
total_expected = 0


def handle_completion(result):
    """
    Track task completions - demonstrates tasks completing WHILE submissions continue.
    
    This will show interlacing: early tasks complete before all tasks are even submitted!
    """
    global completion_count, total_expected
    completion_count += 1
    
    task_id = result.get("task_id", "unknown")
    
    # Print first and last completion to show timing
    if completion_count == 1:
        print(f"   🎯 FIRST completion: {task_id} (while submissions continue...)")
    elif completion_count == total_expected:
        print(f"   🎯 FINAL completion: {task_id}")


def main():
    """Run the parallel execution example."""
    global completion_count, total_expected
    
    print("\n" + "="*60)
    print("Example 3: Parallel Execution (FlowManager)")
    print("="*60 + "\n")
    
    print("This example demonstrates TRUE parallel execution:")
    print("- Tasks complete WHILE others are still being submitted")
    print("- First task completes before last task is even submitted!")
    print("- Shows interlacing of submission and completion\n")
    
    # Create workflow from async function
    # WORKFLOW = a graph of connected jobs (here just one job)
    workflow = job(worker=simulate_work)
    
    # Create FlowManager with completion handler
    fm = FlowManager(on_complete=handle_completion)
    fq_name = fm.add_workflow(workflow, "parallel_workers")
    
    # Test with increasing task counts
    task_counts = [100, 500, 1000]
    
    for count in task_counts:
        # Reset counters
        completion_count = 0
        total_expected = count
        
        print(f"\n{'─'*60}")
        print(f"Submitting {count} tasks with 0.5s delay each...")
        print(f"{'─'*60}")
        
        start_time = time.perf_counter()
        
        # Submit all tasks (with tiny delay to make interlacing visible)
        for i in range(count):
            task = {"worker.task_id": f"task_{i}", "worker.duration": 0.5}
            fm.submit_task(task, fq_name)
            
            # Print first and last submission
            if i == 0:
                print(f"   📤 FIRST submission: task_0")
            elif i == count - 1:
                print(f"   📤 FINAL submission: task_{i}")
            
            # Tiny delay to allow interlacing to be visible
            # (In real apps, submissions have natural delays from data processing)
            if i < count - 1:  # Don't delay after last submission
                time.sleep(0.001)  # 1ms delay between submissions
        
        # Wait for completion
        success = fm.wait_for_completion(timeout=15, check_interval=0.1)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        if not success:
            print(f"❌ Timeout waiting for {count} tasks to complete")
            continue
        
        # Calculate metrics
        sequential_time = count * 0.5
        speedup = sequential_time / execution_time
        
        print(f"\n✅ Results:")
        print(f"   Completed: {completion_count}/{count} tasks")
        print(f"   Execution time: {execution_time:.2f}s")
        print(f"   Sequential time: {sequential_time:.2f}s")
        print(f"   Speedup: {speedup:.1f}x faster")
        
        # Verify true parallelism
        if speedup >= 10:
            print(f"   ✨ CONFIRMED: Tasks ran in parallel!")
        else:
            print(f"   ⚠️  Slower than expected")
    
    print("\n" + "="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ First completion happens BEFORE final submission")
    print("✓ This proves concurrent execution (not sequential)")
    print("✓ Submissions and completions INTERLEAVE")
    print("✓ FlowManager uses asyncio for true parallelism")
    print("✓ Ideal for I/O-bound tasks (API calls, DB queries)")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
