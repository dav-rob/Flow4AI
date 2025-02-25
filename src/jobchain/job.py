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
  new_state[JobABC.CONTEXT] = {}
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
    RETURN_JOB='RETURN_JOB'
    CONTEXT='CONTEXT'

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        """
        Initialize an JobABC instance.

        Args:
            name (Optional[str], optional): Must be a unique identifier for this job within the context of a JobChain.
                                            If not provided, a unique name will be auto-generated.
            properties (Dict[str, Any], optional): configuration properties passed in by jobs.yaml
        """
        self.name:str = self._getUniqueName() if name is None else name
        self.properties:Dict[str, Any] = properties
        self.expected_inputs:set[str] = set()
        self.next_jobs:list[JobABC] = [] 
        self.timeout = 3000
        self.logger = logging.getLogger(self.__class__.__name__)

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
        """ Responsible for executing the job graph, maintaining state of the graph
        by updating the JobState object and propagating the tail results back up the graph
        when a tail job is reached.

        Can only be used within a job_graph_context set up with:
           ```python
            async with job_graph_context_manager(job_set):
                        result = await job._execute(task)
            ```

        Args:
            task (Union[Task, None]): the input to the first (head) job of the job graph, is None in child jobs.

        Returns:
            Dict[str, Any]: The output of the job graph execution
        """
        job_state_dict:dict = job_graph_context.get()
        job_state = job_state_dict.get(self.name)
        if isinstance(task, dict):
            job_state.inputs.update(task)
            self.get_context()[JobABC.TASK_PASSTHROUGH_KEY] = task
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
                job_state.execution_started = False
                raise TimeoutError(
                    f"Timeout waiting for inputs in {self.name}. "
                    f"Expected: {self.expected_inputs}, "
                    f"Received: {list(job_state.inputs.keys())}"
                )

        result = await self.run(job_state.inputs)
        self.logger.debug(f"Job {self.name} finished running")

        if not isinstance(result, dict):
            result = {'result': result}

        # if isinstance(task, dict):
        #     result[JobABC.TASK_PASSTHROUGH_KEY] = task
        # else:
        #     for input_data in job_state.inputs.values():
        #         if isinstance(input_data, dict) and JobABC.TASK_PASSTHROUGH_KEY in input_data:
        #             result[JobABC.TASK_PASSTHROUGH_KEY] = input_data[JobABC.TASK_PASSTHROUGH_KEY]
        #             break

        # Clear state for potential reuse
        job_state.inputs.clear()
        job_state.input_event.clear()
        job_state.execution_started = False

        # Store the job name that returns the result
        result[JobABC.RETURN_JOB] = self.name

        # If this is a tail job, return immediately
        if not self.next_jobs:
            self.logger.debug(f"Tail Job {self.name} returning result: {result}")
            task = self.get_context()[JobABC.TASK_PASSTHROUGH_KEY]
            result[JobABC.TASK_PASSTHROUGH_KEY] = task
            return result

        # Execute child jobs
        executing_jobs = []
        for next_job in self.next_jobs:
            input_data = result.copy()
            await next_job.receive_input(self.name, input_data)
            next_job_inputs = job_state_dict.get(next_job.name).inputs
            if next_job.expected_inputs.issubset(set(next_job_inputs.keys())):
                executing_jobs.append(next_job._execute(task=None))

        if executing_jobs:
            child_results = await asyncio.gather(*executing_jobs)
            # Find the tail job result (the one that has no next_jobs)
            tail_results = [r for r in child_results if r is not None]
            if tail_results:
                # Always return the first valid tail result
                tail_result = tail_results[0]
                self.logger.debug(f"Job {self.name} propagating tail result: {tail_result}")
                # Preserve the original tail job that generated the result
                return tail_result

        # If no child jobs executed or no tail result found, return None
        return None

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

    def is_head_job(self) -> bool:
        """
        Check if this job is a head job (has no expected inputs).

        Returns:
            bool: True if this is a head job (no expected inputs), False otherwise
        """
        return len(self.expected_inputs) == 0

    def get_context(self) -> Dict[str, Any]:
        """A repository to store state across jobs in a graph for a single coroutine.
           can only be used within a job_graph_context set up with:
           ```python
            async with job_graph_context_manager(job_set):
                        result = await job._execute(task)
            ```
        """
        job_state_dict:dict = job_graph_context.get()
        context = job_state_dict[JobABC.CONTEXT]
        return context

    def get_task(self) -> Union[Dict[str, Any], Task]:
        """
        Get the task associated with this job.

        Returns:
            Union[Dict[str, Any], Task]: The task associated with this job.
        """
        task = self.get_context()[JobABC.TASK_PASSTHROUGH_KEY]
        return task
        
        # if not self.is_head_job(): 
        #     first_parent_result = next(iter(inputs.values()))
        #     task = first_parent_result[JobABC.TASK_PASSTHROUGH_KEY]
        # else:
        #     task = inputs
        # return task

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


