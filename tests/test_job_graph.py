import asyncio
import time
from typing import Any, Dict

from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC, Task, job_graph_context_manager
from flow4ai.job_loader import JobFactory
from flow4ai.jobs.default_jobs import DefaultHeadJob


class MockJob(JobABC):
    def run(self):
        pass

class MockJobSubclass(MockJob):
    pass



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

def collect_result(results):
    """Create a picklable result collector function that appends to the given list."""
    def collector(result):
        results.append(result)
    return collector


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

class E(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class F(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class G(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class H(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class I(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {'result': f'processed by {self.name}'}

class J(MockJob):
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
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

async def execute_graph(graph_definition: dict, jobs: dict, data: dict) -> Any:
    head_job = JobFactory.create_job_graph(graph_definition, jobs)
    job_set = JobABC.job_set(head_job)
    async with job_graph_context_manager(job_set):
        final_result = await head_job._execute(Task(data))
    return final_result

def test_execute_graph1():
    final_result1 = asyncio.run(execute_graph(graph_definition1, jobs, data))
    # Extract just the job result data, ignoring task_pass_through
    result_data = {k: v for k, v in final_result1.items() if k not in ['task_pass_through', 'RETURN_JOB']}
    assert result_data == {
            'dataD1': {},
            'dataD2': {}
        }

def test_job_set():
    head_job = JobFactory.create_job_graph(graph_definition1, jobs)
    job_name_set = head_job.job_set_str()
    assert job_name_set == {'A', 'B', 'C', 'D'}

def test_execute_graph2():
    final_result2 = asyncio.run(execute_graph(graph_definition2, jobs, data))
    # Extract just the job result data, ignoring task_pass_through
    result_data = {k: v for k, v in final_result2.items() if k not in ['task_pass_through', 'RETURN_JOB']}
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
    head_job = JobFactory.create_job_graph(graph_definition_complex, jobs)
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
    head_job = JobFactory.create_job_graph(graph_definition_complex, jobs)
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

def test_multiple_head_nodes():
    """Test that multiple head nodes are handled correctly by creating a DefaultHeadJob."""
    # Test graph with two independent heads
    graph_definition = {
        "A": {"next": ["C"]},
        "B": {"next": ["C"]},
        "C": {"next": []}
    }
    
    job_instances = {
        "A": A("A"),
        "B": B("B"), 
        "C": C("C")
    }
    
    # Create job graph
    head_job = JobFactory.create_job_graph(graph_definition, job_instances)
    
    # Verify default head was created and is correct type
    assert isinstance(head_job, DefaultHeadJob)
    assert head_job.name in job_instances
    
    # Verify graph was updated correctly
    assert head_job.name in graph_definition
    assert set(graph_definition[head_job.name]["next"]) == {"A", "B"}
    
    # Verify next_jobs were set correctly
    assert len(head_job.next_jobs) == 2
    next_job_names = {job.name for job in head_job.next_jobs}
    assert next_job_names == {"A", "B"}


def test_multiple_tail_nodes():
    """Test that multiple tail nodes are handled correctly by creating a DefaultTailJob."""
    # Test graph with two independent tails
    graph_definition = {
        "A": {"next": ["B", "C"]},
        "B": {"next": []},
        "C": {"next": []}
    }
    
    job_instances = {
        "A": A("A"),
        "B": B("B"), 
        "C": C("C")
    }
    
    # Create job graph
    head_job = JobFactory.create_job_graph(graph_definition, job_instances)
    
    # Find the default tail job in the job_instances
    default_tail_jobs = [job for name, job in job_instances.items() 
                        if "DefaultTailJob" in name]
    assert len(default_tail_jobs) == 1, "Expected exactly one DefaultTailJob"
    default_tail_job = default_tail_jobs[0]
    
    # Verify default tail was created and is correct type
    from flow4ai.jobs.default_jobs import DefaultTailJob
    assert isinstance(default_tail_job, DefaultTailJob)
    assert default_tail_job.name in job_instances
    
    # Verify graph was updated correctly
    assert default_tail_job.name in graph_definition
    assert graph_definition[default_tail_job.name]["next"] == []
    
    # Verify original tail nodes now point to the default tail
    assert graph_definition["B"]["next"] == [default_tail_job.name]
    assert graph_definition["C"]["next"] == [default_tail_job.name]
    
    # Verify next_jobs were set correctly for original tail nodes
    b_job = job_instances["B"]
    c_job = job_instances["C"]
    assert len(b_job.next_jobs) == 1
    assert len(c_job.next_jobs) == 1
    assert b_job.next_jobs[0].name == default_tail_job.name
    assert c_job.next_jobs[0].name == default_tail_job.name

def test_simple_parallel_jobs():
    """Test that a graph with multiple head nodes and multiple tail nodes 
    is handled correctly by creating both a DefaultHeadJob and a DefaultTailJob."""
    # Test graph with three independent parallel jobs
    graph_definition = {
        "A": {"next": []},
        "B": {"next": []},
        "C": {"next": []}
    }
    
    job_instances = {
        "A": A("A"),
        "B": B("B"), 
        "C": C("C")
    }
    
    # Create job graph
    head_job = JobFactory.create_job_graph(graph_definition, job_instances)
    
    # Verify default head was created and is correct type
    from flow4ai.jobs.default_jobs import DefaultHeadJob, DefaultTailJob
    assert isinstance(head_job, DefaultHeadJob)
    assert head_job.name in job_instances
    
    # Find the default tail job in the job_instances
    default_tail_jobs = [job for name, job in job_instances.items() 
                        if "DefaultTailJob" in name]
    assert len(default_tail_jobs) == 1, "Expected exactly one DefaultTailJob"
    default_tail_job = default_tail_jobs[0]
    
    # Verify default tail was created and is correct type
    assert isinstance(default_tail_job, DefaultTailJob)
    assert default_tail_job.name in job_instances
    
    # Verify graph structure was updated correctly
    # 1. DefaultHead points to A, B, C
    assert head_job.name in graph_definition
    assert set(graph_definition[head_job.name]["next"]) == {"A", "B", "C"}
    
    # 2. A, B, C point to DefaultTail
    assert graph_definition["A"]["next"] == [default_tail_job.name]
    assert graph_definition["B"]["next"] == [default_tail_job.name]
    assert graph_definition["C"]["next"] == [default_tail_job.name]
    
    # 3. DefaultTail has no next nodes
    assert graph_definition[default_tail_job.name]["next"] == []
    
    # Verify next_jobs were set correctly
    # 1. DefaultHead has 3 next jobs: A, B, C
    assert len(head_job.next_jobs) == 3
    head_next_job_names = {job.name for job in head_job.next_jobs}
    assert head_next_job_names == {"A", "B", "C"}
    
    # 2. A, B, C each have 1 next job: DefaultTail
    a_job = job_instances["A"]
    b_job = job_instances["B"]
    c_job = job_instances["C"]
    assert len(a_job.next_jobs) == 1
    assert len(b_job.next_jobs) == 1
    assert len(c_job.next_jobs) == 1
    assert a_job.next_jobs[0].name == default_tail_job.name
    assert b_job.next_jobs[0].name == default_tail_job.name
    assert c_job.next_jobs[0].name == default_tail_job.name
    
    # 3. DefaultTail has no next jobs
    assert len(default_tail_job.next_jobs) == 0


def test_execute_multiple_head_nodes():
    """Test execution of a graph with multiple head nodes."""
    # Create a graph with multiple head nodes
    graph_definition = {
        "A": {"next": ["D"]},
        "B": {"next": ["D"]},
        "C": {"next": ["D"]},
        "D": {"next": []}
    }
    
    # Create job instances
    job_instances = {
        "A": A("A"),
        "B": B("B"),
        "C": C("C"),
        "D": D("D")
    }
    
    # Execute the graph
    data = {"input": "test"}
    final_result = asyncio.run(execute_graph(graph_definition, job_instances, data))
    
    # Extract just the job result data, ignoring task_pass_through
    result_data = {k: v for k, v in final_result.items() if k not in ['task_pass_through', 'RETURN_JOB']}
    
    # Verify final job data is returned (only D's data is in the final result)
    assert result_data == {
        'dataD1': {},
        'dataD2': {}
    }
    
    # Verify the RETURN_JOB is D
    assert final_result['RETURN_JOB'] == 'D'
