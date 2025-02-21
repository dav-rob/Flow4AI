import asyncio
# In theory it makes sense to use dill with the "multiprocess" package
# instead of pickle with "multiprocessing", but in practice it leads to 
# performance and stability issues.
import multiprocessing as mp
import pickle
import queue
from collections import OrderedDict
from multiprocessing import freeze_support, set_start_method
from typing import Any, Callable, Collection, Dict, Optional, Union

from . import jc_logging as logging
from .job import JobABC, SimpleJobFactory, Task, job_graph_context_manager
from .job_loader import ConfigLoader, JobFactory
from .utils.monitor_utils import should_log_task_stats
from .utils.print_utils import printh
from pydantic import BaseModel

class JobChain:
    """
    JobChain executes up to thousands of tasks in parallel using one or more Jobs passed into constructor.
    Optionally passes results to a pre-existing result processing function after task completion.

    Args:
        job (Union[Dict[str, Any], JobABC, Collection[JobABC]]): If missing, jobs will be loaded from config file.
            Otherwise either a dictionary containing job configuration,
            a single JobABC instance, or a collection of JobABC instances.

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
    # Constants
    JOB_MAP_LOAD_TIME = 5  # Timeout in seconds for job map loading

    def __init__(self, job: Optional[Any] = None, result_processing_function: Optional[Callable[[Any], None]] = None, 
                 serial_processing: bool = False):
        # Get logger for JobChain
        self.logger = logging.getLogger('JobChain')
        self.logger.info("Initializing JobChain")
        if not serial_processing and result_processing_function:
            self._check_picklable(result_processing_function)
        # tasks are created by submit_task(), with ["job_name"] added to the task dict
        # tasks are then sent to queue for processing
        self._task_queue: mp.Queue[Task] = mp.Queue()  
        # INTERNAL USE ONLY. DO NOT ACCESS DIRECTLY.
        # This queue is for internal communication between the job executor and result processor.
        # To process results, use the result_processing_function parameter in the JobChain constructor.
        # See test_result_processing.py for examples of proper result handling.
        self._result_queue = mp.Queue()  # type: mp.Queue
        self.job_executor_process = None
        self.result_processor_process = None
        self._result_processing_function = result_processing_function
        self._serial_processing = serial_processing
        # This holds a map of job name to job, 
        # when _execute is called on the job, the task must have a job_name
        # associated with it, if there is more than one job in the job_map
        self.job_map: OrderedDict[str, JobABC] = OrderedDict()
        
        # Create a manager for sharing objects between processes
        self._manager = mp.Manager()
        # Create a shared dictionary for job name mapping
        self._job_name_map = self._manager.dict()
        # Create an event to signal when jobs are loaded
        self._jobs_loaded = mp.Event()

        if job:
            self.create_job_map(job)
        
        self._start()

    def create_job_map(self, job):
        if isinstance(job, Dict):
            job_context: Dict[str, Any] = job.get("job_context") or {}
            loaded_job = SimpleJobFactory.load_job(job_context)
            if isinstance(loaded_job, JobABC):
                self.job_map[loaded_job.name] = loaded_job
        elif isinstance(job, JobABC):
            self.job_map[job.name] = job
        elif isinstance(job, Collection) and not isinstance(job, (str, bytes, bytearray)):
            if not job:  # Check if collection is empty
                raise ValueError("Job collection cannot be empty")
            if not all(isinstance(j, JobABC) for j in job):
                raise TypeError("All items in job collection must be JobABC instances")
            for j in job:
                if isinstance(j, JobABC):
                    if j.name in self.job_map:
                        raise ValueError(f"Duplicate job name found: {j.name}")
                    self.job_map[j.name] = j
                else:
                    raise TypeError("Items in job collection must be JobABC instances")
        else:
            raise TypeError("job must be either Dict[str, Any], JobABC instance, or Collection[JobABC]")

        self._job_name_map.clear()
        self._job_name_map.update({job.name: job.job_set_str() for job in self.job_map.values()})

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
                self.logger.debug("Terminating job executor process")
                self.job_executor_process.terminate()
                self.logger.debug("Joining job executor process")
                self.job_executor_process.join()
                self.logger.debug("Job executor process joined")
        
        if self.result_processor_process:
            if self.result_processor_process.is_alive():
                self.logger.debug("Terminating result processor process")
                self.result_processor_process.terminate()
                self.logger.debug("Joining result processor process")
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
            args=(self.job_map, self._task_queue, self._result_queue, self._job_name_map, self._jobs_loaded, ConfigLoader.directories),
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
    # TODO: add resource usage monitoring which returns False if resource use is too high.
    def submit_task(self, task: Union[Dict[str, Any], str], job_name: Optional[str] = None):
        """
        Submit a task to be processed by the job.

        Args:
            task: Either a dictionary containing task data or a string that will be converted to a task.
                    if this is None then the task will be skipped.
            job_name: The name of the job to execute this task. Required if there is more than one job in the job_map,
                     unless the task is a dictionary that includes a 'job_name' key.

        Raises:
            ValueError: If job_name is required but not provided, or if the specified job cannot be found.
            TypeError: If the task is not a dictionary or string.
        """
        try:
            # Wait for jobs to be loaded
            if not self._jobs_loaded.wait(timeout=self.JOB_MAP_LOAD_TIME):
                raise TimeoutError("Timed out waiting for jobs to be loaded")

            if task is None:
                self.logger.warning("Received None task, skipping")
                return
            
            if isinstance(task, str):
                task_dict = {'task': task}
            elif isinstance(task, dict):
                task_dict = task.copy()
            else:
                self.logger.warning(f"Received invalid task type {type(task)}, converting to string")
                task_dict = {'task': str(task)}

            # If job_name parameter is provided, it takes precedence
            if job_name is not None:
                if job_name not in self._job_name_map:
                    raise ValueError(
                        f"Job '{job_name}' not found. Available jobs: {list(self._job_name_map.keys())}"
                    )
                task_dict['job_name'] = job_name
            
            # If there's more than one job, we need a valid job name
            if len(self._job_name_map) > 1:
                if 'job_name' not in task_dict or not isinstance(task_dict['job_name'], str) or not task_dict['job_name']:
                    raise ValueError(
                        "When multiple jobs are present, you must either:\n"
                        "1) Provide the job_name parameter in submit_task() OR\n"
                        "2) Include a non-empty string 'job_name' in the task dictionary"
                    )
                if task_dict['job_name'] not in self._job_name_map:
                    raise ValueError(
                        f"Job '{task_dict['job_name']}' not found. Available jobs: {list(self._job_name_map.keys())}"
                    )
            elif len(self._job_name_map) == 1:
                # If there's only one job, use its name
                task_dict['job_name'] = next(iter(self._job_name_map.keys()))
            else:
                raise ValueError("No jobs available in JobChain")

            task_obj = Task(task_dict)
            self._task_queue.put(task_obj)
        except Exception as e:
            self.logger.error(f"Error submitting task: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)

    def mark_input_completed(self):
        """Signal completion of input and wait for all processes to finish and shut down."""
        self.logger.debug("Marking input as completed")
        self.logger.info("*** task_queue ended ***")
        self._task_queue.put(None)
        self._wait_for_completion()

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    # TODO: it may be necessary to put a flag to execute this using asyncio event loops
    #          for example, when handing off to an async web service
    @staticmethod
    def _result_processor(process_fn: Callable[[Any], None], result_queue: 'mp.Queue'):
        """Process that handles processing results as they arrive."""
        logger = logging.getLogger('ResultProcessor')
        logger.debug("Starting result processor")

        while True:
            try:
                result = result_queue.get()
                if result is None:
                    logger.debug("Received completion signal from result queue")
                    break
                logger.debug(f"ResultProcessor received result: {result}")
                try:
                    # Handle both dictionary and non-dictionary results
                    task_id = result.get('task', str(result)) if isinstance(result, dict) else str(result)
                    logger.debug(f"Processing result for task {task_id}")
                    process_fn(result)
                    logger.debug(f"Finished processing result for task {task_id}")
                except Exception as e:
                    logger.error(f"Error processing result: {e}")
                    logger.info("Detailed stack trace:", exc_info=True)
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
        logger = logging.getLogger('JobChain')
        logger.debug(f'Processing data type: {type(data)}')

        if isinstance(data, dict):
            return {k: JobChain._replace_pydantic_models(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [JobChain._replace_pydantic_models(item) for item in data]
        elif isinstance(data, BaseModel):
            logger.info(f'Converting pydantic model {data.__class__.__name__}')
            return data.model_dump_json()
        return data

    # Must be static because it's passed as a target to multiprocessing.Process
    # Instance methods can't be pickled properly for multiprocessing
    @staticmethod
    def _async_worker(job_map: Dict[str, JobABC], task_queue: 'mp.Queue', result_queue: 'mp.Queue', 
                     job_name_map: 'mp.managers.DictProxy', jobs_loaded: 'mp.Event', 
                     directories: list[str] = []):
        """Process that handles making workflow calls using asyncio."""
        # Get logger for AsyncWorker
        logger = logging.getLogger('AsyncWorker')
        logger.debug("Starting async worker")

        # If job_map is empty, create it from SimpleJobLoader
        if not job_map:
            # logger.info("Creating job map from SimpleJobLoader")
            # job = SimpleJobFactory.load_job({"type": "file", "params": {}})
            # job_map = {job.name: job}
            logger.info("Creating job map from JobLoader")
            logger.info(f"Using directories from process: {directories}")
            ConfigLoader._set_directories(directories)
            ConfigLoader.reload_configs()
            head_jobs = JobFactory.get_head_jobs_from_config()
            job_map = {job.name: job for job in head_jobs}
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
                if len(job_map) == 1:
                    job = next(iter(job_map.values()))
                else:
                    # Otherwise, get the job from the map using job_name
                    job_name = task.get('job_name')
                    if not job_name:
                        raise ValueError("Task missing job_name when multiple jobs are present")
                    job = job_map[job_name]
                job_set = JobABC.job_set(job) #TODO: create a map of job to jobset in _async_worker
                async with job_graph_context_manager(job_set):
                    result = await job._execute(task)
                    processed_result = JobChain._replace_pydantic_models(result)
                    logger.info(f"[TASK_TRACK] Completed task {task_id}, returned by job {processed_result[JobABC.RETURN_JOB]}")

                    result_queue.put(processed_result)
                    logger.debug(f"[TASK_TRACK] Result queued for task {task_id}")
            except Exception as e:
                logger.error(f"[TASK_TRACK] Failed task {task_id}: {e}")
                logger.info("Detailed stack trace:", exc_info=True)
                raise

        async def queue_monitor():
            """Monitor the task queue and create tasks as they arrive"""
            logger.debug("Starting queue monitor")
            tasks = set()
            pending_tasks = []
            tasks_created = 0
            tasks_completed = 0
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
                    tasks_completed += len(done_tasks)
                    logger.debug(f"Cleaned up {len(done_tasks)} completed tasks. Total completed: {tasks_completed}")
                    logger.debug(f"Active tasks remaining: {len(tasks)}")
                tasks.difference_update(done_tasks)

                # Log task stats periodically
                if tasks_completed != 0 and tasks_completed % 5 == 0:
                    if should_log_task_stats(queue_monitor, tasks_created, tasks_completed):
                        logger.info(f"Tasks stats - Created: {tasks_created}, Completed: {tasks_completed}, Active: {len(tasks)}")

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

    def get_job_names(self) -> list[str]:
        """
        Returns a list of job names after ensuring the job_name_map is loaded.

        Returns:
            list[str]: List of job names from the job_name_map

        Raises:
            TimeoutError: If waiting for jobs to be loaded exceeds timeout
        """
        self.logger.debug("Waiting for jobs to be loaded before returning job names")
        if not self._jobs_loaded.wait(timeout=self.JOB_MAP_LOAD_TIME):
            raise TimeoutError("Timed out waiting for jobs to be loaded")
        
        return list(self._job_name_map.keys())

    def get_job_graph_mapping(self) -> dict[str, set[str]]:
        """
        Returns a mapping of head job names to their complete set of job names in their graph.
        
        Returns:
            dict[str, set[str]]: Dictionary mapping each head job name to a set of all job names
                                reachable from that job (including itself).

        Raises:
            TimeoutError: If waiting for jobs to be loaded exceeds timeout
        """
        self.logger.debug("Waiting for jobs to be loaded before returning job graph mapping")
        if not self._jobs_loaded.wait(timeout=self.JOB_MAP_LOAD_TIME):
            raise TimeoutError("Timed out waiting for jobs to be loaded")
        
        return dict(self._job_name_map)

class JobChainFactory:
    _instance = None
    _job_chain = None

    def __init__(self, *args, **kwargs):
        if not JobChainFactory._instance:
            self._job_chain = JobChain(*args, **kwargs)
            JobChainFactory._instance = self

    @classmethod
    def init(cls, start_method="spawn", *args, **kwargs):
      """
      Initializes the JobChainFactory using the given start method.
      args and kwargs are passed down to the JobChain constructor.

      Args:
        start_method: The start method of multiprocessing. Defaults to "spawn".
        args: The parameters to be passed to the JobChain's constructor
        kwargs: The keyword parameters to be passed to the JobChain's constructor
        
      """
      freeze_support()
      set_start_method(start_method)
      if not cls._instance:
        cls._instance = cls(*args, **kwargs)
      return cls._instance

    @staticmethod
    def get_instance()->JobChain:
        if not JobChainFactory._instance:
            raise RuntimeError("JobChainFactory not initialized")
        return JobChainFactory._instance._job_chain
