"""
Example 4: Multiprocessing with FlowManagerMP

Demonstrates FlowManagerMP's multi-process parallel execution:
- True parallelism across CPU cores
- CPU-bound task processing
- Proper cleanup with close_processes()
"""

import time
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


def main():
    """Run the multiprocessing example."""
    print("\n" + "="*60)
    print("Example 4: Multiprocessing (FlowManagerMP)")
    print("="*60 + "\n")
    
    print("Processing CPU-intensive tasks across multiple processes...\n")
    
    # Wrap the CPU-intensive function
    jobs = wrap({"compute": cpu_intensive_task})
    dsl = jobs["compute"]
    
    # Create FlowManagerMP instance
    fm = FlowManagerMP(dsl)
    fq_name = fm.get_fq_names()[0]
    
    # Submit multiple CPU-intensive tasks
    task_data_sizes = [1000, 2000, 3000, 5000, 10000]
    
    print(f"Submitting {len(task_data_sizes)} CPU-intensive tasks...")
    start_time = time.perf_counter()
    
    for size in task_data_sizes:
        task = {"compute.data_size": size}
        fm.submit_task(task, fq_name)
    
    # Close processes and wait for completion
    # This will wait for all tasks to complete and clean up worker processes
    fm.close_processes()
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"\n✅ All tasks completed in {execution_time:.2f}s")
    print(f"   Average time per task: {execution_time / len(task_data_sizes):.2f}s")
    
    print("\nKey Points:")
    print("  - FlowManagerMP uses multiprocessing for true parallelism")
    print("  - Multiple CPU cores process tasks simultaneously")
    print("  - Ideal for CPU-bound tasks (computation, data processing)")
    print("  - close_processes() waits for completion and cleans up")
    
    print("\n⚠️  Note: Multiprocessing requires picklable functions and data")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
