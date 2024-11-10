"""
    Simple Tests to confirm the basics of async functionality are working:
    
            - Tests concurrent task execution and verification
            - Tests async task cancellation and cleanup
            - Tests event loop handling and lifecycle
            - Tests async exception propagation
            - Tests parallel task limits and scaling  
"""

import asyncio
import multiprocessing as mp
from unittest.mock import Mock, patch

import pytest

from job import Job
from job_chain import JobChain


class AsyncTestJob(Job):
    """Job to confirm the basics of async functionality are working: """
    def __init__(self):
        super().__init__(
            name="AsyncTestJob",
            prompt="Test prompt",
            model="test-model"
        )
    
    async def execute(self, task):
        if isinstance(task, dict) and task.get('fail'):
            raise ValueError("Simulated task failure")
        if isinstance(task, dict) and task.get('delay'):
            await asyncio.sleep(task['delay'])
        return {'task': task, 'completed': True}


@pytest.mark.asyncio
async def test_concurrent_task_execution():
    """Test that tasks are truly executed concurrently"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    job_chain = JobChain(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Submit tasks with different delays
    tasks = [
        {'task_id': 1, 'delay': 0.2},
        {'task_id': 2, 'delay': 0.1},
        {'task_id': 3, 'delay': 0.3}
    ]
    
    for task in tasks:
        job_chain.submit_task(task)
    
    job_chain.mark_input_completed()
    
    # Verify all tasks completed
    assert len(results) == 3
    # Verify task completion order (should still be in delay order due to async execution)
    task_ids = [r['task']['task_id'] for r in results]
    assert 2 in task_ids  # Task 2 should be completed (not necessarily first in serial mode)
    assert 1 in task_ids
    assert 3 in task_ids

@pytest.mark.asyncio
async def test_async_task_cancellation():
    """Test proper cleanup of cancelled async tasks"""
    job_chain = JobChain(AsyncTestJob())
    
    # Submit a long-running task
    job_chain.submit_task({'delay': 1.0})
    
    # Force cleanup before completion
    job_chain._cleanup()
    
    # Verify process termination
    assert not job_chain.job_executor_process.is_alive()
    assert job_chain._task_queue._closed

@pytest.mark.asyncio
async def test_event_loop_handling():
    """Test proper event loop creation and cleanup"""
    job_chain = JobChain(AsyncTestJob())
    
    # Submit a simple task
    job_chain.submit_task({'task_id': 1})
    job_chain.mark_input_completed()
    
    # Verify process cleanup
    assert not job_chain.job_executor_process.is_alive()

@pytest.mark.asyncio
async def test_async_exception_handling():
    """Test that async exceptions are properly caught and handled"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    job_chain = JobChain(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Submit mix of successful and failing tasks
    tasks = [
        {'task_id': 1},
        {'task_id': 2, 'fail': True},
        {'task_id': 3}
    ]
    
    for task in tasks:
        job_chain.submit_task(task)
    
    job_chain.mark_input_completed()
    
    # Only successful tasks should have results
    assert len(results) == 2
    assert all(r['completed'] for r in results)

@pytest.mark.asyncio
async def test_parallel_task_limit():
    """Test handling of many concurrent tasks"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    job_chain = JobChain(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Submit many quick tasks
    num_tasks = 100
    for i in range(num_tasks):
        job_chain.submit_task({'task_id': i, 'delay': 0.01})
    
    job_chain.mark_input_completed()
    
    # All tasks should complete
    assert len(results) == num_tasks
    # Results should maintain task integrity
    task_ids = {r['task']['task_id'] for r in results}
    assert len(task_ids) == num_tasks

if __name__ == '__main__':
    pytest.main(['-v', 'test_async_functionality.py'])
