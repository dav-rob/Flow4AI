import asyncio
import uuid
from abc import ABC, ABCMeta, abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional, Type, Union

from . import f4a_logging as logging
from .utils.otel_wrapper import trace_function

SPLIT_STR = "$$"


# DSL imports moved inline to avoid circular imports


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
        data (Union[Dict[str, Any], str]): 
            The task data as a dictionary or string. If a string,
            it will be converted to a dictionary with a 'task' key.
        fq_name (Optional[str], optional): 
            The name of the job graph that will process this task.
            Required if there is more than one job graph in the
            FlowManagerMP class. If "fq_name" key is already in
            the data dictionary, it will be used instead of the
            fq_name parameter.
    """
    def __init__(self, data: Dict[str, Any], fq_name: Optional[str] = None):
        # Convert string input to dict
        if isinstance(data, dict):
            data = data.copy()  # Create a copy to avoid modifying the original
        else:
            raise ValueError("Task data must be a dictionary")
        
        super().__init__(data)
        self.task_id:str = str(uuid.uuid4())
        if fq_name is not None and self.get('fq_name') is None:
            self['fq_name'] = fq_name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.task_id == other.task_id
    
    def get_fq_name(self) -> str:
        return self.get('fq_name')

    # mypy highlights this as an error because dicts are mutable
    #   and so not hashable, but I want each Task to have a unique id
    #   so it is hashable.
    def __hash__(self) -> int:
        return hash(self.task_id)

    def __repr__(self) -> str:
        fq_name = self.get('fq_name', 'None')
        task_preview = str(dict(self))[:50] + '...' if len(str(dict(self))) > 50 else str(dict(self))
        return f"Task(id={self.task_id}, fq_name={fq_name}, data={task_preview})"

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
  new_state[JobABC.CONTEXT][JobABC.SAVED_RESULTS] = {}
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
    
    # Key used to pass task metadata through the job graph
    TASK_PASSTHROUGH_KEY: str = 'task_pass_through'
    RETURN_JOB='RETURN_JOB'
    CONTEXT='CONTEXT'
    SAVED_RESULTS='SAVED_RESULTS'

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        """
        Initialize an JobABC instance.

        Args:
            name (Optional[str], optional): Must be a unique identifier for this job within the context of a FlowManager.
                                            If not provided, a unique name will be auto-generated.
            properties (Dict[str, Any], optional): configuration properties passed in by jobs.yaml
        """
        self.name:str = self._getUniqueName() if name is None else name
        self.save_result: bool = bool(properties.get("save_result", False))
        self.properties:Dict[str, Any] = properties
        self.expected_inputs:set[str] = set()
        self.next_jobs:list[JobABC] = [] 
        self.timeout = 3000
        self.logger = logging.getLogger(self.__class__.__name__)
        self.global_ctx = None

    def __or__(self, other):
        """Implements the | operator for parallel composition"""
        # Import DSL classes inline to avoid circular imports
        from .dsl import Parallel, Serial
        from .jobs.wrapping_job import WrappingJob

        if isinstance(other, Parallel):
            # If right side is already a parallel component, add to its components
            return Parallel(*([self] + other.components))
        elif isinstance(other, JobABC):
            return Parallel(self, other)
        elif isinstance(other, Serial):
            return Parallel(self, other)
        else:
            # If other is a raw object, wrap it first
            return Parallel(self, WrappingJob(other))
    
    def __rshift__(self, other):
        """Implements the >> operator for serial composition"""
        # Import DSL classes inline to avoid circular imports
        from .dsl import Parallel, Serial
        from .jobs.wrapping_job import WrappingJob

        if isinstance(other, Serial):
            # If right side is already a serial component, add to its components
            return Serial(*([self] + other.components))
        elif isinstance(other, JobABC):
            return Serial(self, other)
        elif isinstance(other, Parallel):
            return Serial(self, other)
        else:
            # If other is a raw object, wrap it first
            return Serial(self, WrappingJob(other))
    
    @classmethod
    def create_FQName(cls, graph_name, parameter_name, short_graph_job_name, dsl_id=None):
        """
        Creates a unique, fully qualified name from the graph, parameter and job names.
        
        Args:
            graph_name: Name of the graph
            parameter_name: Parameter name (usually variant)
            short_graph_job_name: The job name (short form)
            dsl_id: Optional unique identifier for the source DSL to prevent FQ name collisions
            
        Returns:
            str: A fully qualified name in format graph_name$$parameter_name$$short_graph_job_name$$
                 or graph_name$$parameter_name-dsl_id$$short_graph_job_name$$ if dsl_id is provided
        """
        # If a DSL identifier is provided, incorporate it into the parameter name
        # This ensures unique FQ names while maintaining compatibility with existing parsing logic
        if dsl_id:
            # Embed the DSL ID in the parameter name to maintain compatibility with parsers
            if parameter_name:
                enhanced_param_name = f"{parameter_name}-{dsl_id}"
            else:
                enhanced_param_name = dsl_id
        else:
            enhanced_param_name = parameter_name
            
        unique_job_name = graph_name + SPLIT_STR + enhanced_param_name + SPLIT_STR + short_graph_job_name + SPLIT_STR
        return unique_job_name

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
            parts = name.split(SPLIT_STR)
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

        This is a classic dataflow execution model, where computation proceeds based on data 
        availability rather than a predetermined sequence.

        WARNING: DO NOT OVERRIDE THIS METHOD IN CUSTOM JOB CLASSES.
        This method is part of the core Flow4AI execution flow and handles critical operations
        including job graph traversal, state management, and result propagation.
        
        Instead, implement the abstract 'run' method to define custom job behavior.

        Can only be used within a job_graph_context set up with:
           ```python
            async with job_graph_context_manager(job_set):
                        result = await job._execute(task)
            ```
        The recursive nature of the algorithm means that results flow upwards, with the head job appearing
        to return the result of the tail job.

        Args:
            task (Union[Task, None]): the input to the first (head) job of the job graph, is None in child jobs.

        Returns:
            Dict[str, Any]: The output of the job graph execution
        """
        job_state_dict:dict = job_graph_context.get()
        job_state = job_state_dict.get(self.name)
        if self.is_head_job() and  isinstance(task, dict):
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

        result = await self.run(task)
        self.logger.debug(f"Job {self.name} finished running")

        if self.save_result:
            saved_results = self.get_context()[JobABC.SAVED_RESULTS]
            saved_results[self.name] = result

        if not isinstance(result, dict):
            result = {'result': result}

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
            saved_results = self.get_context().get(JobABC.SAVED_RESULTS, {})
            if saved_results:
                result[JobABC.SAVED_RESULTS] = {JobABC.parse_job_name(k): v for k, v in saved_results.items()}
            return result

        # Check if any child jobs are ready to execute once given this result as input
        executing_jobs = []
        for next_job in self.next_jobs:
            input_data = result.copy()
            # add result data from this job as an input to the next job
            await next_job.receive_input(self.name, input_data)
            next_job_inputs = job_state_dict.get(next_job.name).inputs
            # if the next job has all its inputs add coroutine to list to execute
            if next_job.expected_inputs.issubset(set(next_job_inputs.keys())):
                the_task = self.get_task()
                executing_jobs.append(next_job._execute(task=the_task))

        # If there are any child jobs ready to execute, execute them, else return None 
        if executing_jobs:
            # await for all futures to return results
            child_results = await asyncio.gather(*executing_jobs)
            not_none_results = [r for r in child_results if r is not None]
            if not_none_results:
                # Return the first valid result.
                # The recursive nature of the algorithm means that results flow upwards, with the head job appearing
                # to return the result of the tail job, so returning the first valid result will return the tail job
                # result up the stack.
                first_valid_result = not_none_results[0]
                self.logger.debug(f"Job {self.name} propagating first valid result: {first_valid_result}")
                return first_valid_result

        # If no child jobs executed or no valid result found, return None
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
        """
        Returns an object that can be used to store context across jobs in a graph for a single coroutine.
           can only be used within a job_graph_context set up with:
           ```python
            async with job_graph_context_manager(job_set):
                        result = await job._execute(task)
        """
        job_state_dict:dict = job_graph_context.get()
        context = job_state_dict[JobABC.CONTEXT]
        return context

    def _get_long_name_inputs(self) -> Dict[str, Any]:
        """
        Returns the inputs for this job.

        Returns:
            Dict[str, Any]: Returns the inputs to this job with long fully qualified job names as keys
        """
        job_state_dict:dict = job_graph_context.get()
        jobstate:JobState = job_state_dict[self.name]
        inputs: Dict[str, Dict[str, Any]] = jobstate.inputs
        return inputs   
    
    def get_inputs(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the inputs to this job with short job names as keys.

        Returns:
            Dict[str, Dict[str, Any]]: The inputs to this job.
        """
        inputs: Dict[str, Dict[str, Any]] = self._get_long_name_inputs()
        inputs_with_short_job_name = {JobABC.parse_job_name(k): v for k, v in inputs.items()}
        self.logger.debug(f"Returning inputs: {inputs_with_short_job_name}")
        return inputs_with_short_job_name

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

    def update_context(self, new_context: Dict[str, Any]) -> None:
        """
        Update the context dictionary with new values.
        
        Args:
            new_context: Dictionary with new context values
        """
        self.global_ctx.update(new_context)

    @abstractmethod
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass

# SimpleJob and SimpleJobFactory have been moved to tests/test_utils/simple_job.py
# They are only used for testing purposes and not for production code.
