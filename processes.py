import multiprocessing as mp
import asyncio
import time
from time import sleep
from utils.print_utils import printh
from job_chain import JobChain


# Scraping function
def scrape_website(task_queue):
    """Simulates web scraping by submitting batches of 4 pages to the task queue."""
    batch_of_pages = []
    i = 0
    
    for batch in range(5):
        # Collect 4 pages into a batch
        for _ in range(4):
            page = f"Page {i}"
            print(f"Scraping: {page}")
            batch_of_pages.append(page)
            i += 1
            
        # Submit the batch of 4 pages to task queue
        task_queue.put(batch_of_pages)
        batch_of_pages = []
        
        # Add delay between batches (except after last batch)
        if batch < 4:
            sleep(0.2)
    
    # Signal that scraping is complete
    printh("task_queue ended")
    task_queue.put(None)

# Function to collate and summarize results
def collate_and_summarise_analysis(result):
    """Processes and summarizes the result from the analyzer."""
    sleep(2) 
    print(f"Collating and summarizing: {result}")

# Main function to manage the job chain
def main():
    start_time = time.perf_counter()
    job_chain_context = {
        "job_context":{"type":"file","params":{}}
    }

    job_chain = JobChain(job_chain_context, collate_and_summarise_analysis)
    job_chain.start()

    # Start web scraping and feed the task queue
    scrape_website(job_chain.task_queue)

    # Wait for all processes to finish
    job_chain.wait_for_completion()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds")

if __name__ == "__main__":
    main()
