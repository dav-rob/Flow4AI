"""
Base class for Flow Manager implementations.

This module provides the abstract base class that defines the common interface
for all Flow Manager implementations in the Flow4AI framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

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
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Initialize the FlowManager instance.
        
        Each implementation should handle its own initialization with appropriate parameters.
        """
        self.job_map: Dict[str, JobABC] = {}
        self.head_jobs: List[JobABC] = []
        
    def get_head_jobs(self) -> List[JobABC]:
        """
        Get all head jobs in the job graph.
        
        Head jobs are the entry points of the job graph with no predecessors.
        
        Returns:
            List[JobABC]: A list of all head jobs in the job graph
        """
        return self.head_jobs

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

    def add_dsl(self, dsl: DSLComponent, graph_name: str = "", variant: str = "") -> str:
        """
        Adds a DSL component to the FlowManager. Each DSL component should only be added once
        as it is modified during the process by dsl_to_precedence_graph.

        Args:
            dsl: The DSL component defining the data flow between jobs.
                This DSL will be modified by being converted to a precedence graph.
            graph_name: The name of the graph. Used to generate fully qualified job names.
                If empty, a name will be automatically generated based on head jobs.
            variant: The variant of the graph e.g. "dev", "prod"

        Returns:
            str: The fully qualified name of the head job in the graph, to be used with submit().

        Warning:
            Do not add the same DSL object multiple times, as it will be modified each time.
            Instead, get the fully qualified name (FQ name) from the first call and reuse it.
        """
        if dsl is None:
            raise ValueError("graph cannot be None")

        # Check if this DSL has a tracking attribute to prevent multiple additions
        if hasattr(dsl, "_f4a_already_added") and dsl._f4a_already_added:
            # Try to find the existing graph for this DSL
            for job in self.head_jobs:
                # Check if this job's associated DSL is the same object
                if hasattr(job, "_f4a_source_dsl") and job._f4a_source_dsl is dsl:
                    self.logger.info(f"DSL already added, returning existing FQ name: {job.name}")
                    return job.name

            self.logger.warning(
                f"DSL appears to have been added already but existing graph not found. "
                f"Creating a new graph, which may lead to duplicate processing."
            )

        # Transform the DSL into a precedence graph (this modifies the DSL)
        graph, jobs = dsl_to_precedence_graph(dsl)

        # Mark this DSL as added to prevent multiple additions
        setattr(dsl, "_f4a_already_added", True)
        
        # If no graph_name was provided, generate one based on head jobs
        if not graph_name:
            graph_name = self.create_graph_name(graph)
            self.logger.info(f"Auto-generated graph name: {graph_name}")

        # Check for FQ name collisions from different DSL objects with same structure
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

        # Add the graph to our job map with potentially modified variant name
        fq_name = self.add_graph(graph, jobs, graph_name, enhanced_variant)

        # Store the reference to the source DSL in the head job
        head_job = self.job_map[fq_name]
        setattr(head_job, "_f4a_source_dsl", dsl)

        return fq_name

    def add_dsl_dict(self, dsl_dict: Dict) -> List[str]:
        """
        Adds multiple graphs to the task manager from a dictionary structure.

        Args:
            dsl_dict: A dictionary containing graph definitions, with optional variants.
                Format can be either:
                {
                    "graph1": {
                        "dev": dsl1d,
                        "prod": dsl1p
                    }
                    "graph2": {
                        "dev": dsl2d,
                        "prod": dsl2p
                    }
                }
                Or without variants:
                {
                    "graph1": dsl1,
                    "graph2": dsl2
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
            # Check if graph_data is a DSL component directly (no variants)
            if not isinstance(graph_data, dict):
                # No variants, graph_data is the DSL directly
                dsl = graph_data

                fq_name = self.add_dsl(dsl, graph_name)
                fq_names.append(fq_name)
            else:
                # Check if this is a variant structure or old-style direct dsl structure
                if "dsl" in graph_data:
                    # Old format - no variants, direct dsl
                    dsl = graph_data.get("dsl")

                    if dsl is None:
                        raise ValueError(f"Graph '{graph_name}' is missing required 'dsl'")

                    fq_name = self.add_dsl(dsl, graph_name)
                    fq_names.append(fq_name)
                else:
                    # With variants - each key is a variant name, value is the DSL
                    for variant, variant_data in graph_data.items():
                        # Check if variant_data is a dict with 'dsl' key (old format)
                        if isinstance(variant_data, dict) and "dsl" in variant_data:
                            # Old format with nested 'dsl' key
                            dsl = variant_data.get("dsl")

                            if dsl is None:
                                raise ValueError(f"Graph '{graph_name}' variant '{variant}' is missing required 'dsl'")
                        else:
                            # New format - variant_data is the DSL directly
                            dsl = variant_data

                        fq_name = self.add_dsl(dsl, graph_name, variant)
                        fq_names.append(fq_name)

        return fq_names

    def add_graph(self, precedence_graph: PrecedenceGraph, jobs: JobsDict, graph_name: str, variant: str = "") -> str:
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
        self.job_map.update({job.name: job for job in self.head_jobs})
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
        for existing_key in self.job_map.keys():
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
        
        for existing_key in self.job_map.keys():
            match = suffix_pattern.match(existing_key)
            if match and match.group(1).isdigit():
                existing_suffixes.add(int(match.group(1)))
        
        # Find the next available suffix number
        suffix_num = 1
        while suffix_num in existing_suffixes:
            suffix_num += 1
        
        return f"_{suffix_num}"
