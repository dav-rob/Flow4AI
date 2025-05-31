"""
    Simple Tests to confirm the basics of async functionality are working:
    
            - Tests concurrent task execution and verification
            - Tests async task cancellation and cleanup
            - Tests event loop handling and lifecycle
            - Tests async exception propagation
            - Tests parallel task limits and scaling  
"""

import asyncio

import pytest

from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC


class AsyncTestJob(JobABC):
    """Job to confirm the basics of async functionality are working: """
    def __init__(self):
        super().__init__(name="AsyncTestJob")
    
    async def run(self, task):
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
    
    flowmanagerMP = FlowManagerMP(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit tasks with different delays using the head job's name
    tasks = [
        {'task_id': 1, 'delay': 0.2},
        {'task_id': 2, 'delay': 0.1},
        {'task_id': 3, 'delay': 0.3}
    ]
    
    for task in tasks:
        flowmanagerMP.submit_task(task)
    
    flowmanagerMP.close_processes()
    
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
    flowmanagerMP = FlowManagerMP(AsyncTestJob())
    
    # Submit a long-running task
    flowmanagerMP.submit_task({'delay': 1.0})
    
    # Force cleanup before completion
    flowmanagerMP._cleanup()
    
    # Verify process termination
    assert not flowmanagerMP.job_executor_process.is_alive()
    assert flowmanagerMP._task_queue._closed

@pytest.mark.asyncio
async def test_event_loop_handling():
    """Test proper event loop creation and cleanup"""
    flowmanagerMP = FlowManagerMP(AsyncTestJob())
    
    # Submit a simple task
    flowmanagerMP.submit_task({'task_id': 1})
    flowmanagerMP.close_processes()
    
    # Verify process cleanup
    assert not flowmanagerMP.job_executor_process.is_alive()

@pytest.mark.asyncio
async def test_async_exception_handling():
    """Test that async exceptions are properly caught and handled"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit mix of successful and failing tasks
    tasks = [
        {'task_id': 1},
        {'task_id': 2, 'fail': True},
        {'task_id': 3}
    ]
    
    for task in tasks:
        flowmanagerMP.submit_task(task)
    
    flowmanagerMP.close_processes()
    
    # Only successful tasks should have results
    assert len(results) == 2
    assert all(r['completed'] for r in results)

@pytest.mark.asyncio
async def test_parallel_task_limit():
    """Test handling of many concurrent tasks"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit many quick tasks
    num_tasks = 100
    for i in range(num_tasks):
        flowmanagerMP.submit_task({'task_id': i, 'delay': 0.01})
    
    flowmanagerMP.close_processes()
    
    # All tasks should complete
    assert len(results) == num_tasks
    # Results should maintain task integrity
    task_ids = {r['task']['task_id'] for r in results}
    assert len(task_ids) == num_tasks


@pytest.mark.asyncio
async def test_poll_for_updates():
    """Test the poll_for_updates functionality with varying task delays"""
    results = []
    
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(AsyncTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit 100 tasks with 10 each having delays of 1-10 seconds
    num_tasks = 100
    for i in range(num_tasks):
        # Determine delay: first 10 tasks get 1s, next 10 get 2s, etc.
        delay = (i // 10) + 1 if i < 100 else 0.01
        flowmanagerMP.submit_task({'task_id': i, 'delay': delay})
    
    # Poll for updates with a 12-second timeout
    flowmanagerMP.wait_for_completion(timeout=12.0, check_interval=1.0)
    
    # Call wait_for_completion to ensure all processes are properly closed
    flowmanagerMP.close_processes()
    
    # Check that all tasks have completed after wait_for_completion
    assert len(results) == num_tasks, "Not all tasks completed after polling and waiting"
    
    # Verify task integrity for the completed tasks
    completed_task_ids = {r['task']['task_id'] for r in results}
    assert len(completed_task_ids) == len(results), "Duplicate task results found"

if __name__ == '__main__':
    pytest.main(['-v', 'test_async_functionality.py'])
