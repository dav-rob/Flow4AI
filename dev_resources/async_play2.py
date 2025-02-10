import asyncio
import time
from collections import deque

from jobchain.taskmanager import TaskManager


async def sample_task():
    """A simple async task that sleeps briefly and returns."""
    await asyncio.sleep(0.1)  # Simulate  async work
    return "ok"

def test_concurrency():
    task_manager = TaskManager()
    concurrency_levels = [10, 50, 100, 500, 1000, 3000, 5000, 10000, 20000]
    
    print("Starting concurrency tests...")
    
    for n in concurrency_levels:
        # Capture initial state before submitting new tasks
        initial_counts = task_manager.get_counts()
        initial_processed = initial_counts['completed'] + initial_counts['errors']
        
        # Submit N tasks
        submit_start = time.time()
        for _ in range(n):
            task_manager.submit(sample_task)
        submit_time = time.time() - submit_start
        
        print(f"\nSubmitted {n} tasks in {submit_time:.3f}s. Waiting for completion...")
        
        # Track processing time
        processing_start = time.time()
        last_reported = time.time()
        while True:
            current = task_manager.get_counts()
            current_processed = current['completed'] + current['errors']
            target_processed = initial_processed + n
            
            # Periodically log progress to avoid appearing frozen
            if time.time() - last_reported > 5:  # Log every 5 seconds
                elapsed = time.time() - processing_start
                print(f"  Waiting... {elapsed:.1f}s elapsed. Processed: {current_processed - initial_processed}/{n}")
                last_reported = time.time()
            
            if current_processed >= target_processed:
                total_time = time.time() - processing_start
                # Calculate errors specific to this test batch
                errors_in_test = current['errors'] - initial_counts['errors']
                print(f"Concurrency {n}: Processed {n} tasks in {total_time:.3f}s. Errors: {errors_in_test}")
                break
            
            time.sleep(0.1)  # Avoid high CPU usage while waiting
    
    print("\nConcurrency test completed.")

if __name__ == "__main__":
    test_concurrency()
