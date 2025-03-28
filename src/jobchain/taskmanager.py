import asyncio
import threading
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Union

import jobchain.jc_logging as logging
from jobchain.dsl_graph import PrecedenceGraph, dsl_to_precedence_graph
from jobchain.jc_graph import validate_graph

from . import JobABC
from .dsl import DSLComponent, JobsDict
from .job import SPLIT_STR, Task, job_graph_context_manager
from .job_loader import JobFactory


class TaskManager:
    _instance = None
    _lock = threading.Lock()  # Class-level lock for singleton creation

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False
        return cls._instance

    def __init__(self, file_config=False):
        self.file_config = file_config
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
        
        This ensures that the job execution happens within the proper context for job graph execution.
        
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

        try:
            # Execute the job with context manager instead of directly calling _execute
            coro = self._execute_with_context(job, task)
        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)
            with self._data_lock:
                self.error_count += 1
                self.error_results[job.name].append({
                    "error": e,
                    "task": task
                })
            return

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(
            lambda f: self._handle_completion(f, job, task)
        )

    def _handle_completion(self, future, job: JobABC, task: Task):
        try:
            result = future.result()
            with self._data_lock:
                self.completed_count += 1
                self.completed_results[job.name].append({
                    "result": result,
                    "task": task
                })
        except Exception as e:
            self.logger.error(f"Error processing result: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)
            with self._data_lock:
                self.error_count += 1
                self.error_results[job.name].append({
                    "error": e,
                    "task": task
                })
    
    def add_dsl(self, dsl: DSLComponent, jobs: JobsDict, graph_name: str, variant: str = "") -> str:
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
        if not jobs:
            raise ValueError("jobs cannot be None or empty")
        precedence_graph: PrecedenceGraph = dsl_to_precedence_graph(dsl)
        return self.add_graph(precedence_graph, jobs, graph_name, variant)
        
    def add_dsl_dict(self, dsl_dict: Dict) -> List[str]:
        """
        Adds multiple graphs to the task manager from a dictionary structure.
        
        Args:
            dsl_dict: A dictionary containing graph definitions, with optional variants.
                Format can be either:
                {
                    "graph1": {
                        "dev": {
                            "dsl": dsl1d,
                            "jobs": jobs1d
                        },
                        "prod": {
                            "dsl": dsl1p,
                            "jobs": jobs1p
                        }
                    }
                }
                Or without variants:
                {
                    "graph1": {
                        "dsl": dsl1,
                        "jobs": jobs1
                    },
                    "graph2": {
                        "dsl": dsl2,
                        "jobs": jobs2
                    }
                }
        
        Returns:
            List[str]: The fully qualified names of all added graphs.
        
        Raises:
            ValueError: If the dictionary structure is invalid or missing required components.
        """
        if not dsl_dict:
            raise ValueError("dsl_dict cannot be None or empty")
        
        result = []
        
        for graph_name, graph_data in dsl_dict.items():
            # Check if this is a variant structure or direct dsl/jobs
            if "dsl" in graph_data and "jobs" in graph_data:
                # No variants, direct dsl/jobs
                dsl = graph_data.get("dsl")
                jobs = graph_data.get("jobs")
                
                if dsl is None or not jobs:
                    raise ValueError(f"Graph '{graph_name}' is missing required 'dsl' or 'jobs'")
                    
                graph_id = self.add_dsl(dsl, jobs, graph_name)
                result.append(graph_id)
            else:
                # With variants
                for variant, variant_data in graph_data.items():
                    dsl = variant_data.get("dsl")
                    jobs = variant_data.get("jobs")
                    
                    if dsl is None or not jobs:
                        raise ValueError(f"Graph '{graph_name}' variant '{variant}' is missing required 'dsl' or 'jobs'")
                        
                    graph_id = self.add_dsl(dsl, jobs, graph_name, variant)
                    result.append(graph_id)
        
        return result

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

