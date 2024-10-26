from time import sleep
from utils.timing import timing_decorator
from job_chain import JobChain

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
def process_results_function(result):
    """ Call any code you want to process each result returned by JobChain"""
    sleep(0.5) 
    print(f"Collating and summarizing: {result}")

# Main function to manage the job chain
@timing_decorator
def main():
    # Pass in a context describing the jobs to execute asynchronously on data
    #   passed in from a synchronous context.
    job_chain_context = {
        "job_context":{"type":"file","params":{}}
    }
    # Initialise a JobChain which spawns a seperate process for asynchronously 
    #   processing tasks passed in from a synchronous context. 
    # process_results_function is called synchronously after jobs have completed
    job_chain = JobChain(job_chain_context, process_results_function)
    # First synchronous function to send tasks to be executed asynchronously
    #   by JobChain
    send_tasks_1(job_chain)
    # Second synchronous function sends tasks to be executed asynchronously
    #   - send as many tasks as you want to
    #   - take as long as you want to between calls
    send_tasks_2(job_chain)
    # When you're finished tell JobChain there's no more input so it can close down.
    job_chain.mark_input_completed()

if __name__ == "__main__":
    main()
