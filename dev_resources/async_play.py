import asyncio
import sys
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional, Type, Union

import jobchain.jc_logging as logging
from jobchain.job import Task, create_job_graph
from jobchain.utils import timing_decorator


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

context_int: ContextVar[int] = ContextVar('context_int')

@asynccontextmanager
async def create_async_context():
  """Create a new context for job execution, with a new JobState."""
  new_int = 10
  token = context_int.set(new_int)
  try:
      yield
  finally:
      context_int.reset(token)

class JobABC(ABC):
    _instance_counts: Dict[Type, int] = {}
    TASK_PASSTHROUGH_KEY: str = 'task_pass_through'

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):

        self.name:str = self._getUniqueName() if name is None else name
        self.properties:Dict[str, Any] = properties
        self.expected_inputs:set[str] = set()
        self.next_jobs:list[JobABC] = [] 
        self.timeout = 3000 


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


    @abstractmethod
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        pass

    @classmethod
    def _getUniqueName(cls):
        # Increment the counter for the current class
        cls._instance_counts[cls] = cls._instance_counts.get(cls, 0) + 1
        # Return a unique name based on the current class
        return f"{cls.__name__}_{cls._instance_counts[cls]}"


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

jobs = {
    'A': A('A'),
    'B': B('B'),
    'C': C('C'),
    'D': D('D')
}

graph_definition1 = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {'next': ['D']},
    'D': {'next': []}
} 

async def test_simple_graph():

    head_job:JobABC = create_job_graph(graph_definition1, jobs)
    job_set = JobABC.job_set(head_job)
    # Create 50 tasks to run concurrently
    tasks = []
    for _ in range(5):
      async with job_graph_context_manager(job_set):
        task = asyncio.create_task(head_job._execute(Task({'1': {},'2': {}})))
        tasks.append(task)
    
    # Run all tasks concurrently and gather results
    results = await asyncio.gather(*tasks)
    
    # Verify each result matches the expected final output from job D
    for final_result in results:
        # Extract just the job result data, ignoring task_pass_through
        result_data = {k: v for k, v in final_result.items() if k not in ['task_pass_through']}
        assert result_data == {
                'dataD1': {},
                'dataD2': {}
            }

class AsyncPlay:

    async def execute(self, task):
      job_state_dict:dict = job_graph_context.get()
      job_state = job_state_dict.get(task["name"]) or JobState()

      job_state.inputs.update(task)
      job_state.execution_started = True
      result = await self.run(task)
      return result
  
    async def run(self, task: dict) -> Dict:
      job_state_dict:dict = job_graph_context.get()
      job_state = job_state_dict.get(task["name"])
      print (f" execution started = {job_state.execution_started}, inputs = {job_state.inputs}")
      await asyncio.sleep(1)
      print(f"Finished {task}")
      return {"task": task}

# Using create_task() for concurrency
async def run_tasks():
    # Create multiple tasks to run concurrently
    head_job:JobABC = create_job_graph(graph_definition1, jobs)
    job_set = JobABC.job_set(head_job)
    async_play = AsyncPlay()
    tasks = []
    for job in job_set:
      async with job_graph_context_manager(job_set):
        tasks.append(asyncio.create_task(async_play.execute(Task({"name": job.name}))))
    
    # await each task
    results = await asyncio.gather(*tasks)
    print(results)
    return results

# Using asyncio.run() as entry point
@timing_decorator
def main():
    asyncio.run(run_tasks())

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == 'main':
    main()
  elif len(sys.argv) > 1 and sys.argv[1] == 'test':
    asyncio.run(test_simple_graph())
  else:
    print("Usage: python async_play.py [main|test]")
