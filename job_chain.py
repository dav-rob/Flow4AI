import asyncio
import logging
import multiprocessing as mp
import pickle
# TODO: use dil instead of pickle in multiprocessor
import queue
from time import sleep
from typing import Any, Callable, Dict, Optional, Union

from job import Job, JobFactory
from logging_config import setup_logging
from utils.print_utils import printh

# Initialize logging configuration
setup_logging()

class JobChain:
    """
    JobChain executes up to thousands of tasks in parallel using a Job passed into constructor.
    Optionally passes results to a pre-existing result processing function after task completion.

    Args:
        job (Union[Dict[str, Any], Job]): Either a dictionary containing job configuration or a Job instance.

        result_processing_function (Optional[Callable[[Any], None]]): Code to handle results after the Job executes its task.
            By default, this hand-off happens in parallel, immediately after a Job processes a task.
            Typically, this function is from an existing codebase that JobChain is supplementing.
            This function must be picklable, for parallel execution, see serial_processing parameter below.
            This code is not assumed to be asyncio compatible.

        serial_processing (bool, optional): Forces result_processing_function to execute only after all tasks are completed by the Job.
            Enables an unpicklable result_processing_function to be used by setting serial_processing=True.
            However, in most cases changing result_processing_function to be picklable is straightforward and should be the default.
            Defaults to False.
    """
    def __init__(self, job: Union[Dict[str, Any], Job], result_processing_function: Optional[Callable[[Any], None]] = None, serial_processing: bool = False):
        # Get logger for JobChain
        self.logger = logging.getLogger('JobChain')
        self.logger.info("Initializing JobChain")
        if not serial_processing and result_processing_function:
            self._check_picklable(result_processing_function)
        self._task_queue = mp.Queue()
        self._result_queue = mp.Queue()
        self.job_executor_process = None
        self.result_processor_process = None
        self._result_processing_function = result_processing_function
        self._serial_processing = serial_processing
        
        if isinstance(job, Dict):
            self.job_chain_context = job
            job_context: Dict[str, Any] = job.get("job_context")
            self.job = JobFactory.load_job(job_context)
        elif isinstance(job, Job):
            self.job_chain_context = {"job_context": {"type": "direct", "job": job}}
            self.job = job
        else:
            raise TypeError("job must be either Dict[str, Any] or Job instance")
        
        self._start()

    # We will not to use context manager as it makes semantics of JobChain use less flexible
    # def __enter__(self):
    #     """Initialize resources when entering the context."""
    #     self._start()
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Clean up resources when exiting the context."""
    #     self._cleanup()

    # belt and braces, _cleanup is called by _wait_for_completion() via mark_input_completed()
    def __del__(self):
        self._cleanup

    def _cleanup(self):
        """Clean up resources when the object is destroyed."""
        self.logger.info("Cleaning up JobChain resources")
        
        if self.job_executor_process:
            if self.job_executor_process.is_alive():
                self.job_executor_process.terminate()
                self.job_executor_process.join()
        
        if self.result_processor_process:
            if self.result_processor_process.is_alive():
                self.result_processor_process.terminate()
                self.result_processor_process.join()
        
        if hasattr(self, '_task_queue'):
            self._task_queue.close()
            self._task_queue.join_thread()
        
        if hasattr(self, '_result_queue'):
            self._result_queue.close()
            self._result_queue.join_thread()

    def _check_picklable(self, result_processing_function):
        try:
            # Try to pickle just the function itself
            pickle.dumps(result_processing_function)
            
            # Try to pickle any closure variables
            if hasattr(result_processing_function, '__closure__') and result_processing_function.__closure__:
                for cell in result_processing_function.__closure__:
                    pickle.dumps(cell.cell_contents)
                    
        except Exception as e:
            self.logger.error(f"""Result processing function or its closure variables cannot be pickled: {e}.  
                              Use serial_processing=True for unpicklable functions.""")
            raise TypeError(f"Result processing function must be picklable in parallel mode: {e}")

    
    def _start(self):
        """Start the job executor and result processor processes - non-blocking."""
        self.logger.debug("Starting job executor process")
        self.job_executor_process = mp.Process(
            target=self._async_worker,
            args=(self.job, self._task_queue, self._result_queue),
            name="JobExecutorProcess"
        )
        self.job_executor_process.start()
        self.logger.info(f"Job executor process started with PID {self.job_executor_process.pid}")

        if self._result_processing_function and not self._serial_processing:
            self.logger.debug("Starting result processor process")
            self.result_processor_process = mp.Process(
                target=self._result_processor,
                args=(self._result_processing_function, self._result_queue),
                name="ResultProcessorProcess"
            )
            self.result_processor_process.start()
            self.logger.info(f"Result processor process started with PID {self.result_processor_process.pid}")
    # TODO: add ability to submit a task or an iterable: Iterable
    # TODO: throw error, or just skip, if submitted task is None because this is a reserved value.
    def submit_task(self, task):
        """Submit a task to be processed."""
        self.logger.debug(f"Submitting task: {task}")
        self._task_queue.put(task)

    def mark_input_completed(self):
        """Signal completion of input and wait for all processing to finish."""
        self.logger.debug("Marking input as completed")
        printh("task_queue ended")
        self._task_queue.put(None)
        self._wait_for_completion()

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    # TODO: it may be necessary to put a flag to execute this using asyncio event loops
    #          for example, when handing off to an async web service
    @staticmethod
    def _result_processor(process_fn: Callable[[Any], None], result_queue: mp.Queue):
        """Process that handles processing results as they arrive."""
        logger = logging.getLogger('ResultProcessor')
        logger.debug("Starting result processor")

        while True:
            try:
                result = result_queue.get()
                if result is None:
                    logger.debug("Received completion signal from result queue")
                    break

                try:
                    # Handle both dictionary and non-dictionary results
                    task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                    logger.debug(f"Processing result for task {task_id}")
                    process_fn(result)
                    logger.debug(f"Finished processing result for task {task_id}")
                except Exception as e:
                    logger.error(f"Error processing result: {e}")
            except queue.Empty:
                continue

        logger.debug("Result processor shutting down")

    def _wait_for_completion(self):
        """Wait for completion of all processing."""
        self.logger.debug("Entering wait for completion")

        if self._result_processing_function and self._serial_processing:
            self._process_serial_results()
        
        # Wait for job executor to finish
        if self.job_executor_process and self.job_executor_process.is_alive():
            self.logger.debug("Waiting for job executor process")
            self.job_executor_process.join()
            self.logger.debug("Job executor process completed")

        # Wait for result processor to finish
        if self.result_processor_process and self.result_processor_process.is_alive():
            self.logger.debug("Waiting for result processor process")
            self.result_processor_process.join()
            self.logger.debug("Result processor process completed")
        
        self._cleanup()

    def _process_serial_results(self):
        while True:
            try:
                self.logger.debug("Attempting to get result from queue")
                result = self._result_queue.get(timeout=0.1)
                if result is None:
                    self.logger.debug("Received completion signal (None) from result queue")
                    self.logger.info("No more results to process.")
                    break
                if self._result_processing_function:
                    try:
                        # Handle both dictionary and non-dictionary results
                        task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                        self.logger.debug(f"Processing result for task {task_id}")
                        self._result_processing_function(result)
                        self.logger.debug(f"Finished processing result for task {task_id}")
                    except Exception as e:
                        self.logger.error(f"Error processing result: {e}")
            except queue.Empty:
                job_executor_is_alive = self.job_executor_process and self.job_executor_process.is_alive()
                self.logger.debug(f"Queue empty, job executor process alive status = {job_executor_is_alive}")
                if not job_executor_is_alive:
                    self.logger.debug("Job executor process is not alive, breaking wait loop")
                    break
                continue

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    @staticmethod
    def _async_worker(job: Job, task_queue: mp.Queue, result_queue: mp.Queue):
        """Process that handles making workflow calls using asyncio."""
        # Get logger for AsyncWorker
        logger = logging.getLogger('AsyncWorker')
        logger.debug("Starting async worker")

        async def process_task(task):
            """Process a single task and return its result"""
            logger.debug(f"Processing task: {task}")
            try:
                result = await job.execute(task)
                logger.debug(f"Task {task} completed successfully")
                result_queue.put(result)
                logger.debug(f"Result for task {task} put in queue")
            except Exception as e:
                logger.error(f"Error processing task {task}: {e}")
                raise

        async def queue_monitor():
            """Monitor the task queue and create tasks as they arrive"""
            logger.debug("Starting queue monitor")
            tasks = set()
            pending_tasks = []
            end_signal_received = False
            tasks_created = 0
            tasks_completed = 0

            # If there is no end signal or tasks are still remaining, then loop
            while not end_signal_received or tasks:
                # Collect available tasks
                while True:
                    try:
                        task = task_queue.get_nowait()
                        if task is None:
                            logger.info("Received end signal in task queue")
                            end_signal_received = True
                            break
                        pending_tasks.append(task)
                    except queue.Empty:
                        break

                # Create tasks in batch if we have any pending
                if pending_tasks:
                    logger.debug(f"Creating {len(pending_tasks)} new tasks")
                    new_tasks = {asyncio.create_task(process_task(t)) for t in pending_tasks}
                    tasks.update(new_tasks)
                    tasks_created += len(new_tasks)
                    logger.debug(f"Total tasks created: {tasks_created}")
                    pending_tasks.clear()

                # Clean up completed tasks
                done_tasks = {t for t in tasks if t.done()}
                if done_tasks:
                    tasks_completed += len(done_tasks)
                    logger.debug(f"Cleaned up {len(done_tasks)} completed tasks. Total completed: {tasks_completed}")
                tasks.difference_update(done_tasks)

                # A short pause to reduce CPU usage and avoid a busy-wait state.             
                await asyncio.sleep(0.0001)

            # Wait for remaining tasks to complete
            if tasks:
                logger.debug(f"Waiting for {len(tasks)} remaining tasks")
                await asyncio.gather(*tasks)
                logger.debug("All remaining tasks completed")

            # Signal completion
            logger.debug("Sending completion signal to result queue")
            logger.debug(f"Final stats - Created: {tasks_created}, Completed: {tasks_completed}")
            printh("result_queue ended")
            result_queue.put(None)

        # Run the event loop
        logger.debug("Creating event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.debug("Running queue monitor")
            loop.run_until_complete(queue_monitor())
        except Exception as e:
            logger.error(f"Error in async worker: {e}")
            raise
        finally:
            logger.info("Closing event loop")
            loop.close()
