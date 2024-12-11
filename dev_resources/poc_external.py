import asyncio
import os
import sys
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, Union

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import jc_logging as logging
from job import JobABC, Task, create_job_graph


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


def execute_graph(graph_definition: dict, jobs: dict, data: dict) -> Any:
    head_job = create_job_graph(graph_definition, jobs)
    task = Task(data)
    final_result = asyncio.run(head_job._execute(task))
    return final_result

# Usage example:
jobs = {
    'A': A('A'),
    'B': B('B'),
    'C': C('C'),
    'D': D('D')
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