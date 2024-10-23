import multiprocessing as mp
import asyncio
import queue
from time import sleep
from typing import Any, Dict
from utils.print_utils import printh
from job import JobFactory

class JobChain:
    def __init__(self, job_chain_context:dict[str, Any]):
        self.job_chain_context = job_chain_context
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.analyzer_process = None
        job_context:dict[str, any]= job_chain_context.get("job_context")
        self.job = JobFactory.load_job(job_context)

    def start(self):
        self.analyzer_process = mp.Process(target=self.async_worker)
        self.analyzer_process.start()

    def wait_for_completion(self):
        self.analyzer_process.join()

    def async_worker(self):
        """Process that handles making workflow calls using asyncio."""

        async def task_loop():
            while True:
                try:
                    # Block until new task is available
                    task = self.task_queue.get(timeout=5)  # Sub: Task queue gets page
                    if task is None:
                        break  # Exit signal
                    
                    # Call async Job and push result to result_queue
                    result = await self.job.execute(task)
                    # Push analysis result into result_queue
                    self.result_queue.put(result)  # Pub: Push result into result_queue

                except queue.Empty:
                    printh("task_queue timeout")
                    continue  # No task, keep waiting

        asyncio.run(task_loop())
        # Signal that the analyzer has finished
        printh("result_queue ended")
        self.result_queue.put(None)  # Pub: Signal that analysis is done
