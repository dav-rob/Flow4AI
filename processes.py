import multiprocessing as mp
import asyncio
import time
from time import sleep
from utils.print_utils import printh
from job_chain import JobChain


# Scraping function (remains synchronous)
def scrape_website(task_queue):
    """Simulates web scraping."""
    pages = [f"Page {i}" for i in range(10)]  # Simulated pages
    for page in pages:
        print(f"Scraping: {page}")
        # Push the scraped page to task_queue
        task_queue.put(page)  # Pub: Push page into task_queue
        sleep(0.1)  # Simulate network delay
    # Signal that scraping is complete
    task_queue.put(None)

def handle_results(result_queue):
    """Continuously handle results from result_queue."""
    while True:
        result = result_queue.get()  # Block until new result is available
        if result is None:
            print("No more results to process.")
            break  # Exit loop when analyzer is done
        collate_and_summarise_analysis(result)  # Process each result as it comes

# Function to collate and summarize results
def collate_and_summarise_analysis(result):
    """Processes and summarizes the result from the analyzer."""
    sleep(2) 
    print(f"Collating and summarizing: {result}")

# Main function to manage the job chain
def main():
    start_time = time.perf_counter()
    pdf = "path_to_pdf.pdf"  # Replace with your actual PDF path

    job_chain = JobChain(pdf)
    job_chain.start()

    # Start web scraping and feed the task queue
    scrape_website(job_chain.task_queue)

    # Handle results while analyzer is running
    handle_results(job_chain.result_queue)

    # Wait for the analyzer to finish
    job_chain.wait_for_completion()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds")

if __name__ == "__main__":
    main()
