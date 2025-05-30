"""
    Test resilience under error conditions:

        - Tests basic error handling and propagation
        - Tests timeout scenarios
        - Tests process termination handling
        - Tests invalid input handling
        - Tests resource cleanup
        - Tests on_complete errors
        - Tests memory error handling
        - Tests unpicklable result scenarios
"""

import asyncio

import pytest

from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC


class ErrorTestJob(JobABC):
    """Job implementation for testing error conditions"""
    def __init__(self):
        super().__init__(name="ErrorTestJob")
    
    async def run(self, task):
        if task.get('raise_error'):
            raise Exception(task.get('error_message', 'Simulated error'))
        if task.get('timeout'):
            await asyncio.sleep(float(task['timeout']))
            return {'task': task, 'status': 'timeout_completed'}
        if task.get('memory_error'):
            # Explicitly raise MemoryError instead of trying to create a large list
            raise MemoryError("Simulated memory error")
        if task.get('invalid_result'):
            # Return an unpicklable object
            return lambda x: x  # Functions can't be pickled
        return {'task': task, 'status': 'completed'}


def test_basic_error_handling():
    """Test handling of basic exceptions during task execution"""
    results = []
    errors = []
    
    def collect_result(result):
        if isinstance(result, Exception):
            errors.append(result)
        else:
            results.append(result)
    
    flowmanagerMP = FlowManagerMP(ErrorTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit mix of successful and failing tasks
    tasks = [
        {'task_id': 1},
        {'task_id': 2, 'raise_error': True, 'error_message': 'Task 2 error'},
        {'task_id': 3},
        {'task_id': 4, 'raise_error': True, 'error_message': 'Task 4 error'}
    ]
    
    for task in tasks:
        flowmanagerMP.submit_task(task)
    
    flowmanagerMP.close_processes()
    
    # Verify successful tasks completed
    assert len(results) == 2
    assert all(r['status'] == 'completed' for r in results)
    
    # Verify errors were captured
    assert len(errors) == 0  # Errors should be logged, not passed to result processor

def test_timeout_handling():
    """Test handling of task timeouts"""
    results = []
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(ErrorTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name to use in task submissions
    head_jobs = flowmanagerMP.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    
    # Submit tasks with varying timeouts
    tasks = [
        {'task_id': 1, 'timeout': 0.3},
        {'task_id': 2, 'timeout': 0.2},
        {'task_id': 3, 'timeout': 0.1}
    ]
    
    for task in tasks:
        flowmanagerMP.submit_task(task)
    
    flowmanagerMP.close_processes()
    
    # Verify all tasks eventually completed
    assert len(results) == 3
    assert all(r['status'] == 'timeout_completed' for r in results)
    
    # Verify tasks completed in order of timeout
    task_ids = [r['task']['task_id'] for r in results]
    assert task_ids == [3, 2, 1]

def test_process_termination():
    """Test handling of process termination"""
    flowmanagerMP = FlowManagerMP(ErrorTestJob())
    
    # Submit a long-running task
    flowmanagerMP.submit_task({'task_id': 1, 'timeout': 1.0})
    
    # Force terminate the process
    flowmanagerMP.job_executor_process.terminate()
    
    # Verify cleanup handles terminated process
    flowmanagerMP._cleanup()
    assert not flowmanagerMP.job_executor_process.is_alive()

def test_invalid_input():
    """Test handling of invalid input data"""
    flowmanagerMP = FlowManagerMP(ErrorTestJob())
    
    # Test various invalid inputs
    invalid_inputs = [
        None,
        "",
        {},
        {'task_id': None},
        {'task_id': object()},  # Unpicklable object
        []
    ]
    
    for invalid_input in invalid_inputs:
        flowmanagerMP.submit_task(invalid_input)
    
    flowmanagerMP.close_processes()
    # Should complete without raising exceptions

def test_resource_cleanup():
    """Test proper cleanup of resources"""
    flowmanagerMP = FlowManagerMP(ErrorTestJob())
    
    # Submit some tasks
    for i in range(5):
        flowmanagerMP.submit_task({'task_id': i})
    
    # Get queue references
    task_queue = flowmanagerMP._task_queue
    result_queue = flowmanagerMP._result_queue
    
    # Cleanup
    flowmanagerMP._cleanup()
    
    # Verify queues are closed
    assert task_queue._closed
    assert result_queue._closed
    
    # Verify processes are terminated
    assert not flowmanagerMP.job_executor_process.is_alive()
    if flowmanagerMP.result_processor_process:
        assert not flowmanagerMP.result_processor_process.is_alive()

def test_error_in_on_complete_callable():
    """Test handling of errors in on_complete function"""
    def failing_processor(result):
        raise Exception("Result processing error")
    
    flowmanagerMP = FlowManagerMP(ErrorTestJob(), failing_processor, serial_processing=True)
    
    # Submit tasks
    for i in range(3):
        flowmanagerMP.submit_task({'task_id': i})
    
    flowmanagerMP.close_processes()
    # Should complete without hanging or crashing

def test_memory_error_handling():
    """Test handling of memory errors"""
    results = []
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(ErrorTestJob(), collect_result, serial_processing=True)
    
    # Submit task that will cause memory error
    flowmanagerMP.submit_task({'task_id': 1, 'memory_error': True})
    
    flowmanagerMP.close_processes()
    
    # Process should handle the memory error gracefully
    assert len(results) == 0  # No results should be processed

def test_unpicklable_result():
    """Test handling of unpicklable results"""
    results = []
    def collect_result(result):
        results.append(result)
    
    flowmanagerMP = FlowManagerMP(ErrorTestJob(), collect_result, serial_processing=True)
    
    # Submit task that returns unpicklable result
    flowmanagerMP.submit_task({'task_id': 1, 'invalid_result': True})
    
    flowmanagerMP.close_processes()
    
    # Process should handle the pickling error gracefully
    assert len(results) == 0  # No results should be processed

if __name__ == '__main__':
    pytest.main(['-v', 'test_error_conditions.py'])
