import multiprocessing as mp
import threading
import asyncio
import queue
import logging
import os
from time import sleep
from typing import Any, Dict, Callable, Union, Optional
from utils.print_utils import printh
from job import JobFactory, Job
from logging_config import setup_logging

# Initialize logging configuration
setup_logging()

class JobChain:
    def __init__(self, job_input: Union[Dict[str, Any], Job], result_processing_function: Optional[Callable[[Any], None]] = None):
        # Get logger for JobChain
        self.logger = logging.getLogger('JobChain')
        self.logger.info("Initializing JobChain")

        self._task_queue = mp.Queue()
        self._result_queue = mp.Queue()
        self.job_executor_process = None
        self._result_processing_function = result_processing_function
        if isinstance(job_input, Dict):
            self.job_chain_context = job_input
            job_context: Dict[str, Any] = job_input.get("job_context")
            self.job = JobFactory.load_job(job_context)
        elif isinstance(job_input, Job):
            self.job_chain_context = {"job_context": {"type": "direct", "job": job_input}}
            self.job = job_input
        else:
            raise TypeError("job_input must be either Dict[str, Any] or Job instance")

        # Start the job executor process immediately upon construction
        self._start()

    def __del__(self):
        """Clean up resources when the object is destroyed."""
        try:
            self.logger.info("Cleaning up JobChain resources")
            
            # Clean up job executor process
            if not hasattr(self, 'job_executor_process'):
                self.logger.warning("job_executor_process attribute not found during cleanup")
                return

            process = self.job_executor_process
            if process is None:
                self.logger.warning("job_executor_process has become None before cleanup")
                return

            self.logger.debug(f"Job executor process state during cleanup: {process}")
            
            try:
                if process.is_alive():
                    self.logger.info("Terminating live job executor process")
                    try:
                        process.terminate()
                        process.join()
                        self.logger.info("Job executor process terminated successfully")
                    except AttributeError:
                        self.logger.warning("Job executor process became None during termination attempt")
                    except Exception as e:
                        self.logger.error(f"Error terminating job executor process: {e}")
                else:
                    self.logger.info("Job executor Process is not alive, skipping termination")
            finally:
                self.job_executor_process = None
            
            # Clean up queues
            if hasattr(self, '_task_queue'):
                try:
                    self._task_queue.close()
                    self._task_queue.join_thread()
                except Exception as e:
                    self.logger.error(f"Error closing task queue: {e}")
            
            if hasattr(self, '_result_queue'):
                try:
                    self._result_queue.close()
                    self._result_queue.join_thread()
                except Exception as e:
                    self.logger.error(f"Error closing result queue: {e}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            pass

    def _start(self):
        """Start the job executor process - non-blocking."""
        self.logger.debug("Starting job executor process")
        self.job_executor_process = mp.Process(
            target=self._async_worker,
            args=(self._result_processing_function,),
            name="JobExecutorProcess"
        )
        self.job_executor_process.start()
        self.logger.info(f"Job executor process started with PID {self.job_executor_process.pid}")

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

    def _wait_for_completion(self):
        """Wait for completion of all processing."""
        self.logger.debug("Entering wait for completion")
        
        # Wait for job executor to finish
        if self.job_executor_process and self.job_executor_process.is_alive():
            self.logger.debug("Waiting for job executor process")
            self.job_executor_process.join()
            self.logger.debug("Job executor process completed")

    def _async_worker(self, result_processing_function):
        """Process that handles making workflow calls using asyncio and processes results."""
        # Get logger for AsyncWorker
        logger = logging.getLogger('AsyncWorker')
        logger.debug("Starting async worker")

        # Create event for signaling result processor to stop
        stop_processing = threading.Event()

        def result_processor():
            """Thread that handles processing results as they arrive."""
            logger = logging.getLogger('ResultProcessor')
            logger.debug("Starting result processor")

            # Create a queue for result processing
            result_queue = queue.Queue()
            processing_threads = []
            max_threads = 10  # Limit concurrent result processing threads

            def process_single_result(result):
                """Process a single result"""
                try:
                    if result_processing_function:
                        task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                        logger.debug(f"Processing result for task {task_id}")
                        result_processing_function(result)
                        logger.debug(f"Finished processing result for task {task_id}")
                except Exception as e:
                    logger.error(f"Error processing result: {e}")

            while not stop_processing.is_set():
                try:
                    # Clean up completed threads
                    processing_threads[:] = [t for t in processing_threads if t.is_alive()]

                    # Only process new results if we haven't hit thread limit
                    if len(processing_threads) < max_threads:
                        result = self._result_queue.get(timeout=0.1)
                        if result is None:
                            logger.debug("Received completion signal from result queue")
                            break

                        # Start new thread for this result
                        thread = threading.Thread(
                            target=process_single_result,
                            args=(result,),
                            daemon=True
                        )
                        thread.start()
                        processing_threads.append(thread)
                    else:
                        # Wait a bit if we've hit thread limit
                        sleep(0.1)
                except queue.Empty:
                    continue

            # Wait for all result processing threads to complete
            for thread in processing_threads:
                thread.join()
            logger.debug("Result processor shutting down")

        # Start result processor thread
        result_thread = None
        if result_processing_function:
            result_thread = threading.Thread(target=result_processor, name="ResultProcessorThread")
            result_thread.daemon = True
            result_thread.start()
            logger.info("Result processor thread started")

        async def process_task(task):
            """Process a single task and return its result"""
            logger.debug(f"Processing task: {task}")
            try:
                result = await self.job.execute(task)
                logger.debug(f"Task {task} completed successfully")
                self._result_queue.put(result)
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
                        task = self._task_queue.get_nowait()
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
            self._result_queue.put(None)

            # Wait for result processor to finish
            if result_thread:
                stop_processing.set()
                result_thread.join()

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
