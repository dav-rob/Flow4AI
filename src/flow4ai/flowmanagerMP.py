import asyncio
# In theory it makes sense to use dill with the "multiprocess" package
# instead of pickle with "multiprocessing", but in practice it leads to 
# performance and stability issues.
import multiprocessing as mp
import pickle
import queue
import time  # Added for poll_for_updates
from multiprocessing import freeze_support, set_start_method
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel

from flow4ai.flowmanager_base import FlowManagerABC

from . import f4a_logging as logging
from .dsl import DSLComponent
from .job import JobABC, Task, job_graph_context_manager
from .job_loader import ConfigLoader, JobFactory
from .utils.monitor_utils import should_log_task_stats


class FlowManagerMP(FlowManagerABC):
    """
    FlowManagerMP executes up to thousands of tasks in parallel using one or more Jobs passed into constructor.
    FlowManagerMP is a multiprocessing implementation of FlowManager, so tasks and results are passed between entirely
    different processes, which means that results and tasks must be picklable.
    Optionally passes results to a pre-existing on_complete function after task completion.

    Args:
        dsl (Union[Dict[str, Any], DSLComponent, List[DSLComponent]]): If missing, jobs will be loaded from config file.
            Otherwise either a dictionary containing job configuration,
            a single DSLComponent instance, or a list of DSLComponent instances.

        on_complete (Optional[Callable[[Any], None]]): Code to handle results after the Job executes its task.
            By default, this hand-off happens in parallel, immediately after a Job processes a task.
            Typically, this function is from an existing codebase that FlowManagerMP is supplementing.
            This function must be picklable, for parallel execution, see serial_processing parameter below.
            This code is not assumed to be asyncio compatible.

        serial_processing (bool, optional): Forces on_complete to execute only after all tasks are completed by the Job.
            Enables an unpicklable on_complete to callable be used by setting serial_processing=True.  However, in most cases 
            changing on_complete to be picklable is straightforward and should be the default.
            Defaults to False.
    """
    _lock = mp.RLock()  # Lock for thread-safe initialization
    _instance = None  # Singleton instance
    # Constants
    JOB_MAP_LOAD_TIME = 5  # Timeout in seconds for job map loading
    EXECUTOR_SHUTDOWN_TIMEOUT = -1  # Timeout in seconds for executor shutdown
    RESULT_PROCESSOR_SHUTDOWN_TIMEOUT = -1  # Timeout in seconds for result processor shutdown

    def __init__(self, dsl: Optional[Any] = None, on_complete: Optional[Callable[[Any], None]] = None, 
                 serial_processing: bool = False):
        super().__init__()
        # Get logger for FlowManagerMP
        self.logger = logging.getLogger('FlowManagerMP')
        self.logger.info("Initializing FlowManagerMP")
        if not serial_processing and on_complete:
            self._check_picklable(on_complete)
        # tasks are created by submit_task(), with [fq_name] added to the task dict
        # tasks are then sent to queue for processing
        self._task_queue: mp.Queue[Task] = mp.Queue()  
        # INTERNAL USE ONLY. DO NOT ACCESS DIRECTLY.
        # This queue is for internal communication between the job executor and result processor.
        # To process results, use the on_complete parameter in the FlowManagerMP constructor.
        # See test_result_processing.py for examples of proper result handling.
        self._result_queue = mp.Queue()  # type: mp.Queue
        self.job_executor_process = None
        self.result_processor_process = None
        self.on_complete = on_complete
        self.serial_processing = serial_processing
        
        # Create a manager for sharing objects between processes
        self._manager = mp.Manager()
        # !! This object allows us to pass the job name map between processes
        #     so we don't have to pickle the entire job map
        self._fq_name_map = self._manager.dict()
        # Create an event to signal when jobs are loaded
        self._jobs_loaded = mp.Event()

        # Initialize shared counters for task monitoring
        self.tasks_submitted = mp.Value('i', 0)
        self.tasks_in_progress = mp.Value('i', 0)
        self.tasks_completed = mp.Value('i', 0)
        self.post_processing_tasks = mp.Value('i', 0)
        self.job_errors = mp.Value('i', 0) # Added job_errors counter

        if dsl:
            self.create_job_graph_map(dsl)
            self._fq_name_map.clear()
            self._fq_name_map.update({job.name: job.job_set_str() for job in self.job_graph_map.values()})
        
        self._start()

    # We will not to use context manager as it makes semantics of FlowManagerMP use less flexible
    # def __enter__(self):
    #     """Initialize resources when entering the context."""
    #     self._start()
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     """Clean up resources when exiting the context."""
    #     self._cleanup()

    # belt and braces, _cleanup is called by _wait_for_completion() via mark_input_completed()
    def __del__(self):
        self._cleanup() # Fixed: call _cleanup

    def _cleanup(self):
        """Clean up resources when the object is destroyed."""
        self.logger.info("Cleaning up FlowManagerMP resources")
        
        if self.job_executor_process:
            if self.job_executor_process.is_alive():
                self.logger.debug("Terminating job executor process")
                self.job_executor_process.terminate()
                self.logger.debug("Joining job executor process")
                if self.EXECUTOR_SHUTDOWN_TIMEOUT != -1:
                    self.job_executor_process.join(timeout=self.EXECUTOR_SHUTDOWN_TIMEOUT)
                else:
                    self.job_executor_process.join()
                self.logger.debug("Job executor process joined")
        
        if self.result_processor_process:
            if self.result_processor_process.is_alive():
                self.logger.debug("Terminating result processor process")
                self.result_processor_process.terminate()
                self.logger.debug("Joining result processor process")
                if self.RESULT_PROCESSOR_SHUTDOWN_TIMEOUT != -1:
                    self.result_processor_process.join(timeout=self.RESULT_PROCESSOR_SHUTDOWN_TIMEOUT)
                else:
                    self.result_processor_process.join()
                self.logger.debug("Result processor process joined")
        
        if hasattr(self, '_task_queue'):
            self.logger.debug("Closing task queue")
            self._task_queue.close()
            self.logger.debug("Joining task queue thread")
            self._task_queue.join_thread()
            self.logger.debug("Task queue thread joined")
        
        if hasattr(self, '_result_queue'):
            self.logger.debug("Closing result queue")
            self._result_queue.close()
            self.logger.debug("Joining result queue thread")
            self._result_queue.join_thread()
            self.logger.debug("Result queue thread joined")
        
        self.logger.debug("Cleanup completed")

    def _check_picklable(self, on_complete):
        try:
            # Try to pickle just the function itself
            pickle.dumps(on_complete)
            
            # Try to pickle any closure variables
            if hasattr(on_complete, '__closure__') and on_complete.__closure__:
                for cell in on_complete.__closure__:
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
            args=(self.job_graph_map, self._task_queue, self._result_queue, 
                  self._fq_name_map, self._jobs_loaded, ConfigLoader.directories,
                  self.tasks_in_progress, self.tasks_completed, self.job_errors), # Pass counters
            name="JobExecutorProcess"
        )
        self.job_executor_process.start()
        self.logger.info(f"Job executor process started with PID {self.job_executor_process.pid}")

        if self.on_complete and not self.serial_processing:
            self.logger.debug("Starting result processor process")
            self.result_processor_process = mp.Process(
                target=self._result_processor,
                args=(self.on_complete, self._result_queue, 
                      self.post_processing_tasks), # Pass counter
                name="ResultProcessorProcess"
            )
            self.result_processor_process.start()
            self.logger.info(f"Result processor process started with PID {self.result_processor_process.pid}")

    # TODO: add resource usage monitoring which returns False if resource use is too high.
    def submit_task(self, task: Union[Dict[str, Any], List[Dict[str, Any]], str], fq_name: Optional[str] = None):
        # Wait for jobs to be loaded and the self._job_name_map to be populated
        if not self._jobs_loaded.wait(timeout=self.JOB_MAP_LOAD_TIME):
            # Check stderr from JobExecutorProcess for underlying errors
            stderr_output = ""
            if self.job_executor_process and hasattr(self.job_executor_process, 'stderr') and self.job_executor_process.stderr:
                try:
                    # This might not be available or might block, handle carefully
                    stderr_output = self.job_executor_process.stderr.read() 
                except Exception as e:
                    self.logger.warning(f"Could not read stderr from JobExecutorProcess: {e}")
            
            error_message = "Timed out waiting for jobs to be loaded"
            if stderr_output:
                error_message += f"\nJobExecutorProcess stderr:\n{stderr_output}"
            self.logger.error(error_message)
            raise TimeoutError(error_message)


        if task is None:
            self.logger.warning("Received None task, skipping")
            return

        fq_name = self.check_fq_name_and_job_graph_map(fq_name, self._fq_name_map)

        if isinstance(task, list):
            for single_task in task:
                self._submit_single_task(single_task, fq_name)
        else:
            self._submit_single_task(task, fq_name)

    def _submit_single_task(self, task: Union[Dict[str, Any], str], fq_name: str) -> None:
        """Process and submit a single task to the task queue.
        
        Args:
            task: The task to process, either as a dictionary or string
            fq_name: The fully qualified name for the task
        """
        if not isinstance(task, dict):
            task = {'task': str(task)}
        task_obj = Task(task, fq_name)
        # Check the string based _fq_name_map to ensure the fq_name is valid
        # Once the task is sent to the separate process the job graph will be 
        # looked up by the job name
        job_name = self._fq_name_map.get(task_obj.get_fq_name())
        if job_name is None:
            raise ValueError(f"Job not found for fq_name: {task_obj.get_fq_name()}")
        self._task_queue.put(task_obj)
        with self.tasks_submitted.get_lock():
            self.tasks_submitted.value += 1


    def close_processes(self, timeout=10, check_interval=0.1):
        """Signal completion of input and wait for all processes to finish and shut down."""
        self.logger.debug("Marking input as completed")
        self.logger.info("*** task_queue ended ***")
        self._task_queue.put(None)
        self.wait_for_completion(timeout=timeout, check_interval=check_interval)
        self._close_running_processes()

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    # TODO: it may be necessary to put a flag to execute this using asyncio event loops
    #          for example, when handing off to an async web service
    @staticmethod
    def _result_processor(on_complete: Callable[[Any], None], result_queue: 'mp.Queue', 
                          post_processing_counter: 'mp.Value'):
        """Process that handles processing results as they arrive."""
        logger = logging.getLogger('ResultProcessor')
        logger.debug("Starting result processor")

        while True:
            try:
                result = result_queue.get()
                if result is None:
                    logger.debug("Received completion signal from result queue")
                    break
                
                with post_processing_counter.get_lock():
                    post_processing_counter.value += 1
                
                logger.debug(f"ResultProcessor received result: {result}")
                try:
                    # Handle both dictionary and non-dictionary results
                    task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                    logger.debug(f"Processing result for task {task_id}")
                    on_complete(result)
                    logger.debug(f"Finished processing result for task {task_id}")
                except Exception as e:
                    logger.error(f"Error processing result: {e}")
                    logger.info("Detailed stack trace:", exc_info=True)
            except queue.Empty:
                continue

        logger.debug("Result processor shutting down")

    def _close_running_processes(self):
        """Close all running processes."""
        self.logger.debug("Entering close running processes")

        if self.on_complete and self.serial_processing:
            self._process_serial_results()
        
        # Wait for job executor to finish
        if self.job_executor_process and self.job_executor_process.is_alive():
            self.logger.debug("Waiting for job executor process")
            if self.EXECUTOR_SHUTDOWN_TIMEOUT != -1:
                self.job_executor_process.join(timeout=self.EXECUTOR_SHUTDOWN_TIMEOUT)
            else:
                self.job_executor_process.join()
            self.logger.debug("Job executor process completed")

        # Wait for result processor to finish
        if self.result_processor_process and self.result_processor_process.is_alive():
            self.logger.debug("Waiting for result processor process")
            if self.RESULT_PROCESSOR_SHUTDOWN_TIMEOUT != -1:
                self.result_processor_process.join(timeout=self.RESULT_PROCESSOR_SHUTDOWN_TIMEOUT)
            else:
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
                
                with self.post_processing_tasks.get_lock():
                    self.post_processing_tasks.value += 1

                if self.on_complete:
                    try:
                        # Handle both dictionary and non-dictionary results
                        task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                        self.logger.debug(f"Processing result for task {task_id}")
                        self.on_complete(result)
                        self.logger.debug(f"Finished processing result for task {task_id}")
                    except Exception as e:
                        self.logger.error(f"Error processing result: {e}")
                        self.logger.info("Detailed stack trace:", exc_info=True)
            except queue.Empty:
                job_executor_is_alive = self.job_executor_process and self.job_executor_process.is_alive()
                self.logger.debug(f"Queue empty, job executor process alive status = {job_executor_is_alive}")
                if not job_executor_is_alive:
                    self.logger.debug("Job executor process is not alive, breaking wait loop")
                    break
                continue

    @staticmethod
    def _replace_pydantic_models(data: Any) -> Any:
        """Recursively replace pydantic.BaseModel instances with their JSON dumps."""
        logger = logging.getLogger('FlowManagerMP')
        logger.debug(f'Processing data type: {type(data)}')

        if isinstance(data, dict):
            return {k: FlowManagerMP._replace_pydantic_models(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [FlowManagerMP._replace_pydantic_models(item) for item in data]
        elif isinstance(data, BaseModel):
            logger.info(f'Converting pydantic model {data.__class__.__name__}')
            return data.model_dump_json()
        return data

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    @staticmethod
    def _async_worker(job_graph_map: Dict[str, JobABC], task_queue: 'mp.Queue', result_queue: 'mp.Queue', 
                     job_name_map: 'mp.managers.DictProxy', jobs_loaded: 'mp.Event', 
                     directories: list[str] = [],
                     tasks_in_progress_counter: 'mp.Value' = None, 
                     tasks_completed_counter: 'mp.Value' = None,
                     job_errors_counter: 'mp.Value' = None): # Added job_errors_counter
        """Process that handles making workflow calls using asyncio."""
        # Get logger for AsyncWorker
        logger = logging.getLogger('AsyncWorker')
        logger.debug("Starting async worker")

        # If job_map is empty, create it from SimpleJobLoader
        if not job_graph_map:
            logger.info("Creating job map from JobLoader")
            logger.info(f"Using directories from process: {directories}")
            ConfigLoader._set_directories(directories)
            ConfigLoader.reload_configs()
            head_jobs = JobFactory.get_head_jobs_from_config()
            job_graph_map = {job.name: job for job in head_jobs}
            # Update the shared job_name_map with each head job's complete set of reachable jobs
            job_name_map.clear()
            job_name_map.update({job.name: job.job_set_str() for job in head_jobs})
            logger.info(f"Created job map with head jobs: {list(job_name_map.keys())}")

        # Signal that jobs are loaded
        jobs_loaded.set()

        async def process_task(task: Task):
            """Process a single task and return its result"""
            task_id = task.task_id  # task_id is not held in the dictionary itself i.e. NOT task['task_id']
            logger.debug(f"[TASK_TRACK] Starting task {task_id}")
            try:
                # If there's only one job, use it directly
                if len(job_graph_map) == 1:
                    job = next(iter(job_graph_map.values()))
                else:
                    # Otherwise, get the job from the map using fq_name
                    fq_name = task.get('fq_name')
                    if not fq_name:
                        raise ValueError("Task missing fq_name when multiple jobs are present")
                    job = job_graph_map[fq_name]
                job_set = JobABC.job_set(job) #TODO: create a map of job to jobset in _async_worker
                async with job_graph_context_manager(job_set):
                    result = await job._execute(task)
                    processed_result = FlowManagerMP._replace_pydantic_models(result)
                    logger.debug(f"[TASK_TRACK] Completed task {task_id}, returned by job {processed_result[JobABC.RETURN_JOB]}")
                    
                    if tasks_completed_counter:
                        with tasks_completed_counter.get_lock():
                            tasks_completed_counter.value += 1
                    
                    result_queue.put(processed_result)
                    logger.debug(f"[TASK_TRACK] Result queued for task {task_id}")
            except Exception as e:
                logger.error(f"[TASK_TRACK] Failed task {task_id}: {e}")
                logger.info("Detailed stack trace:", exc_info=True)
                if job_errors_counter: # Increment job_errors_counter
                    with job_errors_counter.get_lock():
                        job_errors_counter.value += 1
                raise

        async def queue_monitor():
            """Monitor the task queue and create tasks as they arrive"""
            logger.debug("Starting queue monitor")
            tasks = set()
            pending_tasks = []
            tasks_created = 0
            tasks_completed_local = 0 # Renamed to avoid confusion with shared counter
            end_signal_received = False

            while not end_signal_received or tasks:
                # Get all available tasks from the queue
                while True:
                    try:
                        task = task_queue.get_nowait()
                        if task is None:
                            logger.info("Received end signal in task queue")
                            end_signal_received = True
                            break
                        
                        if tasks_in_progress_counter:
                            with tasks_in_progress_counter.get_lock():
                                tasks_in_progress_counter.value += 1
                        
                        pending_tasks.append(task)
                    except queue.Empty:
                        break

                # Create tasks in batch if we have any pending
                if pending_tasks:
                    logger.debug(f"Creating {len(pending_tasks)} new tasks")
                    new_tasks = {asyncio.create_task(process_task(pending_tasks[i])) for i in range(len(pending_tasks))}
                    tasks.update(new_tasks)
                    tasks_created += len(new_tasks)
                    logger.debug(f"Total tasks created: {tasks_created}")
                    pending_tasks.clear()

                # Clean up completed tasks
                done_tasks = {t for t in tasks if t.done()}
                if done_tasks:
                    for done_task in done_tasks:
                        try:
                            # Check if task raised an exception
                            exc = done_task.exception()
                            if exc:
                                logger.error(f"Task failed with exception: {exc}")
                                logger.info("Detailed stack trace:", exc_info=True)
                        except asyncio.InvalidStateError:
                            pass  # Task was cancelled or not done
                    tasks_completed_local += len(done_tasks)
                    logger.debug(f"Cleaned up {len(done_tasks)} completed tasks. Total completed locally: {tasks_completed_local}")
                    logger.debug(f"Active tasks remaining: {len(tasks)}")
                tasks.difference_update(done_tasks)

                # Log task stats periodically
                if tasks_completed_local != 0 and tasks_completed_local % 5 == 0:
                    if should_log_task_stats(queue_monitor, tasks_created, tasks_completed_local):
                        logger.info(f"Tasks stats - Created: {tasks_created}, Completed Locally: {tasks_completed_local}, Active: {len(tasks)}")

                # A short pause to reduce CPU usage and avoid a busy-wait state.             
                await asyncio.sleep(0.0001)

            # Wait for remaining tasks to complete
            if tasks:
                logger.debug(f"Waiting for {len(tasks)} remaining tasks")
                await asyncio.gather(*tasks)
                logger.debug("All remaining tasks completed")

            # Signal completion
            logger.debug("Sending completion signal to result queue")
            logger.debug(f"Final stats - Created: {tasks_created}, Completed Locally: {tasks_completed_local}")
            logger.info("*** result_queue ended ***")
            result_queue.put(None)

        # Run the event loop
        logger.debug("Creating event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.debug("Running queue monitor")
            loop.run_until_complete(queue_monitor())
        except Exception as e:
            import traceback
            logger.error(f"Error in async worker: {e}\n{traceback.format_exc()}")
            logger.info("Detailed stack trace:", exc_info=True)
        finally:
            logger.info("Closing event loop")
            loop.close()

    def get_fq_names(self) -> list[str]:
        """
        Returns a list of fully qualified job names after ensuring the fq_name_map is loaded.

        Returns:
            list[str]: List of fully qualified job names from the fq_name_map

        Raises:
            TimeoutError: If waiting for jobs to be loaded exceeds timeout
        """
        self.logger.debug("Waiting for jobs to be loaded before returning job names")
        if not self._jobs_loaded.wait(timeout=self.JOB_MAP_LOAD_TIME):
            raise TimeoutError("Timed out waiting for jobs to be loaded")
        
        return list(self._fq_name_map.keys())

    def wait_for_completion(self, timeout=10, check_interval=0.1):
        """
        Periodically logs the status of task processing counters.
        Exits when all submitted tasks have been processed by worker processes.
        Note: This does not guarantee that post-processing (if any) is complete.
              `wait_for_completion` ensures all stages, including post-processing, are finished.

        Args:
            interval (float, optional): The polling interval in seconds. Defaults to 1.0.
            timeout (Optional[float], optional): Maximum time in seconds to poll. 
                                                 If None, polls indefinitely until completion or KeyboardInterrupt. 
                                                 Defaults to None.

        Raises:
            RuntimeError: If raise_on_error is True and there are errors, raises an exception
        """
        start_time = time.time()
        self.logger.info("Starting to poll for task processing updates...")
        try:
            while True:
                submitted = self.tasks_submitted.value
                in_progress = self.tasks_in_progress.value
                completed = self.tasks_completed.value
                post_processing = self.post_processing_tasks.value
                errors = self.job_errors.value # Get job_errors value

                self.logger.info(
                    f"Task Stats: \nErrors={errors}, Submitted={submitted}, In Progress={in_progress}, "
                    f"Completed={completed}, Post-Processing={post_processing}" # Added Errors to log
                )

                # Break if all submitted tasks are completed by workers OR if no tasks were submitted at all
                if (submitted > 0 and (completed + errors) >= submitted) or (submitted == 0 and time.time() - start_time > check_interval): 
                    if submitted == 0:
                        self.logger.info("No tasks were submitted. Completing poll early.")
                    else:
                        self.logger.info("All submitted tasks have been processed by workers.")
                        if self.on_complete:
                            # Log current post-processing status but don't wait here.
                            # wait_for_completion will ensure post-processing finishes.
                            self.logger.info(
                                f"Worker processing complete. Current post-processing: {post_processing}/{completed}. "
                                "Final post-processing will be handled by wait_for_completion."
                            )
                    break 
                
                # Break if timeout is reached
                if timeout is not None and (time.time() - start_time) > timeout:
                    self.logger.warning(f"Polling timed out after {timeout} seconds.")
                    break
                
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("Polling interrupted by user.")
        finally:
            errors = self.job_errors.value
            self.logger.info("Finished polling for updates.")
            
            # If raise_on_error is True and there are errors, raise an exception
            if self.get_raise_on_error() and errors > 0:
                raise RuntimeError(f"Flow execution completed with {errors} error(s). Check logs for details.")


    @classmethod
    def instance(cls, dsl=None, on_complete=None, serial_processing=False) -> 'FlowManagerMP':
        """
        Get or create the singleton instance of FlowManagerMP.
        
        Args:
            dsl: A dictionary of job DSLs, a job DSL, a JobABC instance, or a collection of JobABC instances.
            on_complete: Code to handle results after the Job executes its task.
            serial_processing: Forces on_complete to execute only after all tasks are completed.
            
        Returns:
            The singleton instance of FlowManagerMP
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    # Platform-specific multiprocessing initialization
                    import platform
                    if platform.system() == 'Windows':
                        # Windows-specific multiprocessing setup
                        freeze_support()  # Required for Windows support
                        try:
                            set_start_method('spawn')  # Windows only supports 'spawn'
                        except RuntimeError:
                            # If the start method is already set, this will raise a RuntimeError
                            # We can safely ignore it as the method is already configured
                            pass
                    # Create the singleton instance
                    cls._instance = cls(dsl, on_complete, serial_processing)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.
        
        This method clears the stored singleton instance, allowing a new instance to be created
        the next time instance() is called.
        """
        with cls._lock:
            if cls._instance is not None:
                # Ensure cleanup before resetting
                cls._instance._cleanup()
                cls._instance = None
