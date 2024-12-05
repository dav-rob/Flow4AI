import unittest
import asyncio
import time
import queue
from job import JobABC
from job_chain import JobChain

def run_job_chain(job, tasks, use_direct_job=False, result_collector=None):
    """
    Helper function to run a job chain with a set of tasks and collect all results.

    Args:
        job: A JobABC instance, a collection of JobABC instances, or a job configuration dictionary
        tasks: List of tasks to process
        use_direct_job: If True, passes the job directly. If False, wraps it in a configuration dictionary
        result_collector: Optional function to process results

    Returns:
        List of results from processing all tasks
    """
    if use_direct_job:
        job_chain = JobChain(job, result_collector)
    else:
        job_chain = JobChain({"job_context": job}, result_collector)

    # Submit all tasks
    for task in tasks:
        job_chain.submit_task(task)

    # Mark that no more input is coming
    job_chain.mark_input_completed()

    # Collect all results
    results = []
    while True:
        try:
            result = job_chain._result_queue.get(timeout=0.1)
            if result is None:
                break
            results.append(result)
        except queue.Empty:
            if not job_chain.job_executor_process.is_alive():
                break
        except ValueError:  # Queue is closed
            if not job_chain.job_executor_process.is_alive():
                break

    return results

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
        await asyncio.sleep(self.delay)
        return {'input': task, 'output': f'processed by {self.name}'}

class TestJobGraph(unittest.TestCase):
    def test_job_name_always_present(self):
        # Test with explicit name
        job1 = MockJob(name="explicit_name")
        self.assertEqual(job1.name, "explicit_name")
        
        # Test with auto-generated name
        job2 = MockJob()
        self.assertIsNotNone(job2.name)
        self.assertIsInstance(job2.name, str)
        self.assertGreater(len(job2.name), 0)

        # Test subclass with explicit name
        job3 = MockJobSubclass(name="subclass_name")
        self.assertEqual(job3.name, "subclass_name")
        
        # Test subclass with auto-generated name
        job4 = MockJobSubclass()
        self.assertIsNotNone(job4.name)
        self.assertIsInstance(job4.name, str)
        self.assertGreater(len(job4.name), 0)

    def test_auto_generated_names_are_unique(self):
        # Create multiple jobs without explicit names
        num_jobs = 100  # Test with a significant number of jobs
        jobs = [MockJob() for _ in range(num_jobs)]
        
        # Collect all names in a set
        names = {job.name for job in jobs}
        
        # If all names are unique, the set should have the same length as the list
        self.assertEqual(len(names), num_jobs)
        
        # Test uniqueness across different subclass instances
        mixed_jobs = [
            MockJob() if i % 2 == 0 else MockJobSubclass()
            for i in range(num_jobs)
        ]
        mixed_names = {job.name for job in mixed_jobs}
        self.assertEqual(len(mixed_names), num_jobs)

    def test_parallel_execution_job_graph(self):
        """Test parallel execution with multiple jobs in a job graph."""
        # Test with both 1s and 2s delays
        for delay in [1.0, 2.0]:
            # Create 5 jobs with the same delay
            jobs = [DelayedMockJob(f'job_{i}', delay) for i in range(5)]
            
            # Create tasks for each job
            tasks = []
            for i in range(5):
                for j in range(4):  # 4 tasks per job = 20 total tasks
                    tasks.append({'task': f'task_{i}_{j}', 'job_name': f'job_{i}'})

            # Time the execution
            start_time = time.time()
            
            # Run the job chain with all jobs and collect results
            results = []
            def result_collector(result):
                results.append(result)
            job_chain = JobChain(jobs, result_collector, serial_processing=True)
            for task in tasks:
                job_chain.submit_task(task)
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

    @staticmethod
    def collect_result(results):
        """Create a picklable result collector function that appends to the given list."""
        def collector(result):
            results.append(result)
        return collector

if __name__ == '__main__':
    unittest.main()
