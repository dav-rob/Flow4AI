import multiprocessing as mp
import asyncio
import queue
from utils.print_utils import printh
from job import Job, JobFactory

class JobChain:
    def __init__(self, context):
        self.context = context
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.analyzer_process = None

    def start(self):
        self.analyzer_process = mp.Process(target=self.worker_analyzer)
        self.analyzer_process.start()

    def wait_for_completion(self):
        self.analyzer_process.join()

    def add_job(self, job: Job):
        self.task_queue.put(job)

    def worker_analyzer(self):
        """Process that handles executing jobs using asyncio."""

        async def analyzer_loop():
            while True:
                try:
                    # Block until new task is available
                    job = self.task_queue.get(timeout=5)  # Sub: Task queue gets job
                    if job is None:
                        break  # Exit signal

                    # Execute the job and push result to result_queue
                    result = await job.execute(self.context)
                    # Push job result into result_queue
                    self.result_queue.put(result)  # Pub: Push result into result_queue

                except queue.Empty:
                    printh("task_queue timeout")
                    continue  # No task, keep waiting

        asyncio.run(analyzer_loop())
        # Signal that the analyzer has finished
        printh("task_queue ended")
        self.result_queue.put(None)  # Pub: Signal that analysis is done

# Example usage:
if __name__ == "__main__":
    context = {"pdf": "example.pdf"}
    job_chain = JobChain(context)

    # Load jobs (this could be done dynamically in a real scenario)
    job1 = JobFactory._load_from_file("job1_config.json")
    job2 = JobFactory._load_from_datastore("job2_id")

    # Add jobs to the chain
    job_chain.add_job(job1)
    job_chain.add_job(job2)

    # Start the job chain
    job_chain.start()

    # Process results (this could be done in a separate consumer process)
    while True:
        result = job_chain.result_queue.get()
        if result is None:
            break
        print(f"Received result: {result}")

    # Wait for completion
    job_chain.wait_for_completion()
