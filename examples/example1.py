from time import sleep
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.timing import timing_decorator
from job_chain import JobChain
from job import Job

# Custom Job implementation for demonstration
class ExampleJob(Job):
    def __init__(self):
        super().__init__("Example Job", "Sample prompt", "example-model")

    async def execute(self, task):
        print(f"Processing task: {task}")
        await asyncio.sleep(0.1)  # Simulate processing
        return f"Processed {task}"

# Simulates web scraping.
def send_tasks_2(job_chain):
    """ Pass the JobChain instance to any code you want processing quickly in parallel """
    pages = [f"Page {i}" for i in range(12,22)]  # Simulated pages
    for page in pages:
        print(f"Scraping: {page}")
        # Push the scraped page to task_queue
        job_chain.submit_task(page)  # Pub: Push page into task_queue
        sleep(0.1)  # Simulate network delay

# Simulates web scraping in batches
def send_tasks_1(job_chain):
    """ Pass the JobChain instance to any code you want processing quickly in parallel """
    batch_of_pages = []
    i = 0
    
    for batch in range(3):
        # Collect 4 pages into a batch
        for _ in range(4):
            page = f"Page {i}"
            batch_of_pages.append(page)
            i += 1           
        # Submit the batch of 4 pages to task queue
        print(f"Submitting batch of scraped pages: {batch_of_pages}")
        job_chain.submit_task(batch_of_pages)
        batch_of_pages = []        
        # Add delay between batches (except after last batch)
        if batch < 4:
            sleep(0.2)

# Function to simulate serially collating results returned by JobChain
def process_after_results_fn(result):
    """ Call any code you want to process each result returned by JobChain"""
    sleep(0.5) 
    print(f"Collating and summarizing: {result}")

# Example using dictionary-based initialization
@timing_decorator
def run_with_dict_init():
    print("\nRunning with dictionary-based initialization:")
    # Pass in a context describing the jobs to execute asynchronously.
    job_chain_context = {
        "job_context": {"type": "file", "params": {}}
    }
    # Initialize JobChain with dictionary configuration
    job_chain = JobChain(job_chain_context, process_after_results_fn)
    send_tasks_1(job_chain)
    send_tasks_2(job_chain)
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

# Example using direct Job instance initialization
@timing_decorator
def run_with_direct_job():
    print("\nRunning with direct Job instance initialization:")
    # Create a Job instance directly
    job = ExampleJob()
    # Initialize JobChain with Job instance
    job_chain = JobChain(job, process_after_results_fn)
    send_tasks_1(job_chain)
    send_tasks_2(job_chain)
    # Indicate there is no more input data to process to initiate shutdown
    job_chain.mark_input_completed()

# Main function demonstrating both initialization methods
def main():
    # Run example with dictionary-based initialization
    run_with_dict_init()
    
    # Run example with direct Job instance
    run_with_direct_job()

if __name__ == "__main__":
    main()
