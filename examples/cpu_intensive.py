import asyncio
import time
import sys
import os
import argparse
import logging

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job import Job
from job_chain import JobChain
from logging_config import setup_logging

# Initialize logging configuration
setup_logging()

class CPUIntensiveJob(Job):
    def __init__(self):
        super().__init__("CPU Intensive", "Calculate primes", "cpu-model")
        self.logger = logging.getLogger('CPUIntensiveJob')
        self.logger.debug("Initializing CPUIntensiveJob")
        
    async def execute(self, task) -> dict:
        """Calculate prime numbers up to n using CPU-intensive operations"""
        self.logger.debug(f"Starting prime calculation for n={task}")
        
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
                msg = f"Task {n}: Checked {checked}/{n} numbers, found {len(primes)} primes..."
                print(msg)
                self.logger.debug(msg)
                
        duration = time.time() - start_time
        result = {
            "task": task,
            "primes_found": len(primes),
            "largest_prime": primes[-1] if primes else None,
            "duration": duration
        }
        
        self.logger.debug(f"Completed task {task} in {duration:.2f}s")
        self.logger.debug(f"Found {len(primes)} primes, largest: {primes[-1] if primes else None}")
            
        return result

def result_processor(result):
    """Print results as they complete"""
    logger = logging.getLogger('ResultProcessor')
    msg = f"\nCompleted task {result['task']}: Found {result['primes_found']} primes, " \
          f"largest: {result['largest_prime']}, " \
          f"took {result['duration']:.2f}s"
    print(msg)
    logger.debug(f"Processed result: {msg}")

def main(target_duration: float = 30.0):
    # Create job chain
    job = CPUIntensiveJob()
    job_chain = JobChain(job, result_processor)
    
    print(f"Starting CPU intensive tasks (target duration: {target_duration} seconds)...")
    print("You can now inspect this process with tools like top, ps, htop, etc.")
    print(f"Process ID: {job_chain.job_executor_process.pid}")
    
    # Use numbers that take roughly 1 second each to process
    numbers = [15000, 15500, 16000]  # Each should take ~1 second
    
    start_time = time.time()
    tasks_submitted = 0
    
    # Submit just enough tasks to fill the target duration
    num_tasks = max(1, int(target_duration))  # One task per second
    
    for _ in range(num_tasks):
        # Cycle through our numbers
        n = numbers[tasks_submitted % len(numbers)]
        job_chain.submit_task(str(n))
        print(f"Submitted task to find primes up to {n}")
        tasks_submitted += 1
        
        elapsed_time = time.time() - start_time
        print(f"\nElapsed time: {elapsed_time:.2f}s / {target_duration:.2f}s")
        
        if elapsed_time >= target_duration:
            break
    
    # Mark completion and wait
    job_chain.mark_input_completed()
    
    total_duration = time.time() - start_time
    print(f"\nAll tasks completed in {total_duration:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run CPU intensive tasks for a specified duration.')
    parser.add_argument('--duration', type=float, default=3.0,
                       help='Target duration in seconds (default: 30.0)')
    args = parser.parse_args()
    
    main(args.duration)
