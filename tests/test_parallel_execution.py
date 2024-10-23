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
