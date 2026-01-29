import asyncio
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

from flow4ai import f4a_logging as logging
from flow4ai.flowmanager_base import FlowManagerABC
from flow4ai.job import SPLIT_STR, JobABC, Task, job_graph_context_manager
from flow4ai.job_loader import JobFactory


class FlowManager(FlowManagerABC):
    _lock = threading.Lock()  # Lock for thread-safe initialization
    _instance = None  # Singleton instance
    
    def __init__(self, dsl=None, jobs_dir_mode=False, on_complete: Optional[Callable[[Any], None]] = None):
        """Initialize the FlowManager.
        
        Args:
            dsl: A dictionary of job DSLs, a job DSL, a JobABC instance, or a collection of JobABC instances.
            jobs_dir_mode: If True, the FlowManager will load jobs from a directory.
            on_complete: A callback function to be called when a job is completed.
        """
        super().__init__()
        self.jobs_dir_mode = jobs_dir_mode
        self.on_complete = on_complete
        self._initialize()
        
        # Add DSL dictionary if provided
        if dsl:
            self.create_job_graph_map(dsl)

    def _initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.head_jobs: List[JobABC] = []
        if self.jobs_dir_mode:
            self.head_jobs = JobFactory.get_head_jobs_from_config()
            self.job_graph_map = {job.name: job for job in self.head_jobs}
        self.submitted_count = 0
        self.completed_count = 0
        self.error_count = 0
        self.post_processing_count = 0
        self.completed_results = defaultdict(list)
        self.error_results = defaultdict(list)

        self._data_lock = threading.Lock()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _execute_with_context(self, job: JobABC, task: Task):
        """Execute a job with the job graph context manager.
        
        This ensures that the local async context variables are reset for each
        coroutine that is executed.

        Args:
            job: The job to execute
            task: The task to process
            
        Returns:
            The result of the job execution
        """
        # Create a job set for this job
        job_set = JobABC.job_set(job)
        
        # Execute the job within the context manager
        async with job_graph_context_manager(job_set):
            return await job._execute(task)
    

    def submit_task(self, task: Union[Dict[str, Any], List[Dict[str, Any]], str], fq_name: str = None):
        fq_name = self.check_fq_name_and_job_graph_map(fq_name)

        # Handle single task or list of tasks
        if isinstance(task, list):
            for single_task in task:
                self._submit_single_task(single_task, fq_name)
        else:
            self._submit_single_task(task, fq_name)

    def _submit_single_task(self, task: Dict[str, Any], fq_name: str):
        """Helper method to submit a single task to the job.
        
        Args:
            task: The task to submit
            fq_name: The fully qualified name of the job graph
        """
        with self._data_lock:
            self.submitted_count += 1
        if not isinstance(task, dict):
            task = {'task': str(task)}
        task_obj = Task(task, fq_name)
        job = self.job_graph_map.get(task_obj.get_fq_name())
        if job is None:
            raise ValueError(f"Job not found for fq_name: {task_obj.get_fq_name()}")
        coro = self._execute_with_context(job, task_obj)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(
            lambda f: self._handle_completion(f, job, task_obj)
        )

    def _handle_completion(self, future, job: JobABC, task: Task):
        result = None
        exception = None
        try:
            result = future.result()
            with self._data_lock:
                self.completed_count += 1
                # job.name is fq_name
                self.completed_results[job.name].append(result)
                
            if self.on_complete:
                with self._data_lock:
                    self.post_processing_count += 1
                #try: don't catch the exception let it bubble up
                self.on_complete(result)
       
        except Exception as e:
            exception = e
            self.logger.error(f"Error processing result: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)
            with self._data_lock:
                self.error_count += 1
                self.error_results[job.name].append({
                    "error": e,
                    "task": task
                })

    def get_fq_names_by_graph(self, graph_name, variant=""):
        """
        Get the fully qualified names for a specific graph and variant.
        
        This handles cases where multiple DSLs with the same structure 
        might have been added with the same graph_name and variant, 
        but received different FQ names due to collision handling.
        
        Args:
            graph_name: The name of the graph
            variant: The variant name, defaults to empty string
            
        Returns:
            The list of matching fully qualified names, or empty list if none found
        """
        matching_names = []
        base_prefix = f"{graph_name}{SPLIT_STR}{variant}"
        
        # Import re for regex pattern matching
        import re

        # Find exact match first
        for job_name in self.job_graph_map.keys():
            if job_name.startswith(base_prefix + SPLIT_STR):
                matching_names.append(job_name)
                
        # Also look for variants with numeric suffixes (added by collision handling)
        pattern = re.compile(re.escape(graph_name + SPLIT_STR) + 
                           re.escape(variant) + r'_\d+' + 
                           re.escape(SPLIT_STR))
        
        for job_name in self.job_graph_map.keys():
            if pattern.match(job_name):
                # Only add if not already added (could happen if exact match already found)
                if job_name not in matching_names:
                    matching_names.append(job_name)
                    
        return matching_names
    
    def submit_short(self, task: Union[Dict[str, Any], List[Dict[str, Any]], str], graph_name, variant=""):
        """
        Submit task(s) using just the short graph name (e.g. RAG), plus the variant name (e.g. pinecone or chromaDB) if needed, 
        rather than the fully qualified job name.
        
        Args:
            task: The task or list of tasks to submit 
            graph_name: The name of the graph (e.g. RAG)
            variant: The variant name, defaults to empty string (e.g. pinecone or chromaDB) 
            
        Returns:
            None
            
        Raises:
            ValueError: If no matching graph is found or if multiple matches found
        """
        matching_fq_names = self.get_fq_names_by_graph(graph_name, variant)
        
        if not matching_fq_names:
            error_msg = f"No graph found with name '{graph_name}' and variant '{variant}'"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if len(matching_fq_names) > 1:
            # If multiple matches, log them all and raise an error
            self.logger.error(f"Multiple matching graphs found for '{graph_name}' variant '{variant}': {matching_fq_names}")
            error_msg = (f"Multiple matching graphs found. Please use submit() with the specific FQ name "
                        f"from these options: {matching_fq_names}")
            raise ValueError(error_msg)
        
        # If exactly one match, use it
        fq_name = matching_fq_names[0]
        return self.submit_task(task, fq_name)

    def get_counts(self):
        with self._data_lock:
            return {
                'submitted': self.submitted_count,
                'completed': self.completed_count,
                'errors': self.error_count,
                'post_processing': self.post_processing_count
            }

    def pop_results(self):
        with self._data_lock:
            completed = dict(self.completed_results)
            errors = dict(self.error_results)
            self.completed_results.clear()
            self.error_results.clear()
            return {
                'completed': completed,
                'errors': errors
            }
            
    def wait_for_completion(self, timeout=10, check_interval=0.1, log_interval=1.0):
        """
        Wait for all submitted tasks to complete or error out.
        
        Args:
            timeout: Maximum time to wait in seconds. Defaults to 10 seconds.
            check_interval: How often to check for completion in seconds. Defaults to 0.1 seconds.
            log_interval: How often to log status updates in seconds. Defaults to 1.0 seconds.
            
        Returns:
            bool: True if all tasks completed or errored, False if timed out
        """
        
        start_time = time.time()
        last_log_time = start_time
        
        while (time.time() - start_time) < timeout:
            counts = self.get_counts()
            
            # Throttle logging - only log every log_interval seconds
            current_time = time.time()
            if current_time - last_log_time >= log_interval:
                self.logger.info(f"Task Stats:\nErrors: {counts['errors']}, Submitted: {counts['submitted']}, Completed: {counts['completed']}, Post-processing: {counts['post_processing']}")
                last_log_time = current_time
            
            # Return immediately if all tasks are complete or if there are no tasks at all
            if counts['submitted'] == 0 or counts['submitted'] == (counts['completed'] + counts['errors']):
                return True
            time.sleep(check_interval)
            
        # Check one last time before returning
        counts = self.get_counts()
        completion_status = counts['submitted'] == (counts['completed'] + counts['errors'])
        
        # If raise_on_error is True and there are errors, raise an exception
        if self.get_raise_on_error() and counts['errors'] > 0:
            raise RuntimeError(f"Flow execution completed with {counts['errors']} error(s). Check logs for details.")
            
        return completion_status
        
    def execute(self, task, dsl=None, graph_name=None, fq_name=None, timeout=10):
        """
        Simplified execution method that handles the entire workflow.
        
        Args:
            task: The task to process
            dsl: Optional DSL component (if not using an existing graph)
            graph_name: Name for the graph if providing a DSL
            fq_name: Fully qualified name for an existing graph
            timeout: Maximum time to wait for completion
            
        Returns:
            A tuple of (errors, result) where errors is a list of error dictionaries and
            result is the result dictionary of the completed job(s)
        
        Raises:
            ValueError: If required parameters are missing
            TimeoutError: If tasks don't complete within the timeout period
            Exception: If any errors occurred during execution
        """
        if dsl and graph_name:
            fq_name = self.add_workflow(dsl, graph_name)
            
        if not fq_name:
            raise ValueError("Either provide both dsl and graph_name or an fq_name")
            
        self.submit_task(task, fq_name)
        success = self.wait_for_completion(timeout=timeout)
        
        if not success:
            raise TimeoutError(f"Timed out waiting for tasks to complete after {timeout} seconds")
            
        results = self.pop_results()
        
        # Check for errors and raise if present
        if results["errors"]:
            error_messages = []
            for job_name, job_errors in results["errors"].items():
                for error_data in job_errors:
                    error_msg = f"{job_name}: {error_data['error']}"
                    error_messages.append(error_msg)
            
            raise Exception("Errors occurred during job execution:\n" + "\n".join(error_messages))
            
        # Extract the result directly using the known fq_name
        result = None
        if results["completed"] and fq_name in results["completed"] and results["completed"][fq_name]:
            result = results["completed"][fq_name][0]
            
        return (results["errors"], result)
        
    def get_result(self, results=None, job_name_filter=None):
        """
        Extract a specific result from the completed results.
        
        Args:
            results: Results dictionary from pop_results() or None to use latest results
            job_name_filter: Optional string to filter job names (e.g., "add" to match jobs containing "add")
            
        Returns:
            The result data dictionary for the matched job, or None if not found
        """
        if results is None:
            results = self.pop_results()
            
        # Simple implementation - just find the job with the matching name
        for job_name, job_results in results["completed"].items():
            if job_name_filter is None or job_name_filter in job_name:
                if job_results:  # Make sure there's at least one result
                    return job_results[0]
        return None
        
    def get_result_value(self, results=None, job_name_filter=None):
        """
        Extract just the result value from a specific job result.
        
        Args:
            results: Results dictionary from pop_results() or None to use latest results
            job_name_filter: Optional string to filter job names
            
        Returns:
            The value of the "result" key for the matched job, or None if not found
        """
        result = self.get_result(results, job_name_filter)
        if result and "result" in result:
            return result["result"]
        return None
        
    def get_result_by_graph_name(self, graph_name, results=None):
        """
        Get the result dictionary for a specific graph by name.
        
        This simplifies result extraction by handling the lookup of the fully qualified name.
        Note: This method is primarily for backward compatibility - new code should use execute
        which directly returns the result.
        
        Args:
            graph_name: The graph name used when adding the DSL or executing the task
            results: Results dictionary from pop_results() or None to use latest results
            
        Returns:
            The result dictionary for the matched graph, or None if not found
        """
        if results is None:
            results = self.pop_results()
            
        # Find the fully qualified name based on the graph name
        fq_name = None
        for key in results["completed"].keys():
            if graph_name in key:
                fq_name = key
                break
                
        if fq_name is None:
            return None
            
        # Get the result dictionary
        if results["completed"][fq_name]:
            return results["completed"][fq_name][0]
            
        return None
        
    def get_fq_names(self):
        """
        Returns a list of all fully qualified names of graphs added to the FlowManager.
        
        Returns:
            List[str]: List of fully qualified names
        """
        return [job.name for job in self.head_jobs]

    @classmethod
    def run(cls, dsl, task, graph_name="default_graph", timeout=10):
        """
        Static helper method for one-line execution of a DSL graph with a task.
        
        Args:
            dsl: The DSL component defining the job graph
            task: Task dictionary to process
            graph_name: Name for the graph
            timeout: Maximum time to wait for completion
            
        Returns:
            A tuple of (errors, result) where errors is a list of error dictionaries and
            result is the result dictionary of the completed job(s)
        
        Raises:
            TimeoutError: If tasks don't complete within the timeout period
            Exception: If any errors occurred during execution
        """
        tm = cls()
        return tm.execute(task, dsl=dsl, graph_name=graph_name, timeout=timeout)

    def display_results(self, results=None):
        """
        Display results in a Jupyter/Colab-friendly format with rich formatting.
        
        Args:
            results: Results dictionary from pop_results() or None to use latest results
            
        Returns:
            The results dictionary for chaining
        """
        try:
            from IPython.display import HTML, Markdown, display
            jupyter_available = True
        except ImportError:
            jupyter_available = False
            
        if results is None:
            results = self.pop_results()
        
        if jupyter_available:
            # Display in rich Jupyter format
            if results["completed"]:
                display(Markdown("## Completed Tasks"))
                for job_name, job_results in results["completed"].items():
                    display(Markdown(f"### {job_name}"))
                    for result_data in job_results:
                        display(result_data["result"])
            
            if results["errors"]:
                display(Markdown("## Errors"))
                for job_name, job_errors in results["errors"].items():
                    display(Markdown(f"### {job_name}"))
                    for error_data in job_errors:
                        display(HTML(f"<div style='color:red'>{error_data['error']}</div>"))
        else:
            # Fallback to plain text output
            if results["completed"]:
                print("\nCompleted tasks:")
                for job_name, job_results in results["completed"].items():
                    for result_data in job_results:
                        print(f"- {job_name}: {result_data['result']}")
            
            if results["errors"]:
                print("\nErrors:")
                for job_name, job_errors in results["errors"].items():
                    for error_data in job_errors:
                        print(f"- {job_name}: {error_data['error']}")
        
        return results
    @classmethod
    def instance(cls, dsl=None, jobs_dir_mode=False, on_complete: Optional[Callable[[Any], None]] = None) -> 'FlowManager':
        """Get or create the singleton instance of FlowManager.
        
        Args:
            dsl: A dictionary of job DSLs, a job DSL, a JobABC instance, or a collection of JobABC instances.
            jobs_dir_mode: If True, the FlowManager will load jobs from a directory.
            on_complete: A callback function to be called when a job is completed.
            
        Returns:
            The singleton instance of FlowManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(dsl, jobs_dir_mode, on_complete)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance.
        
        This method clears the stored singleton instance, allowing a new instance to be created
        the next time instance() is called.
        """
        with cls._lock:
            cls._instance = None