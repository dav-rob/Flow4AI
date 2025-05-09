# Flow4AI API Instructions

This document provides instructions for using the Flow4AI API to execute job graphs, focusing on the `FlowManager` class in `src/flow4ai/flowmanager.py`.

## API Usage

The following sections describe how to use the Flow4AI API, starting with simple usage patterns and progressing to more complex scenarios.

### Understanding the DSL (Domain Specific Language)

The Flow4AI DSL allows you to define complex job graphs with elegant syntax. Underneath, the DSL is transformed into a precedence graph structure that determines the execution flow.

#### DSL Operators

- **Sequence operator `>>`**: Connects jobs in sequence (output of one job becomes input to the next)
- **Parallel operator `|`**: Creates parallel branches (both jobs receive the same input)
- **Parallel function `p()`**: Groups multiple jobs to be executed in parallel

#### Graph Structure and Validation

When you create a DSL, it's transformed into a precedence graph via `dsl_to_precedence_graph()`. This graph is then validated to ensure it's a proper directed acyclic graph (DAG) with the following checks:

1. No cycles in the graph
2. No cross-graph reference violations
3. Proper head node structure (default head node added if multiple head nodes exist)
4. Proper tail node structure (default tail node added if multiple tail nodes exist)

This validation ensures your job graph can execute correctly without deadlocks or unintended behavior.

#### Simple vs Complex DSL Example

**Simple Linear Pipeline:**
```python
# Linear sequence: job1 >> job2 >> job3
dsl = jobs["job1"] >> jobs["job2"] >> jobs["job3"]
```

**Complex Pipeline with Parallel Branches:**
```python
# Multiple parallel sources into a transformer, then branching, then aggregation
dsl = (p(jobs["analyzer"], jobs["cache_manager"], jobs["processor"]) 
      >> jobs["transformer"] 
      >> (jobs["branch1"] | jobs["branch2"])  # Parallel branches 
      >> jobs["aggregator"])
```

The `dsl_to_precedence_graph()` function converts these DSL expressions into a directed graph (adjacency list) that determines how data flows through your jobs.

### 1. Basic Job Graph Execution

The simplest way to execute a job graph is using the static `run` method:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Define functions to be wrapped into jobs
def square(x):
    return x**2
    
def double(x):
    return x*2

# Create wrapped jobs and a DSL pipeline
jobs = wrap({
    "square": square,
    "double": double
})

# Build the DSL pipeline
dsl = jobs["square"] >> jobs["double"]

# Execute with a task
task = {"square.x": 5}  # Task with input for square job (short form)
errors, result = FlowManager.run(dsl, task, graph_name="simple_math")

# Access the result
print(result["result"])  # Output: 50 (5² * 2)
```

### 2. Using a FlowManager Instance

For more control, create an instance of `FlowManager` and interact with it directly:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Define functions or job classes
def process_text(text):
    return text.upper()

# Create wrapped jobs
jobs = wrap({"processor": process_text})

# Create FlowManager instance
fm = FlowManager()

# Add DSL to FlowManager
fq_name = fm.add_dsl(jobs["processor"], "text_processor")

# Create and submit a task
task = {"processor.text": "hello world"}
fm.submit(task, fq_name)

# Wait for completion
fm.wait_for_completion()

# Get results
results = fm.pop_results()
```

### 3. Creating Complex Job Pipelines with Multiple Steps

Create more complex pipelines with multiple processing steps:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap, p

# Define functions for each step
def generate_numbers(start, count):
    return list(range(start, start + count))

def square_numbers(numbers):
    return [n * n for n in numbers]

def calculate_sum(numbers):
    return sum(numbers)

# Wrap functions into jobs
jobs = wrap({
    "generator": generate_numbers,
    "transformer": square_numbers,
    "aggregator": calculate_sum
})

# Enable saving of intermediate results
jobs["generator"].save_result = True
jobs["transformer"].save_result = True

# Build the pipeline
dsl = jobs["generator"] >> jobs["transformer"] >> jobs["aggregator"]

# Execute the pipeline
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "number_processor")
task = {"generator.start": 1, "generator.count": 5}  # Will generate [1,2,3,4,5]
fm.submit(task, fq_name)
fm.wait_for_completion()
results = fm.pop_results()

# The result should be the sum of squares: 1² + 2² + 3² + 4² + 5² = 55
```

### 4. Parallel Processing with Branched Pipelines

Create pipelines with branches that execute in parallel:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap, p

# Define functions for different branches
def generate_numbers(start, count):
    return list(range(start, start + count))

def square_numbers(numbers):
    return [n * n for n in numbers]
    
def double_numbers(numbers):
    return [n * 2 for n in numbers]

def combine_results(j_ctx):
    # Access results from both branches
    inputs = j_ctx["inputs"]
    squared = inputs["square"]["result"]
    doubled = inputs["double"]["result"]
    return {"squared": squared, "doubled": doubled}

# Wrap functions into jobs
jobs = wrap({
    "generator": generate_numbers,
    "square": square_numbers,
    "double": double_numbers,
    "combiner": combine_results
})

# Enable saving of intermediate results
jobs["generator"].save_result = True

# Build the pipeline with parallel branches
# Method 1: Using the pipe operator
dsl = jobs["generator"] >> (jobs["square"] | jobs["double"]) >> jobs["combiner"]

# Method 2: Using the p() function (alternative)
# dsl = jobs["generator"] >> p(jobs["square"], jobs["double"]) >> jobs["combiner"]

# Execute the pipeline
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "parallel_processor")
task = {"generator.start": 1, "generator.count": 3}  # Will generate [1,2,3]
fm.submit(task, fq_name)
fm.wait_for_completion()
results = fm.pop_results()
```

### 5. Using the Simplified Execute Method

The `execute` method provides a simpler way to run a job graph:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Define functions
def add(x):
    return x + 5
    
def multiply(result):
    return result * 2

# Create wrapped jobs
jobs = wrap({"add": add, "multiply": multiply})
jobs["add"].save_result = True

# Build DSL
dsl = jobs["add"] >> jobs["multiply"]

# Create FlowManager
fm = FlowManager()

# Execute the job graph in one step
task = {"add.x": 10}
errors, result = fm.execute(task, dsl=dsl, graph_name="math_pipeline")

# Result should be (10+5)*2 = 30
print(result["result"])  # Output: 30
```

### 6. Using Custom Job Classes

Create custom job classes by inheriting from `JobABC`:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC
from flow4ai.dsl import wrap

class NumberGenerator(JobABC):
    async def run(self, task):
        start = task.get("start", 0)
        count = task.get("count", 5)
        return {"numbers": list(range(start, start + count))}

class MathOperation(JobABC):
    def __init__(self, name, operation="square"):
        super().__init__(name)
        self.operation = operation
    
    async def run(self, task):
        # Get inputs from previous job using get_inputs method
        inputs = self.get_inputs()
        
        # Get numbers from first job
        numbers = inputs["generator"]["numbers"]
        
        if self.operation == "square":
            result = [n * n for n in numbers]
        elif self.operation == "double":
            result = [n * 2 for n in numbers]
        else:
            result = numbers
            
        return {"result": result, "operation": self.operation}

# Create job instances
generator = NumberGenerator("generator")
math_op = MathOperation("math_op", "square")

# Wrap jobs and create DSL
jobs = wrap({"generator": generator, "math_op": math_op})
dsl = jobs["generator"] >> jobs["math_op"]

# Execute
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "custom_jobs")
task = {"start": 1, "count": 3}
fm.submit(task, fq_name)
fm.wait_for_completion()
results = fm.pop_results()
```

### 7. Using Context Parameter in Wrapped Functions

Use the `j_ctx` parameter to access context information in wrapped functions:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Simple function without context
def generate_data(value):
    return {"data": [value, value*2, value*3]}

# Function using context to access task data and inputs
def process_with_context(j_ctx):
    # Access task data
    task = j_ctx["task"]
    
    # Access inputs from predecessor jobs
    inputs = j_ctx["inputs"]
    data = inputs["generator"]["data"]
    
    # Process data based on task parameter
    operation = task.get("operation", "sum")
    if operation == "sum":
        result = sum(data)
    elif operation == "product":
        from functools import reduce
        import operator
        result = reduce(operator.mul, data, 1)
    else:
        result = data
        
    return {"result": result, "operation": operation}

# Wrap functions
jobs = wrap({
    "generator": generate_data,
    "processor": process_with_context
})

# Enable result saving for the generator job
jobs["generator"].save_result = True

# Create DSL pipeline
dsl = jobs["generator"] >> jobs["processor"]

# Execute
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "context_example")
task = {"generator.value": 5, "processor.operation": "sum"}
fm.submit(task, fq_name)
fm.wait_for_completion()
results = fm.pop_results()
```

### 8. Working with Multiple Graphs and Variants

Create and manage multiple job graphs with different variants:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Create helper function to build math pipelines
def create_math_pipeline(operation):
    def calculate(x):
        if operation == "square":
            return x * x
        elif operation == "double":
            return x * 2
        elif operation == "increment":
            return x + 1
        return x
        
    return wrap({"calculator": calculate})["calculator"]

# Create different DSL pipelines for different operations
square_dsl = create_math_pipeline("square")
double_dsl = create_math_pipeline("double")
increment_dsl = create_math_pipeline("increment")

# Create DSL dictionary with variants
dsl_dict = {
    "math": {
        "dev": square_dsl,
        "prod": double_dsl
    },
    "simple": increment_dsl
}

# Initialize FlowManager with the DSL dictionary
fm = FlowManager(dsl_dict=dsl_dict)

# Submit a task to the math-dev (square) variant
task1 = {"calculator.x": 5}
fm.submit_by_graph(task1, "math", "dev")

# Submit a task to the math-prod (double) variant
task2 = {"calculator.x": 10}
fm.submit_by_graph(task2, "math", "prod")

# Submit a task to the simple graph (increment)
task3 = {"calculator.x": 7}
fm.submit_by_graph(task3, "simple")

# Wait for all tasks to complete
fm.wait_for_completion()

# Get and process results
results = fm.pop_results()
```

### 9. On-Completion Callbacks

Register a callback function to be called when a task completes:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

def process_data(x):
    return x * 2

def on_complete_callback(result):
    print(f"Task completed with result: {result['result']}")
    # Could store result in database, send notification, etc.

# Create and initialize FlowManager with callback
fm = FlowManager(on_complete=on_complete_callback)

# Create simple job
job = wrap({"processor": process_data})["processor"]

# Add DSL to FlowManager
fq_name = fm.add_dsl(job, "callback_example")

# Submit task
task = {"processor.x": 10}
fm.submit(task, fq_name)

# Wait for completion
fm.wait_for_completion()
```

### 10. Submitting Multiple Tasks

Submit multiple tasks at once:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap
from flow4ai.job import Task

def process_value(value):
    return {"result": value * 2, "original": value}

# Create and set up FlowManager
fm = FlowManager()
job = wrap({"processor": process_value})["processor"]
fq_name = fm.add_dsl(job, "batch_processor")

# Create a list of tasks
tasks = [
    Task({"processor.value": 1}),
    Task({"processor.value": 2}),
    Task({"processor.value": 3}),
    Task({"processor.value": 4}),
    Task({"processor.value": 5})
]

# Submit all tasks at once
fm.submit(tasks, fq_name)

# Wait for completion
fm.wait_for_completion()

# Get results
results = fm.pop_results()
```

### 11. Task Parameter Formats

Flow4AI supports two formats for providing task parameters:

#### Short Form (Dot Notation)

The short form uses dot notation to specify job parameters:

```python
# Short form task parameters using dot notation
task = {
    "times.x": 5,                      # Parameter x=5 for job "times"
    "add.args": [100],                 # Positional argument 100 for job "add"
    "add.y": 5,                        # Parameter y=5 for job "add"
    "square.x": 3,                     # Parameter x=3 for job "square"
    "join.kwargs": {"a": 1, "b": 2, "c": 3}  # Multiple kwargs for job "join"
}
```

#### Long Form (Nested Dictionaries)

The long form uses nested dictionaries for a more structured format:

```python
# Long form task parameters using nested dictionaries
task = {
    "times": {"x": 5},                  # times(x=5) -> 10
    "add": {"args": [100], "y": 5},     # add(100, y=5) -> 105
                                        # Note: 'args' implicitly takes precedence
                                        # over named params for positionals
    "square": {"x": 3},                 # square(x=3) -> 9
                                        # This would be overridden by output of add
    "join": {"kwargs": {"a": 1, "b": 2, "c": 3}}  # Multiple kwargs for join
                                        # join(result=square_output, extra="data")
}
```

Both formats are supported and can be used interchangeably based on your preference:

```python
# Create a FlowManager and add a DSL
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "task_params_example")

# Submit with short form parameters
fm.submit({"job1.x": 5, "job2.y": 10}, fq_name)

# Or submit with long form parameters
fm.submit({"job1": {"x": 5}, "job2": {"y": 10}}, fq_name)
```

## Clarification and Improvements

This section addresses common questions and suggests potential enhancements based on the current codebase.

### Clarifications Provided

1.  **Error Handling**:
    *   When using `submit()` and `wait_for_completion()`: Errors occurring within a job's `run` method or if a job times out waiting for its inputs are caught by `FlowManager`. These errors are collected in an internal `error_results` list. You can retrieve these errors using `fm.pop_results()`, which returns a dictionary like `{'completed': [...], 'errors': [...]}`. Each error entry typically includes the exception object and the task data.
    *   The `fm.execute()` method simplifies this by automatically checking `pop_results()` and raising a consolidated `Exception` if any errors were recorded.
    *   Note: If an `on_complete` callback function (passed to `FlowManager` constructor) itself raises an exception, this exception is *not* caught by `FlowManager`'s internal error handling and will propagate.

2.  **Task Parameters vs. Job Names**: This is well-understood. Flow4AI supports:
    *   **Short form (dot notation)**: e.g., `"my_job.input_param": value`. `WrappingJob` internally converts this to the long form.
    *   **Long form (nested dictionaries)**: e.g., `{"my_job": {"input_param": value}}`.
    *   Special keys like `"args"` (for positional arguments) and `"kwargs"` (for a dictionary of keyword arguments) are also supported within a job's parameter dictionary. `args` generally take precedence for positional mapping.

3.  **DSL Transformation**: The process is:
    *   User defines a DSL using operators (`>>`, `|`) or helper functions (`p()`, `s()`).
    *   `FlowManager.add_dsl()` calls `dsl_graph.dsl_to_precedence_graph()`, which traverses the DSL structure and builds:
        *   A `PrecedenceGraph`: A dictionary representing the graph's structure (e.g., `{'JobA': {'next': ['JobB']}}`).
        *   A `JobsDict`: A dictionary mapping short job names to their `JobABC` instances.
    *   `FlowManager.add_dsl()` then calls `FlowManager.add_graph()`.
    *   `FlowManager.add_graph()` calls `f4a_graph.validate_graph()` to check for cycles, valid references, etc. It then uses `JobFactory.create_job_graph()` to link the `JobABC` instances according to the precedence graph, including adding default head/tail jobs if necessary.

4.  **FQ_Name Generation and Collision Handling**:
    *   **Generation**: FQNs are created by `JobABC.create_FQName(graph_name, variant, short_job_name)`. The format is `graph_name$$variant$$short_job_name$$`.
    *   **Collision Handling in `FlowManager.add_dsl`**:
        *   **Same DSL Object**: If the *exact same DSL object instance* is passed to `add_dsl` multiple times, `FlowManager` attempts to detect this (using internal attributes `_f4a_already_added` on the DSL and `_f4a_source_dsl` on head jobs) and aims to return the FQ name from its first addition.
        *   **Different DSL Objects, Same Name/Variant**: If *different DSL objects* are added but are given the same `graph_name` and `variant` by the user, `flowmanager_utils.find_unique_variant_suffix` is invoked. This utility checks `FlowManager.job_map` for existing FQNs that start with `graph_name$$variant$$`. If a potential collision is found, it generates a unique numeric suffix (e.g., `_1`, `_2`) which is appended to the `variant` string (e.g., `variant_1`). This modified variant is then used when `JobABC.create_FQName` is called, ensuring the final FQName stored in `job_map` is unique.

5.  **Return Value Processing**:
    *   The main dictionary returned by `FlowManager` (e.g., from `pop_results()` or `execute()`) primarily represents the output of the *tail job* of the executed graph.
    *   If the tail job's `run` method returns a non-dictionary value, `JobABC._execute` wraps this into a dictionary: `{"result": <value>}`.
    *   The key `JobABC.RETURN_JOB` (string: `'RETURN_JOB'`) in the result dictionary stores the FQ name of the job that produced this primary result (typically the tail job).
    *   The key `JobABC.TASK_PASSTHROUGH_KEY` (string: `'task_pass_through'`) contains the original task dictionary that was submitted to the graph.
    *   The key `JobABC.SAVED_RESULTS` (string: `'SAVED_RESULTS'`) is a dictionary containing outputs from any intermediate jobs in the pipeline that had their `save_result` attribute set to `True`. These intermediate results are keyed by their *short job names*.
    *   Therefore, accessing `final_result["some_key"]` (where `some_key` is not one of the special keys) typically means you are accessing an output field directly from the tail job. Accessing `final_result["SAVED_RESULTS"]["intermediate_job_short_name"]` retrieves the full output dictionary from an earlier job in the pipeline.

6.  **Graph Validation**:
    *   `f4a_graph.validate_graph()` is called by `FlowManager.add_graph()`. It checks for:
        *   Cycles within the graph.
        *   Invalid cross-graph references (ensuring nodes only reference others at the same graph level).
        *   Presence of head nodes (nodes with no incoming edges). It logs a warning if multiple are found.
        *   Presence of tail nodes (nodes with no outgoing edges). It logs a warning if multiple are found.
    *   `JobFactory.create_job_graph()` (used by `FlowManager` when loading from config or processing a DSL) automatically adds a `DefaultHeadJob` if the graph definition has multiple head nodes, and a `DefaultTailJob` if there are multiple tail nodes. This ensures that the graph, as managed internally for execution, effectively has a single entry and exit point.

7.  **Handling Timeouts**:
    *   **`FlowManager.wait_for_completion(timeout=X)`**: This is a top-level timeout for all submitted tasks to either complete or error out.
        *   If this timeout (`X` seconds) is reached, `wait_for_completion()` returns `False`.
        *   If using `fm.execute()`, a `False` return from `wait_for_completion()` causes `fm.execute()` to raise a `TimeoutError`. In this scenario, `execute()` does not return any partial results.
        *   If using `fm.submit()` and `fm.wait_for_completion()` manually, and `wait_for_completion()` returns `False`, then calling `fm.pop_results()` will provide results for any tasks that *did* complete or error out before the timeout. Tasks that were still running or pending will not be included.
    *   **`JobABC.timeout`** (instance attribute, default 3000s): This is an internal timeout used within `JobABC._execute`. A job will wait up to `self.timeout` seconds for all its `expected_inputs` to be received from predecessor jobs. If this specific input-wait timeout occurs for an individual job, that job's execution path will raise an `asyncio.TimeoutError`. This error is caught by `FlowManager._handle_completion`, and the task is recorded in `fm.error_results`. Other independent tasks or branches in the graph can continue their execution.

8.  **Multiple Submit Behavior (`FlowManager`)**:
    *   `FlowManager` (non-MP version) operates using a single `asyncio` event loop, which runs in a dedicated background thread.
    *   When tasks are submitted (e.g., `fm.submit(task1)`, `fm.submit([task2, task3])`), the execution of each task through its job graph is scheduled as an asyncio coroutine (`_execute_with_context`) on this event loop via `asyncio.run_coroutine_threadsafe`.
    *   These coroutines run concurrently on the event loop, managed by asyncio's cooperative multitasking. This means they yield control to allow other tasks to run, providing concurrency but not true parallelism across multiple CPU cores (for that, `FlowManagerMP` is used).
    *   Within a single graph execution, if the DSL defines parallel branches (e.g., `A >> (B | C)`), the jobs `B` and `C` are gathered using `asyncio.gather` in `JobABC._execute`, allowing them to run concurrently within that task's execution flow.

### Potential Improvements

1.  **Consistent Result Access API**: While the structure is now clearer (tail job output vs. `SAVED_RESULTS`), a more streamlined API or helper methods to access specific job outputs could improve usability.
2.  **Enhanced Error Reporting**: Provide more structured error objects in `pop_results()['errors']`, perhaps including the FQ name of the job that failed and more context. The current `execute()` method consolidates errors into a single string, which could be improved.
3.  **Progress Monitoring**: Implement ways to query the status of submitted tasks (e.g., pending, running, percentage complete for long jobs if feasible).
4.  **Interactive Dashboards**: Leverage `graph_pic.py` or similar to create dynamic, web-based visualizations of graph structures and their live execution status.
5.  **DSL Visualization**: Integrate `graph_pic.py` more directly to allow users to easily visualize the graph derived from their DSL, aiding in debugging and understanding.
6.  **Result Streaming**: For long-running jobs or graphs, allow results (or partial results/status updates) to be streamed back as they become available, rather than only via `pop_results()` after `wait_for_completion()`.
7.  **Persistent Job Graphs**: Allow `FlowManager` to serialize its `job_map` (including graph structures) and reload it, to persist defined workflows across sessions.
8.  **Type Annotations & Pydantic Integration**: Continue enhancing type annotations. The use of Pydantic models for job properties (as seen in `OpenAIJob` with `response_format`) is good; expand this for clearer configuration schemas.
9.  **Task Cancellation**: Implement a mechanism to cancel tasks that have been submitted but are not yet complete, or are long-running. This would likely involve `asyncio.Task.cancel()`.
10. **Documentation Improvements**:
    *   More detailed examples for `add_dsl_dict` and graph/variant management.
    *   Clearer explanation of the `JobABC.timeout` (input wait timeout) vs. `FlowManager.wait_for_completion()` timeout.
    *   Best practices for writing `on_complete` callbacks, especially regarding error handling within them.
11. **Synchronous API Wrapper**: For simple use cases or integration with synchronous codebases, a synchronous wrapper around `FlowManager` might be beneficial, though the core remains async.
12. **Execution Hooks/Middleware**: Allow users to register functions that are called at various lifecycle stages (e.g., before/after job run, on task submission/completion) for metrics, logging, or custom logic.
13. **Parameter Validation**: `WrappingJob._validate_params` checks if provided args/kwargs can be bound to the callable's signature. This could be extended, or a pre-submission validation step could be added.
14. **Graph Optimization**: For complex graphs, explore possibilities for static analysis and optimization (e.g., merging compatible jobs, reordering independent branches).
15. **Job-Specific Timeouts**: Allow individual `JobABC` instances to define an execution timeout for their `run` method, distinct from the input-wait timeout.
16. **Retry Mechanisms**: Implement configurable retry policies (e.g., number of retries, backoff strategy) for jobs that might fail due to transient issues.
17. **Dynamic Graph Modification**: (Advanced) Explore safe ways to allow modification of a loaded graph structure, though this adds significant complexity.
18. **Granular `save_result` Control**: Instead of a boolean `save_result`, allow specifying *which* output keys from a job should be saved to `SAVED_RESULTS` to reduce memory footprint.
19. **Context Propagation Control**: Provide more explicit mechanisms to control how context (accessed via `j_ctx` or `self.get_context()`) is shared or isolated, especially across parallel branches or within sub-graphs.
20. **Standardized Job Configuration Schema**: While `jobs.yaml` allows arbitrary `properties`, defining a more standardized schema for common job configurations (e.g., API keys, resource limits) could improve consistency. The `OpenAIJob`'s structured `properties` (client, api, rate_limit) is a good example.
21. **Plugin System for Job Types**: Formalize `JobFactory.register_job_type` into a more discoverable plugin system, perhaps using entry points, for easier extension by users.
22. **Improved DSL Error Messages**: When DSL syntax is incorrect or leads to an invalid graph structure during `dsl_to_precedence_graph`, provide more user-friendly error messages that pinpoint the issue within the DSL expression.
23. **Async Resource Management in Jobs**: Offer guidance or helper utilities for managing asynchronous resources (like `aiohttp.ClientSession`) within `JobABC.run()` methods, ensuring they are properly acquired and released, especially when jobs are part of a larger application. The `OpenAIClient` singleton is one pattern for managing shared clients.
