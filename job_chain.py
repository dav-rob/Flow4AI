import multiprocessing as mp
import threading
import asyncio
import queue
import logging
import os
import pickle
import inspect
from time import sleep
from typing import Any, Dict, Callable, Union, Optional
from utils.print_utils import printh
from job import JobFactory, Job
from logging_config import setup_logging

# Initialize logging configuration
setup_logging()

class JobChain:
    def __init__(self, job_input: Union[Dict[str, Any], Job], result_processing_function: Optional[Callable[[Any], None]] = None, serial_processing: bool = False):
        # Get logger for JobChain
        self.logger = logging.getLogger('JobChain')
        self.logger.info("Initializing JobChain")

        # If not in serial mode, verify function and its closure can be pickled
        if not serial_processing and result_processing_function:
            try:
                # Try to pickle the function
                pickle.dumps(result_processing_function)
                
                # Try to pickle any closure variables
                if hasattr(result_processing_function, '__closure__') and result_processing_function.__closure__:
                    for cell in result_processing_function.__closure__:
                        pickle.dumps(cell.cell_contents)
                
                # Try to pickle globals used by the function
                if hasattr(result_processing_function, '__code__'):
                    func_globals = {name: result_processing_function.__globals__[name] 
                                  for name in result_processing_function.__code__.co_names 
                                  if name in result_processing_function.__globals__}
                    pickle.dumps(func_globals)
                
            except Exception as e:
                self.logger.error(f"Result processing function or its dependencies cannot be pickled: {e}")
                self.logger.info("Use serial_processing=True for unpicklable functions")
                raise TypeError(f"Result processing function and its dependencies must be picklable in parallel mode: {e}")

        self._task_queue = mp.Queue() if not serial_processing else queue.Queue()
        self._result_queue = mp.Queue() if not serial_processing else queue.Queue()
        self.job_executor_process = None
        self.result_processor_process = None
        self._result_processing_function = result_processing_function
        self._serial_processing = serial_processing
        
        if isinstance(job_input, Dict):
            self.job_chain_context = job_input
            job_context: Dict[str, Any] = job_input.get("job_context")
            self.job = JobFactory.load_job(job_context)
        elif isinstance(job_input, Job):
            self.job_chain_context = {"job_context": {"type": "direct", "job": job_input}}
            self.job = job_input
        else:
            raise TypeError("job_input must be either Dict[str, Any] or Job instance")

        # Start processing based on mode
        if serial_processing:
            self.logger.info("Running in serial processing mode")
        else:
            self.logger.info("Running in parallel processing mode")
            self._start_parallel()

    def __del__(self):
        """Clean up resources when the object is destroyed."""
        try:
            self.logger.info("Cleaning up JobChain resources")
            
            if not self._serial_processing:
                # Clean up result processor process
                if hasattr(self, 'result_processor_process'):
                    process = self.result_processor_process
                    if process and process.is_alive():
                        try:
                            process.terminate()
                            process.join()
                        except Exception as e:
                            self.logger.error(f"Error terminating result processor process: {e}")
                    self.result_processor_process = None
                
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

    def _start_parallel(self):
        """Start the job executor and result processor processes - non-blocking."""
        self.logger.debug("Starting job executor process")
        self.job_executor_process = mp.Process(
            target=self._async_worker,
            args=(self.job, self._task_queue, self._result_queue),
            name="JobExecutorProcess"
        )
        self.job_executor_process.start()
        self.logger.info(f"Job executor process started with PID {self.job_executor_process.pid}")

        if self._result_processing_function:
            self.logger.debug("Starting result processor process")
            self.result_processor_process = mp.Process(
                target=self._result_processor,
                args=(self._result_processing_function, self._result_queue),
                name="ResultProcessorProcess"
            )
            self.result_processor_process.start()
            self.logger.info(f"Result processor process started with PID {self.result_processor_process.pid}")

    def submit_task(self, task):
        """Submit a task to be processed."""
        self.logger.debug(f"Submitting task: {task}")
        self._task_queue.put(task)

    def mark_input_completed(self):
        """Signal completion of input and wait for all processing to finish."""
        self.logger.debug("Marking input as completed")
        printh("task_queue ended")
        self._task_queue.put(None)
        
        if self._serial_processing:
            return self._process_tasks_serial()
        else:
            self._wait_for_completion()

    async def _process_tasks_serial(self):
        """Process tasks serially in the current event loop."""
        self.logger.debug("Processing tasks serially")
        
        while True:
            try:
                task = self._task_queue.get_nowait()
                if task is None:
                    break
                
                # Execute task
                result = await self.job.execute(task)
                
                # Process result immediately if function provided
                if self._result_processing_function:
                    self._result_processing_function(result)
            except queue.Empty:
                break

    def _wait_for_completion(self):
        """Wait for completion of all processing."""
        self.logger.debug("Entering wait for completion")
        
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
