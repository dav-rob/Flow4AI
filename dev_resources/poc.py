import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, Union


class JobABC(ABC):
    def __init__(self, next_jobs: List['JobABC']):
        self.next_jobs = next_jobs
        self.job_id = self.__class__.__name__
        self.inputs = {}
        self.input_event = asyncio.Event()
        self.expected_inputs = set()
        self.execution_started = False  # New flag to track execution status

    async def _execute(self, task: Any) -> Any:
        # Single input case (like A, B, C receiving from parent)
        if isinstance(task, dict):
            self.inputs.update(task)
        else:
            # Convert single input to dict format
            self.inputs[self.job_id] = task

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
                    f"Timeout waiting for inputs in {self.job_id}. "
                    f"Expected: {self.expected_inputs}, "
                    f"Received: {list(self.inputs.keys())}"
                )

        # Process inputs
        result = await self._process(self.inputs)

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
            await next_job.receive_input(self.job_id, result)
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
    async def _process(self, inputs: Dict[str, Any]) -> Any:
        """Override in concrete classes to implement processing logic"""
        pass
    
class A(JobABC):
  async def _process(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nA expected inputs: {self.expected_inputs}")
    print(f"A data inputs: {inputs}")
    dataA:dict = {
        'dataA1': {},
        'dataA2': {}
    }
    print(f"A returned: {dataA}")
    return dataA

class B(JobABC):
  async def _process(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nB expected inputs: {self.expected_inputs}")
    print(f"B data inputs: {inputs}")
    dataB:dict = {
        'dataB1': {},
        'dataB2': {}
    }
    print(f"B returned: {dataB}")
    return dataB

class C(JobABC):
  async def _process(self, inputs: Dict[str, Any]) -> Any:
    print(f"\nC expected inputs: {self.expected_inputs}")
    print(f"C data inputs: {inputs}")
    dataC:dict = {
        'dataC1': {},
        'dataC2': {}
    } 
    print(f"C returned: {dataC}")
    return dataC

class D(JobABC):
  async def _process(self, inputs: Dict[str, Any]) -> Any:
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
    for job_id in graph_definition:
        job_class = job_classes[job_id]
        nodes[job_id] = job_class([])

    # Find the head node (node with no incoming edges)
    incoming_edges = {job_id: set() for job_id in graph_definition}
    for job_id, config in graph_definition.items():
        for next_job_id in config['next']:
            incoming_edges[next_job_id].add(job_id)
    
    head_job_id = next(job_id for job_id, inputs in incoming_edges.items() 
                      if not inputs)

    # Set next_jobs for each node
    for job_id, config in graph_definition.items():
        nodes[job_id].next_jobs = [nodes[next_id] for next_id in config['next']]

    # Set expected_inputs for each node
    for job_id, inputs in incoming_edges.items():
        if inputs:  # if node has incoming edges
            nodes[job_id].expected_inputs = inputs

    # Set reference to final node in head node
    # Find node with no next jobs
    final_job_id = next(job_id for job_id, config in graph_definition.items() 
                       if not config['next'])
    nodes[head_job_id].final_node = nodes[final_job_id]

    return nodes[head_job_id]

# Usage example:
graph_definition = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {'next': ['D']},
    'D': {'next': []}
} 

jobs = {
    'A': A,
    'B': B,
    'C': C,
    'D': D
}

head_job = create_job_graph(graph_definition, jobs)
data:dict = {
    '1': {},
    '2': {}
}
final_result = asyncio.run(head_job._execute(data))
print(f"Final result: {final_result}")