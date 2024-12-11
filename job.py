import asyncio
import uuid
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Optional, Set, Type, Union

import jc_logging as logging
from utils.otel_wrapper import trace_function


def _is_traced(method):
    """Helper function to check if a method is traced."""
    return hasattr(method, '_is_traced') and method._is_traced


def _has_own_traced_execute(cls):
    """Helper function to check if a class has its own traced _execute (not inherited)."""
    return '_execute' in cls.__dict__ and _is_traced(cls.__dict__['_execute'])


def _mark_traced(method):
    """Helper function to mark a method as traced."""
    method._is_traced = True
    return method


def traced_job(cls: Type) -> Type:
    """
    Class decorator that ensures the execute method is traced.
    This is only applied to the JobABC class itself.
    """
    if hasattr(cls, '_execute'):
        original_execute = cls._execute
        traced_execute = trace_function(original_execute, detailed_trace=True)
        traced_execute = _mark_traced(traced_execute)
        # Store original as executeNoTrace
        cls.executeNoTrace = original_execute
        # Replace execute with traced version
        cls._execute = traced_execute
    return cls


class JobMeta(ABCMeta):
    """Metaclass that automatically applies the traced_job decorator to JobABC only."""
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name == 'JobABC':  # Only decorate the JobABC class itself
            return traced_job(cls)
        # For subclasses, ensure they inherit JobABC's traced _execute
        if '_execute' in namespace:
            # If subclass defines its own _execute, ensure it's not traced again
            # but still inherits the tracing from JobABC
            del namespace['_execute']
            cls = super().__new__(mcs, name, bases, namespace)
        return cls


class Task(dict):
    """A task dictionary with a unique identifier.
    
    Args:
        data (Union[Dict[str, Any], str]): The task data as a dictionary or string. If a string,
                                            it will be converted to a dictionary with a 'task' key.
        job_name (Optional[str], optional): The name of the job that will process this task.
                                            Required if there is more than one job in the job_map,
                                            otherwise optional."""
    def __init__(self, data: Union[Dict[str, Any], str], job_name: Optional[str] = None):
        # Convert string input to dict
        if isinstance(data, str):
            data = {'task': data}
        elif isinstance(data, dict):
            data = data.copy()  # Create a copy to avoid modifying the original
        else:
            data = {'task': str(data)}
        
        super().__init__(data)
        self.jobchain_unique_id:str = str(uuid.uuid4())
        if job_name is not None:
            self['job_name'] = job_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.jobchain_unique_id == other.jobchain_unique_id

    def __hash__(self) -> int:
        return hash(self.jobchain_unique_id)


class JobABC(ABC, metaclass=JobMeta):
    """
    Abstract base class for jobs. Only this class will have tracing enabled through the JobMeta metaclass.
    Subclasses will inherit the traced version of _execute but won't add additional tracing.
    """

    # class variable to keep track of instance counts for each class
    _instance_counts = {}

    def __init__(self, name: str = None):
        """
        Initialize an JobABC instance.

        Args:
            name (str, optional): A unique identifier for this job within the context of a JobChain.
                       The name must be unique among all jobs in the same JobChain to ensure
                       proper job identification and dependency resolution. If not provided,
                       a unique name will be auto-generated.

        Note:
            The uniqueness of the name is crucial for proper JobChain operation. Using
            duplicate names within the same JobChain can lead to unexpected behavior
            in job execution and dependency management.
        """
        self.name:str = self._getUniqueName() if name is None else name
        self.next_jobs:list[JobABC] = []   # next_jobs is the outgoing edges in the graph definition, 
                                #  it is the jobs to execute after executing this job.
        self.expected_inputs:set[str] = set() # a set of job names that are expected to provide data
                                # as inputs to this job by calling receive_input(). The job will wait
                                # until all expected inputs are received before running _execute().
        self.inputs:Dict[str, Dict[str, Any]] = {} # inputs are set by preceding jobs 
                                # by calling receive_input(). The key is the name of the job that 
                                # sent the input, and the value is the result of the _execute()
                                # method of that job
        
        self.input_event = asyncio.Event()
        self.execution_started = False  # New flag to track execution status
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def _getUniqueName(cls):
        # Increment the counter for the current class
        cls._instance_counts[cls] = cls._instance_counts.get(cls, 0) + 1
        # Return a unique name based on the current class
        return f"{cls.__name__}_{cls._instance_counts[cls]}"

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name}>"

    async def _execute(self, task: Task) -> Dict[str, Any]:
        # Single input case (like A, B, C receiving from parent)
        if isinstance(task, dict):
            self.inputs.update(task)
        else:
            # Convert single input to dict format
            self.inputs[self.name] = task

        # If we expect multiple inputs, wait for them
        if self.expected_inputs:
            if self.execution_started:
                # If execution already started, just return
                return None
            
            self.execution_started = True
            try:
                await asyncio.wait_for(self.input_event.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                self.execution_started = False  # Reset on timeout
                raise TimeoutError(
                    f"Timeout waiting for inputs in {self.name}. "
                    f"Expected: {self.expected_inputs}, "
                    f"Received: {list(self.inputs.keys())}"
                )

        # Process inputs
        result = await self.run(self.inputs)

        # Clear state for potential reuse
        self.inputs.clear()
        self.input_event.clear()
        self.execution_started = False

        # If this is a single job or a tail job in a graph, return the result.
        if not self.next_jobs:
            return result

        # Execute all next jobs concurrently
        executing_jobs = []
        for next_job in self.next_jobs:
            # Tell the next job where this input data came from.
            # so, the job can store its inputs data to with this job's name as a key.
            await next_job.receive_input(self.name, result)
            # If the next job has all its inputs, trigger its execution
            if next_job.expected_inputs.issubset(set(next_job.inputs.keys())):
                executing_jobs.append(next_job._execute(None))
        
        if executing_jobs:
            results = await asyncio.gather(*executing_jobs)
            if any(results):  # If any result is not None
                return results[0]  # Return the first non-None result
        
        #  this returns the result of the last, tail, job in the Job Graph
        return result

    async def receive_input(self, from_job: str, data: Dict[str, Any]) -> None:
        """Receive input from a predecessor job"""
        self.inputs[from_job] = data
        if self.expected_inputs.issubset(set(self.inputs.keys())):
            self.input_event.set()


    @abstractmethod
    async def run(self, task: Task) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass


class SimpleJob(JobABC):
    """A Job implementation that provides a simple default behavior."""
    
    async def run(self, task: Task) -> Dict[str, Any]:
        """Run a simple job that logs and returns the task."""
        self.logger.info(f"Async JOB for {task}")
        await asyncio.sleep(1)  # Simulate network delay
        return {"task": task._data, "status": "complete"}


class JobFactory:
    """Factory class for creating Job instances with proper tracing."""
    
    @staticmethod
    def _load_from_file(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from file configuration."""
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job with params: {params}")
        return SimpleJob("File Job")

    @staticmethod
    def _load_from_datastore(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from datastore."""
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job from datastore with params: {params}")
        return SimpleJob("Datastore Job")

    @staticmethod
    def load_job(job_context: Dict[str, Any]) -> JobABC:
        """Load a job instance with proper tracing based on context."""
        load_type = job_context.get("type", "").lower()
        params = job_context.get("params", {})

        if load_type == "file":
            return JobFactory._load_from_file(params)
        elif load_type == "datastore":
            return JobFactory._load_from_datastore(params)
        else:
            raise ValueError(f"Unsupported job type: {load_type}")

def create_job_graph(graph_definition: dict[str, dict], job_classes: dict[str, JobABC]) -> JobABC:
    """
    graph definition defines the job graph and looks like this:

    graph_definition: dict[str, Any] = {
        "A": {"next": ["B", "C"]},
        "B": {"next": ["D"]},
        "C": {"next": ["D"]},
        "D": {"next": []},
    }

    job classes are a dictionary of job classes in the job graph and looks like this:

    job_classes: dict[str, JobABC] = {
        "A": SimpleJob("A"),
        "B": SimpleJob("B"),
        "C": SimpleJob("C"),
        "D": SimpleJob("D"),
    }
    
    """
    
    nodes:dict[str, JobABC] = {} # nodes holds Jobs which will be hydrated with next_jobs 
                                # and expected_inputs fields from the graph_definition.
    for job_name in graph_definition:
        job_obj = job_classes[job_name]
        nodes[job_name] = job_obj

    # determine the incoming edges i.e the Jobs that each Job depends on
    # so we can determine the head node ( which depends on no Jobs) 
    # and set the expected_inputs (i.e. the dependencies) for each Job.
    incoming_edges: dict[str, set[str]] = {job_name: set() for job_name in graph_definition}
    for job_name, config in graph_definition.items():
        for next_job_name in config['next']:
            incoming_edges[next_job_name].add(job_name)
    
    # 1) Find the head node (node with no incoming edges)
    head_job_name = next(job_name for job_name, inputs in incoming_edges.items() 
                      if not inputs)

    # 2) Set next_jobs for each node
    for job_name, config in graph_definition.items():
        nodes[job_name].next_jobs = [nodes[next_name] for next_name in config['next']]

    # 3) Set expected_inputs for each node
    for job_name, input_job_names_set in incoming_edges.items():
        if input_job_names_set:  # if node has incoming edges
            nodes[job_name].expected_inputs = input_job_names_set

    # 4) Set reference to final node in head node -- not needed!
    # Find node with no next jobs
    # final_job_name = next(job_name for job_name, config in graph_definition.items() 
    #                    if not config['next'])
    # nodes[head_job_name].final_node = nodes[final_job_name]

    return nodes[head_job_name]
