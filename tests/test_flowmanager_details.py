import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, JobsDict, job
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC, Task

# Configure logging
logger = logging.getLogger(__name__)


class NumberGenerator(JobABC):
    """Generates a sequence of numbers starting from 'start' with length 'count'."""
    def __init__(self, name):
        super().__init__(name)
    
    async def run(self, task):
        start = task.get("start", 0)
        count = task.get("count", 5)
        numbers = list(range(start, start + count))
        logger.info(f"[{self.name}] Generated numbers: {numbers}")
        return {"numbers": numbers}


class MathOperation(JobABC):
    """Performs a mathematical operation on numbers from previous job."""
    def __init__(self, name, operation="square"):
        super().__init__(name)
        self.operation = operation
    
    async def run(self, task):
        # Get inputs from previous job using the get_inputs method
        inputs = self.get_inputs()
        logger.info(f"[{self.name}] Received inputs: {inputs}")
        
        # Get the numbers from the input job (assuming it's the first input)
        input_job_name = list(inputs.keys())[0] if inputs else None
        numbers = inputs.get(input_job_name, {}).get("numbers", [])
        
        # Override operation if specified in task
        operation = task.get("operation", self.operation)
        
        if not numbers:
            logger.warning(f"[{self.name}] No numbers found in inputs")
            return {"result": [], "operation": operation}
            
        logger.info(f"[{self.name}] Performing {operation} on {numbers}")
        
        # Perform the requested operation
        if operation == "square":
            result = [n * n for n in numbers]
        elif operation == "double":
            result = [n * 2 for n in numbers]
        elif operation == "increment":
            result = [n + 1 for n in numbers]
        elif operation == "sum":
            result = [sum(numbers)]
        elif operation == "multiply":
            import operator
            from functools import reduce
            result = [reduce(operator.mul, numbers, 1)]
        else:
            result = numbers
            
        logger.info(f"[{self.name}] Result: {result}")
        return {"numbers": result, "operation": operation}


class Aggregator(JobABC):
    """Aggregates results from previous math operations."""
    def __init__(self, name):
        super().__init__(name)
    
    async def run(self, task):
        # Get inputs from all previous jobs
        inputs = self.get_inputs()
        logger.info(f"[{self.name}] Aggregator inputs: {inputs}")
        
        all_results = {}
        
        # Collect all numbers from inputs
        for job_name, job_result in inputs.items():
            if "numbers" in job_result:
                all_results[job_name] = {
                    "numbers": job_result.get("numbers", []),
                    "operation": job_result.get("operation", "unknown")  
                }
        
        # Calculate statistics on all collected numbers
        all_numbers = []
        for job_info in all_results.values():
            all_numbers.extend(job_info.get("numbers", []))
            
        if not all_numbers:
            logger.warning(f"[{self.name}] No numbers found to aggregate")
            return {"sum": 0, "avg": 0, "min": 0, "max": 0, "count": 0}
        
        stats = {
            "sum": sum(all_numbers),
            "avg": sum(all_numbers) / len(all_numbers),
            "min": min(all_numbers),
            "max": max(all_numbers),
            "count": len(all_numbers)
        }
        
        logger.info(f"[{self.name}] Aggregated stats: {stats}")
        return stats


class SimpleJob(JobABC):
    """Example component that implements JobABC interface for testing."""
    def __init__(self, name):
        super().__init__(name)
    
    async def run(self, task):
        logger.info(f"Processing task in {self.name}")
        return {"result": f"Job {self.name} processed task"}


def test_add_dsl_resubmission():
    """Test that resubmitting the same DSL returns the original FQ name.
    
    This verifies our enhancement to the add_dsl method that tracks previously added DSLs
    and returns their FQ name without reprocessing them.
    """
    # Create job instances
    job1 = SimpleJob("job1")
    job2 = SimpleJob("job2")
    
    # Wrap jobs in a dictionary
    jobs = job({
        "job1": job1,
        "job2": job2
    })
    
    # Create a simple pipeline: job1 >> job2
    dsl = jobs["job1"] >> jobs["job2"]
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # First submission - should process normally
    logger.info("First DSL submission")
    fq_name1 = fm.add_dsl(dsl, "test_graph", "test")
    logger.info(f"Received FQ name: {fq_name1}")
    
    # Verify DSL is marked as already added
    assert hasattr(dsl, "_f4a_already_added")
    assert dsl._f4a_already_added is True
    
    # Verify head job has reference to source DSL
    head_job = fm.job_graph_map[fq_name1]
    assert hasattr(head_job, "_f4a_source_dsl")
    assert head_job._f4a_source_dsl is dsl
    
    # Second submission with same DSL - should return original FQ name
    logger.info("Second DSL submission (same object)")
    fq_name2 = fm.add_dsl(dsl, "test_graph", "test")
    logger.info(f"Received FQ name: {fq_name2}")
    
    # Should be the same FQ name
    assert fq_name1 == fq_name2, f"Expected same FQ name: {fq_name1} != {fq_name2}"
    
    # Third submission with different graph name and variant
    # Since it's the same DSL object, should still return original FQ name
    logger.info("Third DSL submission (same object, different graph name)")
    fq_name3 = fm.add_dsl(dsl, "different_graph", "different")
    logger.info(f"Received FQ name: {fq_name3}")
    
    # Still should be the same FQ name
    assert fq_name1 == fq_name3, f"Expected same FQ name: {fq_name1} != {fq_name3}"


def test_dsl_submission_with_tasks():
    """Test submitting tasks to a reused DSL FQ name."""
    # Create job instances
    processor1 = SimpleJob("processor1")
    processor2 = SimpleJob("processor2")
    
    # Wrap jobs
    jobs = job({
        "processor1": processor1,
        "processor2": processor2
    })
    
    # Enable result saving
    jobs["processor1"].save_result = True
    jobs["processor2"].save_result = True
    
    # Create pipeline
    dsl = jobs["processor1"] >> jobs["processor2"]
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # First submission
    fq_name = fm.add_dsl(dsl, "test_pipeline")
    
    # Create and submit a task
    task = Task({"input": "test data"})
    fm.submit_task(task, fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Task did not complete successfully"
    
    # Get results
    results = fm.pop_results()
    assert "completed" in results
    assert len(results["completed"]) > 0, "No completed results found"
    
    # Submit the same DSL again - should get same FQ name
    same_fq_name = fm.add_dsl(dsl, "different_name")
    assert fq_name == same_fq_name, "Did not get the same FQ name for resubmitted DSL"
    
    # Submit another task using the returned FQ name
    task2 = Task({"input": "more test data"})
    fm.submit_task(task2, same_fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Second task did not complete successfully"
    
    # Get results
    results2 = fm.pop_results()
    assert "completed" in results2
    assert len(results2["completed"]) > 0, "No completed results found for second task"


def test_new_dsl_with_same_structure():
    """Test that two DSLs with the same structure get unique FQ names.
    
    This test confirms the updated system behavior: Different DSL objects get unique FQ names
    even if they have the same structure, to prevent collisions and ensure correct input handling.
    """
    # Create a FlowManager
    fm = FlowManager()
    
    # Create first DSL
    job1 = SimpleJob("job1")
    job2 = SimpleJob("job2")
    jobs1 = job({
        "job1": job1,
        "job2": job2
    })
    dsl1 = jobs1["job1"] >> jobs1["job2"]
    
    # Add first DSL
    logger.info("Adding first DSL")
    fq_name1 = fm.add_dsl(dsl1)
    logger.info(f"First DSL FQ name: {fq_name1}")
    
    # Extract the auto-generated graph name
    graph_name1 = fq_name1.split('$$')[0]
    
    # Create second DSL with same structure but different objects
    job3 = SimpleJob("job1")  # Same name but different object
    job4 = SimpleJob("job2")  # Same name but different object
    jobs2 = job({
        "job1": job3,
        "job2": job4
    })
    dsl2 = jobs2["job1"] >> jobs2["job2"]
    
    # Add second DSL
    logger.info("Adding second DSL with same structure but different objects")
    fq_name2 = fm.add_dsl(dsl2)
    logger.info(f"Second DSL FQ name: {fq_name2}")
    
    # Extract the auto-generated graph name
    graph_name2 = fq_name2.split('$$')[0]
    
    # New behavior: Different DSLs should get unique FQ names even with the same structure
    assert fq_name1 != fq_name2, "Different DSL objects with same structure should get unique FQ names"
    
    # Check the _f4a_source_dsl reference for the first DSL's head job
    head_job1 = fm.job_graph_map[fq_name1]
    assert hasattr(head_job1, "_f4a_source_dsl")
    assert head_job1._f4a_source_dsl is dsl1, "First head job should reference first DSL"
    
    # Check the _f4a_source_dsl reference for the second DSL's head job
    head_job2 = fm.job_graph_map[fq_name2]
    assert hasattr(head_job2, "_f4a_source_dsl")
    assert head_job2._f4a_source_dsl is dsl2, "Second head job should reference second DSL"
    
    # Create a third DSL with different job name structure
    job5 = SimpleJob("processorA")
    job6 = SimpleJob("processorB")
    jobs3 = job({
        "processorA": job5,
        "processorB": job6
    })
    dsl3 = jobs3["processorA"] >> jobs3["processorB"]
    
    # Add third DSL
    logger.info("Adding third DSL with different job names")
    fq_name3 = fm.add_dsl(dsl3)
    logger.info(f"Third DSL FQ name: {fq_name3}")
    
    # Extract the auto-generated graph name
    graph_name3 = fq_name3.split('$$')[0]
    
    # FQ name should be different with different job names
    assert fq_name1 != fq_name3, "DSLs with different job names should get different FQ names"


def test_add_dsl_dict_single_graph_no_variants():
    """Test add_dsl_dict with a single graph without variants.
    
    This tests the simplified DSL dictionary format:
    { "graph_name": dsl }
    
    Uses math operations to demonstrate data flow between jobs.
    """
    # Create job instances for a math pipeline
    generator = NumberGenerator("generator")
    squarer = MathOperation("squarer", operation="square")
    aggregator = Aggregator("aggregator")
    
    # Wrap jobs in a dictionary
    jobs = job({
        "generator": generator,
        "squarer": squarer,
        "aggregator": aggregator
    })
    
    # Create a math pipeline: generator -> squarer -> aggregator
    dsl = jobs["generator"] >> jobs["squarer"] >> jobs["aggregator"]
    
    # Save results for context between pipeline steps
    jobs["generator"].save_result = True
    jobs["squarer"].save_result = True
    
    # Create DSL dict with a single graph, no variants
    dsl_dict = {
        "math_graph": dsl
    }
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # Add the DSL dict
    logger.info("Adding DSL dict with single graph, no variants")
    fq_names = fm.add_dsl_dict(dsl_dict)
    
    # Verify a single FQ name was returned
    assert len(fq_names) == 1, "Should return exactly one FQ name"
    fq_name = fq_names[0]
    logger.info(f"Received FQ name: {fq_name}")
    
    # Verify the head job exists in the job map
    assert fq_name in fm.job_graph_map, f"FQ name {fq_name} should be in job_map"
    
    # Submit a task with numbers 1-5 to be squared
    task = Task({
        "start": 1,
        "count": 5,
        "operation": "square"
    })
    logger.info("Submitting task to the graph")
    fm.submit_task(task)  # No need to specify fq_name when only one graph exists
    
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for task to complete"
    
    # Check results
    results = fm.pop_results()
    logger.info(f"Results: {results}")
    assert not results["errors"], f"Errors occurred during task execution: {results['errors']}"
    assert len(results["completed"]) > 0, "No completed tasks found"
    
    # Get the task result
    task_result = results['completed'][fq_name][0]
    logger.info(f"Task result: {task_result}")
    
    # Verify specific result values from the aggregator
    # For numbers 1,2,3,4,5 squared to 1,4,9,16,25, the sum is 55
    assert 'sum' in task_result, "Missing 'sum' in aggregator result"
    assert task_result['sum'] == 55, f"Expected sum=55, got {task_result['sum']}"
    
    # The average should be 55/5 = 11
    assert 'avg' in task_result, "Missing 'avg' in aggregator result"
    assert task_result['avg'] == 11.0, f"Expected avg=11.0, got {task_result['avg']}"
    
    # Min should be 1, max should be 25
    assert 'min' in task_result, "Missing 'min' in aggregator result"
    assert task_result['min'] == 1, f"Expected min=1, got {task_result['min']}"
    
    assert 'max' in task_result, "Missing 'max' in aggregator result"
    assert task_result['max'] == 25, f"Expected max=25, got {task_result['max']}"
    
    # Count should be 5
    assert 'count' in task_result, "Missing 'count' in aggregator result" 
    assert task_result['count'] == 5, f"Expected count=5, got {task_result['count']}"
    
    # Check saved results from each stage
    if "SAVED_RESULTS" in task_result:
        saved_results = task_result.get("SAVED_RESULTS", {})
        logger.info(f"Saved results: {saved_results}")
        
        # Verify generator results (numbers 1-5)
        assert "generator" in saved_results, "Missing generator in saved results"
        assert "numbers" in saved_results["generator"], "Missing 'numbers' in generator result"
        assert saved_results["generator"]["numbers"] == [1, 2, 3, 4, 5], \
            f"Expected [1,2,3,4,5], got {saved_results['generator']['numbers']}"
        
        # Verify squarer results (numbers squared: 1,4,9,16,25)
        assert "squarer" in saved_results, "Missing squarer in saved results"
        assert "numbers" in saved_results["squarer"], "Missing 'numbers' in squarer result"
        assert saved_results["squarer"]["numbers"] == [1, 4, 9, 16, 25], \
            f"Expected [1,4,9,16,25], got {saved_results['squarer']['numbers']}"
        assert saved_results["squarer"]["operation"] == "square", \
            f"Expected operation='square', got {saved_results['squarer']['operation']}"


def test_add_dsl_dict_single_graph_with_variants():
    """Test add_dsl_dict with a single graph with variants.
    
    This tests the DSL dictionary format with variants:
    { "graph_name": { "variant1": dsl1, "variant2": dsl2 } }
    
    Uses math operations with different configurations for each variant.
    """
    # Create a helper function to build a DSL pipeline with specified operation
    def create_math_pipeline(prefix: str, operation: str):
        generator = NumberGenerator(f"{prefix}_generator")
        math_op = MathOperation(f"{prefix}_operation", operation=operation)
        aggregator = Aggregator(f"{prefix}_aggregator")
        
        jobs = job({
            "generator": generator,
            "operation": math_op,
            "aggregator": aggregator
        })
        
        # Save results for all jobs to verify later
        jobs["generator"].save_result = True
        jobs["operation"].save_result = True
        
        return jobs["generator"] >> jobs["operation"] >> jobs["aggregator"]
    
    # Create pipelines for each variant with different operations
    dev_dsl = create_math_pipeline("dev", "square")   # Square operation for dev
    prod_dsl = create_math_pipeline("prod", "double")  # Double operation for prod
    
    # Create DSL dict with a single graph with variants
    dsl_dict = {
        "math_graph": {
            "dev": dev_dsl,
            "prod": prod_dsl
        }
    }
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # Add the DSL dict
    logger.info("Adding DSL dict with single graph, with variants")
    fq_names = fm.add_dsl_dict(dsl_dict)
    
    # Verify two FQ names were returned (one for each variant)
    assert len(fq_names) == 2, "Should return exactly two FQ names (one for each variant)"
    logger.info(f"Received FQ names: {fq_names}")
    
    # Verify the head jobs exist in the job map
    for fq_name in fq_names:
        assert fq_name in fm.job_graph_map, f"FQ name {fq_name} should be in job_map"
    
    # Test the dev variant (square operation)
    dev_fq_name = [name for name in fq_names if "dev" in name][0]
    logger.info(f"Testing dev variant: {dev_fq_name}")
    
    # Submit a task with numbers 1-5 to be squared
    dev_task = Task({
        "start": 1,
        "count": 5
    })
    
    # Submit to the dev variant
    fm.submit_task(dev_task, dev_fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for dev task to complete"
    
    # Check results for dev variant
    dev_results = fm.pop_results()
    assert not dev_results["errors"], f"Errors occurred during dev task execution: {dev_results['errors']}"
    assert len(dev_results["completed"]) > 0, "No completed tasks found for dev variant"
    
    # Get the dev task result
    dev_task_result = dev_results['completed'][dev_fq_name][0]
    logger.info(f"Dev task result: {dev_task_result}")
    
    # Verify dev variant results (square operation)
    # For numbers 1,2,3,4,5 squared to 1,4,9,16,25, the sum is 55
    assert dev_task_result['sum'] == 55, f"Expected sum=55 for dev variant, got {dev_task_result['sum']}"
    assert dev_task_result['avg'] == 11.0, f"Expected avg=11.0 for dev variant, got {dev_task_result['avg']}"
    
    # Check saved results to verify operation type and input/output data
    if "SAVED_RESULTS" in dev_task_result:
        saved_results = dev_task_result.get("SAVED_RESULTS", {})
        logger.info(f"Dev variant saved results: {saved_results}")
        
        # Find the operation job results
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        assert saved_results[op_key]["operation"] == "square", \
            f"Expected operation='square' for dev variant, got {saved_results[op_key]['operation']}"
        assert saved_results[op_key]["numbers"] == [1, 4, 9, 16, 25], \
            f"Expected [1,4,9,16,25] for dev variant, got {saved_results[op_key]['numbers']}"
    
    # Test the prod variant (double operation)
    prod_fq_name = [name for name in fq_names if "prod" in name][0]
    logger.info(f"Testing prod variant: {prod_fq_name}")
    
    # Submit a task with numbers 1-5 to be doubled
    prod_task = Task({
        "start": 1,
        "count": 5
    })
    
    # Submit to the prod variant
    fm.submit_task(prod_task, prod_fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for prod task to complete"
    
    # Check results for prod variant
    prod_results = fm.pop_results()
    assert not prod_results["errors"], f"Errors occurred during prod task execution: {prod_results['errors']}"
    assert len(prod_results["completed"]) > 0, "No completed tasks found for prod variant"
    
    # Get the prod task result
    prod_task_result = prod_results['completed'][prod_fq_name][0]
    logger.info(f"Prod task result: {prod_task_result}")
    
    # Verify prod variant results (double operation)
    # For numbers 1,2,3,4,5 doubled to 2,4,6,8,10, the sum is 30
    assert prod_task_result['sum'] == 30, f"Expected sum=30 for prod variant, got {prod_task_result['sum']}"
    assert prod_task_result['avg'] == 6.0, f"Expected avg=6.0 for prod variant, got {prod_task_result['avg']}"
    
    # Check saved results to verify operation type and input/output data
    if "SAVED_RESULTS" in prod_task_result:
        saved_results = prod_task_result.get("SAVED_RESULTS", {})
        logger.info(f"Prod variant saved results: {saved_results}")
        
        # Find the operation job results
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        assert saved_results[op_key]["operation"] == "double", \
            f"Expected operation='double' for prod variant, got {saved_results[op_key]['operation']}"
        assert saved_results[op_key]["numbers"] == [2, 4, 6, 8, 10], \
            f"Expected [2,4,6,8,10] for prod variant, got {saved_results[op_key]['numbers']}"


def test_add_dsl_dict_multiple_graphs_no_variants():
    """Test add_dsl_dict with multiple graphs without variants.
    
    This tests the simplified DSL dictionary format with multiple graphs:
    { "graph1": dsl1, "graph2": dsl2 }
    
    Uses different math operations for each graph to demonstrate data flow.
    """
    # Create job instances for first graph - sum operation
    sum_generator = NumberGenerator("sum_generator")
    sum_operation = MathOperation("sum_operation", operation="sum")
    sum_aggregator = Aggregator("sum_aggregator")
    
    # Create job instances for second graph - multiply operation
    multiply_generator = NumberGenerator("multiply_generator")
    multiply_operation = MathOperation("multiply_operation", operation="multiply")
    multiply_aggregator = Aggregator("multiply_aggregator")
    
    # Wrap jobs for first graph (sum)
    sum_jobs = job({
        "generator": sum_generator,
        "operation": sum_operation,
        "aggregator": sum_aggregator
    })
    
    # Wrap jobs for second graph (multiply)
    multiply_jobs = job({
        "generator": multiply_generator,
        "operation": multiply_operation,
        "aggregator": multiply_aggregator
    })
    
    # Save results for context between pipeline steps
    sum_jobs["generator"].save_result = True
    sum_jobs["operation"].save_result = True
    multiply_jobs["generator"].save_result = True
    multiply_jobs["operation"].save_result = True
    
    # Create pipelines
    sum_dsl = sum_jobs["generator"] >> sum_jobs["operation"] >> sum_jobs["aggregator"]
    multiply_dsl = multiply_jobs["generator"] >> multiply_jobs["operation"] >> multiply_jobs["aggregator"]
    
    # Create DSL dict with multiple graphs, no variants
    dsl_dict = {
        "sum_graph": sum_dsl,
        "multiply_graph": multiply_dsl
    }
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # Add the DSL dict
    logger.info("Adding DSL dict with multiple graphs, no variants")
    fq_names = fm.add_dsl_dict(dsl_dict)
    
    # Verify two FQ names were returned
    assert len(fq_names) == 2, "Should return exactly two FQ names"
    logger.info(f"Received FQ names: {fq_names}")
    
    # Verify the head jobs exist in the job map
    for fq_name in fq_names:
        assert fq_name in fm.job_graph_map, f"FQ name {fq_name} should be in job_map"
    
    # Test data for both graphs - numbers 1 through 5
    task_data = {
        "start": 1,
        "count": 5
    }
    
    # Find each graph's FQ name
    sum_fq_name = [name for name in fq_names if "sum" in name][0]
    multiply_fq_name = [name for name in fq_names if "multiply" in name][0]
    
    # Submit tasks to each graph
    logger.info(f"Submitting task to sum graph: {sum_fq_name}")
    fm.submit_task(Task(task_data), sum_fq_name)  # Must specify fq_name with multiple graphs
    
    logger.info(f"Submitting task to multiply graph: {multiply_fq_name}")
    fm.submit_task(Task(task_data), multiply_fq_name)  # Must specify fq_name with multiple graphs
    
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Check results
    results = fm.pop_results()
    logger.info(f"Results: {results}")
    assert not results["errors"], f"Errors occurred during task execution: {results['errors']}"
    assert len(results["completed"]) == 2, "Expected 2 completed tasks"
    
    # Verify sum graph results
    sum_result = results["completed"][sum_fq_name][0]
    logger.info(f"Sum graph result: {sum_result}")
    
    # For numbers 1,2,3,4,5, the sum operation gives [15], which should produce these statistics
    assert sum_result["sum"] == 15, f"Expected sum=15 for sum graph, got {sum_result['sum']}"
    assert sum_result["avg"] == 15.0, f"Expected avg=15.0 for sum graph, got {sum_result['avg']}"
    assert sum_result["count"] == 1, f"Expected count=1 for sum graph, got {sum_result['count']}"
    
    # Check saved results to verify operation and data flow
    if "SAVED_RESULTS" in sum_result:
        saved_results = sum_result.get("SAVED_RESULTS", {})
        logger.info(f"Sum graph saved results: {saved_results}")
        
        # Verify the operation performed
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        assert saved_results[op_key]["operation"] == "sum", \
            f"Expected operation='sum', got {saved_results[op_key]['operation']}"
        assert saved_results[op_key]["numbers"] == [15], \
            f"Expected [15], got {saved_results[op_key]['numbers']}"
    
    # Verify multiply graph results
    multiply_result = results["completed"][multiply_fq_name][0]
    logger.info(f"Multiply graph result: {multiply_result}")
    
    # For numbers 1,2,3,4,5, the multiply operation gives [120], which should produce these statistics
    assert multiply_result["sum"] == 120, f"Expected sum=120 for multiply graph, got {multiply_result['sum']}"
    assert multiply_result["avg"] == 120.0, f"Expected avg=120.0 for multiply graph, got {multiply_result['avg']}"
    assert multiply_result["count"] == 1, f"Expected count=1 for multiply graph, got {multiply_result['count']}"
    
    # Check saved results to verify operation and data flow
    if "SAVED_RESULTS" in multiply_result:
        saved_results = multiply_result.get("SAVED_RESULTS", {})
        logger.info(f"Multiply graph saved results: {saved_results}")
        
        # Verify the operation performed
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        assert saved_results[op_key]["operation"] == "multiply", \
            f"Expected operation='multiply', got {saved_results[op_key]['operation']}"
        assert saved_results[op_key]["numbers"] == [120], \
            f"Expected [120], got {saved_results[op_key]['numbers']}"


def test_add_dsl_dict_multiple_graphs_with_variants():
    """Test add_dsl_dict with multiple graphs with variants.
    
    This tests the DSL dictionary format with multiple graphs and variants:
    {
        "graph1": { "dev": dsl1d, "prod": dsl1p },
        "graph2": { "dev": dsl2d, "prod": dsl2p }
    }
    
    Uses different math operations for each graph-variant combination to demonstrate data flow.
    """
    # Create a helper function to build a DSL pipeline with specified operation
    def create_math_pipeline(prefix: str, operation: str):
        generator = NumberGenerator(f"{prefix}_generator")
        math_op = MathOperation(f"{prefix}_operation", operation=operation)
        aggregator = Aggregator(f"{prefix}_aggregator")
        
        jobs = job({
            "generator": generator,
            "operation": math_op,
            "aggregator": aggregator
        })
        
        # Save results for all jobs to verify later
        jobs["generator"].save_result = True
        jobs["operation"].save_result = True
        
        return jobs["generator"] >> jobs["operation"] >> jobs["aggregator"]
    
    # Create DSL dict with different operations for each graph and variant
    dsl_dict = {
        "first": {
            "dev": create_math_pipeline("first_dev", "square"),    # Square operation
            "prod": create_math_pipeline("first_prod", "double")   # Double operation
        },
        "second": {
            "dev": create_math_pipeline("second_dev", "sum"),      # Sum operation
            "prod": create_math_pipeline("second_prod", "multiply") # Multiply operation
        }
    }
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # Add the DSL dict
    logger.info("Adding DSL dict with multiple graphs, with variants")
    fq_names = fm.add_dsl_dict(dsl_dict)
    
    # Verify four FQ names were returned (one for each graph-variant combination)
    assert len(fq_names) == 4, "Should return exactly four FQ names"
    logger.info(f"Received FQ names: {fq_names}")
    
    # Verify the head jobs exist in the job map
    for fq_name in fq_names:
        assert fq_name in fm.job_graph_map, f"FQ name {fq_name} should be in job_map"
    
    # Function to find a specific graph-variant combination from fq_names
    def find_fq_name(graph, variant):
        return [name for name in fq_names if graph in name and variant in name][0]
    
    # Define test data - numbers 1 through 5
    task_data = {
        "start": 1,
        "count": 5
    }
    
    # Test all four graph-variant combinations with the same input data
    combinations = [
        {"graph": "first", "variant": "dev", "operation": "square", "expected": [1, 4, 9, 16, 25]},
        {"graph": "first", "variant": "prod", "operation": "double", "expected": [2, 4, 6, 8, 10]},
        {"graph": "second", "variant": "dev", "operation": "sum", "expected": [15]},
        {"graph": "second", "variant": "prod", "operation": "multiply", "expected": [120]}
    ]
    
    for combo in combinations:
        # Find the correct FQ name
        fq_name = find_fq_name(combo["graph"], combo["variant"])
        logger.info(f"Testing {combo['graph']}-{combo['variant']} with {combo['operation']} operation: {fq_name}")
        
        # Submit the task
        fm.submit_task(Task(task_data), fq_name)
        
        # Wait for completion
        success = fm.wait_for_completion()
        assert success, f"Timed out waiting for {combo['graph']}-{combo['variant']} task to complete"
        
        # Check results
        results = fm.pop_results()
        assert not results["errors"], f"Errors occurred during {combo['graph']}-{combo['variant']} execution: {results['errors']}"
        assert len(results["completed"]) > 0, f"No completed tasks found for {combo['graph']}-{combo['variant']}"
        
        # Get the result
        result = results["completed"][fq_name][0]
        logger.info(f"{combo['graph']}-{combo['variant']} result: {result}")
        
        # Check saved results to verify operation and data flow
        if "SAVED_RESULTS" in result:
            saved_results = result.get("SAVED_RESULTS", {})
            logger.info(f"{combo['graph']}-{combo['variant']} saved results: {saved_results}")
            
            # Find the operation job results
            op_key = [key for key in saved_results.keys() if "operation" in key][0]
            
            # Verify the operation performed
            assert saved_results[op_key]["operation"] == combo["operation"], \
                f"Expected operation='{combo['operation']}', got {saved_results[op_key]['operation']}"
            
            # Verify the expected result of the operation
            assert saved_results[op_key]["numbers"] == combo["expected"], \
                f"Expected {combo['expected']}, got {saved_results[op_key]['numbers']}"
            
            # For aggregate operations (sum, multiply) that return a single value
            if combo["operation"] in ["sum", "multiply"]:
                # Check the aggregate value
                single_value = combo["expected"][0]
                assert result["sum"] == single_value, \
                    f"Expected sum={single_value}, got {result['sum']}"
                assert result["avg"] == single_value, \
                    f"Expected avg={single_value}, got {result['avg']}"
                assert result["count"] == 1, \
                    f"Expected count=1, got {result['count']}"
                
            # For square operation on numbers 1-5, sum should be 55, avg 11.0
            elif combo["operation"] == "square":
                assert result["sum"] == 55, f"Expected sum=55, got {result['sum']}"
                assert result["avg"] == 11.0, f"Expected avg=11.0, got {result['avg']}"
                
            # For double operation on numbers 1-5, sum should be 30, avg 6.0
            elif combo["operation"] == "double":
                assert result["sum"] == 30, f"Expected sum=30, got {result['sum']}"
                assert result["avg"] == 6.0, f"Expected avg=6.0, got {result['avg']}"
            
        # Verify generator inputs are consistent
        if "SAVED_RESULTS" in result:
            gen_key = [key for key in result["SAVED_RESULTS"].keys() if "generator" in key][0]
            assert result["SAVED_RESULTS"][gen_key]["numbers"] == [1, 2, 3, 4, 5], \
                f"Expected generator numbers [1,2,3,4,5], got {result['SAVED_RESULTS'][gen_key]['numbers']}"
