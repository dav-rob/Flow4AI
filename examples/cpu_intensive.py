import asyncio
import time
import sys
import os
import argparse

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job import Job
from job_chain import JobChain

class CPUIntensiveJob(Job):
    def __init__(self):
        super().__init__("CPU Intensive", "Calculate primes", "cpu-model")
        
    async def execute(self, task) -> dict:
        """Calculate prime numbers up to n using CPU-intensive operations"""
        n = int(task)
        
        def is_prime(num):
            if num < 2:
                return False
            # More intensive check - don't use sqrt optimization
            for i in range(2, num):
                if num % i == 0:
                    return False
            return True
        
        start_time = time.time()
        primes = []
        
        # CPU intensive work - check every number
        checked = 0
        for i in range(2, n):
            checked += 1
            if is_prime(i):
                primes.append(i)
            
            # Print progress every 1000 numbers
            if checked % 1000 == 0:
                print(f"Task {n}: Checked {checked}/{n} numbers, found {len(primes)} primes...")
                
        duration = time.time() - start_time
        return {
            "task": task,
            "primes_found": len(primes),
            "largest_prime": primes[-1] if primes else None,
            "duration": duration
        }

def result_processor(result):
    """Print results as they complete"""
    print(f"\nCompleted task {result['task']}: Found {result['primes_found']} primes, "
          f"largest: {result['largest_prime']}, "
          f"took {result['duration']:.2f}s")

async def main(target_duration: float = 30.0):
    # Create job chain
    job = CPUIntensiveJob()
    job_chain = JobChain(job, result_processor)
    
    print(f"Starting CPU intensive tasks (target duration: {target_duration} seconds)...")
    print("You can now inspect this process with tools like top, ps, htop, etc.")
    print(f"Process ID: {job_chain.analyzer_process.pid}")
    
    # Base ranges for each batch
    ranges = [5000, 7000, 9000, 11000, 13000]
    batch = 1
    
    start_time = time.time()
    
    while True:
        # Submit a batch of tasks
        print(f"\nSubmitting batch {batch}...")
        for n in ranges:
            scaled_n = n * batch  # Increase size with each batch
            job_chain.submit_task(str(scaled_n))
            print(f"Submitted task to find primes up to {scaled_n}")
        
        elapsed_time = time.time() - start_time
        print(f"\nElapsed time: {elapsed_time:.2f}s / {target_duration:.2f}s")
        
        if elapsed_time >= target_duration:
            break
            
        batch += 1
        
        # Small delay between batches to allow some results to process
        await asyncio.sleep(0.1)
    
    # Mark completion and wait
    job_chain.mark_input_completed()
    
    total_duration = time.time() - start_time
    print(f"\nAll tasks completed in {total_duration:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run CPU intensive tasks for a specified duration.')
    parser.add_argument('--duration', type=float, default=30.0,
                       help='Target duration in seconds (default: 30.0)')
    args = parser.parse_args()
    
    asyncio.run(main(args.duration))
