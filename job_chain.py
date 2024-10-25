import multiprocessing as mp
import asyncio
import queue
from time import sleep
from typing import Any, Dict, Callable
from utils.print_utils import printh
from job import JobFactory

class JobChain:
    def __init__(self, job_chain_context: Dict[str, Any], result_processing_function: Callable[[Any], None]):
        self.job_chain_context = job_chain_context
        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()
        self.analyzer_process = None
        self._result_processing_function = result_processing_function
        job_context: Dict[str, Any] = job_chain_context.get("job_context")
        self.job = JobFactory.load_job(job_context)

    def start(self):
        """Start the analyzer process - non-blocking."""
        self.analyzer_process = mp.Process(target=self.async_worker)
        self.analyzer_process.start()

    def wait_for_completion(self):
        """Wait for completion and process results."""
        # Process results until we get None or analyzer process dies
        while True:
            try:
                result = self.result_queue.get(timeout=1)
                if result is None:
                    print("No more results to process.")
                    break
                if self._result_processing_function:
                    self._result_processing_function(result)
            except queue.Empty:
                if not self.analyzer_process.is_alive():
                    break

        # Wait for analyzer process to complete
        if self.analyzer_process and self.analyzer_process.is_alive():
            self.analyzer_process.join()

    def async_worker(self):
        """Process that handles making workflow calls using asyncio."""
        async def process_task(task):
            """Process a single task and return its result"""
            result = await self.job.execute(task)
            self.result_queue.put(result)

        async def queue_monitor():
            """Monitor the task queue and create tasks as they arrive"""
            tasks = set()
            pending_tasks = []
            end_signal_received = False
            # If there is no end signal or tasks are still remaining, then loop
            while not end_signal_received or tasks:
                # Collect available tasks
                while True:
                    try:
                        task = self.task_queue.get_nowait()
                        if task is None:
                            end_signal_received = True
                            break
                        pending_tasks.append(task)
                    except queue.Empty:
                        break

                # Create tasks in batch if we have any pending
                if pending_tasks:
                    new_tasks = {asyncio.create_task(process_task(t)) for t in pending_tasks}
                    tasks.update(new_tasks)
                    pending_tasks.clear()

                # Clean up completed tasks
                done_tasks = {t for t in tasks if t.done()}
                tasks.difference_update(done_tasks)

                # Very small sleep to prevent busy waiting
                await asyncio.sleep(0.001)

            # Wait for remaining tasks to complete
            if tasks:
                await asyncio.gather(*tasks)

            # Signal completion
            printh("result_queue ended")
            self.result_queue.put(None)

        asyncio.run(queue_monitor())
