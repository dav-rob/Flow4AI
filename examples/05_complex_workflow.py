"""
Example 5: Complex Workflow

Demonstrates advanced Flow4AI features:
- Mix of JobABC classes, functions, and lambdas
- Parallel branches with p() operator
- SAVED_RESULTS for intermediate data access
- task_pass_through for original task data
"""

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p, JobsDict
from flow4ai.job import JobABC


class DataProcessor(JobABC):
    """Custom job class for data processing."""
    
    def __init__(self, name, processor_type):
        super().__init__(name)
        self.processor_type = processor_type
    
    async def run(self, task):
        """Process data based on processor type."""
        # Use get_params() to access task parameters for this job (if provided)
        params = self.get_params()
        priority = params.get("priority", "normal")
        return f"Processed by {self.name} ({self.processor_type}, priority={priority})"


def context_aggregator(j_ctx):
    """Aggregate results using job context."""
    task = j_ctx["task"]
    inputs = j_ctx["inputs"]
    return {
        "original_task": task,
        "all_inputs": inputs
    }


def main():
    """Run the complex workflow example."""
    print("\n" + "="*60)
    print("Example 5: Complex Workflow")
    print("="*60 + "\n")
    
    # Define jobs: lambdas, functions, and JobABC classes
    times_two = lambda x: x * 2
    add_three = lambda x: x + 3
    square = lambda x: x ** 2
    
    # Create JobABC instances
    analyzer = DataProcessor("Analyzer", "analysis")
    transformer = DataProcessor("Transformer", "transformation")
    formatter = DataProcessor("Formatter", "formatting")
    aggregator = DataProcessor("Aggregator", "aggregation")
    cache_manager = DataProcessor("CacheManager", "caching")
    
    # Wrap everything into job dictionary
    jobs: JobsDict = job({
        "analyzer": analyzer,
        "cache_manager": cache_manager,
        "times": times_two,
        "transformer": transformer,
        "formatter": formatter,
        "add": add_three,
        "square": square,
        "aggregator": aggregator,
        "context": context_aggregator
    })
    
    # Save intermediate results
    jobs["times"].save_result = True
    jobs["add"].save_result = True
    jobs["square"].save_result = True
    
    # Build complex workflow:
    # WORKFLOW = a graph of connected jobs (created once, reused for many tasks)
    # 1. Three parallel initial jobs (analyzer, cache_manager, times)
    # 2. Serial transformer
    # 3. Serial formatter
    # 4. Two parallel jobs (add, square)
    # 5. Context aggregator
    # 6. Final aggregator
    workflow = (
        p(jobs["analyzer"], jobs["cache_manager"], jobs["times"])
        >> jobs["transformer"]
        >> jobs["formatter"]
        >> (jobs["add"] | jobs["square"])
        >> jobs["context"]
        >> jobs["aggregator"]
    )
    
    print("Workflow structure:")
    print("  p(analyzer, cache_manager, times) >>")
    print("    transformer >>")
    print("      formatter >>")
    print("        (add | square) >>")
    print("          context >>")
    print("            aggregator\n")
    
    # Execute workflow
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow)
    
    task = {
        "times": {"fn.x": 5},
        "add": {"fn.x": 10},
        "square": {"fn.x": 7}
    }
    
    print(f"Input task: times(5), add(10), square(7)\n")
    print("Executing workflow...\n")
    
    fm.submit_task(task, fq_name)
    success = fm.wait_for_completion()
    
    if not success:
        print("❌ Timeout waiting for tasks to complete")
        return False
    
    results = fm.pop_results()
    
    if results["errors"]:
        print(f"❌ Errors occurred: {results['errors']}")
        return False
    
    result_dict = list(results["completed"].values())[0][0]
    
    print("✅ Workflow complete!\n")
    
    # Show SAVED_RESULTS (intermediate job outputs)
    print("SAVED_RESULTS (intermediate outputs):")
    saved = result_dict.get("SAVED_RESULTS", {})
    print(f"  - times(5) = {saved.get('times')} (should be 10)")
    print(f"  - add(10) = {saved.get('add')} (should be 13)")
    print(f"  - square(7) = {saved.get('square')} (should be 49)")
    
    # Show task_pass_through (original task data)
    print("\ntask_pass_through (original task data):")
    task_passthrough = result_dict.get("task_pass_through", {})
    for key, value in task_passthrough.items():
        print(f"  - {key}: {value}")
    
    print("\nKey Features Demonstrated:")
    print("  ✓ Mixed job types (JobABC, functions, lambdas)")
    print("  ✓ Parallel execution with p() operator")
    print("  ✓ Serial execution with >> operator")
    print("  ✓ SAVED_RESULTS for intermediate data")
    print("  ✓ task_pass_through for original task data")
    print("  ✓ Context functions accessing inputs with j_ctx")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
