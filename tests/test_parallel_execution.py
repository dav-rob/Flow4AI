import multiprocessing as mp
import asyncio
import time
from time import sleep
from utils.print_utils import printh
from job_chain import JobChain
from job import Job, JobFactory
import pytest

class DelayedJob(Job):
    def __init__(self, name: str, prompt: str, model: str, time_delay: float):
        super().__init__(name, prompt, model)
        self.time_delay = time_delay

    async def execute(self, task) -> dict:
        print(f"Async DelayedJob for {task} with delay {self.time_delay}")
        await asyncio.sleep(self.time_delay)  # Use specified delay
        return {"task": task, "status": "complete"}

# Extend JobFactory to handle delayed jobs
def create_delayed_job(params: dict) -> Job:
    time_delay = params.get('time_delay', 1.0)
    return DelayedJob("Delayed Job", "Test prompt", "test-model", time_delay)

JobFactory._load_from_file = create_delayed_job

async def run_job_chain(time_delay: float) -> float:
    """Run job chain with specified delay and return execution time"""
    start_time = time.perf_counter()
    
    job_chain_context = {
        "job_context": {
            "type": "file",
            "params": {"time_delay": time_delay}
        }
    }

    job_chain = JobChain(job_chain_context)
    job_chain.start()

    # Feed 10 tasks with a delay between each to simulate data gathering
    for i in range(10):
        job_chain.task_queue.put(f"Task {i}")
        await asyncio.sleep(0.2)  # Simulate time taken to gather data
    job_chain.task_queue.put(None)

    # Collect results
    results = []
    while True:
        result = job_chain.result_queue.get()
        if result is None:
            break
        results.append(result)

    job_chain.wait_for_completion()
    execution_time = time.perf_counter() - start_time
    print(f"Execution time for delay {time_delay}s: {execution_time:.2f}s")
    return execution_time

def test_parallel_execution():
    # Test with 1 second delay
    time_1s = asyncio.run(run_job_chain(1.0))
    
    # Test with 2 second delay
    time_2s = asyncio.run(run_job_chain(2.0))
    
    # Calculate the ratio of execution times
    time_ratio = time_2s / time_1s
    print(f"\nTime with 1s delay: {time_1s:.2f}s")
    print(f"Time with 2s delay: {time_2s:.2f}s")
    print(f"Ratio: {time_ratio:.2f}x")
    
    # With 0.2s delay between tasks (total 1.8s for adding tasks)
    # If tasks run in parallel:
    #   - 10 tasks with 1s delay should take ~2.8s (1.8s for adding + 1s for execution)
    #   - 10 tasks with 2s delay should take ~3.8s (1.8s for adding + 2s for execution)
    # Allow +0.5s for system overhead and timing variations
    
    assert time_1s <= 3.3, (
        f"Expected tasks to complete in ~3.3s (including data gathering + overhead), took {time_1s:.2f}s. "
        "This suggests tasks are running sequentially"
    )
    
    assert time_2s <= 4.3, (
        f"Expected tasks to complete in ~4.3s (including data gathering + overhead), took {time_2s:.2f}s. "
        "This suggests tasks are running sequentially"
    )
    
    # Ratio should still be close to 1 since most time is spent gathering data
    assert time_ratio <= 1.5, (
        f"Expected time ratio <= 1.5, got {time_ratio:.2f}. "
        "This suggests tasks are running sequentially instead of in parallel"
    )

async def run_batch_job_chain() -> float:
    """Run job chain with batches of website analysis jobs"""
    start_time = time.perf_counter()
    
    # Configure JobChain with 7-second analysis jobs
    job_chain_context = {
        "job_context": {
            "type": "file",
            "params": {"time_delay": 0.70}  # Each analysis takes 7 seconds
        }
    }

    job_chain = JobChain(job_chain_context)
    job_chain.start()

    # Process 4 batches of 25 links each
    for batch in range(4):
        # Simulate scraping 25 links, 1 second per link
        for link in range(25):
            job_chain.task_queue.put(f"Batch{batch}_Link{link}")
            await asyncio.sleep(0.10)  # Simulate time to scrape each link
    
    job_chain.task_queue.put(None)  # Signal end of tasks

    # Collect all results
    results = []
    while True:
        result = job_chain.result_queue.get()
        if result is None:
            break
        results.append(result)

    job_chain.wait_for_completion()
    execution_time = time.perf_counter() - start_time
    print(f"\nTotal execution time: {execution_time:.2f}s")
    print(f"Number of processed results: {len(results)}")
    return execution_time

def test_parallel_execution_in_batches():
    """Test parallel execution of website analysis in batches while scraping continues"""
    execution_time = asyncio.run(run_batch_job_chain())
    
    # Expected timing:
    # - 4 batches * 25 links * 1s per link = 100s for scraping
    # - Analysis jobs (7s each) should run in parallel while scraping continues
    # Allow +10s for system overhead and timing variations
    
    assert execution_time <= 11, (
        f"Expected execution to complete in ~107s = (scraping time) + 1 x analysis time, took {execution_time:.2f}s. "
        "This suggests analysis jobs are not running in parallel with scraping"
    )
    
    # Ensure execution doesn't complete too quickly, which would indicate incorrect implementation
    assert execution_time >= 9.5, (
        f"Execution completed too quickly in {execution_time:.2f}s. "
        "Expected ~100s for scraping all links"
    )

async def run_parallel_load_test(num_tasks: int) -> float:
    """Run a load test with specified number of parallel tasks"""
    start_time = time.perf_counter()
    
    job_chain_context = {
        "job_context": {
            "type": "file",
            "params": {"time_delay": 1.0}  # Each task takes 1 second
        }
    }

    job_chain = JobChain(job_chain_context)
    job_chain.start()

    # Submit all tasks immediately
    for i in range(num_tasks):
        job_chain.task_queue.put(f"Task_{i}")
    job_chain.task_queue.put(None)

    # Collect results
    results = []
    while True:
        result = job_chain.result_queue.get()
        if result is None:
            break
        results.append(result)

    job_chain.wait_for_completion()
    execution_time = time.perf_counter() - start_time
    print(f"\nExecution time for {num_tasks} tasks: {execution_time:.2f}s")
    print(f"Number of completed tasks: {len(results)}")
    return execution_time

def test_maximum_parallel_execution():
    """Test the maximum theoretical parallel execution capacity"""
    
    # Test with increasing number of tasks
    task_counts = [100, 500, 2500, 10000, 15000]
    
    for count in task_counts:
        execution_time = asyncio.run(run_parallel_load_test(count))
        
        assert execution_time < 2.0, (
            f"Expected {count} tasks to complete in under 2 seconds with parallel execution, "
            f"took {execution_time:.2f}s"
        )
        
        tasks_per_second = count / execution_time
        print(f"Tasks per second with {count} tasks: {tasks_per_second:.2f}")
