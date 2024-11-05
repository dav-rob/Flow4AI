import asyncio
import multiprocessing as mp
import os
import time
from time import sleep

from job import Job
from job_chain import JobChain


class ResultTimingJob(Job):
    def __init__(self):
        super().__init__("Result Timing Job", "Test prompt", "test-model")
        self.executed_tasks = set()

    async def execute(self, task) -> dict:
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

async def parallel_mode():
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
            await asyncio.sleep(0.1)
        
        job_chain.mark_input_completed()
        assert False, "Expected parallel mode to fail with unpicklable processor"
    except Exception as e:
        print(f"Parallel mode failed as expected: {e}")
        assert "pickle" in str(e).lower(), "Expected pickling error"
    finally:
        if 'unpicklable' in locals():
            unpicklable.__del__()

    

async def serial_mode():
    print("\nTesting serial mode (should work):")
    try:
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
            await asyncio.sleep(0.1)
        
        # Process tasks and wait for completion
        await job_chain.mark_input_completed()
        
        # Verify results were written to file
        with open('temp.log', 'r') as f:
            content = f.read()
        assert "Processing: " in content, "Expected results to be logged"

        # Verify that all tasks were executed
        assert job.executed_tasks == expected_tasks, f"Not all tasks were executed. Expected {expected_tasks}, got {job.executed_tasks}"
        print(f"Verified all tasks were executed: {job.executed_tasks}")

    except Exception as e:
        assert False, f"Serial mode should not fail: {e}"
    finally:
        if 'unpicklable' in locals():
            unpicklable.__del__()

def test_parallel_result_processor_fails_with_unpicklable():
    asyncio.run(parallel_mode())
    

def test_serial_result_processor_succeeds_with_unpicklable():
    asyncio.run(serial_mode())
