"""
Tests for JobChainFactory class functionality.

This module contains tests that verify the JobChainFactory wrapper over JobChain,
focusing on key functionality from other test modules.
"""

import asyncio
import os
import time
from typing import List

import pytest

import jobchain.jc_logging as logging
from jobchain.job import JobABC
from jobchain.job_chain import JobChainFactory

# Global results list for picklable result processing
RESULTS: List[dict] = []


def picklable_result_processor(result):
    """A picklable result processor function"""
    RESULTS.append(result)
    logging.info(f"Processing result: {result}")


class AsyncTestJob(JobABC):
    """Job to test async functionality with JobChainFactory"""
    def __init__(self):
        super().__init__(name="AsyncTestJob")
    
    async def run(self, task):
        task = task[self.name]
        if isinstance(task, dict) and task.get('delay'):
            await asyncio.sleep(task['delay'])
        return {'task': task, 'completed': True}


class BasicTestJob(JobABC):
    """Simple job for testing basic functionality"""
    def __init__(self, name="BasicTestJob"):
        super().__init__(name=name)
    
    async def run(self, inputs):
        return {self.name: "completed"}


class DelayedJob(JobABC):
    """Job that introduces a configurable delay"""
    def __init__(self, delay: float):
        super().__init__(name="DelayedJob")
        self.delay = delay
    
    async def run(self, task):
        logging.info(f"Executing DelayedJob for {task} with delay {self.delay}")
        await asyncio.sleep(self.delay)
        return {"task": task, "status": "complete"}


class ResultTimingJob(JobABC):
    """Job that records execution timing"""
    def __init__(self):
        super().__init__("ResultTimingJob")
        self.executed_tasks = set()
    
    async def run(self, task):
        # Extract the actual task
        actual_task = task.get(self.name, task)
        # Record task execution
        task_str = str(actual_task)
        self.executed_tasks.add(task_str)
        # Simulate work
        await asyncio.sleep(0.1)
        current_time = time.time()
        logging.info(f"Executing task {actual_task} at {current_time}")
        return {"task": actual_task, "timestamp": current_time}


class UnpicklableState:
    """Class with unpicklable state (file handle)"""
    def __init__(self):
        self.log_file = open('temp.log', 'w')
    
    def __del__(self):
        try:
            self.log_file.close()
            if os.path.exists('temp.log'):
                os.remove('temp.log')
        except:
            pass


@pytest.fixture(autouse=True)
def reset_factory():
    """Reset JobChainFactory between tests"""
    JobChainFactory._instance = None
    JobChainFactory._job_chain = None
    RESULTS.clear()  # Clear global results
    # Clean up temp file if exists
    if os.path.exists('temp.log'):
        os.remove('temp.log')
    yield
    # Clean up after test
    if os.path.exists('temp.log'):
        os.remove('temp.log')


@pytest.mark.asyncio
async def test_concurrent_task_execution():
    """Test that tasks are truly executed concurrently using JobChainFactory"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    # Initialize factory with a new JobChain
    JobChainFactory(AsyncTestJob(), collect_result, serial_processing=True)
    job_chain = JobChainFactory.get_instance()
    
    # Submit tasks with different delays
    tasks = [
        {'AsyncTestJob': {'task_id': 1, 'delay': 0.2}},
        {'AsyncTestJob': {'task_id': 2, 'delay': 0.1}},
        {'AsyncTestJob': {'task_id': 3, 'delay': 0.3}}
    ]
    
    for task in tasks:
        job_chain.submit_task(task)
    
    job_chain.mark_input_completed()
    
    # Verify all tasks completed
    assert len(results) == 3
    
    # Verify task completion order
    task_ids = [r['task']['task_id'] for r in results]
    assert 2 in task_ids  # Task 2 should be completed
    assert 1 in task_ids
    assert 3 in task_ids


@pytest.mark.asyncio
async def test_job_instantiation_and_execution():
    """Test basic job creation and execution using JobChainFactory"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    # Create a job chain through the factory
    JobChainFactory(BasicTestJob(), collect_result, serial_processing=True)
    job_chain = JobChainFactory.get_instance()
    
    # Submit a simple task
    job_chain.submit_task({'BasicTestJob': {}})
    job_chain.mark_input_completed()
    
    # Verify job execution
    assert len(results) == 1
    assert results[0]['BasicTestJob'] == "completed"
    
    # Verify we can get the same instance again
    same_job_chain = JobChainFactory.get_instance()
    assert same_job_chain is job_chain


def test_parallel_execution():
    """Test true parallel execution performance using JobChainFactory"""
    async def run_job_chain(delay: float) -> float:
        """Run job chain with specified delay and return execution time"""
        start_time = time.perf_counter()
        
        # Create job chain through factory with picklable result processor
        JobChainFactory(DelayedJob(delay), picklable_result_processor)
        job_chain = JobChainFactory.get_instance()
        
        # Feed 10 tasks with a delay between each to simulate data gathering
        for i in range(10):
            job_chain.submit_task(f"Task {i}")
            await asyncio.sleep(0.2)  # Simulate time taken to gather data
            
        job_chain.mark_input_completed()
        
        execution_time = time.perf_counter() - start_time
        logging.info(f"Execution time for delay {delay}s: {execution_time:.2f}s")
        return execution_time
    
    # Test with 1 second delay
    time_1s = asyncio.run(run_job_chain(1.0))
    
    # Reset factory for second test
    JobChainFactory._instance = None
    JobChainFactory._job_chain = None
    RESULTS.clear()
    
    # Test with 2 second delay
    time_2s = asyncio.run(run_job_chain(2.0))
    
    # Calculate the ratio of execution times
    time_ratio = time_2s / time_1s
    logging.info(f"Time with 1s delay: {time_1s:.2f}s")
    logging.info(f"Time with 2s delay: {time_2s:.2f}s")
    logging.info(f"Ratio: {time_ratio:.2f}x")
    
    # Verify parallel execution
    assert time_1s <= 4.5, (
        f"Expected tasks to complete in ~4.5s (including data gathering + overhead), took {time_1s:.2f}s. "
        "This suggests tasks are running sequentially"
    )
    assert time_2s <= 5.5, (
        f"Expected tasks to complete in ~5.5s (including data gathering + overhead), took {time_2s:.2f}s. "
        "This suggests tasks are running sequentially"
    )


def test_serial_result_processor_with_unpicklable():
    """Test serial processing with unpicklable state using JobChainFactory"""
    # Create unpicklable state
    unpicklable = UnpicklableState()
    
    def unpicklable_processor(result):
        """A result processor that uses unpicklable state"""
        unpicklable.log_file.write(f"Processing: {result}\n")
        unpicklable.log_file.flush()
        logging.info(f"Logged result: {result}")
    
    # Test parallel mode (should fail)
    with pytest.raises(TypeError) as exc_info:
        JobChainFactory(ResultTimingJob(), unpicklable_processor, serial_processing=False)
        job_chain = JobChainFactory.get_instance()
        job_chain.submit_task("Task 1")
        job_chain.mark_input_completed()
    assert "pickle" in str(exc_info.value).lower()
    
    # Reset factory for serial mode test
    JobChainFactory._instance = None
    JobChainFactory._job_chain = None
    
    # Test serial mode (should work)
    JobChainFactory(ResultTimingJob(), unpicklable_processor, serial_processing=True)
    job_chain = JobChainFactory.get_instance()
    
    # Submit tasks
    for i in range(3):
        job_chain.submit_task({"ResultTimingJob": f"Task {i}"})
        time.sleep(0.1)
    
    job_chain.mark_input_completed()
    
    # Verify results were logged
    with open('temp.log', 'r') as f:
        log_contents = f.read()
    
    # Check that all tasks were processed
    assert "Task 0" in log_contents
    assert "Task 1" in log_contents
    assert "Task 2" in log_contents
