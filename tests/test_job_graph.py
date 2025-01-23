import asyncio
import time
from typing import Any, Dict

from jobchain.job import JobABC, Task, create_job_graph
from jobchain.job_chain import JobChain


class MockJob(JobABC):
    def run(self):
        pass

class MockJobSubclass(MockJob):
    pass

class DelayedMockJob(MockJob):
    """A mock job that introduces a configurable delay in processing."""
    def __init__(self, name: str, delay: float):
        super().__init__(name=name)
        self.delay = delay

    async def run(self, inputs):
        inputs = inputs[self.name]  # Get the task from inputs dict
        await asyncio.sleep(self.delay)
        return {'input': inputs, 'output': f'processed by {self.name}'}

def test_job_name_always_present():
    # Test with explicit name
    job1 = MockJob(name="explicit_name")
    assert job1.name == "explicit_name"
    
    # Test with auto-generated name
    job2 = MockJob()
    assert job2.name is not None
    assert isinstance(job2.name, str)
    assert len(job2.name) > 0

    # Test subclass with explicit name
    job3 = MockJobSubclass(name="subclass_name")
    assert job3.name == "subclass_name"
    
    # Test subclass with auto-generated name
    job4 = MockJobSubclass()
    assert job4.name is not None
    assert isinstance(job4.name, str)
    assert len(job4.name) > 0

def test_auto_generated_names_are_unique():
    # Create multiple jobs without explicit names
    num_jobs = 100  # Test with a significant number of jobs
    jobs = [MockJob() for _ in range(num_jobs)]
    
    # Collect all names in a set
    names = {job.name for job in jobs}
    
    # If all names are unique, the set should have the same length as the list
    assert len(names) == num_jobs
    
    # Test uniqueness across different subclass instances
    mixed_jobs = [
        MockJob() if i % 2 == 0 else MockJobSubclass()
        for i in range(num_jobs)
    ]
    mixed_names = {job.name for job in mixed_jobs}
    assert len(mixed_names) == num_jobs

def test_parallel_execution_multiple_jobs():
    """Test parallel execution with multiple jobs in a job graph."""
    # Test with both 1s and 2s delays
    for delay in [1.0, 2.0]:
        # Create 5 jobs with the same delay
        jobs = [DelayedMockJob(f'job_{i}', delay) for i in range(5)]
        
        # Create tasks for each job
        tasks = []
        for i in range(5):
            for j in range(4):  # 4 tasks per job = 20 total tasks
                tasks.append({f'job_{i}': {'task': f'task_{i}_{j}', 'job_name': f'job_{i}'}})

        # Time the execution
        start_time = time.time()
        
        # Run the job chain with all jobs and collect results
        results = []
        def result_collector(result):
            results.append(result)
        job_chain = JobChain(jobs, result_collector, serial_processing=True)
        for task in tasks:
            job_name = next(iter(task.keys()))  # Get the job name from the task dict
            job_chain.submit_task(task, job_name=job_name)
        job_chain.mark_input_completed()
        
        end_time = time.time()
        execution_time = end_time - start_time

        # Verify results
        assert len(results) == 20  # Should have 20 results
        
        # Check that each task was processed by the correct job
        for result in results:
            input_task = result['input']
            job_name = input_task['job_name']
            assert result['output'] == f'processed by {job_name}'
        
        # Verify parallel execution - should take ~4 * delay seconds (4 batches of tasks)
        # Add some buffer time for overhead
        assert execution_time < (4 * delay + 1), f"Execution took {execution_time} seconds, expected less than {4 * delay + 1} seconds"

def collect_result(results):
    """Create a picklable result collector function that appends to the given list."""
    def collector(result):
        results.append(result)
    return collector


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

class E(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class F(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class G(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class H(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class I(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class J(MockJob):
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

jobs = {
    'A': A('A'),
    'B': B('B'),
    'C': C('C'),
    'D': D('D')
}
jobs.update({
    'E': E('E'),
    'F': F('F'),
    'G': G('G'),
    'H': H('H'),
    'I': I('I'),
    'J': J('J'),
})

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

graph_definition_complex = {
    'A': {'next': ['B', 'C', 'E']},  # Head job with 3 branches
    'B': {'next': ['D', 'F']},       # Branch 1
    'C': {'next': ['F', 'G']},       # Branch 2
    'D': {'next': ['H']},            # Merge point 1
    'E': {'next': ['G', 'I']},       # Branch 3
    'F': {'next': ['H']},            # Merge point 2
    'G': {'next': ['I']},            # Merge point 3
    'H': {'next': ['J']},            # Pre-final merge
    'I': {'next': ['J']},            # Pre-final merge
    'J': {'next': []}                # Tail job
}

def execute_graph(graph_definition: dict, jobs: dict, data: dict) -> Any:
    head_job = create_job_graph(graph_definition, jobs)
    final_result = asyncio.run(head_job._execute(Task(data)))
    return final_result

def test_execute_graph1():
    final_result1 = execute_graph(graph_definition1, jobs, data)
    # Extract just the job result data, ignoring task_pass_through
    result_data = {k: v for k, v in final_result1.items() if k not in ['task_pass_through']}
    assert result_data == {
            'dataD1': {},
            'dataD2': {}
        }

def test_job_set():
    head_job = create_job_graph(graph_definition1, jobs)
    job_set = head_job.job_set_str()
    assert job_set == {'A', 'B', 'C', 'D'}

def test_execute_graph2():
    final_result2 = execute_graph(graph_definition2, jobs, data)
    # Extract just the job result data, ignoring task_pass_through
    result_data = {k: v for k, v in final_result2.items() if k not in ['task_pass_through']}
    assert result_data == {
            'dataC1': {},
            'dataC2': {}
        }
    

graph_definition2 = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C']},
    'C': {'next': []},
} 

def test_complex_job_set():
    """
    Test job_set() with a complex graph structure containing:
    - Multiple paths from head to tail
    - Diamond patterns (multiple paths converging)
    - Multiple levels of job dependencies
    Graph structure:
           A
        /  |  \
       B   C   E
      /\  / \  /\
     D  F    G  I
      \ /     \ /
       H       I
        \     /
          J
    """
    head_job = create_job_graph(graph_definition_complex, jobs)
    job_set = head_job.job_set_str()
    expected_jobs = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'}
    assert job_set == expected_jobs, f"Expected {expected_jobs}, but got {job_set}"

def test_complex_job_set_instances():
    """
    Test job_set() with a complex graph structure to verify it returns the actual job instances.
    Uses the same graph structure as test_complex_job_set:
           A
        /  |  \
       B   C   E
      /\  / \  /\
     D  F    G  I
      \ /     \ /
       H       I
        \     /
          J
    """
    head_job = create_job_graph(graph_definition_complex, jobs)
    job_instances = JobABC.job_set(head_job)
    
    # Verify we got the correct number of instances
    expected_count = 10  # A through J
    assert len(job_instances) == expected_count, f"Expected {expected_count} job instances, but got {len(job_instances)}"
    
    # Verify all instances are JobABC types
    assert all(isinstance(job, JobABC) for job in job_instances), "All items in job_set should be JobABC instances"
    
    # Verify the job names match what we expect
    job_names = {job.name for job in job_instances}
    expected_names = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'}
    assert job_names == expected_names, f"Expected jobs named {expected_names}, but got {job_names}"
