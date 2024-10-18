import multiprocessing as mp
import asyncio
import queue
from time import sleep
from utils.print_utils import printh
from job import JobFactory

class JobChain:
    def __init__(self, job_chain_context):
        self.job_chain_context = job_chain_context
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.analyzer_process = None
        job_context:dict[str, any]={"type":"file","params":{}}
        self.job = JobFactory.load_job(job_context)

    def start(self):
        self.analyzer_process = mp.Process(target=self.worker_analyzer)
        self.analyzer_process.start()

    def wait_for_completion(self):
        self.analyzer_process.join()

    def worker_analyzer(self):
        """Process that handles analyzing pages using asyncio."""

        async def analyzer_loop():
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

        asyncio.run(analyzer_loop())
        # Signal that the analyzer has finished
        printh("task_queue ended")
        self.result_queue.put(None)  # Pub: Signal that analysis is done
