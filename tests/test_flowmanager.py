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
    fq_name =fm.add_dsl(dsl, "test_execute_job_graph_from_dsl")
    print(fq_name)
    task = {"times.x": 1, "add.x": 2, "square.x": 3}
    fm.submit(task,fq_name)
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
    assert result_dict["result"] == "Processor test_execute_job_graph_from_dsl$$$$aggregator$$ of type aggregate"
    assert result_dict["task_pass_through"] == task
    assert result_dict["SAVED_RESULTS"] == {"times": 2, "add": 5, "square": 9}
    

def test_completion_callback():
    once = lambda x: x + "upon a time"
    ina = lambda x: x + "galaxy far far away"

    async def collate(j_ctx):
        await asyncio.sleep(2)
        inputs = j_ctx["inputs"]
        output = f"{inputs['once']['result']} {inputs['ina']['result']}"
        return output

    def post_processor(result):
        assert result["result"] == "once upon a time in a galaxy far far away"
            
    jobs = wrap({
        "once": once,
        "ina": ina,
        "collate": collate
    })

    dsl =(jobs["once"] | jobs["ina"] ) >> jobs["collate"]
        
    fm = FlowManager(on_complete=post_processor)
    fq_name =fm.add_dsl(dsl, "test_completion_callback")
    print(fq_name)
    task = {"once.x": "once ", "ina.x": "in a "}
    fm.submit(task,fq_name)
    fm.wait_for_completion()

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
    tm, fq_name = create_tm("test_parallel_execution" + str(delay))
    task = {"delayed": delay}
    start_time = time.perf_counter()
    for i in range(task_count):
        tm.submit(task, fq_name)
    tm.wait_for_completion()
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    logger.info(f"*** Execution time for {task_count} tasks = {execution_time}")
    return execution_time, tm

def test_parallel_execution():
    execution_time, tm = execute_tm_with_delay(1.0)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.5

    execution_time, tm = execute_tm_with_delay(2.0)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5


def test_parallel_load():
    logger.info("Executing parallel load tasks = 500")
    execution_time, tm = execute_tm_with_delay(1.0, 500)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.4

    logger.info("Executing parallel load tasks = 1000")
    execution_time, tm = execute_tm_with_delay(1.0, 1000)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.8

    logger.info("Executing parallel load tasks = 2000")
    execution_time, tm = execute_tm_with_delay(1.0, 2000)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5

    logger.info("Executing parallel load tasks = 5000")
    execution_time, tm = execute_tm_with_delay(1.0, 5000)
    result_count = tm.get_counts()
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
    fm.submit(task, fq_name)
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
    
    # The execute method should raise a TimeoutError when timeout is exceeded
    try:
        # Set timeout to 0.1 seconds, which is less than the 2-second sleep
        fm.execute(task, dsl=dsl, graph_name="test_timeout", timeout=0.1)
        assert False, "execute() did not raise a TimeoutError when timeout was exceeded"
    except TimeoutError:
        pass  # Expected behavior
    except Exception as e:
        assert False, f"Unexpected exception: {e}"

