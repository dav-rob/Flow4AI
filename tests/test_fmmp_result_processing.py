"""
    Tests parallel and serial functionality with picklable and non-picklable result
        processing functions.
"""

import asyncio
import os
import time

from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC


class ResultTimingJob(JobABC):
    def __init__(self):
        super().__init__("Result Timing Job")
        self.executed_tasks = set()

    async def run(self, task) -> dict:
        # Extract the actual task from the wrapped task
        actual_task = task.get(self.name, task)
        # Record task execution using the task string
        if isinstance(actual_task, dict) and 'task' in actual_task:
            task_str = actual_task['task']
        else:
            task_str = str(actual_task)
        self.executed_tasks.add(task_str)
        # Simulate some work
        await asyncio.sleep(0.1)
        current_time = time.time()
        print(f"Executing task {actual_task} at {current_time}")
        return {"task": actual_task, "timestamp": current_time}

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

        # Create FlowManagerMP in parallel mode
        job = ResultTimingJob()
        flowmanagerMP = FlowManagerMP(job, unpicklable_processor, serial_processing=False)

        # Submit some tasks
        for i in range(3):
            flowmanagerMP.submit_task(f"Task {i}")
            time.sleep(0.1)
        
        flowmanagerMP.wait_for_completion()
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

        # Create FlowManagerMP in serial mode
        job = ResultTimingJob()
        flowmanagerMP = FlowManagerMP(job, unpicklable_processor, serial_processing=True)

        # Submit some tasks
        expected_tasks = {f"Task {i}" for i in range(3)}
        for task in expected_tasks:
            flowmanagerMP.submit_task({job.name: {'task': task}}, fq_name=job.name)
            time.sleep(0.1)
        
        # Process tasks and wait for completion
        flowmanagerMP.wait_for_completion()  # Not awaited since it's synchronous
        
        # Give a small delay to ensure all results are processed
        time.sleep(0.5)
        
        # Verify results were written to file
        with open('temp.log', 'r') as f:
            content = f.read()
        
        # Verify all tasks were processed by checking log content
        for task in expected_tasks:
            assert f"'task': {{'task': '{task}'}}" in content, f"Expected task {task} to be processed"
        
        print("All tasks were successfully processed and logged")

    except Exception as e:
        assert False, f"Serial mode should not fail: {e}"


def test_parallel_result_processor_fails_with_unpicklable():
    parallel_mode()
    
def test_serial_result_processor_succeeds_with_unpicklable():
    serial_mode()
