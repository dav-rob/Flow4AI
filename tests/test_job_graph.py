import asyncio
import time

import pytest

from job import JobABC
from job_chain import JobChain


class MockJob(JobABC):
    def run(self):
        pass

class MockJobSubclass(MockJob):
    pass

class DelayedMockJob(MockJob):
    """A mock job that introduces a configurable delay in processing."""
    def __init__(self, name: str, delay: float):
        super().__init__(name=name)
        self.delay = delay

    async def run(self, task):
        task = task[self.name]  # Get the task from inputs dict
        await asyncio.sleep(self.delay)
        return {'input': task, 'output': f'processed by {self.name}'}

def test_job_name_always_present():
    # Test with explicit name
    job1 = MockJob(name="explicit_name")
    assert job1.name == "explicit_name"
    
    # Test with auto-generated name
    job2 = MockJob()
    assert job2.name is not None
    assert isinstance(job2.name, str)
    assert len(job2.name) > 0

    # Test subclass with explicit name
    job3 = MockJobSubclass(name="subclass_name")
    assert job3.name == "subclass_name"
    
    # Test subclass with auto-generated name
    job4 = MockJobSubclass()
    assert job4.name is not None
    assert isinstance(job4.name, str)
    assert len(job4.name) > 0

def test_auto_generated_names_are_unique():
    # Create multiple jobs without explicit names
    num_jobs = 100  # Test with a significant number of jobs
    jobs = [MockJob() for _ in range(num_jobs)]
    
    # Collect all names in a set
    names = {job.name for job in jobs}
    
    # If all names are unique, the set should have the same length as the list
    assert len(names) == num_jobs
    
    # Test uniqueness across different subclass instances
    mixed_jobs = [
        MockJob() if i % 2 == 0 else MockJobSubclass()
        for i in range(num_jobs)
    ]
    mixed_names = {job.name for job in mixed_jobs}
    assert len(mixed_names) == num_jobs

def test_parallel_execution_multiple_jobs():
    """Test parallel execution with multiple jobs in a job graph."""
    # Test with both 1s and 2s delays
    for delay in [1.0, 2.0]:
        # Create 5 jobs with the same delay
        jobs = [DelayedMockJob(f'job_{i}', delay) for i in range(5)]
        
        # Create tasks for each job
        tasks = []
        for i in range(5):
            for j in range(4):  # 4 tasks per job = 20 total tasks
                tasks.append({f'job_{i}': {'task': f'task_{i}_{j}', 'job_name': f'job_{i}'}})

        # Time the execution
        start_time = time.time()
        
        # Run the job chain with all jobs and collect results
        results = []
        def result_collector(result):
            results.append(result)
        job_chain = JobChain(jobs, result_collector, serial_processing=True)
        for task in tasks:
            job_name = next(iter(task.keys()))  # Get the job name from the task dict
            job_chain.submit_task(task, job_name=job_name)
        job_chain.mark_input_completed()
        
        end_time = time.time()
        execution_time = end_time - start_time

        # Verify results
        assert len(results) == 20  # Should have 20 results
        
        # Check that each task was processed by the correct job
        for result in results:
            input_task = result['input']
            job_name = input_task['job_name']
            assert result['output'] == f'processed by {job_name}'
        
        # Verify parallel execution - should take ~4 * delay seconds (4 batches of tasks)
        # Add some buffer time for overhead
        assert execution_time < (4 * delay + 1), f"Execution took {execution_time} seconds, expected less than {4 * delay + 1} seconds"

def collect_result(results):
    """Create a picklable result collector function that appends to the given list."""
    def collector(result):
        results.append(result)
    return collector
