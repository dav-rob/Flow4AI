"""
Tests for FlowManagerMP singleton implementation.

This module contains tests that verify the singleton pattern implementation for FlowManagerMP,
adapting tests from the previous factory pattern implementation.
"""

import asyncio
import os
import threading
import time
from typing import List

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC
from flow4ai.job_loader import ConfigLoader

# Global results list for picklable on_complete
RESULTS: List[dict] = []


def picklable_result_processor(result):
    """A picklable result processor function"""
    RESULTS.append(result)
    logging.info(f"Processing result: {result}")


class AsyncTestJob(JobABC):
    """Job to test async functionality with FlowManagerMP singleton"""
    def __init__(self):
        super().__init__(name="AsyncTestJob")
    
    async def run(self, task):
        if isinstance(task, dict) and task.get('delay'):
            await asyncio.sleep(task['delay'])
        return {'task': task, 'completed': True}


class BasicTestJob(JobABC):
    """Simple job for testing basic functionality"""
    def __init__(self, name="BasicTestJob"):
        super().__init__(name=name)
    
    async def run(self, task):
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
def reset_singleton():
    """Reset FlowManagerMP singleton between tests"""
    FlowManagerMP.reset_instance()
    RESULTS.clear()  # Clear global results
    # Clean up temp file if exists
    if os.path.exists('temp.log'):
        os.remove('temp.log')
    yield
    # Clean up after test
    FlowManagerMP.reset_instance()  # Ensure cleanup
    if os.path.exists('temp.log'):
        os.remove('temp.log')


def test_empty_initialization():
    """Test that FlowManagerMP singleton is initialized correctly"""
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config")])
    
    # Create FlowManagerMP instance
    fm = FlowManagerMP.instance()
    
    # Get head jobs from config to know their names
    head_jobs = sorted(fm.get_fq_names())
    
    # Verify head jobs are loaded - these are the entry point jobs from all graphs and parameter sets
    expected_jobs = sorted([
        'four_stage_parameterized$$params1$$read_file$$',
        'four_stage_parameterized$$params2$$read_file$$',
        'three_stage$$params1$$ask_llm_mini$$',
        'three_stage_reasoning$$$$ask_llm_reasoning$$'
    ])
    
    assert head_jobs == expected_jobs, "FlowManagerMP config not loaded correctly"

    fm.close_processes()


@pytest.mark.asyncio
async def test_concurrent_task_execution():
    """Test that tasks are truly executed concurrently using FlowManagerMP singleton"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    # Initialize with a new FlowManagerMP
    fm = FlowManagerMP.instance(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = fm.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit tasks with different delays
    tasks = [
        {'task_id': 1, 'delay': 0.2},
        {'task_id': 2, 'delay': 0.1},
        {'task_id': 3, 'delay': 0.3}
    ]
    
    for task in tasks:
        fm.submit_task(task)
    
    fm.close_processes()
    
    # Verify all tasks completed
    assert len(results) == 3
    
    # Verify task completion
    task_ids = [r['task']['task_id'] for r in results]
    assert 2 in task_ids  # Task 2 should be completed
    assert 1 in task_ids
    assert 3 in task_ids


@pytest.mark.asyncio
async def test_job_instantiation_and_execution():
    """Test basic job creation and execution using FlowManagerMP singleton"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    # Create a FlowManagerMP through the singleton
    fm = FlowManagerMP.instance(BasicTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = fm.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit a simple task
    fm.submit_task({})
    fm.close_processes()
    
    # Verify job execution
    assert len(results) == 1
    assert results[0][job_name] == "completed"


def test_singleton_pattern():
    """Test that the singleton pattern works correctly"""
    # Create initial instance
    fm1 = FlowManagerMP.instance(BasicTestJob())
    
    # Get another reference to the singleton
    fm2 = FlowManagerMP.instance()
    
    # Verify they are the same instance
    assert fm1 is fm2, "Failed to maintain singleton instance"
    
    # Reset the singleton
    FlowManagerMP.reset_instance()
    
    # Create a new instance
    fm3 = FlowManagerMP.instance(BasicTestJob())
    
    # Verify it's a different instance
    assert fm1 is not fm3, "Failed to create new instance after reset"
    
    # Clean up
    fm3.close_processes()


def test_thread_safety():
    """Test that the singleton pattern is thread-safe"""
    # Set up a barrier to synchronize threads
    barrier = threading.Barrier(3)
    
    # List to store instances
    instances = []
    
    def get_instance():
        # Wait for all threads to be ready
        barrier.wait()
        # Get the instance
        instance = FlowManagerMP.instance(BasicTestJob())
        instances.append(instance)
    
    # Create threads to get the instance concurrently
    threads = [threading.Thread(target=get_instance) for _ in range(3)]
    
    # Start the threads
    for thread in threads:
        thread.start()
    
    # Wait for the threads to finish
    for thread in threads:
        thread.join()
    
    # Verify all threads got the same instance
    assert len(instances) == 3
    assert all(instance is instances[0] for instance in instances), "Singleton is not thread-safe"
    
    # Clean up
    instances[0].wait_for_completion()


def test_reset_instance_cleanup():
    """Test that reset_instance properly cleans up resources"""
    # Create an instance
    fm = FlowManagerMP.instance(BasicTestJob())
    
    # Submit a task
    fm.submit_task({})
    
    # Reset the instance (which should clean up resources)
    FlowManagerMP.reset_instance()
    
    # Create a new instance
    new_fm = FlowManagerMP.instance(BasicTestJob())
    
    # Verify the new instance is ready to use
    new_fm.submit_task({})
    new_fm.close_processes()


def test_multiprocessing_initialization():
    """
    Test that multiprocessing is properly initialized.
    This test verifies that spawn method works correctly for task execution.
    """
    # Use a job that would rely on the spawn method working correctly
    results = []
    
    def collect_result(result):
        results.append(result)
    
    # Create an instance with a job that requires correct multiprocessing initialization
    fm = FlowManagerMP.instance(DelayedJob(0.1), collect_result, serial_processing=True)
    
    # Submit a task
    fm.submit_task({"test": "multiprocessing"})
    
    # Wait for completion
    fm.close_processes()
    
    # Verify the task was processed
    assert len(results) == 1
    assert results[0]["status"] == "complete"
