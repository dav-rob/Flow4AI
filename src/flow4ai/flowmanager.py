import asyncio
import threading
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Optional, Union

from . import JobABC
from . import f4a_logging as logging
from .dsl import DSLComponent, JobsDict
from .dsl_graph import PrecedenceGraph, dsl_to_precedence_graph
from .f4a_graph import validate_graph
from .job import SPLIT_STR, Task, job_graph_context_manager
from .job_loader import JobFactory


class FlowManager:
    _instance = None
    _lock = threading.Lock()  # Class-level lock for singleton creation

    def __new__(cls, *args, **kwargs):  # Accept arbitrary arguments
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False
        return cls._instance

    def __init__(self, file_config=False, on_complete: Optional[Callable[[Any], None]] = None):
        self.file_config = file_config
        self.on_complete = on_complete
        if not hasattr(self, '_TaskManager__initialized') or not self.__initialized:
            with self._lock:
                if not hasattr(self, '_TaskManager__initialized') or not self.__initialized:
                    self._initialize()
                    self.__initialized = True

    def _initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.job_map: Dict[str, JobABC] = {}
        self.head_jobs: List[JobABC] = []
        if self.file_config:
            self.head_jobs = JobFactory.get_head_jobs_from_config()
            self.job_map = {job.name: job for job in self.head_jobs}
        self.submitted_count = 0
        self.completed_count = 0
        self.error_count = 0
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
            
    def submit(self, task: Task, fq_name: str):
        # Check that job_map is not None or empty
        if not self.job_map:
            self.logger.error("job_map is None or empty")
            return
            
        # Get the JobABC instance from the job_map
        job_key = fq_name
        job = None
        
        # Find the job by matching the start of the name
        for key, j in self.job_map.items():
            if key.startswith(job_key):
                job = j
                break
                
        if job is None:
            self.logger.error(f"No job found for graph_name: {fq_name}")
            with self._data_lock:
                self.error_count += 1
                self.error_results[job_key].append({
                    "error": ValueError(f"No job found for graph_name: {fq_name}"),
                    "task": task
                })
            return

        with self._data_lock:
            self.submitted_count += 1

        coro = self._execute_with_context(job, task)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(
            lambda f: self._handle_completion(f, job, task)
        )

    def _handle_completion(self, future, job: JobABC, task: Task):
        result = None
        exception = None
        try:
            result = future.result()
            with self._data_lock:
                self.completed_count += 1
                self.completed_results[job.name].append(result)
                
            if self.on_complete:
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


    def add_dsl(self, dsl: DSLComponent, graph_name: str, variant: str = "") -> str:
        """
        Adds a graph to the task manager.
        
        Args:
            dsl: the dsl defining the data flow between jobs.
            jobs: A dictionary of jobs.
            graph_name: The name of the graph.
            variant: The variant of the graph e.g. "dev", "prod"
        
        Returns:
            str: The fully qualified name of the graph.
        """
        if not graph_name:
            raise ValueError("graph_name cannot be None or empty")
        if dsl is None:
            raise ValueError("graph cannot be None")
        graph, jobs = dsl_to_precedence_graph(dsl)
        return self.add_graph(graph, jobs, graph_name, variant)
        
    def add_dsl_dict(self, dsl_dict: Dict) -> List[str]:
        """
        Adds multiple graphs to the task manager from a dictionary structure.
        
        Args:
            dsl_dict: A dictionary containing graph definitions, with optional variants.
                Format can be either:
                {
                    "graph1": {
                        "dev": {
                            "dsl": dsl1d
                        },
                        "prod": {
                            "dsl": dsl1p
                        }
                    }
                }
                Or without variants:
                {
                    "graph1": {
                        "dsl": dsl1
                    },
                    "graph2": {
                        "dsl": dsl2
                    }
                }
        
        Returns:
            List[str]: The fully qualified names of all added graphs.
        
        Raises:
            ValueError: If the dictionary structure is invalid or missing required components.
        """
        if not dsl_dict:
            raise ValueError("dsl_dict cannot be None or empty")
        
        fq_names = []
        
        for graph_name, graph_data in dsl_dict.items():
            # Check if this is a variant structure or direct dsl/jobs
            if "dsl" in graph_data:
                # No variants, direct dsl/jobs
                dsl = graph_data.get("dsl")
                
                if dsl is None:
                    raise ValueError(f"Graph '{graph_name}' is missing required 'dsl' or 'jobs'")
                    
                fq_name = self.add_dsl(dsl, graph_name)
                fq_names.append(fq_name)
            else:
                # With variants
                for variant, variant_data in graph_data.items():
                    dsl = variant_data.get("dsl")
                    
                    if dsl is None:
                        raise ValueError(f"Graph '{graph_name}' variant '{variant}' is missing required 'dsl' or 'jobs'")
                        
                    fq_name = self.add_dsl(dsl, graph_name, variant)
                    fq_names.append(fq_name)
        
        return fq_names

    def add_graph(self, precedence_graph: PrecedenceGraph, jobs: JobsDict, graph_name: str, variant: str = "") -> str:
        """
        Adds a graph to the task manager.
        
        Args:
            precedence_graph: A precedence graph that defines the data flow between jobs.
            jobs: A dictionary of jobs.
            graph_name: The name of the graph.
            variant: The variant of the graph e.g. "dev", "pr
        
        Returns:
            str: The fully qualified name of the graph.
        """
        if not graph_name:
            raise ValueError("graph_name cannot be None or empty")
        if not jobs:
            raise ValueError("jobs cannot be None or empty")
        if precedence_graph is None:
            raise ValueError("precedence_graph cannot be None")
        validate_graph(precedence_graph)
        for (short_job_name, job) in jobs.items():
            job.name = JobABC.create_FQName(graph_name, variant, short_job_name)
        head_job: JobABC = JobFactory.create_job_graph(precedence_graph, jobs)
        self.head_jobs.append(head_job)
        self.job_map.update({job.name: job for job in self.head_jobs})
        return head_job.name



    def get_counts(self):
        with self._data_lock:
            return {
                'submitted': self.submitted_count,
                'completed': self.completed_count,
                'errors': self.error_count
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
            
    def wait_for_completion(self, timeout=10, check_interval=0.1):
        """
        Wait for all submitted tasks to complete or error out.
        
        Args:
            timeout: Maximum time to wait in seconds. Defaults to 10 seconds.
            check_interval: How often to check for completion in seconds. Defaults to 0.1 seconds.
            
        Returns:
            bool: True if all tasks completed or errored, False if timed out
        """
        import time
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            counts = self.get_counts()
            if counts['submitted'] > 0 and counts['submitted'] == (counts['completed'] + counts['errors']):
                return True
            time.sleep(check_interval)
            
        # Check one last time before returning
        counts = self.get_counts()
        return counts['submitted'] == (counts['completed'] + counts['errors'])
        
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
            fq_name = self.add_dsl(dsl, graph_name)
            
        if not fq_name:
            raise ValueError("Either provide both dsl and graph_name or an fq_name")
            
        self.submit(task, fq_name)
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
        
    # Methods to support a fluent interface
    
    def add_and_submit(self, dsl, task, graph_name="default_graph"):
        """
        Add a DSL component and submit a task in one step.
        
        Args:
            dsl: The DSL component defining the job graph
            task: Task dictionary to process
            graph_name: Name for the graph
            
        Returns:
            self for method chaining
        """
        fq_name = self.add_dsl(dsl, graph_name)
        self.submit(task, fq_name)
        return self
        
    def wait(self, timeout=10):
        """
        Wait for completion and check for success.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            self for method chaining
            
        Raises:
            TimeoutError: If tasks don't complete within the timeout period
        """
        success = self.wait_for_completion(timeout=timeout)
        if not success:
            raise TimeoutError(f"Timed out waiting for tasks to complete after {timeout} seconds")
        return self

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
