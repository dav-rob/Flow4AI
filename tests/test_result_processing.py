"""
    Tests parallel and serial functionality with picklable and non-picklable result
        processing functions.
"""

import asyncio
import os
import time
from time import sleep

from job import JobABC
from job_chain import JobChain


class ResultTimingJob(JobABC):
    def __init__(self):
        super().__init__("Result Timing Job")
        self.executed_tasks = set()

    async def run(self, task) -> dict:
        # Record task execution
        self.executed_tasks.add(task)
        # Simulate some work
        await asyncio.sleep(0.1)
        current_time = time.time()
        print(f"Executing task {task} at {current_time}")
        return {"task": task, "timestamp": current_time}

class UnpicklableState:
    def __init__(self):
        # Create an unpicklable attribute (file handle)
        self.log_file = open('temp.log', 'w')
    
    def __del__(self):
        try:
            self.log_file.close()
            if os.path.exists('temp.log'):
                os.remove('temp.log')
        except:
            pass

def parallel_mode():
    # Clean up any existing log file
    if os.path.exists('temp.log'):
        os.remove('temp.log')

    print("\nTesting parallel mode (should fail):")
    try:
        # Create unpicklable state
        unpicklable = UnpicklableState()
        
        def unpicklable_processor(result):
            """A result processor that uses unpicklable state"""
            unpicklable.log_file.write(f"Processing: {result}\n")
            unpicklable.log_file.flush()
            print(f"Logged result: {result}")

        # Create job chain in parallel mode
        job = ResultTimingJob()
        job_chain = JobChain(job, unpicklable_processor, serial_processing=False)

        # Submit some tasks
        for i in range(3):
            job_chain.submit_task(f"Task {i}")
            sleep(0.1)
        
        job_chain.mark_input_completed()
        assert False, "Expected parallel mode to fail with unpicklable processor"
    except Exception as e:
        print(f"Parallel mode failed as expected: {e}")
        assert "pickle" in str(e).lower(), "Expected pickling error"

def serial_mode():
    print("\nTesting serial mode (should work):")
    try:
        # Clean up any existing log file
        if os.path.exists('temp.log'):
            os.remove('temp.log')
            
        # Create new unpicklable state
        unpicklable = UnpicklableState()
        
        def unpicklable_processor(result):
            """A result processor that uses unpicklable state"""
            unpicklable.log_file.write(f"Processing: {result}\n")
            unpicklable.log_file.flush()
            print(f"Logged result: {result}")

        # Create job chain in serial mode
        job = ResultTimingJob()
        job_chain = JobChain(job, unpicklable_processor, serial_processing=True)

        # Submit some tasks
        expected_tasks = {f"Task {i}" for i in range(3)}
        for task in expected_tasks:
            job_chain.submit_task(task)
            sleep(0.1)
        
        # Process tasks and wait for completion
        job_chain.mark_input_completed()  # Not awaited since it's synchronous
        
        # Give a small delay to ensure all results are processed
        sleep(0.5)
        
        # Verify results were written to file
        with open('temp.log', 'r') as f:
            content = f.read()
        
        # Verify all tasks were processed by checking log content
        for task in expected_tasks:
            assert f"'task': '{task}'" in content, f"Expected task {task} to be processed"
        
        print("All tasks were successfully processed and logged")

    except Exception as e:
        assert False, f"Serial mode should not fail: {e}"


def test_parallel_result_processor_fails_with_unpicklable():
    parallel_mode()
    
def test_serial_result_processor_succeeds_with_unpicklable():
    serial_mode()
