"""
Example 4: Multiprocessing with FlowManagerMP

Demonstrates FlowManagerMP's multi-process parallel execution:
- True parallelism across CPU cores
- CPU-bound task processing
- on_complete callback for result handling
- Proper cleanup with close_processes()
"""

import multiprocessing as mp
import time
from functools import partial
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.dsl import wrap


def cpu_intensive_task(data_size):
    """Simulate CPU-intensive work."""
    # Calculate prime numbers (CPU-bound)
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    # Find primes up to data_size
    primes = [n for n in range(2, data_size) if is_prime(n)]
    
    return {
        "data_size": data_size,
        "primes_found": len(primes),
        "largest_prime": primes[-1] if primes else None
    }


def handle_completion(results_list, result):
    """
    Process completed tasks - runs in child process context.
    
    Must be at module level for pickling (multiprocessing requirement).
    """
    data_size = result.get("data_size", 0)
    primes_found = result.get("primes_found", 0)
    largest_prime = result.get("largest_prime", "N/A")
    
    results_list.append({
        "data_size": data_size,
        "primes_found": primes_found,
        "largest_prime": largest_prime
    })
    
    # Print completion (first and last for simplicity)
    task_num = len(results_list)
    if task_num == 1:
        print(f"   🎯 FIRST completion: data_size={data_size}, found {primes_found} primes")
    elif task_num == 5:  # We know we're submitting 5 tasks
        print(f"   🎯 FINAL completion: data_size={data_size}, found {primes_found} primes")


def main():
    """Run the multiprocessing example."""
    print("\n" + "="*60)
    print("Example 4: Multiprocessing (FlowManagerMP)")
    print("="*60 + "\n")
    
    print("This example demonstrates multiprocessing with on_complete:")
    print("- CPU-intensive tasks run across multiple cores")
    print("- on_complete callback processes results as they finish")
    print("- Shows task completion tracking\n")
    
    # Create a manager for sharing data between processes
    manager = mp.Manager()
    completed_tasks = manager.list()
    
    # Create partial function with shared results list
    collector = partial(handle_completion, completed_tasks)
    
    # Wrap the CPU-intensive function
    dsl = wrap(compute=cpu_intensive_task)
    
    # Create FlowManagerMP with on_complete callback
    fm = FlowManagerMP(dsl, on_complete=collector)
    fq_name = fm.get_fq_names()[0]
    
    # Submit multiple CPU-intensive tasks
    task_data_sizes = [1000, 2000, 3000, 5000, 10000]
    
    print(f"{'─'*60}")
    print(f"Submitting {len(task_data_sizes)} CPU-intensive tasks...")
    print(f"{'─'*60}\n")
    
    start_time = time.perf_counter()
    
    for i, size in enumerate(task_data_sizes):
        task = {"compute.data_size": size}
        fm.submit_task(task, fq_name)
        
        # Print first and last submission
        if i == 0:
            print(f"   📤 FIRST submission: data_size={size}")
        elif i == len(task_data_sizes) - 1:
            print(f"   📤 FINAL submission: data_size={size}")
    
    # Close processes and wait for completion
    # This will wait for all tasks to complete and clean up worker processes
    fm.close_processes()
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("✅ Results:")
    print(f"{'='*60}")
    print(f"   Completed: {len(completed_tasks)}/{len(task_data_sizes)} tasks")
    print(f"   Execution time: {execution_time:.2f}s")
    print(f"   Average per task: {execution_time / len(task_data_sizes):.2f}s")
    
    # Display summary
    print(f"\n   Task Results:")
    for result in completed_tasks:
        print(f"     • Size {result['data_size']:5d}: {result['primes_found']:4d} primes "
              f"(largest: {result['largest_prime']})")
    
    print("\n" + "="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ FlowManagerMP uses multiprocessing for true CPU parallelism")
    print("✓ Multiple CPU cores process tasks simultaneously")
    print("✓ on_complete callback works across process boundaries")
    print("✓ Ideal for CPU-bound tasks (computation, data processing)")
    print("✓ close_processes() waits for completion and cleans up")
    print("="*60 + "\n")
    
    print("⚠️  Note: Multiprocessing requires picklable functions and data\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
