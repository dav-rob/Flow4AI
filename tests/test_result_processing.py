import multiprocessing as mp
import asyncio
import time
from time import sleep
from job_chain import JobChain
from job import Job

class ResultProcessor:
    def __init__(self, timing_queue):
        self.timing_queue = timing_queue

    def process_result(self, result):
        """Track when each result is processed"""
        current_time = time.time()
        timing_data = {
            "task": result["task"],
            "processed_at": current_time,
            "execution_timestamp": result["timestamp"]
        }
        print(f"Processing result for {result['task']} at {current_time}")
        self.timing_queue.put(timing_data)

class ResultTimingJob(Job):
    def __init__(self):
        super().__init__("Result Timing Job", "Test prompt", "test-model")

    async def execute(self, task) -> dict:
        # Simulate some work
        await asyncio.sleep(0.1)
        current_time = time.time()
        print(f"Executing task {task} at {current_time}")
        return {"task": task, "timestamp": current_time}

async def run_timing_test():
    global input_completed_time
    
    # Create a queue to track timing data
    timing_queue = mp.Queue()
    
    # Create result processor with queue
    processor = ResultProcessor(timing_queue)
    
    # Create job chain
    job = ResultTimingJob()
    job_chain = JobChain(job, processor.process_result)

    # Submit tasks with delays to simulate real work
    for i in range(5):
        print(f"Submitting task {i}")
        job_chain.submit_task(f"Task {i}")
        await asyncio.sleep(0.2)  # Simulate time between tasks
    
    # Record when we mark input as completed
    input_completed_time = time.time()
    print(f"Marking input completed at {input_completed_time}")
    job_chain.mark_input_completed()
    
    # Return queue for collecting results
    return timing_queue

def test_result_processing_timing():
    """Test that results are processed before mark_input_completed is called"""
    # Run the test and get the timing queue
    timing_queue = asyncio.run(run_timing_test())
    
    # Give a short time for any final results to be processed
    time.sleep(0.5)
    
    # Collect all results from queue
    processed_results = []
    while not timing_queue.empty():
        processed_results.append(timing_queue.get())
    
    print(f"\nProcessed {len(processed_results)} results:")
    for result in processed_results:
        print(f"Task: {result['task']}")
        print(f"Executed at: {result['execution_timestamp']}")
        print(f"Processed at: {result['processed_at']}")
        print(f"Delay: {result['processed_at'] - result['execution_timestamp']:.3f}s")
        print()
    
    print(f"Input completed at: {input_completed_time}")
    
    # There should be results processed before input_completed_time
    early_results = [r for r in processed_results 
                    if r["processed_at"] < input_completed_time]
    
    assert len(early_results) > 0, (
        "No results were processed before mark_input_completed was called. "
        "Results should be processed as they become available, not held until the end."
    )

    # Calculate timing statistics
    time_diffs = [(r["processed_at"] - r["execution_timestamp"]) 
                 for r in processed_results]
    avg_processing_delay = sum(time_diffs) / len(time_diffs)
    
    assert avg_processing_delay < 0.5, (
        f"Average delay between result execution and processing was {avg_processing_delay:.2f}s. "
        "Results should be processed soon after they are available."
    )

    # Verify results weren't all processed at the end
    last_task_time = max(r["execution_timestamp"] for r in processed_results)
    results_after_last = [r for r in processed_results 
                         if r["processed_at"] > last_task_time + 0.5]
    
    assert len(results_after_last) < len(processed_results), (
        "All results were processed well after the last task completed. "
        "Results should be processed incrementally as they become available."
    )
