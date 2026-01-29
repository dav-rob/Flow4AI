#!/usr/bin/env python3
"""
Tutorial 02: Tasks and Parameters

This is a CORE example! Understanding task structure and parameter passing
is essential to using Flow4AI effectively. Read this early in your learning.

=============================================================================
CORE CONCEPTS
=============================================================================

WORKFLOW: A graph of connected jobs that defines your processing pipeline.
          Created once, then reused for many tasks.

JOB:      A single execution unit (function or class) that processes data.
          Jobs receive parameters from tasks and outputs from predecessors.

TASK:     Data sent to a workflow for processing. Each task can have different
          parameters for each job. Submit 1000 tasks = 1000 independent executions.

=============================================================================
"""

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job
from flow4ai.job import JobABC


# =============================================================================
# SECTION 1: Parameter Injection for Functions
# =============================================================================

def named_params(x: int, y: int = 10):
    """Parameters are auto-extracted from task and injected by name.
    
    If task = {"named_params": {"x": 5, "y": 20}}
    Then x=5 and y=20 are passed automatically.
    """
    result = x + y
    print(f"  named_params: x={x}, y={y} -> {result}")
    return {"sum": result}


def using_kwargs(**kwargs):
    """All job parameters are available via **kwargs.
    
    If task = {"using_kwargs": {"a": 1, "b": 2, "c": 3}}
    Then kwargs = {"a": 1, "b": 2, "c": 3}
    """
    total = sum(kwargs.values())
    print(f"  using_kwargs: {kwargs} -> sum={total}")
    return {"total": total}


def with_context(j_ctx, **kwargs):
    """j_ctx provides access to the full execution context.
    
    - j_ctx["inputs"]: Outputs from predecessor jobs
    - j_ctx["task"]: The full task dictionary
    - **kwargs: Parameters for this specific job
    """
    predecessor_sum = j_ctx["inputs"].get("named_params", {}).get("sum", 0)
    multiplier = kwargs.get("multiplier", 2)
    result = predecessor_sum * multiplier
    print(f"  with_context: predecessor_sum={predecessor_sum}, multiplier={multiplier} -> {result}")
    return {"result": result}


# =============================================================================
# SECTION 2: Parameter Access for Job Classes
# =============================================================================

class DataProcessor(JobABC):
    """Job classes use get_params() for clean parameter access.
    
    self.get_params() returns only the parameters for THIS job.
    self.get_inputs() returns outputs from all predecessor jobs.
    self.get_task() returns the complete task dictionary.
    """
    
    def __init__(self, name, default_factor=1):
        super().__init__(name)
        self.default_factor = default_factor
    
    async def run(self, task):
        # Get this job's parameters from task
        params = self.get_params()
        value = params.get("value", 100)
        factor = params.get("factor", self.default_factor)
        
        # Get results from predecessor jobs
        inputs = self.get_inputs()
        
        result = value * factor
        print(f"  {self.name}: value={value}, factor={factor} -> {result}")
        return {"processed": result, "inputs_received": list(inputs.keys())}


# =============================================================================
# SECTION 3: Task Format Options
# =============================================================================

def demo_task_formats():
    """Demonstrates the two equivalent task formats."""
    
    print("\n" + "="*60)
    print("SECTION 3: Task Format Options")
    print("="*60)
    
    # Both formats are equivalent:
    
    # SHORTHAND FORMAT (recommended for simple cases)
    shorthand_task = {
        "job_a.x": 10,
        "job_a.y": 20,
        "job_b.multiplier": 3
    }
    
    # NESTED FORMAT (recommended for clarity and get_params())
    nested_task = {
        "job_a": {"x": 10, "y": 20},
        "job_b": {"multiplier": 3}
    }
    
    print("\nShorthand format:")
    print(f"  {shorthand_task}")
    print("\nNested format (equivalent):")
    print(f"  {nested_task}")
    print("\nBoth produce the same result - choose based on your preference.")


# =============================================================================
# SECTION 4: Running a Simple Workflow with Different Tasks
# =============================================================================

def demo_function_parameters():
    """Shows parameter injection for functions."""
    
    print("\n" + "="*60)
    print("SECTION 4: Function Parameter Injection")
    print("="*60)
    
    # Create jobs from functions
    jobs = job({
        "named_params": named_params,
        "using_kwargs": using_kwargs,
        "with_context": with_context
    })
    
    # Define workflow: named_params -> with_context, using_kwargs runs in parallel
    workflow = (jobs["named_params"] | jobs["using_kwargs"]) >> jobs["with_context"]
    
    # Run workflow
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "function_demo")
    
    # Task with nested format
    task = {
        "named_params": {"x": 5, "y": 15},      # Sum = 20
        "using_kwargs": {"a": 1, "b": 2, "c": 3}, # Total = 6
        "with_context": {"multiplier": 3}        # Result = 20 * 3 = 60
    }
    
    print(f"\nSubmitting task: {task}")
    print("\nExecution:")
    fm.submit_task(task, fq_name)
    fm.wait_for_completion()
    
    results = fm.pop_results()
    print(f"\nFinal result: {results['completed'][fq_name][0]}")


# =============================================================================
# SECTION 5: Job Class with get_params()
# =============================================================================

def demo_job_class_parameters():
    """Shows get_params() for JobABC classes."""
    
    print("\n" + "="*60)
    print("SECTION 5: Job Class Parameter Access")
    print("="*60)
    
    # Create job instance and wrap it
    processor = DataProcessor("processor", default_factor=2)
    
    # Note: job() with a single entry returns the job directly, not a dict
    workflow = job({"processor": processor})
    
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "class_demo")
    
    # Nested format for get_params()
    task = {"processor": {"value": 50, "factor": 4}}
    
    print(f"\nSubmitting task: {task}")
    print("\nExecution:")
    fm.submit_task(task, fq_name)
    fm.wait_for_completion()
    
    results = fm.pop_results()
    print(f"\nFinal result: {results['completed'][fq_name][0]}")


# =============================================================================
# SECTION 6: Batch Processing - Multiple Tasks with Different Data
# =============================================================================

def demo_batch_processing():
    """Shows submitting multiple tasks with unique data to the same workflow.
    
    This is the key power of Flow4AI: run thousands of tasks through one workflow.
    Each task has its own parameters, and all run concurrently.
    """
    
    print("\n" + "="*60)
    print("SECTION 6: Batch Processing - Multiple Tasks")
    print("="*60)
    
    def process_order(order_id: int, quantity: int, price: float):
        """Processes a single order. Each task = different order."""
        total = quantity * price
        return {"order_id": order_id, "total": total}
    
    # Note: job() with single entry returns the job directly
    workflow = job({"process_order": process_order})
    
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "batch_orders")
    
    # Submit 5 different orders as 5 separate tasks
    orders = [
        {"order_id": 1001, "quantity": 2, "price": 29.99},
        {"order_id": 1002, "quantity": 1, "price": 149.99},
        {"order_id": 1003, "quantity": 5, "price": 9.99},
        {"order_id": 1004, "quantity": 3, "price": 49.99},
        {"order_id": 1005, "quantity": 10, "price": 4.99},
    ]
    
    print(f"\nSubmitting {len(orders)} orders as separate tasks...")
    for order in orders:
        # Each task goes to the "process_order" job
        task = {"process_order": order}
        fm.submit_task(task, fq_name)
    
    fm.wait_for_completion()
    results = fm.pop_results()
    
    print("\nResults (all processed concurrently):")
    for result in results["completed"][fq_name]:
        print(f"  Order {result['order_id']}: ${result['total']:.2f}")


# =============================================================================
# SECTION 7: Task Pass-Through for Correlation
# =============================================================================

def demo_task_passthrough():
    """Shows how task data flows through for correlation.
    
    Any key in the task that doesn't match a job name passes through unchanged.
    Use this to correlate results with original requests.
    """
    
    print("\n" + "="*60)
    print("SECTION 7: Task Pass-Through for Correlation")
    print("="*60)
    
    def analyze(text: str):
        return {"word_count": len(text.split())}
    
    # Note: job() with single entry returns the job directly
    wrapped_analyze = job({"analyze": analyze})
    wrapped_analyze.save_result = True  # Save to SAVED_RESULTS
    
    workflow = wrapped_analyze
    
    fm = FlowManager()
    fq_name = fm.add_workflow(workflow, "passthrough_demo")
    
    # Include correlation data in the task
    task = {
        # Job parameters
        "analyze": {"text": "Hello world this is a test"},
        # Pass-through data for correlation (any keys not matching job names)
        "request_id": "req-12345",
        "user": "alice",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    print(f"\nSubmitting task with correlation data...")
    fm.submit_task(task, fq_name)
    fm.wait_for_completion()
    
    results = fm.pop_results()
    result = results["completed"][fq_name][0]
    
    print("\nResult:")
    print(f"  Analysis: {result.get('SAVED_RESULTS', {}).get('analyze', {})}")
    print(f"  Correlation data (task_pass_through): {result.get('task_pass_through', {})}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Flow4AI Example 10: Tasks and Parameters")
    print("="*60)
    
    demo_task_formats()
    demo_function_parameters()
    demo_job_class_parameters()
    demo_batch_processing()
    demo_task_passthrough()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("""
KEY TAKEAWAYS:

1. WORKFLOW = A pipeline of connected jobs (created once, reused many times)
2. JOB      = Single execution unit (function or class)
3. TASK     = Data for one workflow execution (each task = different data)

TASK FORMATS (both equivalent):
  - Shorthand: {"job.param": value}
  - Nested:    {"job": {"param": value}}

PARAMETER ACCESS:
  - Functions: Named params auto-inject, or use **kwargs
  - JobABC:    Use self.get_params() for clean access

BATCH PROCESSING:
  - Submit 1000 tasks = 1000 concurrent executions
  - Each task carries its own unique data

See tutorials/05_job_types.py for more on functions vs classes.
""")
