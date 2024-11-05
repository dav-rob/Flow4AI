import asyncio
import logging
import os
import sys
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job import Job
from job_chain import JobChain
from utils.timing import timing_decorator


# Custom Job implementation for demonstration
class ExampleJob(Job):
    def __init__(self):
        super().__init__("Example Job", "Sample prompt", "example-model")
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, task):
        self.logger.info(f"Processing task: {task}")
        await asyncio.sleep(0.1)  # Simulate processing
        return {"task": task, "result": f"Processed {task}"}

# Simulates web scraping.
def send_tasks_2(job_chain):
    """ Pass the JobChain instance to any code you want processing quickly in parallel """
    logger = logging.getLogger('WebScraper')
    pages = [f"Page {i}" for i in range(12,22)]  # Simulated pages
    for page in pages:
        logger.info(f"Scraping: {page}")
        # Push the scraped page to task_queue
        job_chain.submit_task(page)  # Pub: Push page into task_queue
        sleep(0.1)  # Simulate network delay

# Simulates web scraping in batches
def send_tasks_1(job_chain):
    """ Pass the JobChain instance to any code you want processing quickly in parallel """
    logger = logging.getLogger('BatchScraper')
    batch_of_pages = []
    i = 0
    
    for batch in range(3):
        # Collect 4 pages into a batch
        for _ in range(4):
            page = f"Page {i}"
            batch_of_pages.append(page)
            i += 1           
        # Submit the batch of 4 pages to task queue
        logger.info(f"Submitting batch of scraped pages: {batch_of_pages}")
        job_chain.submit_task(batch_of_pages)
        batch_of_pages = []        
        # Add delay between batches (except after last batch)
        if batch < 4:
            sleep(0.2)

# Function to simulate serially collating results returned by JobChain
def process_after_results_fn(result):
    """ Call any code you want to process each result returned by JobChain"""
    logger = logging.getLogger('ResultProcessor')
    sleep(0.1) 
    logger.info(f"Collating and summarizing: {result}")

# Example using dictionary-based initialization
@timing_decorator
def run_with_dict_init():
    logger = logging.getLogger('DictInit')
    logger.info("Running with dictionary-based initialization:")
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
    logger = logging.getLogger('DirectInit')
    logger.info("Running with direct Job instance initialization:")
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
