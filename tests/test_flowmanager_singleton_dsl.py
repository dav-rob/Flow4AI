import pytest
from typing import Dict, Any

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, wrap
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC, Task

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


def test_singleton_with_dsl_parameter():
    """Test using the FlowManager singleton pattern with a DSL parameter."""
    # Rule Applied: Test code for correctness and performance
    
    # Reset singleton to ensure clean test state
    FlowManager.reset_instance()
    
    # Create DSL dict with different operations
    dsl_dict = {
        "calculator": {
            "square": create_math_pipeline("calc_square", "square"),
            "double": create_math_pipeline("calc_double", "double"),
            "sum": create_math_pipeline("calc_sum", "sum")
        }
    }
    
    # Initialize FlowManager using the singleton pattern with DSL parameter
    fm = FlowManager.instance(dsl=dsl_dict)
    
    # Create test tasks with different data
    tasks = [
        {"start": 1, "count": 5},
        {"start": 10, "count": 3},
        {"start": 100, "count": 2}
    ]
    
    # Submit tasks to different graph variants
    logger.info("Submitting task to calculator-square graph")
    fm.submit_by_graph(Task(tasks[0]), "calculator", "square")
    
    logger.info("Submitting task to calculator-double graph")
    fm.submit_by_graph(Task(tasks[1]), "calculator", "double")
    
    logger.info("Submitting task to calculator-sum graph")
    fm.submit_by_graph(Task(tasks[2]), "calculator", "sum")
    
    # Wait for all tasks to complete
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Get results
    results = fm.pop_results()
    
    # Print all keys in the completed results for debugging
    logger.info(f"Available result keys: {list(results['completed'].keys())}")
    
    # Verify results for square operation
    square_result_key = "calculator$$square$$generator$$"
    assert square_result_key in results["completed"], f"Missing results for {square_result_key}"
    square_results = results["completed"][square_result_key][0]["SAVED_RESULTS"]["operation"]
    assert square_results["operation"] == "square"
    assert square_results["numbers"] == [1, 4, 9, 16, 25]  # [1^2, 2^2, 3^2, 4^2, 5^2]
    
    # Verify aggregated results for square operation
    square_agg_results = results["completed"][square_result_key][0]
    assert square_agg_results["sum"] == 55
    
    # Verify results for double operation
    double_result_key = "calculator$$double$$generator$$"
    assert double_result_key in results["completed"], f"Missing results for {double_result_key}"
    double_results = results["completed"][double_result_key][0]["SAVED_RESULTS"]["operation"]
    assert double_results["operation"] == "double"
    assert double_results["numbers"] == [20, 22, 24]  # [10*2, 11*2, 12*2]
    
    # Verify aggregated results for double operation
    double_agg_results = results["completed"][double_result_key][0]
    assert double_agg_results["sum"] == 66
    
    # Verify results for sum operation
    sum_result_key = "calculator$$sum$$generator$$"
    assert sum_result_key in results["completed"], f"Missing results for {sum_result_key}"
    sum_results = results["completed"][sum_result_key][0]["SAVED_RESULTS"]["operation"]
    assert sum_results["operation"] == "sum"
    assert sum_results["numbers"] == [201]  # sum of [100, 101]
    
    # Verify aggregated results for sum operation
    sum_agg_results = results["completed"][sum_result_key][0]
    assert sum_agg_results["sum"] == 201
    
    # Test that accessing the singleton again returns the same instance with the same DSL
    fm2 = FlowManager.instance()
    assert fm is fm2, "Should get the same FlowManager instance"
    
    # Create a new task
    new_task = {"start": 5, "count": 2}
    
    # Submit to an existing graph without reinitializing
    logger.info("Submitting new task to calculator-double graph from second reference")
    fm2.submit_by_graph(Task(new_task), "calculator", "double")
    
    success = fm2.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Get new results
    new_results = fm2.pop_results()
    
    # Print available keys for debugging
    logger.info(f"New results available keys: {list(new_results['completed'].keys())}")
    
    # Verify new results for double operation
    # The key should be the same as before since we're submitting to the same graph
    assert double_result_key in new_results["completed"], f"Missing results for {double_result_key} in new results"
    new_double_results = new_results["completed"][double_result_key][0]["SAVED_RESULTS"]["operation"]
    assert new_double_results["operation"] == "double"
    assert new_double_results["numbers"] == [10, 12]  # [5*2, 6*2]
    
    # Verify aggregated results
    new_double_agg_results = new_results["completed"][double_result_key][0]
    assert new_double_agg_results["sum"] == 22


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
