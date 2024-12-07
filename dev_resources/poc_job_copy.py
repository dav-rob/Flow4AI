import asyncio
import os
import sys
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, Union

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import jc_logging as logging
from job import Task


class JobABC(ABC):
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
        self.name = self._getUniqueName() if name is None else name
        self.next_jobs = []
        self.inputs = {}
        self.input_event = asyncio.Event()
        self.expected_inputs = set()
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

    async def _execute(self, task: Any) -> Any:
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

        if not self.next_jobs:
            return result

        # Execute all next jobs concurrently
        tasks = []
        for next_job in self.next_jobs:
            # First send the input to the next job
            await next_job.receive_input(self.name, result)
            # If the next job has all its inputs, trigger its execution
            if next_job.expected_inputs.issubset(set(next_job.inputs.keys())):
                tasks.append(next_job._execute(None))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            if any(results):  # If any result is not None
                return results[0]  # Return the first non-None result

        return result

    async def receive_input(self, from_job: str, data: Any) -> None:
        """Receive input from a predecessor job"""
        self.inputs[from_job] = data
        if self.expected_inputs.issubset(set(self.inputs.keys())):
            self.input_event.set()


    @abstractmethod
    async def run(self, task: Task) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass
    
class A(JobABC):
  async def run(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nA expected inputs: {self.expected_inputs}")
    print(f"A data inputs: {inputs}")
    dataA:dict = {
        'dataA1': {},
        'dataA2': {}
    }
    print(f"A returned: {dataA}")
    return dataA

class B(JobABC):
  async def run(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nB expected inputs: {self.expected_inputs}")
    print(f"B data inputs: {inputs}")
    dataB:dict = {
        'dataB1': {},
        'dataB2': {}
    }
    print(f"B returned: {dataB}")
    return dataB

class C(JobABC):
  async def run(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nC expected inputs: {self.expected_inputs}")
    print(f"C data inputs: {inputs}")
    dataC:dict = {
        'dataC1': {},
        'dataC2': {}
    } 
    print(f"C returned: {dataC}")
    return dataC

class D(JobABC):
  async def run(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nD expected inputs: {self.expected_inputs}")
    print(f"D data inputs: {inputs}")
    dataD:dict = {
        'dataD1': {},
        'dataD2': {}
    } 
    print(f"D returned: {dataD}")
    return dataD

def create_job_graph(graph_definition: dict, job_classes: dict) -> JobABC:
    # First create all nodes with empty next_jobs
    nodes = {}
    for job_name in graph_definition:
        job_class = job_classes[job_name]
        # call the job_class constructor
        nodes[job_name] = job_class()

    # Find the head node (node with no incoming edges)
    incoming_edges = {job_name: set() for job_name in graph_definition}
    for job_name, config in graph_definition.items():
        for next_job_name in config['next']:
            incoming_edges[next_job_name].add(job_name)
    
    head_job_name = next(job_name for job_name, inputs in incoming_edges.items() 
                      if not inputs)

    # Set next_jobs for each node
    for job_name, config in graph_definition.items():
        nodes[job_name].next_jobs = [nodes[next_name] for next_name in config['next']]

    # Set expected_inputs for each node
    for job_name, input_job_names_set in incoming_edges.items():
        if input_job_names_set:  # if node has incoming edges
            nodes[job_name].expected_inputs = input_job_names_set

    # Set reference to final node in head node
    # Find node with no next jobs
    final_job_name = next(job_name for job_name, config in graph_definition.items() 
                       if not config['next'])
    nodes[head_job_name].final_node = nodes[final_job_name]

    return nodes[head_job_name]

def execute_graph(graph_definition: dict, jobs: dict, data: dict) -> Any:
    head_job = create_job_graph(graph_definition, jobs)
    final_result = asyncio.run(head_job._execute(data))
    return final_result

# Usage example:
jobs = {
    'A': A,
    'B': B,
    'C': C,
    'D': D
}
data:dict = {
    '1': {},
    '2': {}
}

graph_definition1 = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {'next': ['D']},
    'D': {'next': []}
} 
final_result1 = execute_graph(graph_definition1, jobs, data)
print(f"Final result: {final_result1} for graph_definition1")

print("\n-------------------------------------------------\n")

graph_definition2 = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C']},
    'C': {'next': []},
} 
final_result2 = execute_graph(graph_definition2, jobs, data)
print(f"Final result: {final_result2} for graph_definition2")