import multiprocessing as mp
import asyncio
import queue
from time import sleep
from typing import Any, Dict
from utils.print_utils import printh
from job import JobFactory

class JobChain:
    def __init__(self, job_chain_context: Dict[str, Any]):
        self.job_chain_context = job_chain_context
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.analyzer_process = None
        job_context: Dict[str, Any] = job_chain_context.get("job_context")
        self.job = JobFactory.load_job(job_context)

    def start(self):
        self.analyzer_process = mp.Process(target=self.async_worker)
        self.analyzer_process.start()

    def wait_for_completion(self):
        self.analyzer_process.join()

    def async_worker(self):
        """Process that handles making workflow calls using asyncio."""

        async def process_task(task):
            """Process a single task and return its result"""
            result = await self.job.execute(task)
            self.result_queue.put(result)

        async def task_loop():
            tasks = []
            # First collect all tasks
            while True:
                try:
                    task = self.task_queue.get(timeout=5)
                    if task is None:
                        break
                    tasks.append(process_task(task))
                except queue.Empty:
                    printh("task_queue timeout")
                    break

            # Execute all tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)

        asyncio.run(task_loop())
        # Signal that the analyzer has finished
        printh("result_queue ended")
        self.result_queue.put(None)  # Pub: Signal that analysis is done
