import asyncio
import os
import sys
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, Union

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import jc_logging as logging
from job import JobABC, Task


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
        job_obj = job_classes[job_name]
        nodes[job_name] = job_obj

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