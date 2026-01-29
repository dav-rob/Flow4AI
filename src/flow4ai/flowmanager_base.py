"""
Base class for Flow Manager implementations.

This module provides the abstract base class that defines the common interface
for all Flow Manager implementations in the Flow4AI framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Collection, Dict, List, Union

from .dsl import DSLComponent, JobsDict
from .dsl_graph import PrecedenceGraph, dsl_to_precedence_graph
from .f4a_graph import validate_graph
from .job import SPLIT_STR, JobABC
from .job_loader import JobFactory


class FlowManagerABC(ABC):
    """
    Abstract base class for Flow Manager implementations.
    
    FlowManagerABC defines the minimal common interface for all Flow Manager implementations.
    Since FlowManager and FlowManagerMP were developed independently with different interfaces,
    this base class focuses on the core conceptual similarities rather than enforcing identical
    method signatures.
    """
    
    # Class variable for controlling error handling behavior
    RAISE_ON_ERROR = False
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Initialize the FlowManager instance.
        
        Each implementation should handle its own initialization with appropriate parameters.
        """
        self.job_graph_map: Dict[str, JobABC] = {}
        self.head_jobs: List[JobABC] = []
        
    def get_head_jobs(self) -> List[JobABC]:
        """
        Get all head jobs in the job graph.
        
        Head jobs are the entry points of the job graph with no predecessors.
        
        Returns:
            List[JobABC]: A list of all head jobs in the job graph
        """
        return self.head_jobs

    @abstractmethod
    def _submit_single_task(self, task: Union[Dict[str, Any], str], fq_name: str) -> None:
        """
        Process and submit a single task to be executed by the job graph. Must be implemented by subclasses.
        
        This is an internal method that handles the submission of a single task. It should:
        1. Convert the dict or string to a Task object if it isn't already one
        2. Validate that the specified job graph exists
        3. Submit the task for execution according to the implementation's concurrency model
        
        Args:
            task: The task to process, either as a dictionary or string. If a string is provided,
                 it will be wrapped in a dictionary with the key 'task'.
            fq_name: The fully qualified name of the job graph to execute the task against.
                   
        Returns:
            None
            
        Raises:
            ValueError: If the specified job graph cannot be found for the given fq_name.
        """
        pass
        
    @abstractmethod
    def submit_task(self, task: Union[Dict[str, Any], List[Dict[str, Any]]], fq_name: str = None) -> None:
        """
        Submit a task or list of tasks to be processed by the job graph. Must be implemented by subclasses.
        
        Args:
            task: A single task dictionary or a list of task dictionaries to be processed.
                  Each task should contain the necessary input data for the job graph.
                  Optionally, each task dict can contain a "fq_name" key to specify the job graph 
                  to execute the task against, if not provided, the fq_name param will be used.
            fq_name: The fully qualified name of the job graph to execute the task(s) against.
                   If not provided and there is only one job graph, it will be used automatically.
                   Required if multiple job graphs are registered.
                   
        Returns:
            None
            
        Raises:
            ValueError: If fq_name is required but not provided, or if the specified job graph cannot be found.
        """
        pass

    def create_graph_name(self, graph: Dict[str, Dict[str, List[str]]]) -> str:
        """
        Create a default graph name based on head jobs in the graph.
        Head jobs are jobs with no predecessors.

        Args:
            graph: The precedence graph structure

        Returns:
            str: A suitable graph name
        """
        # Find all jobs that are referenced as successors
        all_jobs = set(graph.keys())
        successor_jobs = set()
        for job, details in graph.items():
            successor_jobs.update(details['next'])

        # Head jobs are those not present in any 'next' list
        head_jobs = all_jobs - successor_jobs

        if head_jobs:
            # Use the first head job name
            return next(iter(sorted(head_jobs)))  # Sort for deterministic behavior
        else:
            # Fallback to the first job in the graph if no clear head job
            return next(iter(sorted(graph.keys())))

    def get_raise_on_error(self) -> bool:
        """
        Get the current raise_on_error setting.
        
        Returns:
            bool: True if errors should be raised during execution, False if errors should be captured
        """
        return self.__class__.RAISE_ON_ERROR
        
    def set_raise_on_error(self, value: bool) -> None:
        """
        Set the raise_on_error setting.
        
        Args:
            value: True to raise errors during execution, False to capture errors
        """
        self.__class__.RAISE_ON_ERROR = value
        
    def add_workflow(self, workflow: DSLComponent, graph_name: str = "", variant: str = "") -> str:
        """
        Add a workflow to the FlowManager.
        
        A workflow is a graph of connected jobs that defines your processing pipeline.
        Each workflow should only be added once as it is modified during processing.

        Args:
            workflow: The workflow (DSL component) defining the data flow between jobs.
                This will be modified by being converted to a precedence graph.
            graph_name: The name of the graph. Used to generate fully qualified job names.
                If empty, a name will be automatically generated based on head jobs.
            variant: The variant of the graph e.g. "dev", "prod"

        Returns:
            str: The fully qualified name of the head job in the graph, to be used with submit_task().

        Warning:
            Do not add the same workflow object multiple times, as it will be modified each time.
            Instead, get the fully qualified name (FQ name) from the first call and reuse it.
        """
        if workflow is None:
            raise ValueError("workflow cannot be None")

        # Check if this workflow has a tracking attribute to prevent multiple additions
        if hasattr(workflow, "_f4a_already_added") and workflow._f4a_already_added:
            # Try to find the existing graph for this workflow
            for job in self.head_jobs:
                # Check if this job's associated workflow is the same object
                if hasattr(job, "_f4a_source_dsl") and job._f4a_source_dsl is workflow:
                    self.logger.info(f"Workflow already added, returning existing FQ name: {job.name}")
                    return job.name

            self.logger.warning(
                f"Workflow appears to have been added already but existing graph not found. "
                f"Creating a new graph, which may lead to duplicate processing."
            )

        # Transform the workflow into a precedence graph (this modifies the workflow)
        graph, jobs = dsl_to_precedence_graph(workflow)

        # Mark this workflow as added to prevent multiple additions
        setattr(workflow, "_f4a_already_added", True)
        
        # If no graph_name was provided, generate one based on head jobs
        if not graph_name:
            graph_name = self.create_graph_name(graph)
            self.logger.info(f"Auto-generated graph name: {graph_name}")

        # Check for FQ name collisions from different workflow objects with same structure
        # Create a base name prefix to check for collisions
        base_name_prefix = f"{graph_name}{SPLIT_STR}{variant}"

        # If there's already a job in job_map that would lead to a collision,
        # we need to make this variant name unique by adding a suffix
        variant_suffix = self.find_unique_variant_suffix(base_name_prefix)

        # Add the suffix to the variant if needed
        if variant_suffix:
            self.logger.info(f"Detected potential FQ name collision, adding suffix '{variant_suffix}' to variant")
            enhanced_variant = f"{variant}{variant_suffix}"
        else:
            enhanced_variant = variant

        # Add the graph to our job graph map with potentially modified variant name
        fq_name = self.add_to_job_graph_map(graph, jobs, graph_name, enhanced_variant)

        # Store the reference to the source workflow in the head job
        head_job = self.job_graph_map[fq_name]
        setattr(head_job, "_f4a_source_dsl", workflow)

        return fq_name

    # Deprecated alias - commented out to enforce use of add_workflow
    # add_dsl = add_workflow

    def add_workflows(self, workflows_dict: Dict) -> List[str]:
        """
        Add multiple workflows to the FlowManager from a dictionary structure.

        Args:
            workflows_dict: A dictionary containing workflow definitions, with optional variants.
                Format can be either:
                {
                    "workflow1": {
                        "dev": workflow1_dev,
                        "prod": workflow1_prod
                    },
                    "workflow2": {
                        "dev": workflow2_dev,
                        "prod": workflow2_prod
                    }
                }
                Or without variants:
                {
                    "workflow1": workflow1,
                    "workflow2": workflow2
                }

        Returns:
            List[str]: The fully qualified names of all added workflows.

        Raises:
            ValueError: If the dictionary structure is invalid or missing required components.
        """
        if not workflows_dict:
            raise ValueError("workflows_dict cannot be None or empty")

        fq_names = []

        for graph_name, graph_data in workflows_dict.items():
            # Check if graph_data is a workflow directly (no variants)
            if not isinstance(graph_data, dict):
                # No variants, graph_data is the workflow directly
                workflow = graph_data

                fq_name = self.add_workflow(workflow, graph_name)
                fq_names.append(fq_name)
            else:
                # Check if this is a variant structure or old-style direct dsl structure
                if "dsl" in graph_data:
                    # Old format - no variants, direct dsl
                    workflow = graph_data.get("dsl")

                    if workflow is None:
                        raise ValueError(f"Graph '{graph_name}' is missing required 'dsl'")

                    fq_name = self.add_workflow(workflow, graph_name)
                    fq_names.append(fq_name)
                else:
                    # With variants - each key is a variant name, value is the workflow
                    for variant, variant_data in graph_data.items():
                        # Check if variant_data is a dict with 'dsl' key (old format)
                        if isinstance(variant_data, dict) and "dsl" in variant_data:
                            # Old format with nested 'dsl' key
                            workflow = variant_data.get("dsl")

                            if workflow is None:
                                raise ValueError(f"Graph '{graph_name}' variant '{variant}' is missing required 'dsl'")
                        else:
                            # New format - variant_data is the workflow directly
                            workflow = variant_data

                        fq_name = self.add_workflow(workflow, graph_name, variant)
                        fq_names.append(fq_name)

        return fq_names

    # Deprecated alias - commented out to enforce use of add_workflows
    # add_dsl_dict = add_workflows

    def add_to_job_graph_map(self, precedence_graph: PrecedenceGraph, jobs: JobsDict, graph_name: str, variant: str = "") -> str:
        """
        Validates the precedence graph then calls JobFactory.create_job_graph which adds next_jobs and expected_inputs to 
        the job instances, also adds default head and tail jobs to the graph, if necessary.

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
        self.job_graph_map.update({job.name: job for job in self.head_jobs})
        return head_job.name

    def find_unique_variant_suffix(self, base_name_prefix: str) -> str:
        """
        Find a unique numeric suffix to append to a variant name to avoid FQ name collisions.
        
        This function checks for existing keys in job_map that start with the given base_name_prefix
        and returns a suffix that will make the name unique when appended to the variant name.
        
        Args:
            job_map: The job map dictionary containing existing job FQ names as keys
            base_name_prefix: The prefix of the FQ name to check for collisions (graph_name$$variant)
            
        Returns:
            str: A numeric suffix (empty string if no collision found, or "_1", "_2", etc.)
        """
        # If no collision in job_map, no suffix needed
        collision_found = False
        for existing_key in self.job_graph_map.keys():
            if existing_key.startswith(base_name_prefix):
                collision_found = True
                break
                
        if not collision_found:
            return ""
            
        # Find existing suffixes by looking at keys with the same base name prefix
        # Extract suffix numbers from variants like "graph_name$$_1$$job_name$$"
        existing_suffixes = set()
        import re

        # Match variants with numeric suffixes in the format "prefix_N$$"
        suffix_pattern = re.compile(re.escape(base_name_prefix) + r'_([0-9]+)\$\$')
        
        for existing_key in self.job_graph_map.keys():
            match = suffix_pattern.match(existing_key)
            if match and match.group(1).isdigit():
                existing_suffixes.add(int(match.group(1)))
        
        # Find the next available suffix number
        suffix_num = 1
        while suffix_num in existing_suffixes:
            suffix_num += 1
        
        return f"_{suffix_num}"

    def create_job_graph_map(self, dsl):
        if isinstance(dsl, Dict):
            self.add_workflows(dsl)
        elif isinstance(dsl, Collection) and not isinstance(dsl, (str, bytes, bytearray)):
            # Handle collections first, before checking for DSLComponent
            if not dsl:  # Check if collection is empty
                raise ValueError("Job collection cannot be empty")

            # Process each item in the collection individually
            for j in dsl:
                # Add the job to DSL if it's a DSLComponent
                if isinstance(j, DSLComponent):  # Check if it's a DSLComponent
                    self.add_workflow(j)
                else:
                    raise TypeError(f"Items in job collection must be DSLComponent instances, got {type(j)}")
        elif isinstance(dsl, DSLComponent):  # Check if it's a DSLComponent
            # Process as a single DSL component
            self.add_workflow(dsl)
        else:
            raise TypeError(f"dsl must be either Dict[str, Any], DSLComponent instance, or Collection of DSLComponent instances, got {type(dsl)}")

    @abstractmethod
    def wait_for_completion(self, timeout=10, check_interval=1):
        """
        Wait for all submitted tasks to complete within the specified timeout.
        
        Args:
            timeout: Maximum time in seconds to wait for completion.
            check_interval: Time in seconds between completion checks.
            
        Returns:
            bool: True if all tasks completed, False if timeout occurred.
            
        Raises:
            TimeoutError: If timeout is reached before all tasks complete (implementation dependent).
        """
        pass
        
    def check_fq_name_and_job_graph_map(self, fq_name, job_map=None):
        """
        Check that the job graph map is not None or empty and sets the fq_name if it is None and there 
        is only one job graph in the map.
        
        Args:
            fq_name: The fully qualified name of the job graph to check.
            job_map: Uses lightweight job_graph_map for multiprocessing mode, or job_graph_map 
            for thread-based single process mode. If None, uses self.job_graph_map.
            
        Returns:
            The fq_name.
            
        Raises:
            ValueError: If job_map is None or empty, or if the specified fq_name does not exist in the map.
        """
        # Use provided job_map or default to self.job_graph_map
        job_map_to_use = job_map if job_map is not None else self.job_graph_map
        
        # Check that job_map is not None or empty
        if not job_map_to_use:
            error_msg = "job_map is None or empty"
            raise ValueError(error_msg)
            
        # If fq_name is None and there's only one job graph in job_map, use that one
        if fq_name is None and len(job_map_to_use) == 1:
            fq_name = next(iter(job_map_to_use))
            self.logger.debug(f"Using the only available job graph: {fq_name}")

        return fq_name
