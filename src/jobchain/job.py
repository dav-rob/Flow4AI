import asyncio
import uuid
from abc import ABC, ABCMeta, abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional, Type, Union

from . import jc_logging as logging
from .utils.otel_wrapper import trace_function


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
                                            Required if there is more than one job graph in the
                                            JobChain class"""
    def __init__(self, data: Union[Dict[str, Any], str], job_name: Optional[str] = None):
        # Convert string input to dict
        if isinstance(data, str):
            data = {'task': data}
        elif isinstance(data, dict):
            data = data.copy()  # Create a copy to avoid modifying the original
        else:
            data = {'task': str(data)}
        
        super().__init__(data)
        self.task_id:str = str(uuid.uuid4())
        if job_name is not None:
            self['job_name'] = job_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.task_id == other.task_id

    # mypy highlights this as an error because dicts are mutable
    #   and so not hashable, but I want each Task to have a unique id
    #   so it is hashable.
    def __hash__(self) -> int:
        return hash(self.task_id)

    def __repr__(self) -> str:
        job_name = self.get('job_name', 'None')
        task_preview = str(dict(self))[:50] + '...' if len(str(dict(self))) > 50 else str(dict(self))
        return f"Task(id={self.task_id}, job_name={job_name}, data={task_preview})"

class JobState:
  def __init__(self):
      self.inputs: Dict[str, Dict[str, Any]] = {}
      self.input_event = asyncio.Event()
      self.execution_started = False

job_graph_context : ContextVar[dict] = ContextVar('job_graph_context')

@asynccontextmanager
async def job_graph_context_manager(job_set: set['JobABC']):
  """Create a new context for job execution, with a new JobState."""
  new_state = {}
  for job in job_set:
      new_state[job.name] = JobState()
  token = job_graph_context.set(new_state)
  try:
      yield new_state
  finally:
      job_graph_context.reset(token)

class JobABC(ABC, metaclass=JobMeta):
    """
    Abstract base class for jobs. Only this class will have tracing enabled through the JobMeta metaclass.
    Subclasses will inherit the traced version of _execute but won't add additional tracing.
    """

    # class variable to keep track of instance counts for each class
    _instance_counts: Dict[Type, int] = {}
    
    # Key used to pass task metadata through the job chain
    TASK_PASSTHROUGH_KEY: str = 'task_pass_through'

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        """
        Initialize an JobABC instance.

        Args:
            name (Optional[str], optional): A unique identifier for this job within the context of a JobChain.
                       The name must be unique among all jobs in the same JobChain to ensure
                       proper job identification and dependency resolution. If not provided,
                       a unique name will be auto-generated.

        Note:
            The uniqueness of the name is crucial for proper JobChain operation. Using
            duplicate names within the same JobChain can lead to unexpected behavior
            in job execution and dependency management.
        """
        self.name:str = self._getUniqueName() if name is None else name
        self.properties:Dict[str, Any] = properties
        self.expected_inputs:set[str] = set()
        self.next_jobs:list[JobABC] = [] 
        self.timeout = 3000 

    @classmethod
    def parse_job_loader_name(cls, name: str) -> Dict[str, str]:
        """Parse a job loader name into its constituent parts.
        
        Args:
            name: The full job loader name string in format:
                 graph_name$$param_name$$job_name$$
                 
        Returns:
            dict: A dictionary containing graph_name, param_name, and job_name,
                 or {'parsing_message': 'UNSUPPORTED NAME FORMAT'} if invalid
        """
        try:
            parts = name.split("$$")
            if len(parts) != 4 or parts[3] != "" or not parts[0]:
                return {"parsing_message": "UNSUPPORTED NAME FORMAT"}
                
            return {
                "graph_name": parts[0],
                "param_name": parts[1],
                "job_name": parts[2]
            }
        except:
            return {"parsing_message": "UNSUPPORTED NAME FORMAT"}

    @classmethod
    def parse_graph_name(cls, name: str) -> str:
        """Parse and return the graph name from a job loader name.
        
        Args:
            name: The full job loader name string
            
        Returns:
            str: The graph name or 'UNSUPPORTED NAME FORMAT' if invalid
        """
        result = cls.parse_job_loader_name(name)
        return result.get("graph_name", "UNSUPPORTED NAME FORMAT")

    @classmethod
    def parse_param_name(cls, name: str) -> str:
        """Parse and return the parameter name from a job loader name.
        
        Args:
            name: The full job loader name string
            
        Returns:
            str: The parameter name or 'UNSUPPORTED NAME FORMAT' if invalid
        """
        result = cls.parse_job_loader_name(name)
        return result.get("param_name", "UNSUPPORTED NAME FORMAT")

    @classmethod
    def parse_job_name(cls, name: str) -> str:
        """Parse and return the job name from a job loader name.
        
        Args:
            name: The full job loader name string
            
        Returns:
            str: The job name or 'UNSUPPORTED NAME FORMAT' if invalid
        """
        result = cls.parse_job_loader_name(name)
        return result.get("job_name", "UNSUPPORTED NAME FORMAT")

    @classmethod
    def _getUniqueName(cls):
        # Increment the counter for the current class
        cls._instance_counts[cls] = cls._instance_counts.get(cls, 0) + 1
        # Return a unique name based on the current class
        return f"{cls.__name__}_{cls._instance_counts[cls]}"

    @classmethod
    def get_input_from(cls, inputs: Dict[str, Any], job_name: str) -> Dict[str, Any]:
        """Get input data from a specific job in the inputs dictionary.
        
        Args:
            inputs (Dict[str, Any]): Dictionary of inputs from various jobs
            job_name (str): Name of the job whose input we want to retrieve
            
        Returns:
            Dict[str, Any]: The input data from the specified job, or empty dict if not found
        """
        for key in inputs.keys():
            if cls.parse_job_name(key) == job_name:
                return inputs[key]
        return {}

    @classmethod
    def get_task(cls, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get task metadata from inputs dictionary.
        
        Args:
            inputs (Dict[str, Any]): Dictionary of inputs to search for task metadata
            
        Returns:
            Dict[str, Any]: The task metadata or empty dict if not found
            
        Raises:
            TypeError: If inputs is not a dictionary
        """
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")
        return cls.get_input_from(inputs, cls.TASK_PASSTHROUGH_KEY)

    @classmethod
    def job_set(cls, job) -> set['JobABC']:
        """
        Returns a set of all unique job instances in the job graph by recursively traversing
        all possible paths through next_jobs.
        
        Returns:
            set[JobABC]: A set containing all unique job instances in the graph
        """
        result = {job}  # Start with current job instance
        
        # Base case: if no next jobs, return current set
        if not job.next_jobs:
            return result
            
        # Recursive case: add all jobs from each path
        for job in job.next_jobs:
            result.update(cls.job_set(job))
            
        return result

    def __repr__(self):
        next_jobs_str = [job.name for job in self.next_jobs]
        expected_inputs_str = [input_name for input_name in self.expected_inputs]
        return (f"name: {self.name}\n"
                f"next_jobs: {next_jobs_str}\n"
                f"expected_inputs: {expected_inputs_str}\n"
                f"properties: {self.properties}")

    async def _execute(self, task: Union[Task, None]) -> Dict[str, Any]:
        job_state_dict:dict = job_graph_context.get()
        job_state = job_state_dict.get(self.name)
        if isinstance(task, dict):
            job_state.inputs.update(task)
        elif task is None:
            pass 
        else:
            job_state.inputs[self.name] = task

        if self.expected_inputs:
            if job_state.execution_started:
                return None
            
            job_state.execution_started = True
            try:
                await asyncio.wait_for(job_state.input_event.wait(), self.timeout)
            except asyncio.TimeoutError:
                job_state.execution_started = False  # Reset on timeout
                raise TimeoutError(
                    f"Timeout waiting for inputs in {self.name}. "
                    f"Expected: {self.expected_inputs}, "
                    f"Received: {list(job_state.inputs.keys())}"
                )

        result = await self.run(job_state.inputs)
        logging.debug(f"Job {self.name} finished running")

        if not isinstance(result, dict):
            result = {'result': result}

        if isinstance(task, dict):
            # Preserve all task data
            result[self.TASK_PASSTHROUGH_KEY] = task
        else:
            # Find task_pass_through in any of the input results
            for input_data in job_state.inputs.values():
                if isinstance(input_data, dict) and self.TASK_PASSTHROUGH_KEY in input_data:
                    result[self.TASK_PASSTHROUGH_KEY] = input_data[self.TASK_PASSTHROUGH_KEY]
                    break

        # Clear state for potential reuse
        job_state.inputs.clear()
        job_state.input_event.clear()
        job_state.execution_started = False

        # If this is a single job or a tail job in a graph, return the result.
        if not self.next_jobs:
            return result
        
        executing_jobs = []
        for next_job in self.next_jobs:
            input_data = result.copy()
            await next_job.receive_input(self.name, input_data)
            next_job_inputs = job_state_dict.get(next_job.name).inputs
            if next_job.expected_inputs.issubset(set(next_job_inputs.keys())):
                executing_jobs.append(next_job._execute(task=None))
        
        if executing_jobs:
            results = await asyncio.gather(*executing_jobs)
            if any(results):  # If any result is not None
                return results[0]  # Return the first non-None result
        
        #  this appears never to be reached
        return result

    async def receive_input(self, from_job: str, data: Dict[str, Any]) -> None:
        """Receive input from a predecessor job"""
        job_state_dict:dict = job_graph_context.get()
        job_state = job_state_dict.get(self.name)
        job_state.inputs[from_job] = data
        if self.expected_inputs.issubset(set(job_state.inputs.keys())):
            job_state.input_event.set()

    def job_set_str(self) -> set[str]:
        """
        Returns a set of all unique job names in the job graph by recursively traversing
        all possible paths through next_jobs.
        
        Returns:
            set[str]: A set containing all unique job names in the graph
        """
        result = {self.name}  # Start with current job's name
        
        # Base case: if no next jobs, return current set
        if not self.next_jobs:
            return result
            
        # Recursive case: add all jobs from each path
        for job in self.next_jobs:
            result.update(job.job_set_str())
            
        return result

    @abstractmethod
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass


class SimpleJob(JobABC):
    """A Job implementation that provides a simple default behavior."""
    
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Run a simple job that logs and returns the task."""
        logging.info(f"Async JOB for {task}")
        await asyncio.sleep(1)  # Simulate network delay
        return {"task": task, "status": "complete"}


class SimpleJobFactory:
    """Factory class for creating Job instances with proper tracing."""
    
    @staticmethod
    def _load_from_file(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from file configuration."""
        logging.info(f"Loading job with params: {params}")
        return SimpleJob("File Job")

    @staticmethod
    def _load_from_datastore(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from datastore."""
        logging.info(f"Loading job from datastore with params: {params}")
        return SimpleJob("Datastore Job")

    @staticmethod
    def load_job(job_context: Dict[str, Any]) -> JobABC:
        """Load a job instance with proper tracing based on context."""
        load_type = job_context.get("type", "").lower()
        params = job_context.get("params", {})

        if load_type == "file":
            return SimpleJobFactory._load_from_file(params)
        elif load_type == "datastore":
            return SimpleJobFactory._load_from_datastore(params)
        else:
            raise ValueError(f"Unsupported job type: {load_type}")

def create_job_graph(graph_definition: dict[str, dict], job_instances: dict[str, JobABC]) -> JobABC:
    """
    graph definition defines the job graph and looks like this:

    graph_definition: dict[str, Any] = {
        "A": {"next": ["B", "C"]},
        "B": {"next": ["D"]},
        "C": {"next": ["D"]},
        "D": {"next": []},
    }

    job instances are a dictionary of job instances in the job graph and looks like this:

    job_instances: dict[str, JobABC] = {
        "A": SimpleJob("A"),
        "B": SimpleJob("B"),
        "C": SimpleJob("C"),
        "D": SimpleJob("D"),
    }
    
    """
    
    nodes:dict[str, JobABC] = {} # nodes holds Jobs which will be hydrated with next_jobs 
                                # and expected_inputs fields from the graph_definition.
    for job_name in graph_definition:
        job_obj = job_instances[job_name]
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

    # 3) Set expected_inputs for each node using fully qualified names
    for job_name, input_job_names_set in incoming_edges.items():
        if input_job_names_set:  # if node has incoming edges
            # Transform short names to fully qualified names using the job_instances dictionary
            nodes[job_name].expected_inputs = {job_instances[input_name].name for input_name in input_job_names_set}

    # 4) Set reference to final node in head node -- not needed!
    # Find node with no next jobs
    # final_job_name = next(job_name for job_name, config in graph_definition.items() 
    #                    if not config['next'])
    # nodes[head_job_name].final_node = nodes[final_job_name]

    return nodes[head_job_name]
