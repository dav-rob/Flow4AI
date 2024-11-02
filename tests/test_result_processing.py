import multiprocessing as mp
import asyncio
import time
import os
from time import sleep
from job_chain import JobChain
from job import Job

class ResultTimingJob(Job):
    def __init__(self):
        super().__init__("Result Timing Job", "Test prompt", "test-model")

    async def execute(self, task) -> dict:
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

async def run_unpicklable_tests():
    """Run both parallel and serial tests"""
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
        for i in range(3):
            job_chain.submit_task(f"Task {i}")
            await asyncio.sleep(0.1)
        
        # Process tasks and wait for completion
        await job_chain.mark_input_completed()
        print("Serial mode succeeded as expected")
        
        # Verify results were written to file
        with open('temp.log', 'r') as f:
            content = f.read()
        assert "Processing: " in content, "Expected results to be logged"
    except Exception as e:
        assert False, f"Serial mode should not fail: {e}"
    finally:
        if 'unpicklable' in locals():
            unpicklable.__del__()

def test_unpicklable_processor():
    """Test that unpicklable processors work in serial mode but fail in parallel mode"""
    # Run both tests in a single event loop
    asyncio.run(run_unpicklable_tests())
