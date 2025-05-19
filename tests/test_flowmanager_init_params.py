"""Tests for enhanced FlowManager API with convenience methods."""

from typing import Dict, List

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, JobsDict, wrap
from flow4ai.flowmanager import FlowManager
from flow4ai.job import (SPLIT_STR, JobABC,  # Import the separator constant
                         Task)

# Configure logging
logger = logging.getLogger(__name__)


class NumberGenerator(JobABC):
    """Job that generates a range of numbers based on start and count."""
    
    def __init__(self, name):
        super().__init__(name)
        
    async def run(self, task):
        start = task.get("start", 1)
        count = task.get("count", 5)
        numbers = list(range(start, start + count))
        logger.info(f"Generator {self.name} producing numbers: {numbers}")
        return {"numbers": numbers}


class MathOperation(JobABC):
    """Job that performs a math operation on a list of numbers."""
    
    def __init__(self, name, operation="square"):
        super().__init__(name)
        self._operation = operation
    
    @property
    def operation(self):
        """The operation to perform on the numbers."""
        return self._operation
        
    async def run(self, task):
        # Get inputs from predecessor jobs
        inputs = self.get_inputs()
        
        # Get numbers from producer
        numbers = inputs.get("generator", {}).get("numbers", [])
        logger.info(f"Operation {self.name} received numbers: {numbers}")
        
        # Apply the operation
        if self.operation == "square":
            result = [n * n for n in numbers]
        elif self.operation == "double":
            result = [n * 2 for n in numbers]
        elif self.operation == "sum":
            result = [sum(numbers)]
        elif self.operation == "multiply":
            product = 1
            for n in numbers:
                product *= n
            result = [product]
        else:
            result = numbers  # Default: identity operation
            
        logger.info(f"Operation {self.name} applied '{self.operation}', result: {result}")
        return {"numbers": result, "operation": self.operation}


class Aggregator(JobABC):
    """Job that aggregates numbers and computes statistics."""
    
    def __init__(self, name):
        super().__init__(name)
        
    async def run(self, task):
        # Get inputs from predecessor jobs
        inputs = self.get_inputs()
        
        # Get numbers from operation
        numbers = inputs.get("operation", {}).get("numbers", [])
        operation = inputs.get("operation", {}).get("operation", "unknown")
        
        # Compute statistics
        total = sum(numbers)
        avg = total / len(numbers) if numbers else 0
        
        logger.info(f"Aggregator {self.name} computed stats for operation '{operation}': sum={total}, avg={avg}")
        return {
            "numbers": numbers,
            "sum": total,
            "avg": avg,
            "operation": operation
        }


def create_math_pipeline(prefix: str, operation: str) -> DSLComponent:
    """Helper function to create a math pipeline with specified operation."""
    generator = NumberGenerator(f"{prefix}_generator")
    math_op = MathOperation(f"{prefix}_operation", operation=operation)
    aggregator = Aggregator(f"{prefix}_aggregator")
    
    jobs = wrap({
        "generator": generator,
        "operation": math_op,
        "aggregator": aggregator
    })
    
    # Save results for all jobs to verify later
    jobs["generator"].save_result = True
    jobs["operation"].save_result = True
    
    return jobs["generator"] >> jobs["operation"] >> jobs["aggregator"]


def test_flowmanager_constructor_with_dsl_dict():
    """Test initializing FlowManager with DSL dictionary in constructor."""
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
    
    # Initialize FlowManager with DSL dict
    logger.info("Initializing FlowManager with DSL dict")
    fm = FlowManager(dsl=dsl_dict)
    
    # Verify all graphs are properly loaded
    # We should have 4 different FQ names in job_map
    assert len(fm.job_map) == 4, f"Expected 4 graphs, got {len(fm.job_map)}"
    
    # All expected head jobs should be present
    first_dev_jobs = fm.get_fq_names_by_graph("first", "dev")
    first_prod_jobs = fm.get_fq_names_by_graph("first", "prod")
    second_dev_jobs = fm.get_fq_names_by_graph("second", "dev")
    second_prod_jobs = fm.get_fq_names_by_graph("second", "prod")
    
    assert len(first_dev_jobs) == 1, f"Expected 1 first-dev job, got {len(first_dev_jobs)}"
    assert len(first_prod_jobs) == 1, f"Expected 1 first-prod job, got {len(first_prod_jobs)}"
    assert len(second_dev_jobs) == 1, f"Expected 1 second-dev job, got {len(second_dev_jobs)}"
    assert len(second_prod_jobs) == 1, f"Expected 1 second-prod job, got {len(second_prod_jobs)}"
    
    # Ensure the jobs have the expected FQ name structure
    for fq_name in fm.job_map.keys():
        logger.info(f"Found FQ name: {fq_name}")
        parts = fq_name.split(SPLIT_STR)
        assert len(parts) >= 3, f"FQ name should have at least 3 parts: {fq_name}"
        
        graph_name = parts[0]
        variant = parts[1]
        
        assert graph_name in ["first", "second"], f"Unexpected graph name: {graph_name}"
        assert variant in ["dev", "prod"] or variant.startswith(("dev_", "prod_")), \
            f"Unexpected variant: {variant}"


def test_get_fq_names_by_graph():
    """Test getting FQ names by graph name and variant."""
    # Create a FlowManager
    fm = FlowManager()
    
    # Add DSL dictionaries for testing
    dsl_dict = {
        "math": {
            "basic": create_math_pipeline("math_basic", "square"),
            "advanced": create_math_pipeline("math_advanced", "double")
        }
    }
    
    # Add the DSL dict
    fm.add_dsl_dict(dsl_dict)
    
    # Test getting FQ names by graph and variant
    basic_fq_names = fm.get_fq_names_by_graph("math", "basic")
    advanced_fq_names = fm.get_fq_names_by_graph("math", "advanced")
    
    assert len(basic_fq_names) == 1, f"Expected 1 basic FQ name, got {len(basic_fq_names)}"
    assert len(advanced_fq_names) == 1, f"Expected 1 advanced FQ name, got {len(advanced_fq_names)}"
    
    # Test with non-existent graph
    non_existent = fm.get_fq_names_by_graph("nonexistent", "variant")
    assert len(non_existent) == 0, f"Expected 0 matches for non-existent graph, got {len(non_existent)}"
    
    # Add another DSL with same structure (should get different FQ name with suffix)
    dsl_basic2 = create_math_pipeline("math_basic2", "sum")
    fm.add_dsl(dsl_basic2, "math", "basic")
    
    # Now we should have two "math-basic" FQ names
    basic_fq_names_updated = fm.get_fq_names_by_graph("math", "basic")
    assert len(basic_fq_names_updated) == 2, \
        f"Expected 2 basic FQ names after adding same structure, got {len(basic_fq_names_updated)}"


def test_submit_by_graph():
    """Test submitting tasks using the graph name and variant."""
    # Create DSL dict with different operations
    dsl_dict = {
        "calculator": {
            "square": create_math_pipeline("calc_square", "square"),
            "double": create_math_pipeline("calc_double", "double")
        }
    }
    
    # Initialize FlowManager with DSL dict
    fm = FlowManager(dsl=dsl_dict)
    
    # Create test task - numbers 1 through 5
    task_data = {
        "start": 1,
        "count": 5
    }
    
    # Test submit_by_graph with square variant
    logger.info("Submitting task to calculator-square graph")
    fm.submit_by_graph(Task(task_data), "calculator", "square")
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for calculator-square task to complete"
    
    # Check results
    results = fm.pop_results()
    assert not results["errors"], f"Errors occurred during execution: {results['errors']}"
    assert len(results["completed"]) > 0, "No completed tasks found"
    
    # Get the result - should have one key matching calculator-square FQ name
    square_fq_name = fm.get_fq_names_by_graph("calculator", "square")[0]
    result = results["completed"][square_fq_name][0]
    logger.info(f"calculator-square result: {result}")
    
    # Verify the result
    assert result["operation"] == "square", f"Expected operation='square', got {result['operation']}"
    assert result["sum"] == 55, f"Expected sum=55, got {result['sum']}"
    assert result["avg"] == 11.0, f"Expected avg=11.0, got {result['avg']}"
    
    # Check saved results to verify operation
    if "SAVED_RESULTS" in result:
        saved_results = result.get("SAVED_RESULTS", {})
        
        # Find the operation job results
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        
        # Verify the operation performed
        assert saved_results[op_key]["operation"] == "square", \
            f"Expected operation='square', got {saved_results[op_key]['operation']}"
        
        # Verify the expected result of the operation
        assert saved_results[op_key]["numbers"] == [1, 4, 9, 16, 25], \
            f"Expected [1, 4, 9, 16, 25], got {saved_results[op_key]['numbers']}"


def test_submit_by_graph_with_collision():
    """Test submitting when multiple graphs with same name/variant exist."""
    # Create a FlowManager
    fm = FlowManager()
    
    # Create and add two DSLs with same graph name and variant
    dsl1 = create_math_pipeline("collision_test1", "square")
    dsl2 = create_math_pipeline("collision_test2", "double")
    
    # Add both with same graph name and variant
    fq_name1 = fm.add_dsl(dsl1, "calc", "test")
    fq_name2 = fm.add_dsl(dsl2, "calc", "test")
    
    # Verify we got different FQ names
    assert fq_name1 != fq_name2, "Expected different FQ names for different DSLs"
    
    # Verify we can get both by graph name
    calc_test_fq_names = fm.get_fq_names_by_graph("calc", "test")
    assert len(calc_test_fq_names) == 2, f"Expected 2 FQ names, got {len(calc_test_fq_names)}"
    
    # Test that submit_by_graph raises an error for ambiguous graph/variant
    with pytest.raises(ValueError) as excinfo:
        fm.submit_by_graph(Task({"start": 1, "count": 3}), "calc", "test")
    
    # Check that error message contains the FQ names
    error_message = str(excinfo.value)
    assert "Multiple matching graphs found" in error_message
    assert fq_name1 in error_message
    assert fq_name2 in error_message


def test_combined_workflow():
    """Test a complete workflow using the enhanced FlowManager API."""
    # Create DSL dict
    dsl_dict = {
        "workflow": {
            "simple": create_math_pipeline("workflow_simple", "double")
        }
    }
    
    # Initialize FlowManager with DSL dict
    fm = FlowManager(dsl=dsl_dict)
    
    # Get FQ name for verification
    simple_fq_names = fm.get_fq_names_by_graph("workflow", "simple")
    assert len(simple_fq_names) == 1, "Expected one FQ name for workflow-simple"
    simple_fq_name = simple_fq_names[0]
    
    # Task data
    task_data = {"start": 2, "count": 3}  # Will generate [2, 3, 4]
    
    # Submit task using graph and variant
    fm.submit_by_graph(Task(task_data), "workflow", "simple")
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Task did not complete successfully"
    
    # Get results
    results = fm.pop_results()
    assert not results["errors"], f"Errors in execution: {results['errors']}"
    assert simple_fq_name in results["completed"], f"No results for FQ name {simple_fq_name}"
    
    # Verify results
    result = results["completed"][simple_fq_name][0]
    
    # For double operation on [2, 3, 4], result should be [4, 6, 8]
    # Sum should be 18, avg 6.0
    assert result["sum"] == 18, f"Expected sum=18, got {result['sum']}"
    assert result["avg"] == 6.0, f"Expected avg=6.0, got {result['avg']}"
    
    # Verify operation and generator data
    if "SAVED_RESULTS" in result:
        saved_results = result.get("SAVED_RESULTS", {})
        
        # Check generator output
        gen_key = [key for key in saved_results.keys() if "generator" in key][0]
        assert saved_results[gen_key]["numbers"] == [2, 3, 4], \
            f"Expected generator numbers [2, 3, 4], got {saved_results[gen_key]['numbers']}"
        
        # Check operation output
        op_key = [key for key in saved_results.keys() if "operation" in key][0]
        assert saved_results[op_key]["operation"] == "double", \
            f"Expected operation='double', got {saved_results[op_key]['operation']}"
        assert saved_results[op_key]["numbers"] == [4, 6, 8], \
            f"Expected [4, 6, 8], got {saved_results[op_key]['numbers']}"

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