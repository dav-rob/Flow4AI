import asyncio
import contextvars
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC, Task, job_graph_context_manager
from flow4ai.job_loader import ConfigLoader, JobFactory


def returns_collector(shared_results, result):
    shared_results.append(result)

#@pytest.mark.skip("Skipping test due to working yet")
@pytest.mark.asyncio
async def test_concurrency_by_expected_returns():
    # Create a manager for sharing the results list between processes
    manager = mp.Manager()
    shared_results = manager.list()
    
    # Create a partial function with our shared results list
    collector = partial(returns_collector, shared_results)
    
    # Set config directory for test
    config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency_by_returns")
    ConfigLoader._set_directories([config_dir])
    
    # Create JobChain with parallel processing
    flowmanagerMP = FlowManagerMP(result_processing_function=collector)
    logging.info(f"Names of jobs in head job: {flowmanagerMP.get_job_graph_mapping()}")

    def submit_task(range_val:int):
        for i in range(range_val):
            flowmanagerMP.submit_task({'task': f'{i}'})

    def check_results():
        for result in shared_results:
            #logging.info(f"Result: {result}")
            assert result['result'] == 'A.A.B.C.E.A.D.F.G'

        shared_results[:] = []  # Clear the shared_results using slice assignment
    

    submit_task(300)

    flowmanagerMP.mark_input_completed() # this waits for all results to be returned

    check_results()



class A(JobABC):
  async def run(self, task: Dict[str, Any]) -> Any:
    inputs = self.get_inputs()
    print(f"\nA expected inputs: {self.expected_inputs}")
    print(f"A data inputs: {inputs}")
    dataA:dict = {
        'dataA1': {},
        'dataA2': {}
    }
    print(f"A returned: {dataA}")
    return dataA

class B(JobABC):
  async def run(self, task: Dict[str, Any]) -> Any:
    inputs = self.get_inputs()
    print(f"\nB expected inputs: {self.expected_inputs}")
    print(f"B data inputs: {inputs}")
    dataB:dict = {
        'dataB1': {},
        'dataB2': {}
    }
    print(f"B returned: {dataB}")
    return dataB

class C(JobABC):
  async def run(self, task: Dict[str, Any]) -> Any:
    inputs = self.get_inputs()
    print(f"\nC expected inputs: {self.expected_inputs}")
    print(f"C data inputs: {inputs}")
    dataC:dict = {
        'dataC1': {},
        'dataC2': {}
    } 
    print(f"C returned: {dataC}")
    return dataC

class D(JobABC):
  async def run(self, task: Dict[str, Any]) -> Any:
    inputs = self.get_inputs()
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



@pytest.mark.asyncio
async def test_simple_graph():
    head_job:JobABC = JobFactory.create_job_graph(graph_definition1, jobs)
    job_set = JobABC.job_set(head_job)
    # Create 50 tasks to run concurrently
    tasks = []
    for _ in range(50):
      async with job_graph_context_manager(job_set):
        task = asyncio.create_task(head_job._execute(Task({'1': {},'2': {}})))
        tasks.append(task)
    
    # Run all tasks concurrently and gather results
    results = await asyncio.gather(*tasks)
    
    # Verify each result matches the expected final output from job D
    for final_result in results:
        # Extract just the job result data, ignoring task_pass_through
        result_data = {k: v for k, v in final_result.items() if k not in ['task_pass_through', 'RETURN_JOB']}
        assert result_data == {
                'dataD1': {},
                'dataD2': {}
            }
