import asyncio
import logging
import time
import pytest
from job import Job, JobFactory
from job_chain import JobChain

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DelayedJob(Job):
    def __init__(self, name: str, prompt: str, model: str, time_delay: float):
        super().__init__(name, prompt, model)
        self.time_delay = time_delay

    async def execute(self, task) -> dict:
        """Execute a delayed job with tracing."""
        logger.info(f"Executing DelayedJob for {task} with delay {self.time_delay}")
        await asyncio.sleep(self.time_delay)  # Use specified delay
        return {"task": task, "status": "complete"}

def create_delayed_job(params: dict) -> Job:
    time_delay = params.get('time_delay', 1.0)
    return DelayedJob("Test Job", "Test prompt", "test-model", time_delay)

# Store original load_from_file function
original_load_from_file = JobFactory._load_from_file

def setup_module(module):
    """Set up test environment"""
    JobFactory._load_from_file = create_delayed_job

def teardown_module(module):
    """Restore original implementation"""
    JobFactory._load_from_file = original_load_from_file

def dummy_result_processor(result):
    """Dummy function for processing results in tests"""
    logger.info(f"Processing result: {result}")

async def run_parallel_load_test(num_tasks: int) -> float:
    """Run a load test with specified number of parallel tasks
    
    Args:
        num_tasks: Number of tasks to run in parallel
        
    Returns:
        float: Total execution time in seconds
    """
    start_time = time.perf_counter()
    
    job_chain_context = {
        "job_context": {
            "type": "file",
            "params": {"time_delay": 0.01}  # Very small delay for load testing
        }
    }

    job_chain = JobChain(job_chain_context, dummy_result_processor)

    # Submit all tasks immediately
    for i in range(num_tasks):
        job_chain.submit_task(f"Task_{i}")
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

    execution_time = time.perf_counter() - start_time
    logger.info(f"\nExecution time for {num_tasks} tasks: {execution_time:.2f}s")
    return execution_time

async def run_sustained_load_test(tasks_per_second: int, duration: int) -> tuple[float, float]:
    """Run a sustained load test with consistent task submission rate
    
    Args:
        tasks_per_second: Number of tasks to submit per second
        duration: Duration of the test in seconds
        
    Returns:
        tuple[float, float]: (average_latency, max_latency) in seconds
    """
    job_chain_context = {
        "job_context": {
            "type": "file",
            "params": {"time_delay": 0.05}  # 50ms baseline processing time
        }
    }

    job_chain = JobChain(job_chain_context, dummy_result_processor)
    
    start_time = time.perf_counter()
    latencies = []
    
    # Calculate sleep time between tasks to achieve desired rate
    sleep_time = 1.0 / tasks_per_second
    
    # Submit tasks at the specified rate for the specified duration
    task_count = 0
    while time.perf_counter() - start_time < duration:
        task_start = time.perf_counter()
        job_chain.submit_task(f"SustainedTask_{task_count}")
        task_count += 1
        
        # Record latency
        latency = time.perf_counter() - task_start
        latencies.append(latency)
        
        # Sleep to maintain desired rate
        await asyncio.sleep(sleep_time)
    
    # Mark completion and calculate metrics
    job_chain.mark_input_completed()
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    return avg_latency, max_latency

def test_maximum_parallel_execution():
    """Test the maximum theoretical parallel execution capacity
    
    This test verifies the system's ability to handle increasing loads of parallel tasks,
    from 100 to 10,000 tasks. It ensures that execution times stay within expected
    thresholds as the task count increases, demonstrating effective parallel processing.
    
    The test uses progressively larger task counts and adjusts expected completion
    times based on the load, accounting for system overhead and parallel processing
    capabilities.
    
    To run this test:
    Use pytest's --full-suite option: pytest --full-suite
    """
    
    # Test with increasing number of tasks
    task_counts = [100, 500, 2500, 5000, 7500, 10000]
    
    for count in task_counts:
        execution_time = asyncio.run(run_parallel_load_test(count))
        
        # Scale expected time with task count
        if count <= 100:
            expected_time = 2.0
        elif count <= 500:
            expected_time = 4.0
        elif count <= 2500:
            expected_time = 10.0
        elif count <= 5000:
            expected_time = 15.0
        elif count <= 7500:
            expected_time = 20.0
        else:  # 10000 tasks
            expected_time = 25.0
            
        assert execution_time < expected_time, (
            f"Expected {count} tasks to complete in under {expected_time} seconds with parallel execution, "
            f"took {execution_time:.2f}s"
        )
        
        tasks_per_second = count / execution_time
        logger.info(f"Tasks per second with {count} tasks: {tasks_per_second:.2f}")

def test_sustained_load_performance():
    """Test system performance under sustained load
    
    This test verifies the system's ability to handle a consistent stream of tasks
    over time while maintaining acceptable latency. It submits tasks at a fixed rate
    and measures both average and maximum latency to ensure system stability under
    continuous load.
    
    The test runs for a fixed duration, submitting tasks at a specified rate, and
    ensures that latency stays within acceptable bounds throughout the test period.
    
    To run this test:
    Use pytest's --full-suite option: pytest --full-suite
    """
    # Test with moderate sustained load: 10 tasks per second for 30 seconds
    tasks_per_second = 10
    duration = 30
    
    avg_latency, max_latency = asyncio.run(
        run_sustained_load_test(tasks_per_second, duration)
    )
    
    # Verify latency remains within acceptable bounds
    assert avg_latency < 0.1, (
        f"Average latency ({avg_latency:.3f}s) exceeded threshold of 0.1s "
        "under sustained load"
    )
    
    assert max_latency < 0.5, (
        f"Maximum latency ({max_latency:.3f}s) exceeded threshold of 0.5s "
        "under sustained load"
    )
    
    logger.info(f"Sustained load test metrics:")
    logger.info(f"  Average latency: {avg_latency:.3f}s")
    logger.info(f"  Maximum latency: {max_latency:.3f}s")
