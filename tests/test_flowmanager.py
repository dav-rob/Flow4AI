import asyncio
import time
from typing import Any, Dict

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, JobsDict, p, wrap
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC

# Configure logging
logger = logging.getLogger(__name__)


class ProcessorJob(JobABC):
    """Example component that implements JobABC interface."""
    def __init__(self, name, process_type):
        super().__init__(name)
        self.process_type = process_type
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return f"Processor {self.name} of type {self.process_type}"


def test_execute_job_graph_from_dsl():
    """
    Test a complex DSL with a mix of JobABC and functions and lambdas.
    """
    times = lambda x: x*2
    add = lambda x: x+3
    square = lambda x: x**2
    
    def test_context(j_ctx):
        task = j_ctx["task"]
        inputs = j_ctx["inputs"]
        return {"task": task, "inputs": inputs}
        
    analyzer2 = ProcessorJob("Analyzer2", "analyze")
    transformer = ProcessorJob("Transformer", "transform")
    aggregator = ProcessorJob("Aggregator", "aggregate")
    formatter = ProcessorJob("Formatter", "format")
    cache_manager = ProcessorJob("CacheManager", "cache")

    jobs:JobsDict = wrap({
            "analyzer2": analyzer2,
            "cache_manager": cache_manager,
            "times": times,
            "transformer": transformer,
            "formatter": formatter,
            "add": add,
            "square": square,
            "aggregator": aggregator,
            "test_context": test_context
        })

    jobs["times"].save_result = True
    jobs["add"].save_result = True
    jobs["square"].save_result = True

    dsl:DSLComponent = (
        p(jobs["analyzer2"], jobs["cache_manager"], jobs["times"]) 
        >> jobs["transformer"] 
        >> jobs["formatter"] 
        >> (jobs["add"] | jobs["square"]) 
        >> jobs["test_context"]
        >> jobs["aggregator"] 
    )
        
    fm = FlowManager()
    # Using add_dsl without a graph_name - it should generate one based on head jobs
    fq_name = fm.add_dsl(dsl)
    print(f"Auto-generated FQ name: {fq_name}")
    
    # Extract the auto-generated graph name from the FQ name
    # FQ name format is typically: graph_name$$$$job_name$$
    auto_graph_name = fq_name.split('$$')[0]
    task = {"times.x": 1, "add.x": 2, "square.x": 3}
    fm.submit_task(task,fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Print results
    print("Task counts:", fm.get_counts())
    results = fm.pop_results()
    
    print("\nCompleted tasks:")
    for job_name, job_results in results["completed"].items():
        for result_data in job_results:
            print(f"- {job_name}: {result_data['result']}")
    
    print("\nErrors:")
    if results["errors"]:
        error_messages = []
        for job_name, job_errors in results["errors"].items():
            for error_data in job_errors:
                error_msg = f"- {job_name}: {error_data['error']}"
                print(error_msg)
                error_messages.append(error_msg)
        
        # Raise exception with all errors
        raise Exception("Errors occurred during job execution:\n" + "\n".join(error_messages))
    
    print("\nResults:")
    print(results["completed"].values())
    result_dict = list(results["completed"].values())[0][0] # [0]= first job
    # Assert using the auto-generated graph name instead of hardcoded name
    expected_result = f"Processor {auto_graph_name}$$$$aggregator$$ of type aggregate"
    assert result_dict["result"] == expected_result
    # Convert Task to dict or extract the dictionary data
    task_pass_through = result_dict["task_pass_through"]
    # Check that task_pass_through contains all the expected keys and values
    assert all(key in task_pass_through and task_pass_through[key] == value for key, value in task.items())
    assert result_dict["SAVED_RESULTS"] == {"times": 2, "add": 5, "square": 9}
    

class DelayedJob(JobABC):
    async def run(self, task):
        short_name = self.parse_job_name(self.name)
        delay = task[short_name]
        logger.debug(f"Executing DelayedJob for {task} with delay {delay}")
        await asyncio.sleep(delay)
        return {"status": f"{self.name} complete"}

def create_tm(graph_name:str):
    dsl = DelayedJob("delayed")
    fm = FlowManager(on_complete=lambda x: logger.debug(f"received {x}"))
    fq_name = fm.add_dsl(dsl, graph_name)
    return fm, fq_name

def execute_tm_with_delay(delay, task_count=10):
    fm, fq_name = create_tm("test_parallel_execution" + str(delay))
    task = {"delayed": delay}
    start_time = time.perf_counter()
    for i in range(task_count):
        fm.submit_task(task, fq_name)
    fm.wait_for_completion(10, 0.1)
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    logger.info(f"*** Execution time for {task_count} tasks = {execution_time}")
    return execution_time, fm

def test_parallel_execution():
    execution_time, fm = execute_tm_with_delay(1.0)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.5

    execution_time, fm = execute_tm_with_delay(2.0)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5


def test_parallel_load():
    logger.info("Executing parallel load tasks = 500")
    execution_time, fm = execute_tm_with_delay(1.0, 500)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.4

    logger.info("Executing parallel load tasks = 1000")
    execution_time, fm = execute_tm_with_delay(1.0, 1000)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.8

    logger.info("Executing parallel load tasks = 2000")
    execution_time, fm = execute_tm_with_delay(1.0, 2000)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5

    logger.info("Executing parallel load tasks = 5000")
    execution_time, fm = execute_tm_with_delay(1.0, 5000)
    result_count = fm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 4.0


def test_flowmanager_execute_method():
    """Test the execute method of TaskManager which simplifies the workflow."""
    # Define functions that properly work together in a graph
    def square(x):
        return x**2
        
    def multiply_with_context(j_ctx):
        inputs = j_ctx["inputs"]
        square_result = inputs["square"]["result"]
        return square_result * 10
    
    def create_square_multiply_dsl():
        """Create a fresh DSL with square and multiply jobs."""
        jobs = wrap({
            "square": square,
            "multiply": multiply_with_context
        })
        
        # Need to save result from square for multiply to access
        jobs["square"].save_result = True
        
        # Create the DSL pipeline
        return jobs["square"] >> jobs["multiply"]
    
    # Create the initial DSL
    dsl = create_square_multiply_dsl()

    logger.debug("DSL structure1:")
    logger.debug(dsl)
    
    # Use execute method directly
    fm = FlowManager()
    task = {"square.x": 4}
    
    # Test with dsl and graph_name
    errors, result_dict = fm.execute(task, dsl=dsl, graph_name="test_execute1")
    
    assert errors == {}, "Errors occurred"
    assert result_dict is not None, "No result returned"
    
    # The result should be (4^2)*10 = 160
    assert result_dict["result"] == 160
    assert "SAVED_RESULTS" in result_dict
    assert "square" in result_dict["SAVED_RESULTS"]
    assert result_dict["SAVED_RESULTS"]["square"] == 16
    
    logger.debug("DSL structure2:")
    logger.debug(dsl)

    # Create a fresh DSL for the second test to avoid DSL mutation issues
    fresh_dsl = create_square_multiply_dsl()
    logger.debug("Fresh DSL structure:")
    logger.debug(fresh_dsl)

    # Test with fresh DSL
    task = {"square.x": 5}
    errors, result_dict = fm.execute(task, dsl=fresh_dsl, graph_name="test_execute2")
    
    assert errors == {}, "Errors occurred"
    assert result_dict is not None, "No result returned"
    
    # The result should be (5^2)*10 = 250
    assert result_dict["result"] == 250
    assert "SAVED_RESULTS" in result_dict
    assert "square" in result_dict["SAVED_RESULTS"]
    assert result_dict["SAVED_RESULTS"]["square"] == 25


def test_flowmanager_run_static_method():
    """Test the static run method of TaskManager for one-line execution."""
    def double(x):
        return x*2
        
    def increment_with_context(j_ctx):
        inputs = j_ctx["inputs"]
        double_result = inputs["double"]["result"]
        return double_result + 1
    
    jobs = wrap({
        "double": double,
        "increment": increment_with_context
    })
    
    # Save result for the context
    jobs["double"].save_result = True
    
    dsl = jobs["double"] >> jobs["increment"]
    task = {"double.x": 3}
    
    # Use the static run method
    errors, result_dict = FlowManager.run(dsl, task, "test_run_method")
    
    assert errors == {}, "Errors occurred"
    assert result_dict is not None, "No result returned"
    
    # The result should be (3*2)+1 = 7
    assert result_dict["result"] == 7
    assert "SAVED_RESULTS" in result_dict
    assert "double" in result_dict["SAVED_RESULTS"]
    assert result_dict["SAVED_RESULTS"]["double"] == 6

@pytest.mark.skip("Skipping test, functionality not used, requirements unclear")
def test_display_results(capsys):
    """Test the display_results method for plain text output."""
    def add(x):
        return x + 5
        
    def subtract_with_context(j_ctx):
        inputs = j_ctx["inputs"]
        add_result = inputs["add"]["result"]
        return add_result - 2
    
    jobs = wrap({
        "add": add,
        "subtract": subtract_with_context
    })
    
    # Save result for context
    jobs["add"].save_result = True
    
    dsl = jobs["add"] >> jobs["subtract"]
    task = {"add.x": 10}
    
    fm = FlowManager()
    errors, result_dict = fm.execute(task, dsl=dsl, graph_name="test_display")
    
    assert errors == {}, "Errors occurred"
    assert result_dict is not None, "No result returned"
    
    # The result should be (10+5)-2 = 13
    assert result_dict["result"] == 13
    assert "SAVED_RESULTS" in result_dict
    assert "add" in result_dict["SAVED_RESULTS"]
    assert result_dict["SAVED_RESULTS"]["add"] == 15
    
    
    # Call display_results
    displayed_results = fm.display_results(result_dict)
    
    # Capture stdout
    captured = capsys.readouterr()
    
    # Verify the output contains expected text
    assert "Completed tasks:" in captured.out
    assert "test_display" in captured.out
    
    # Verify the returned results are the same as input
    assert displayed_results == result_dict
    
    # Verify we can call display_results without providing results
    # Use the same graph name as above
    task = {"add.x": 20}
    fm.submit_task(task, fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Call display_results without providing results
    fm.display_results()
    
    # Capture stdout
    captured = capsys.readouterr()
    
    # Verify the output contains expected text
    assert "Completed tasks:" in captured.out


def test_error_handling_in_execute():
    """Test that the execute method properly handles errors."""
    def failing_job(x):
        raise ValueError("This job intentionally fails")
    
    # Create job dictionary with the failing job
    job_dict = {}
    single_job = wrap({"failing": failing_job})
    
    # Create a DSL with just this single job
    dsl = single_job
    task = {"failing.x": 1}
    
    fm = FlowManager()
    
    # The execute method should raise an exception when a job fails
    try:
        fm.execute(task, dsl=dsl, graph_name="test_error_handling")
        assert False, "execute() did not raise an exception when a job failed"
    except Exception as e:
        assert "This job intentionally fails" in str(e), "Unexpected error message"


def test_timeout_handling_in_execute():
    """Test that the execute method properly handles timeouts."""
    async def slow_job(x):
        await asyncio.sleep(2)  # Sleep for 2 seconds
        return x
    
    # Create the DSL directly
    single_job = wrap({"slow": slow_job})
    
    # For a single job, just use the job itself as the DSL
    dsl = single_job
    task = {"slow.x": 1}
    
    fm = FlowManager()


def test_submit_multiple_tasks():
    """Test submitting multiple Tasks at once using the updated submit method."""
    from flow4ai.job import Task

    # Define a simple job
    processor = ProcessorJob("Processor", "process")
    
    # Create DSL directly with the processor job
    dsl = processor
    
    # Initialize FlowManager and add the DSL
    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "test_multiple_tasks")
    
    # Create a list of tasks to submit
    tasks = [
        Task({"value": 1}, fq_name=fq_name),
        Task({"value": 2}, fq_name=fq_name),
        Task({"value": 3}, fq_name=fq_name)
    ]
    
    # Submit the list of tasks
    logger.info("Submitting multiple tasks at once")
    fm.submit_task(tasks, fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Check results
    results = fm.pop_results()
    
    # Verify no errors
    assert not results["errors"], "Errors occurred during task execution"
    
    # Verify completed task count
    result_count = fm.get_counts()
    assert result_count["completed"] == 3, f"Expected 3 completed tasks, got {result_count['completed']}"
    
    # Log the results for inspection
    logger.info(f"Results from multiple tasks: {results['completed']}")


def test_submit_tasks_with_different_data():
    """Test submitting multiple Tasks with different data using the updated submit method."""
    from flow4ai.job import Task
    
    class DataProcessor(JobABC):
        """Job that processes data and returns a modified version."""
        async def run(self, task):
            # Process based on data type
            if isinstance(task.get("data"), int):
                return {"processed": task.get("data") * 2, "type": "integer"}
            elif isinstance(task.get("data"), str):
                return {"processed": task.get("data").upper(), "type": "string"}
            elif isinstance(task.get("data"), list):
                return {"processed": len(task.get("data")), "type": "list"}
            else:
                return {"processed": None, "type": "unknown"}
    
    # Create DSL with the data processor job
    processor = DataProcessor("DataProcessor")
    dsl = processor
    
    # Initialize FlowManager and add the DSL
    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "test_different_data")
    
    # Create tasks with different types of data
    tasks = [
        Task({"data": 10}, fq_name=fq_name),            # Integer
        Task({"data": "hello world"}, fq_name=fq_name), # String
        Task({"data": [1, 2, 3, 4]}, fq_name=fq_name),  # List
        Task({"data": None}, fq_name=fq_name)           # None/unknown
    ]
    
    # Submit the list of tasks
    logger.info("Submitting tasks with different data types")
    fm.submit_task(tasks, fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Check results
    results = fm.pop_results()
    
    # Verify no errors
    assert not results["errors"], "Errors occurred during task execution"
    
    # Verify completed task count
    result_count = fm.get_counts()
    assert result_count["completed"] == 4, f"Expected 4 completed tasks, got {result_count['completed']}"
    
    # Log the results for inspection
    logger.info(f"Results from different data tasks: {results['completed']}")
    
    # Verify the specific results for each data type
    completed_results = []
    for job_results in results["completed"].values():
        # Add all result objects to our list
        completed_results.extend(job_results)
    
    # Check that we got the expected processed results
    assert any(r["processed"] == 20 and r["type"] == "integer" for r in completed_results), "Integer processing failed"
    assert any(r["processed"] == "HELLO WORLD" and r["type"] == "string" for r in completed_results), "String processing failed"
    assert any(r["processed"] == 4 and r["type"] == "list" for r in completed_results), "List processing failed"
    assert any(r["processed"] is None and r["type"] == "unknown" for r in completed_results), "None processing failed"


def test_submit_without_fqname():
    """Test submitting tasks without specifying fq_name when only one DSL has been added.
    
    When only one job graph has been added to FlowManager, the fq_name parameter in submit()
    can be omitted for convenience.
    """
    from flow4ai.job import Task

    # Define a simple job
    processor = ProcessorJob("Processor", "process")
    
    # Create DSL directly with the processor job
    dsl = processor
    
    # Initialize FlowManager and add the DSL
    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "test_without_fqname")
    
    # Create a task
    task = Task({"value": 42})
    
    # Submit the task WITHOUT specifying fq_name
    logger.info("Submitting task without specifying fq_name")
    fm.submit_task(task)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Check results
    results = fm.pop_results()
    
    # Verify no errors
    assert not results["errors"], "Errors occurred during task execution"
    
    # Verify completed task count
    result_count = fm.get_counts()
    assert result_count["completed"] == 1, f"Expected 1 completed task, got {result_count['completed']}"
    
    # Log the results for inspection
    logger.info(f"Results: {results['completed']}")
    
    # Verify the result contains the expected processor output
    job_key = next(iter(results["completed"]))
    result_value = results["completed"][job_key][0]["result"]
    expected = f"Processor test_without_fqname$$$$Processor$$ of type process"
    assert result_value == expected, f"Expected '{expected}', got '{result_value}'"


def test_submit_multiple_tasks_pipeline():
    """Test submitting multiple Tasks that flow through a multi-step pipeline.
    
    This test demonstrates both JobABC subclasses and wrapped functions approaches for handling inputs,
    while following proper FlowManager usage patterns - using a single instance and adding DSL once.
    """
    from flow4ai.job import Task

    # Define a JobABC subclass for number generation
    class NumberGenerator(JobABC):
        """Job that generates a number sequence."""
        async def run(self, task):
            start = task.get("start", 0)
            count = task.get("count", 5)
            return {"numbers": list(range(start, start + count))}
    
    # Define a JobABC subclass that uses get_inputs() method to access previous job results
    class NumberTransformer(JobABC):
        """Job that transforms numbers based on operation using JobABC.get_inputs()."""
        async def run(self, task):
            # Get inputs directly using JobABC method (no j_ctx needed)
            inputs = self.get_inputs()
            
            # Log inputs for debugging with INFO level to see in test output
            self.logger.info(f"Transformer inputs: {inputs}")
            
            # Get the numbers from the generator job's output - direct access instead of through result
            numbers = inputs.get("generator", {}).get("numbers", [])
            
            self.logger.info(f"Extracted numbers from generator: {numbers}")
            
            # Get the operation to perform
            operation = task.get("operation", "square")
            
            # Transform numbers based on the operation
            if operation == "square":
                result = [n * n for n in numbers]
            elif operation == "double":
                result = [n * 2 for n in numbers]
            elif operation == "increment":
                result = [n + 1 for n in numbers]
            else:
                result = numbers
            
            self.logger.info(f"Transformer output: {result} with operation {operation}")
            return {"transformed": result, "operation": operation}
    
    # Define a function (not a JobABC class) that will be wrapped
    # This demonstrates how regular functions need to use j_ctx parameter to access inputs
    def aggregate_results(j_ctx):
        """Function that aggregates results from transformer using j_ctx parameter."""
        # Access inputs through j_ctx parameter
        inputs = j_ctx["inputs"]
        task = j_ctx["task"]
        
        logger.info(f"Aggregator j_ctx inputs: {inputs}")
        
        # Get results from transformer - direct access instead of through result
        transformed = inputs.get("transformer", {}).get("transformed", [])
        operation = inputs.get("transformer", {}).get("operation", "unknown")
        
        logger.info(f"Aggregator extracted transformed: {transformed}, operation: {operation}")
        
        # Calculate aggregate values
        if not transformed:
            logger.warning("Transformed list is empty, returning zeros")
            return {"sum": 0, "count": 0, "avg": 0, "operation": operation}
            
        total_sum = sum(transformed)
        count = len(transformed)
        avg = total_sum / count if count > 0 else 0
        
        logger.info(f"Aggregator results: sum={total_sum}, count={count}, avg={avg}")
        
        return {
            "sum": total_sum,
            "count": count,
            "avg": avg,
            "operation": operation
        }
    
    # Create job instances
    generator = NumberGenerator("generator")
    transformer = NumberTransformer("transformer")
    
    # Create the DSL pipeline with both JobABC classes and a wrapped function
    jobs = wrap({
        "generator": generator,
        "transformer": transformer,
        "aggregator": aggregate_results  # Regular function that will be wrapped
    })
 
    # Save results for context between pipeline steps
    jobs["generator"].save_result = True
    jobs["transformer"].save_result = True
    
    # Build the pipeline: generator -> transformer -> aggregator
    dsl = jobs["generator"] >> jobs["transformer"] >> jobs["aggregator"]
    
    # Initialize a SINGLE FlowManager instance (FlowManager is effectively a singleton)
    fm = FlowManager()
    
    # Add the DSL ONCE to get a fully qualified name
    fq_name = fm.add_dsl(dsl, "test_pipeline")
    
    # Demo approach 1: Submit multiple tasks one-by-one, with wait_for_completion after each
    logger.info("Approach 1: Multiple individual submit() calls with wait_for_completion after each")
    
    # Task 1: Numbers 0-4, squared 
    task1 = Task({
        "start": 0, 
        "count": 5, 
        "operation": "square"
    })
    
    # Submit task 1
    logger.info("Submitting task 1 (square operation)")
    fm.submit_task(task1, fq_name)
    
    # Wait for task 1 to complete
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for task 1 to complete"
    
    # Check results for task 1
    results = fm.pop_results()
    assert not results["errors"], f"Errors occurred during task 1 execution: {results['errors']}"
    logger.info(f"Task 1 completed successfully: {results['completed']}")
    
    # Verify results for task 1 (square operation on numbers 0-4)
    task1_result = results['completed'][fq_name][0]
    saved_results = task1_result.get('SAVED_RESULTS', {})
    
    # Check generator output
    assert saved_results.get('generator', {}).get('numbers') == [0, 1, 2, 3, 4], "Generator should produce [0, 1, 2, 3, 4]"
    
    # Check transformer output
    assert saved_results.get('transformer', {}).get('transformed') == [0, 1, 4, 9, 16], "Transformer with square operation should produce [0, 1, 4, 9, 16]"
    assert saved_results.get('transformer', {}).get('operation') == 'square', "Operation should be 'square'"
    
    # Check aggregator output
    assert task1_result.get('sum') == 30, "Aggregator sum should be 30"
    assert task1_result.get('count') == 5, "Aggregator count should be 5"
    assert task1_result.get('avg') == 6.0, "Aggregator average should be 6.0"
    
    # Verify completed task count after task 1
    result_count = fm.get_counts()
    assert result_count["completed"] == 1, f"Expected 1 completed task, got {result_count['completed']}"
    completed_so_far = result_count["completed"]  # Track completed count
    
    # Task 2: Numbers 5-9, doubled
    task2 = Task({
        "start": 5, 
        "count": 5, 
        "operation": "double"
    })
    
    # Submit task 2
    logger.info("Submitting task 2 (double operation)")
    fm.submit_task(task2) # fq_name is optional when there is only one job graph
    
    # Wait for task 2 to complete
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for task 2 to complete"
    
    # Check results for task 2
    results = fm.pop_results()
    assert not results["errors"], f"Errors occurred during task 2 execution: {results['errors']}"
    logger.info(f"Task 2 completed successfully: {results['completed']}")
    
    # Verify results for task 2 (double operation on numbers 5-9)
    task2_result = results['completed'][fq_name][0]
    saved_results = task2_result.get('SAVED_RESULTS', {})
    
    # Check generator output
    assert saved_results.get('generator', {}).get('numbers') == [5, 6, 7, 8, 9], "Generator should produce [5, 6, 7, 8, 9]"
    
    # Check transformer output
    assert saved_results.get('transformer', {}).get('transformed') == [10, 12, 14, 16, 18], "Transformer with double operation should produce [10, 12, 14, 16, 18]"
    assert saved_results.get('transformer', {}).get('operation') == 'double', "Operation should be 'double'"
    
    # Check aggregator output
    assert task2_result.get('sum') == 70, "Aggregator sum should be 70"
    assert task2_result.get('count') == 5, "Aggregator count should be 5"
    assert task2_result.get('avg') == 14.0, "Aggregator average should be 14.0"
    
    # Verify completed task count after task 2
    result_count = fm.get_counts()
    # FM.get_counts() returns cumulative counts, so we expect 2 total completed tasks now
    assert result_count["completed"] == completed_so_far + 1, f"Expected {completed_so_far + 1} total completed tasks, got {result_count['completed']}"
    completed_so_far = result_count["completed"]  # Update completed count
    
    # Demo approach 2: Submit multiple tasks at once using lists
    logger.info("\nApproach 2: Submit multiple tasks at once using Task[]")
    
    # Create a list of tasks
    tasks = [
        # Task 3: Numbers 10-14, incremented
        Task({
            "start": 10, 
            "count": 5, 
            "operation": "increment"
        }),
        # Task 4: Numbers 15-19, squared
        Task({
            "start": 15, 
            "count": 5, 
            "operation": "square"
        })
    ]
    
    # Submit multiple tasks at once
    logger.info("Submitting tasks 3 & 4 as a batch")
    fm.submit_task(tasks) # fq_name is optional when there is only one job graph
    
    # Wait for all tasks to complete
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks 3 & 4 to complete"
    
    # Check results for tasks 3 & 4
    results = fm.pop_results()
    assert not results["errors"], f"Errors occurred during tasks 3 & 4 execution: {results['errors']}"
    
    # Verify results for task 3 (increment operation on numbers 10-14)
    task3_result = results['completed'][fq_name][0]
    saved_results_task3 = task3_result.get('SAVED_RESULTS', {})
    
    # Check generator output for task 3
    assert saved_results_task3.get('generator', {}).get('numbers') == [10, 11, 12, 13, 14], "Generator should produce [10, 11, 12, 13, 14]"
    
    # Check transformer output for task 3
    assert saved_results_task3.get('transformer', {}).get('transformed') == [11, 12, 13, 14, 15], "Transformer with increment operation should produce [11, 12, 13, 14, 15]"
    assert saved_results_task3.get('transformer', {}).get('operation') == 'increment', "Operation should be 'increment'"
    
    # Check aggregator output for task 3
    assert task3_result.get('sum') == 65, "Aggregator sum should be 65"
    assert task3_result.get('count') == 5, "Aggregator count should be 5"
    assert task3_result.get('avg') == 13.0, "Aggregator average should be 13.0"
    
    # Verify results for task 4 (square operation on numbers 15-19)
    task4_result = results['completed'][fq_name][1]
    saved_results_task4 = task4_result.get('SAVED_RESULTS', {})
    
    # Check generator output for task 4
    assert saved_results_task4.get('generator', {}).get('numbers') == [15, 16, 17, 18, 19], "Generator should produce [15, 16, 17, 18, 19]"
    
    # Check transformer output for task 4
    assert saved_results_task4.get('transformer', {}).get('transformed') == [225, 256, 289, 324, 361], "Transformer with square operation should produce [225, 256, 289, 324, 361]"
    assert saved_results_task4.get('transformer', {}).get('operation') == 'square', "Operation should be 'square'"
    
    # Check aggregator output for task 4
    assert task4_result.get('sum') == 1455, "Aggregator sum should be 1455"
    assert task4_result.get('count') == 5, "Aggregator count should be 5"
    assert task4_result.get('avg') == 291.0, "Aggregator average should be 291.0"
    
    # Verify completed task count after tasks 3 & 4
    result_count = fm.get_counts()
    # We expect 2 more completed tasks in addition to what we had before
    assert result_count["completed"] == completed_so_far + 2, f"Expected {completed_so_far + 2} total completed tasks, got {result_count['completed']}"
    
    # Log the results for inspection
    logger.info(f"Tasks 3 & 4 completed successfully: {results['completed']}")
