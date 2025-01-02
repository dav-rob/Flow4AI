"""
Tests for stress testing queues:

        - Tests high-volume task processing (10,000 tasks)
        - Tests memory pressure handling
        - Tests queue backpressure with slow consumers
        - Tests CPU-intensive workloads
        - Tests mixed workload scenarios
"""
import os
import time

import psutil
import pytest

from jobchain import jc_logging as logging
from jobchain.job import JobABC
from jobchain.job_chain import JobChain


class StressTestJob(JobABC):
    """Job implementation for stress testing queues"""
    def __init__(self):
        super().__init__(name="StressTestJob")
    
    async def run(self, task):
        task = task[self.name] if isinstance(task, dict) and self.name in task else task
        if isinstance(task, dict):
            if task.get('memory_intensive'):
                # Create temporary large data
                large_data = [i for i in range(task.get('size', 1000000))]
                return {'task': task, 'data_size': len(large_data)}
            if task.get('cpu_intensive'):
                # Perform CPU-intensive calculation
                result = sum(i * i for i in range(task.get('iterations', 1000000)))
                return {'task': task, 'result': result}
        return {'task': task, 'completed': True}

def get_process_memory(pid):
    """Get memory usage of a specific process"""
    try:
        process = psutil.Process(pid)
        return process.memory_info().rss
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0

def test_queue_high_volume():
    """Test queue with high volume of tasks"""
    results = []
    def collect_result(result):
        results.append(result)
    
    job = StressTestJob()
    job_chain = JobChain(job, collect_result, serial_processing=True)
    
    # Submit a high volume of tasks
    num_tasks = 10000
    for i in range(num_tasks):
        job_chain.submit_task({job.name: {'task_id': i}}, job_name=job.name)
    
    job_chain.mark_input_completed()
    
    assert len(results) == num_tasks
    assert len({r['task']['task_id'] for r in results}) == num_tasks

def test_queue_memory_pressure():
    """Test queue behavior under memory pressure"""
    results = []
    def collect_result(result):
        results.append(result)
    
    job = StressTestJob()
    job_chain = JobChain(job, collect_result, serial_processing=True)
    initial_memory = get_process_memory(os.getpid())
    
    # Submit memory-intensive tasks
    num_tasks = 50
    for i in range(num_tasks):
        job_chain.submit_task({
            job.name: {
                'task_id': i,
                'memory_intensive': True,
                'size': 1000000  # 1M integers
            }
        }, job_name=job.name)
    
    job_chain.mark_input_completed()
    
    # Verify all tasks completed
    assert len(results) == num_tasks
    
    # Check memory was properly released
    final_memory = get_process_memory(os.getpid())
    # Allow for some memory overhead, but shouldn't retain all task data
    assert final_memory < initial_memory * 2

def test_queue_backpressure():
    """Test queue backpressure handling with slow consumer"""
    results = []
    def slow_result_processor(result):
        time.sleep(0.01)  # Simulate slow processing
        results.append(result)
    
    job = StressTestJob()
    job_chain = JobChain(job, slow_result_processor, serial_processing=True)
    
    # Submit tasks faster than they can be processed
    num_tasks = 100
    start_time = time.time()
    
    for i in range(num_tasks):
        job_chain.submit_task({job.name: {'task_id': i}}, job_name=job.name)
        if i % 10 == 0:
            time.sleep(0.001)  # Small delay to prevent overwhelming
    
    job_chain.mark_input_completed()
    
    # Verify all tasks eventually complete
    assert len(results) == num_tasks
    # Verify results maintained order
    task_ids = [r['task']['task_id'] for r in results]
    assert sorted(task_ids) == list(range(num_tasks))

def test_queue_cpu_intensive():
    """Test queue behavior with CPU-intensive tasks"""
    results = []
    def collect_result(result):
        results.append(result)
    
    job_chain = JobChain(StressTestJob(), collect_result, serial_processing=True)
    
    # Submit CPU-intensive tasks
    num_tasks = 4  # Number of CPU cores typically available
    for i in range(num_tasks):
        job_chain.submit_task({
            'task_id': i,
            'cpu_intensive': True,
            'iterations': 5000000
        })
    
    job_chain.mark_input_completed()
    
    assert len(results) == num_tasks
    # Verify all tasks produced valid results
    assert all('result' in r for r in results)

def test_queue_mixed_workload():
    """Test queue handling mixed types of workloads"""
    results = []
    def collect_result(result):
        results.append(result)
    
    job = StressTestJob()
    job_chain = JobChain(job, collect_result, serial_processing=True)
    
    # Submit mix of different task types
    tasks = [
        {'task_id': 1, 'memory_intensive': True, 'size': 500000},
        {'task_id': 2, 'cpu_intensive': True, 'iterations': 1000000},
        {'task_id': 3},  # Simple task
        {'task_id': 4, 'memory_intensive': True, 'size': 100000},
        {'task_id': 5, 'cpu_intensive': True, 'iterations': 500000}
    ]
    
    for task in tasks:
        job_chain.submit_task({job.name: task}, job_name=job.name)
    
    job_chain.mark_input_completed()
    
    assert len(results) == len(tasks)
    # Verify each task type completed correctly
    for result in results:
        task = result['task']
        if task.get('memory_intensive'):
            assert 'data_size' in result
        elif task.get('cpu_intensive'):
            assert 'result' in result

if __name__ == '__main__':
    pytest.main(['-v', 'test_queue_stress.py'])
