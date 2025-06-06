import asyncio
import json
import os
import time

import pytest
import yaml

from flow4ai import f4a_logging as logging
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC
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

async def run_parallel_load_test(num_tasks: int) -> float:
    """Run a load test with specified number of parallel tasks
    
    Args:
        num_tasks: Number of tasks to run in parallel
        
    Returns:
        float: Total execution time in seconds
    """
    start_time = time.perf_counter()
    
    flowmanagerMP_context = {
            "type": "file",
            "params": {"time_delay": 0.01}  # Very small delay for load testing
        }
    loaded_job = SimpleJobFactory.load_job(flowmanagerMP_context)
    flowmanagerMP = FlowManagerMP(loaded_job, dummy_result_processor)

    # Submit all tasks immediately
    for i in range(num_tasks):
        flowmanagerMP.submit_task(f"Task_{i}")
    # Indicate there is no more input data to process to initiate shutdown
    flowmanagerMP.close_processes()

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
    flowmanagerMP_context = {
        "type": "file",
        "params": {"time_delay": 0.05}  # 50ms baseline processing time
    }
    loaded_job = SimpleJobFactory.load_job(flowmanagerMP_context)
    flowmanagerMP = FlowManagerMP(loaded_job, dummy_result_processor)
    
    start_time = time.perf_counter()
    latencies = []
    
    # Calculate sleep time between tasks to achieve desired rate
    sleep_time = 1.0 / tasks_per_second
    
    # Submit tasks at the specified rate for the specified duration
    task_count = 0
    while time.perf_counter() - start_time < duration:
        task_start = time.perf_counter()
        flowmanagerMP.submit_task(f"SustainedTask_{task_count}")
        task_count += 1
        
        # Record latency
        latency = time.perf_counter() - task_start
        latencies.append(latency)
        
        # Sleep to maintain desired rate
        await asyncio.sleep(sleep_time)
    
    # Mark completion and calculate metrics
    flowmanagerMP.close_processes()
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
    
    assert max_latency < 0.6, (
        f"Maximum latency ({max_latency:.3f}s) exceeded threshold of 0.5s "
        "under sustained load"
    )
    
    logger.info(f"Sustained load test metrics:")
    logger.info(f"  Average latency: {avg_latency:.3f}s")
    logger.info(f"  Maximum latency: {max_latency:.3f}s")

@pytest.fixture
def trace_file():
    """Fixture to create and clean up a temporary trace file"""
    trace_file = "tests/temp_parallel_trace.json"
    # Initialize trace file
    os.makedirs("tests", exist_ok=True)
    with open(trace_file, 'w') as f:
        json.dump([], f)
    yield trace_file
    # Cleanup
    if os.path.exists(trace_file):
        os.unlink(trace_file)

@pytest.fixture
def setup_file_exporter(trace_file):
    """Fixture to set up file exporter configuration"""
    config_path = "tests/otel_config.yaml"
    
    # Create and write config file
    config = {
        "exporter": "file",
        "service_name": "ParallelLoadTest",
        "batch_processor": {
            "max_queue_size": 10000,  # Increased for parallel load
            "schedule_delay_millis": 100  # Decreased for faster processing
        },
        "file_exporter": {
            "path": trace_file
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Reset TracerFactory state
    TracerFactory._instance = None
    TracerFactory._config = None
    
    # Set config path in environment
    os.environ['FLOW4AI_OT_CONFIG'] = config_path
    
    yield
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)
    if 'FLOW4AI_OT_CONFIG' in os.environ:
        del os.environ['FLOW4AI_OT_CONFIG']
    TracerFactory._instance = None
    TracerFactory._config = None
    time.sleep(0.1)

def test_maximum_parallel_file_trace(trace_file, setup_file_exporter):
    """Test the impact of file tracing on parallel execution capacity
    
    This test verifies the system's ability to handle increasing loads of parallel tasks
    while simultaneously writing trace data to a file. It helps identify any potential
    bottlenecks in the AsyncFileExporter when under heavy parallel load.
    
    The test uses progressively larger task counts and measures both execution time
    and trace file integrity to ensure proper operation under load.
    
    To run this test:
    Use pytest's --full-suite option: pytest --full-suite
    """
    # Test with increasing number of tasks
    task_counts = [100, 500, 2500, 5000]  # Reduced counts for trace testing
    total_tasks = 0
    
    for count in task_counts:
        execution_time = asyncio.run(run_parallel_load_test(count))
        total_tasks += count
        
        # Scale expected time with task count, allowing extra time for tracing
        if count <= 100:
            expected_time = 3.0  # Additional second for tracing overhead
        elif count <= 500:
            expected_time = 6.0
        elif count <= 2500:
            expected_time = 15.0
        else:  # 5000 tasks
            expected_time = 25.0
            
        assert execution_time < expected_time, (
            f"Expected {count} tasks to complete in under {expected_time} seconds with parallel execution and tracing, "
            f"took {execution_time:.2f}s"
        )
        
        tasks_per_second = count / execution_time
        logger.info(f"Tasks per second with {count} tasks (with tracing): {tasks_per_second:.2f}")
        
        # Verify trace file integrity
        time.sleep(1.0)  # Allow time for traces to be written
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
            
            # Verify we have traces
            assert len(trace_data) > 0, "No traces were recorded"
            
            # Verify trace structure for a sample of traces
            sample_size = min(10, len(trace_data))
            for trace in trace_data[:sample_size]:
                assert 'name' in trace, "Trace missing name"
                assert 'context' in trace, "Trace missing context"
                assert 'trace_id' in trace['context'], "Trace missing trace_id"
                assert 'span_id' in trace['context'], "Trace missing span_id"
                assert 'attributes' in trace, "Trace missing attributes"
    
    # After all tests complete, verify total number of traces matches total tasks executed
    time.sleep(2.0)  # Additional time to ensure all traces are written
    with open(trace_file, 'r') as f:
        trace_data = json.load(f)
        trace_count = len(trace_data)
        # We expect at least one trace per task (there might be more due to additional instrumentation)
        assert trace_count >= total_tasks, (
            f"Expected at least {total_tasks} traces for all executed tasks, "
            f"but found only {trace_count} traces"
        )
        logger.info(f"Total traces recorded: {trace_count} for {total_tasks} tasks executed")
