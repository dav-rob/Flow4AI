# Flow4AI API Instructions

This document provides instructions for using the Flow4AI API to execute job graphs, focusing on the `FlowManager` class in `src/flow4ai/flowmanager.py`.

## API Usage

The following sections describe how to use the Flow4AI API, starting with simple usage patterns and progressing to more complex scenarios.

### Understanding the DSL (Domain Specific Language)

The Flow4AI DSL allows you to define complex job graphs with elegant syntax. Underneath, the DSL is transformed into a precedence graph structure that determines the execution flow.

#### DSL Operators

- **Sequence operator `>>`**: Connects jobs in sequence (output of one job becomes input to the next).
- **Parallel operator `|`**: Creates parallel branches (both jobs receive the same input and can run concurrently).
- **Parallel function `p()`**: A helper function that groups multiple jobs to be executed in parallel, often used as the first element in a sequence or as an argument to `|` or `>>`.
- **Serial function `s()`**: A helper function that groups multiple jobs to be executed in sequence, equivalent to chaining with `>>`.

#### DSL Transformation and Graph Validation

When you add a DSL component to the `FlowManager` using `fm.add_dsl(your_dsl_component, "graph_name")`:
1.  **Transformation to Precedence Graph**: `FlowManager` calls `dsl_graph.dsl_to_precedence_graph()`. This function traverses your DSL structure (which can be a nested combination of `Serial`, `Parallel`, and `JobABC` instances) and builds two key structures:
    *   A **`PrecedenceGraph`**: This is a dictionary representing the graph's topology, e.g., `{'JobA': {'next': ['JobB', 'JobC']}}`, where keys are short job names.
    *   A **`JobsDict`**: A dictionary mapping these short job names to their actual `JobABC` instances.
2.  **Graph Validation**: The `PrecedenceGraph` is then passed to `f4a_graph.validate_graph()`. This function performs crucial checks:
    *   **Cycles**: Ensures there are no circular dependencies.
    *   **Cross-Graph References**: Verifies that jobs only reference other jobs within the same logical graph level.
    *   **Head/Tail Nodes**: Checks for the presence of head nodes (no incoming dependencies) and tail nodes (no outgoing dependencies). It logs warnings if multiple are found.
3.  **Job Graph Assembly**: `JobFactory.create_job_graph()` takes the validated `PrecedenceGraph` and `JobsDict`. It links the `JobABC` instances by setting their `next_jobs` and `expected_inputs` attributes.
    *   **Automatic Head/Tail Jobs**: If the graph definition implies multiple entry points (head jobs) or multiple exit points (tail jobs), `JobFactory.create_job_graph()` automatically inserts a `DefaultHeadJob` or `DefaultTailJob` respectively. This ensures the graph processed by the core execution logic has a single effective entry and exit point, simplifying execution management.

This entire process ensures that your DSL is converted into a valid, executable job graph.

#### Simple vs Complex DSL Example

**Simple Linear Pipeline:**
```python
# Method 1: Using the >> operator
dsl1 = jobs["job1"] >> jobs["job2"] >> jobs["job3"]

# Method 2: Using the s() helper function (equivalent to dsl1)
dsl2 = s(jobs["job1"], jobs["job2"], jobs["job3"])
```

**Complex Pipeline with Parallel Branches:**
```python
# Multiple parallel sources into a transformer, then branching, then aggregation
dsl = (p(jobs["analyzer"], jobs["cache_manager"], jobs["processor"])  # Parallel sources
      >> jobs["transformer"]                                      # Sequential step
      >> (jobs["branch1"] | jobs["branch2"])                       # Parallel branches 
      >> jobs["aggregator"])                                       # Final sequential step
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

For more control, create an instance of `FlowManager`. This allows you to add multiple job graphs, manage variants, and have finer-grained control over task submission and result retrieval.

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap
from flow4ai.job import Task # Import Task for explicit task creation

# Define functions or job classes
def process_text(text_input): # Renamed for clarity
    return text_input.upper()

# Create wrapped jobs
jobs = wrap({"processor": process_text})
dsl_component = jobs["processor"] # The DSL component is the job itself

# Create FlowManager instance
fm = FlowManager()

# Add DSL to FlowManager and get its Fully Qualified Name (FQN)
# The FQN is essential for submitting tasks to this specific graph.
# Format: graph_name$$variant$$short_job_name$$
# 'variant' is empty if not specified. 'short_job_name' is the head job's short name.
fq_name = fm.add_dsl(dsl_component, "text_processor_graph")
# Example fq_name: "text_processor_graph$$$$processor$$"

# Create a task (explicitly using Task or as a dict)
task_data = {"processor.text_input": "hello world"} # Use short-form dot notation
# task_data = {"processor": {"text_input": "hello world"}} # Or long-form
task_instance = Task(task_data)

# Submit the task to the specific graph using its FQN
fm.submit(task_instance, fq_name)

# Wait for all submitted tasks to complete or timeout
# Default timeout is 10 seconds.
# Returns True if all tasks completed/errored, False if timed out.
completed_in_time = fm.wait_for_completion(timeout=5)

if completed_in_time:
    # Retrieve and clear results from FlowManager's internal store
    # Results include 'completed' and 'errors' dictionaries
    results_data = fm.pop_results()
    
    if results_data['errors']:
        print(f"Errors occurred: {results_data['errors']}")
    
    if fq_name in results_data['completed']:
        # Results for a specific graph are keyed by its FQN
        # It's a list because multiple tasks could have been submitted to this graph
        task_results_list = results_data['completed'][fq_name]
        if task_results_list:
            first_task_result = task_results_list[0]
            print(f"Result from tail job: {first_task_result.get('result')}") # "HELLO WORLD"
            # Access original task: first_task_result['task_pass_through']
            # Access intermediate saved results: first_task_result['SAVED_RESULTS']
else:
    print("Processing timed out.")
    # Partial results might be available via pop_results()
    partial_results = fm.pop_results()
    # Handle partial_results or log timeout
```

#### Error Handling with `submit()` and `wait_for_completion()`
When using `fm.submit()` followed by `fm.wait_for_completion()`:
- Errors occurring within a job's `run` method (or if a job times out waiting for inputs via `JobABC.timeout`) are caught by `FlowManager`.
- These errors are collected in an internal `error_results` list.
- `fm.pop_results()` returns a dictionary like `{'completed': [...], 'errors': [...]}`. Each error entry in the `'errors'` list typically includes the exception object and the task data that caused the error.
- If `fm.wait_for_completion(timeout=X)` itself times out (returns `False`), tasks that were still running or pending will not be in the results from `fm.pop_results()`. Only tasks that finished (completed or errored) *before* this top-level timeout will be available.

#### `FlowManager` Concurrency Model
The standard `FlowManager` (non-MP version) uses a single `asyncio` event loop running in a background thread.
- When tasks are submitted, their execution is scheduled as asyncio coroutines on this event loop.
- These coroutines run **concurrently** due to asyncio's cooperative multitasking (yielding control on `await`). This is not true multi-core parallelism.
- Parallel branches within a DSL (e.g., `A >> (B | C)`) are executed concurrently using `asyncio.gather`.
For multi-core parallelism, `FlowManagerMP` should be used.

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

The `execute` method combines `add_dsl`, `submit`, `wait_for_completion`, and `pop_results` into a single call for simpler use cases.

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Define functions
def add(x_val): # Renamed for clarity
    return x_val + 5
    
def multiply_output(input_val): # Renamed for clarity
    return input_val * 2

# Create wrapped jobs
jobs = wrap({"add_job": add, "multiply_job": multiply_output}) # Use descriptive short names
jobs["add_job"].save_result = True # Save intermediate result from 'add_job'

# Build DSL
dsl = jobs["add_job"] >> jobs["multiply_job"]

# Create FlowManager
fm = FlowManager()

# Execute the job graph in one step
task_data = {"add_job.x_val": 10} 
# 'errors_from_execute' will be an empty dict if no errors, or populated if execute() catches them.
# 'result_dict' is the output from the tail job.
errors_from_execute, result_dict = fm.execute(task_data, dsl=dsl, graph_name="math_pipeline")

if not errors_from_execute: # Check if the error dict is empty
    # Result should be (10+5)*2 = 30
    print(f"Tail job output: {result_dict.get('result')}")  # Output: 30
    # Access saved intermediate result:
    # print(f"Saved 'add_job' output: {result_dict['SAVED_RESULTS']['add_job']}") # Output: 15
else:
    print(f"Errors during execution: {errors_from_execute}")

```
#### Error Handling with `execute()`
The `fm.execute()` method simplifies error handling:
- It internally calls `pop_results()`.
- If any errors were recorded in `error_results`, `execute()` will raise a consolidated `Exception` that summarizes these errors. You typically use a `try...except` block around `fm.execute()`.
- If `wait_for_completion` (called internally by `execute`) times out, `execute()` will raise a `TimeoutError`.
The first element returned by `execute` (`errors_from_execute` in the example) will be the `errors` part of `pop_results()`. If `execute` raises an exception due to errors, this variable might not be relevant as the exception would be caught.

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

### 8. Working with Multiple Graphs, Variants, and FQN Management

`FlowManager` can manage multiple distinct job graphs, each potentially having different "variants" (e.g., "dev", "prod"). This is handled through Fully Qualified Names (FQNs) and careful DSL management.

#### FQN Generation and Collision Handling
-   **Generation**: FQNs are created by `JobABC.create_FQName(graph_name, variant, short_job_name)`. The format is `graph_name$$variant$$short_job_name$$`.
-   **Collision Handling in `FlowManager.add_dsl`**:
    *   **Re-adding the Same DSL Object**: If you pass the *exact same Python DSL object instance* to `fm.add_dsl()` multiple times (even with different `graph_name` or `variant` arguments), `FlowManager` attempts to detect this. It uses internal attributes (`_f4a_already_added` on the DSL object and `_f4a_source_dsl` on existing head jobs). If a match is found, it typically returns the FQ name generated during the first addition of that specific DSL object, preventing re-processing and modification of the already processed DSL.
    *   **Different DSL Objects, Same `graph_name` and `variant`**: If you add *different DSL objects* but provide the same `graph_name` and `variant` strings to `fm.add_dsl()`, a collision in the FQN prefix (`graph_name$$variant$$`) could occur. To prevent this, `flowmanager_utils.find_unique_variant_suffix` is invoked. This utility checks `FlowManager.job_map` for existing FQNs that start with the conflicting prefix. If a potential collision is found, it generates a unique numeric suffix (e.g., `_1`, `_2`) which is appended to the user-provided `variant` string (e.g., `variant` becomes `variant_1`). This modified variant is then used when `JobABC.create_FQName` is called, ensuring the final FQN stored in `job_map` is unique.

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Helper to create simple DSLs
def create_pipeline(op_name, func):
    return wrap({op_name: func})[op_name]

# Define DSLs
dsl_square = create_pipeline("calculator", lambda x: x*x)
dsl_double = create_pipeline("calculator", lambda x: x*2)
dsl_increment = create_pipeline("incrementor", lambda x: x+1) # Different short job name

# Initialize FlowManager
fm = FlowManager()

# Add first graph with variants
fqn_math_dev = fm.add_dsl(dsl_square, graph_name="math_ops", variant="dev")
# fqn_math_dev might be "math_ops$$dev$$calculator$$"
fqn_math_prod = fm.add_dsl(dsl_double, graph_name="math_ops", variant="prod")
# fqn_math_prod might be "math_ops$$prod$$calculator$$"

# Add a second, different DSL with the same graph_name and variant as an existing one
# This will trigger collision handling for the variant part of the FQN
fqn_math_dev_v2 = fm.add_dsl(create_pipeline("calculator_v2", lambda x: x*x*x), graph_name="math_ops", variant="dev")
# fqn_math_dev_v2 might become "math_ops$$dev_1$$calculator_v2$$" due to collision with fqn_math_dev's prefix

# Add a completely separate graph
fqn_simple_inc = fm.add_dsl(dsl_increment, graph_name="simple_ops")
# fqn_simple_inc might be "simple_ops$$$$incrementor$$"

# Submitting tasks:
# Using the direct FQN is the most robust way if you've stored it
fm.submit({"calculator.x": 5}, fqn_math_dev)
fm.submit({"calculator.x": 10}, fqn_math_prod)
fm.submit({"incrementor.x": 7}, fqn_simple_inc)
fm.submit({"calculator_v2.x": 2}, fqn_math_dev_v2)


# Alternatively, use submit_by_graph (careful if collisions led to suffixed variants)
# This works if "math_ops" and "dev" uniquely identify fqn_math_dev
try:
    fm.submit_by_graph({"calculator.x": 6}, graph_name="math_ops", variant="dev")
except ValueError as e:
    # This might happen if "math_ops", "dev" matches multiple FQNs
    # (e.g., "math_ops$$dev$$calculator$$" and "math_ops$$dev_1$$calculator_v2$$")
    print(f"Error with submit_by_graph: {e}")
    # In such cases, you must use the specific FQN.
    # You can get all matching FQNs:
    # matching_fqns = fm.get_fq_names_by_graph("math_ops", "dev")

fm.wait_for_completion()
results = fm.pop_results()
# Process results, keyed by their respective FQNs
```

#### Using `add_dsl_dict`
For convenience, you can add multiple graphs and variants using a dictionary:
```python
dsl_dict = {
    "math_operations": { # graph_name
        "dev_variant": dsl_square,  # variant_name: dsl_component
        "prod_variant": dsl_double
    },
    "simple_increment_graph": dsl_increment # graph_name (no variants)
}
# fm = FlowManager(dsl_dict=dsl_dict) # Can pass at init
fm.add_dsl_dict(dsl_dict) # Or add later
# FQNs are generated based on these graph_names and variant_names
```

### 9. On-Completion Callbacks

You can register a callback function with `FlowManager` that will be executed each time a task successfully completes.

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

def process_data_job(data_input):
    return data_input * 2

def my_completion_callback(result_dict):
    # result_dict is the full result object for the completed task
    # (same structure as one item from pop_results()['completed'][fq_name])
    print(f"Task for graph '{result_dict[JobABC.RETURN_JOB]}' completed.")
    print(f"  Tail job output: {result_dict.get('result')}")
    # IMPORTANT: Handle potential errors within the callback itself.
    # If this callback raises an exception, FlowManager will not catch it.
    try:
        # Example: Log to a database or send a notification
        pass
    except Exception as e:
        print(f"Error in on_complete_callback: {e}")


# Initialize FlowManager with the callback
fm = FlowManager(on_complete=my_completion_callback)

# Create and add DSL
job = wrap({"processor": process_data_job})["processor"]
fq_name = fm.add_dsl(job, "callback_graph")

# Submit task
task = {"processor.data_input": 10}
fm.submit(task, fq_name)

fm.wait_for_completion()
# The callback would have been triggered upon task completion.
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

This section summarizes key operational details and suggests potential enhancements.

### Clarifications Provided (Summary)

The detailed explanations for these points have been integrated into the relevant sections above.

1.  **Error Handling**: ✅ Errors within jobs are caught and retrievable via `pop_results()`. `execute()` raises exceptions for these. `on_complete` callback errors are not caught by `FlowManager`.
2.  **Task Parameters vs. Job Names**: ✅ Short-form (dot notation) and long-form (nested dicts) are supported, with `args`/`kwargs` for callables.
3.  **DSL Transformation**: ✅ `add_dsl` -> `dsl_to_precedence_graph` (handles `>>`, `|`, `p()`, `s()`) -> `validate_graph` -> `JobFactory.create_job_graph` (with auto default head/tail).
4.  **FQ_Name Generation and Collision Handling**: ✅ `JobABC.create_FQName` used; `FlowManager` handles same-object DSL re-addition and uses `find_unique_variant_suffix` for different DSLs with clashing names/variants.
5.  **Return Value Processing**: ✅ Results primarily from tail job, with `RETURN_JOB`, `TASK_PASSTHROUGH_KEY`, and `SAVED_RESULTS` (keyed by short names) providing additional context.
6.  **Graph Validation**: ✅ `validate_graph` checks cycles, references, head/tail nodes. `JobFactory` adds default head/tail jobs.
7.  **Handling Timeouts**: ✅ `FlowManager.wait_for_completion(timeout=X)` is a top-level timeout. `JobABC.timeout` is for individual jobs awaiting inputs.
8.  **Multiple Submit Behavior (`FlowManager`)**: ✅ Uses `asyncio` for concurrent (not parallel) execution on a single event loop.

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
