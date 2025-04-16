"""
    Tests parallel workloads with some meaningful load in parallel execution mode:
        - test_parallel_execution: makes sure long running tasks are executed in 
            parallel with short running tasks, and that task results are processed in 
            parallel.
        - run_batch_job_chain: simulates running a Job on several batches of tasks.
        - test_parallel_execution_in_batches: runs batches in parallel
"""
import asyncio
import json
import os
import time

import yaml

from flow4ai import jc_logging as logging
from flow4ai.job import JobABC
from flow4ai.job_chain import JobChain
from flow4ai.utils.otel_wrapper import TracerFactory
from tests.test_utils.simple_job import SimpleJobFactory

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DelayedJob(JobABC):
    def __init__(self, name: str, time_delay: float):
        super().__init__(name)
        self.time_delay = time_delay

    async def run(self, task) -> dict:
        """Execute a delayed job with tracing."""
        logger.info(f"Executing DelayedJob for {task} with delay {self.time_delay}")
        await asyncio.sleep(self.time_delay)  # Use specified delay
        return {"task": task, "status": "complete"}

def create_delayed_job(params: dict) -> JobABC:
    time_delay = params.get('time_delay', 1.0)
    return DelayedJob("Test Job", time_delay)

# Store original load_from_file function
original_load_from_file = SimpleJobFactory._load_from_file

def setup_module(module):
    """Set up test environment"""
    SimpleJobFactory._load_from_file = create_delayed_job

def teardown_module(module):
    """Restore original implementation"""
    SimpleJobFactory._load_from_file = original_load_from_file

def dummy_result_processor(result):
    """Dummy function for processing results in tests"""
    logger.info(f"Processing result: {result}")

async def run_job_chain(time_delay: float, use_direct_job: bool = False) -> float:
    """Run job chain with specified delay and return execution time"""
    start_time = time.perf_counter()
    
    if use_direct_job:
        # Create and pass Job instance directly
        job = DelayedJob("Test Job", time_delay)
        job_chain = JobChain(job, dummy_result_processor)
    else:
        # Use traditional dictionary initialization
        job_chain_context = {
                "type": "file",
                "params": {"time_delay": time_delay}
            }
        loaded_job = SimpleJobFactory.load_job(job_chain_context)
        job_chain = JobChain(loaded_job, dummy_result_processor)

    # Feed 10 tasks with a delay between each to simulate data gathering
    for i in range(10):
        job_chain.submit_task(f"Task {i}")
        await asyncio.sleep(0.2)  # Simulate time taken to gather data
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

    execution_time = time.perf_counter() - start_time
    logger.info(f"Execution time for delay {time_delay}s: {execution_time:.2f}s")
    return execution_time

def test_parallel_execution():
    # Test with 1 second delay
    time_1s = asyncio.run(run_job_chain(1.0))
    
    # Test with 2 second delay
    time_2s = asyncio.run(run_job_chain(2.0))
    
    # Calculate the ratio of execution times
    time_ratio = time_2s / time_1s
    logger.info(f"\nTime with 1s delay: {time_1s:.2f}s")
    logger.info(f"Time with 2s delay: {time_2s:.2f}s")
    logger.info(f"Ratio: {time_ratio:.2f}x")
    
    assert time_1s <= 3.8, (
        f"Expected tasks to complete in ~3.8s (including data gathering + overhead), took {time_1s:.2f}s. "
        "This suggests tasks are running sequentially"
    )
    
    assert time_2s <= 4.8, (
        f"Expected tasks to complete in ~4.8s (including data gathering + overhead), took {time_2s:.2f}s. "
        "This suggests tasks are running sequentially"
    )
    
    assert time_ratio <= 1.5, (
        f"Expected time ratio <= 1.5, got {time_ratio:.2f}. "
        "This suggests tasks are running sequentially instead of in parallel"
    )

def test_direct_job_initialization():
    """Test that direct Job instance initialization works equivalently"""
    # Run with dictionary initialization
    time_dict = asyncio.run(run_job_chain(1.0, use_direct_job=False))
    
    # Run with direct Job instance
    time_direct = asyncio.run(run_job_chain(1.0, use_direct_job=True))
    
    # Calculate the ratio of execution times
    time_ratio = abs(time_direct - time_dict) / time_dict
    logger.info(f"\nTime with dict initialization: {time_dict:.2f}s")
    logger.info(f"Time with direct Job instance: {time_direct:.2f}s")
    logger.info(f"Difference ratio: {time_ratio:.2f}")
    
    # The execution times should be very similar (within 10% of each other)
    assert time_ratio <= 0.1, (
        f"Expected similar execution times, but difference ratio was {time_ratio:.2f}. "
        "This suggests the two initialization methods are not equivalent"
    )

async def run_batch_job_chain() -> float:
    """Run job chain with batches of website analysis jobs"""
    start_time = time.perf_counter()
    
    job_chain_context = {
        "type": "file",
        "params": {"time_delay": 0.70}
    }
    loaded_job = SimpleJobFactory.load_job(job_chain_context)
    job_chain = JobChain(loaded_job, dummy_result_processor)

    # Process 4 batches of 25 links each
    for batch in range(4):
        # Simulate scraping 25 links, 1 second per link
        for link in range(25):
            job_chain.submit_task(f"Batch{batch}_Link{link}")
            await asyncio.sleep(0.10)  # Simulate time to scrape each link
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

    execution_time = time.perf_counter() - start_time
    logger.info(f"\nTotal execution time: {execution_time:.2f}s")
    return execution_time

def test_parallel_execution_in_batches():
    """Test parallel execution of website analysis in batches while scraping continues"""
    execution_time = asyncio.run(run_batch_job_chain())
    
    assert execution_time <= 11.8, (
        f"Expected execution to complete in ~11.8s, took {execution_time:.2f}s. "
        "This suggests analysis jobs are not running in parallel with scraping"
    )
    
    assert execution_time >= 9.5, (
        f"Execution completed too quickly in {execution_time:.2f}s. "
        "Expected ~10s for scraping all links"
    )

async def run_job_chain_without_result_processor() -> bool:
    """Run job chain without a result processing function"""
    try:
        job = DelayedJob("Test Job",  0.1)
        job_chain = JobChain(job)  # Pass no result_processing_function

        # Submit a few tasks
        for i in range(3):
            job_chain.submit_task(f"Task {i}")
        # Indicate there is no more input data to process to initiate shutdown
        job_chain.mark_input_completed()
        return True
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return False

def test_no_result_processor():
    """Test that JobChain works without setting result_processing_function"""
    success = asyncio.run(run_job_chain_without_result_processor())
    assert success, "JobChain should execute successfully without result_processing_function"

async def run_traced_job_chain(time_delay: float) -> float:
    """Run job chain with specified delay and return execution time"""
    start_time = time.perf_counter()
    
    # Use traditional dictionary initialization
    job_chain_context = {
        "type": "file",
        "params": {"time_delay": time_delay}
    }
    # Load job from context
    loaded_job = SimpleJobFactory.load_job(job_chain_context)
    job_chain = JobChain(loaded_job, dummy_result_processor)

    # Feed 10 tasks with a delay between each to simulate data gathering
    for i in range(10):
        job_chain.submit_task(f"Task {i}")
        await asyncio.sleep(0.2)  # Simulate time taken to gather data
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

    execution_time = time.perf_counter() - start_time
    logger.info(f"Execution time for delay {time_delay}s: {execution_time:.2f}s")
    return execution_time

def test_parallel_execution_with_tracing(tmp_path):
    """Test parallel execution with OpenTelemetry tracing enabled"""
    logger.info("Starting parallel execution with tracing test")
    
    # Set up temporary trace file
    trace_file = str(tmp_path / "temp_otel_trace.json")
    logger.info(f"Setting up trace file at: {trace_file}")
    with open(trace_file, 'w') as f:
        json.dump([], f)

    # Set up temporary config file
    config_path = str(tmp_path / "otel_config.yaml")
    config = {
        "exporter": "file",
        "service_name": "JobChainTest",
        "batch_processor": {
            "max_queue_size": 1000,
            "schedule_delay_millis": 1000
        },
        "file_exporter": {
            "path": trace_file
        }
    }
    
    logger.info(f"Writing config to: {config_path}")
    logger.info(f"Config content: {config}")
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    try:
        # Set environment variable before creating processes
        os.environ['JOBCHAIN_OT_CONFIG'] = config_path
        logger.info(f"Set JOBCHAIN_OT_CONFIG to: {os.environ.get('JOBCHAIN_OT_CONFIG')}")

        # Reset TracerFactory state
        TracerFactory._instance = None
        TracerFactory._config = None

        # Run the job chain
        logger.info("Starting job chain execution")
        execution_time = asyncio.run(run_traced_job_chain(1.0))
        logger.info("Job chain execution completed")

        # Verify execution time
        assert execution_time <= 3.5, (
            f"Expected tasks to complete in ~3.5s (including data gathering + overhead), took {execution_time:.2f}s. "
            "This suggests tasks are running sequentially"
        )

        # Wait for traces to be exported
        logger.info("Waiting for traces to be exported...")
        time.sleep(2.0)

        # Verify traces
        logger.info(f"Reading trace file: {trace_file}")
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
        logger.info(f"Raw trace data: {json.dumps(trace_data, indent=2)}")
            
        # Count execute method traces
        execute_traces = [
            span for span in trace_data 
            if span['name'].endswith('._execute')
        ]
        logger.info(f"Found {len(execute_traces)} execute traces")
        if len(execute_traces) > 0:
            logger.info("Sample trace names:")
            for trace in execute_traces[:3]:  # Show first 3 traces as sample
                logger.info(f"  - {trace['name']}")
        
        assert len(execute_traces) == 10, (
            f"Expected 10 execute traces (one per task), but found {len(execute_traces)}. "
            "This suggests not all tasks were traced properly."
        )

    finally:
        # Cleanup
        logger.info("Cleaning up test resources")
        if os.path.exists(trace_file):
            os.unlink(trace_file)
        if os.path.exists(config_path):
            os.unlink(config_path)
        if 'JOBCHAIN_OT_CONFIG' in os.environ:
            del os.environ['JOBCHAIN_OT_CONFIG']
        TracerFactory._instance = None
        TracerFactory._config = None
