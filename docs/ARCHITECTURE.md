# Flow4AI Architecture: Key Concepts

> **Terminology Clarification**: Throughout this document, "job graph" refers specifically to the technical implementation of execution flow, while "workflow" describes the higher-level business process being automated. A job graph is the concrete realization of a workflow in the Flow4AI system.

> **Asynchronous Framework**: Flow4AI is fundamentally an asynchronous framework. All job implementations should leverage async/await patterns and avoid blocking operations. Synchronous code and frameworks should be adapted or avoided when possible to maintain the performance benefits of the asynchronous execution model.

## FlowManager and FlowManagerMP
FlowManager and FlowManagerMP, use similar semantics for submit_task and wait_for_completion methods, but they differ in implementation:

### FlowManager (Single-Process, Threaded Asyncio):

`submit_task(task, fq_name)`: Schedules the job's _execute coroutine on an internal asyncio event loop running in a background thread.
Uses a callback (_handle_completion) to track completed/errored tasks and store results.
`wait_for_completion(timeout=10, check_interval=0.1)`: Polls internal counters (submitted_count, completed_count, error_count).  Returns True if all submitted tasks are accounted for (completed or errored) within the timeout, False otherwise.  Tests for FlowManager often assert this boolean return value.

### FlowManagerMP (Multi-Process Asyncio):

`submit_task(task, fq_name)`: Puts the Task object onto a multiprocessing.Queue.
A separate worker process (_async_worker) consumes tasks from this queue, runs an asyncio event loop to execute the job graph, and puts results onto another queue.
An optional result_processing_function (potentially in another process) consumes these results.
`wait_for_completion()`: Signals the end of input to the worker process(es) by putting None on the task queue.  Calls process.join() on the worker process(es), blocking until they terminate (i.e., have processed all tasks).  Does not take a timeout parameter and does not return a boolean status. Completion is implied by the method returning.
Tests for FlowManagerMP use this as a blocking call and then verify results, not checking a return value from wait_for_completion itself.

### Differences:

The primary difference in `wait_for_completion` is due to their concurrency models:

- FlowManager polls internal state for task completion within its own process, making a timeout a natural way to limit the waiting period.
- FlowManagerMP waits for external OS processes to finish their work and terminate, for which process.join() is the standard mechanism.
Point of Unification:


Timeout Semantics: A timeout in FlowManager means "stop polling and check status." A timeout for FlowManagerMP's process.join() would mean a process failed to terminate, a more critical issue potentially requiring forceful termination.
Completion Definition: FlowManager uses task counters. FlowManagerMP relies on worker processes finishing all queued work and exiting.

## Domain Specific Language (DSL) for Job Graphs

Flow4AI provides a powerful DSL for defining job graphs using an intuitive, chainable syntax. This allows you to express complex execution patterns with minimal code.

### DSL Operators

The DSL provides operators and helper functions for constructing job graphs:

1.  **Sequence Operator `>>`**: Connects jobs serially.
    `dsl = jobs["A"] >> jobs["B"]` (A's output goes to B)
2.  **Parallel Operator `|`**: Creates parallel branches.
    `dsl = jobs["source"] >> (jobs["branch1"] | jobs["branch2"])` (source output goes to both branch1 and branch2 concurrently)
3.  **Parallel Function `p()`**: Groups jobs for parallel execution an alternative to using the parallel operator `|`
    `dsl = p(jobs["job1"], jobs["job2"]) >> jobs["sink"]`
4.  **Serial Function `s()`**: Groups jobs for sequential execution, an alternative to chaining with `>>`.
    `dsl = s(jobs["job1"], jobs["job2"], jobs["job3"])`

### Graph Transformation and Validation

When a DSL is added to FlowManager via the dsl_dict parameter of the constructor, or by using the `add_dsl()` or `add_dsl_dict()` methods, the following process occurs:

1. The DSL is transformed into a precedence graph via `dsl_to_precedence_graph()`
2. The resulting graph is validated to ensure it's a proper directed acyclic graph (DAG)
3. Validation includes checks for:
   - No cycles in the graph
   - No cross-graph reference violations
   - Proper head node structure (adding a default head node if multiple head nodes exist)
   - Proper tail node structure (adding a default tail node if multiple tail nodes exist)

This validation ensures your job graph can execute correctly without deadlocks or unintended behavior.

### Complex DSL Examples

```python
# Multiple sources feeding into a transformer
dsl = p(jobs["analyzer"], jobs["cache_manager"], jobs["processor"]) >> jobs["transformer"]

# Parallel branches with join
dsl = jobs["generator"] >> (jobs["square"] | jobs["double"]) >> jobs["aggregator"]

# Complex flow with multiple parallel sections
dsl = (
    p(jobs["analyzer"], jobs["cache_manager"], jobs["times"]) 
    >> jobs["transformer"] 
    >> jobs["formatter"] 
    >> (jobs["add"] | jobs["square"]) 
    >> jobs["aggregator"] 
)
```

## Flow4AI Job Types

There are two job types in Flow4AI:

### JobABC
The abstract base class that defines the core contract for job execution. All custom jobs must inherit from this class and implement the required `run` method.  For complex jobs that benefit from encapsulation, inheritance, and other OOP principles, subclassing JobABC provides a more natural structure.

### WrappingJob
A specialized job implementation that wraps regular Python functions, enabling them to be integrated into Flow4AI job graphs without creating custom `JobABC` subclasses.  This method is often used to wrap functions from LangChain, LlamaIndex, or other AI and data processing frameworks, or simply by those who prefer to use regular Python functions.

##  Task Parameter Formats for different job types

Tasks pass data to jobs in job graphs.  A job graph can support 1000s or 10s of thousands of tasks being submitted concurrently.  Flow4AI can pass task parameters in the two formats ways:

1. To any JobABC subclass
2. To any Python function that is automatically wrapped and assigned a job name using the `wrap()` function

### JobABC Subclass Task Format

If the job is a JobABC subclass, it is responsible for parsing its own task parameters.  It can do this by looking at the task using `get_task()` and extracting the parameters it needs from the task.  For example in the below task a "parse_labels" job may expect  data in the task to be specified in this way, but it is up to the job to decided how to parse the task:

```python
task = {
    "parse_labels": {
        "llm": {
            "model": "gpt-4",
            "temperature": 0.2,
            "max_tokens": 1000,
            "top_p": 0.95,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "stop_sequences": ["\n\n", "###"]
        },
        "input_file": "raw_labels.csv",
        "output_format": "json",
        "batch_size": 50,
        "extract_categories": True,
        "confidence_threshold": 0.75,
        "retry_count": 3,
        "timeout": 60
    }
}
```

If the job is a wrapped function, then the parameters are passed as arguments to the function, as shown below.  Parameters can be passed in short form or long form.

### Wrapped Function Short Form (Dot Notation)

The short form uses dot notation to specify job parameters to wrapped functions.

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

### Wrapped Function Long Form (Nested Dictionaries)

The long form uses nested dictionaries for a more structured format that resembles the typical JobABC subclass task format.

```python
# Long form task parameters using nested dictionaries
task = {
    "times": {"x": 5},                  # times(x=5) -> 10
    "add": {"args": [100], "y": 5},     # add(100, y=5) -> 105
                                        # 'args' takes precedence over named params for positionals
    "square": {"x": 3},                 # square(x=3) -> 9
                                        # This would be overridden by output of add
    "join": {"kwargs": {"a": 1, "b": 2, "c": 3}}  # Multiple kwargs for join
}
```

Both formats are supported and can be used interchangeably based on your preference and use case.

## FlowManager: Singleton Pattern

The FlowManager is implemented with a singleton pattern to enable all components can access the same FlowManager instance and its state


### Implementation Details

The singleton pattern is implemented using the
`instance` class method with a reset capability using `reset_instance` class method.


### Usage Examples

#### Simple Initialization

```python
# Get or create the FlowManager instance
fm = FlowManager.instance()

# Add a DSL
fq_name = fm.add_dsl(my_dsl)

# Use the same instance elsewhere in the code
fm2 = FlowManager.instance()  # Returns the same instance
```

#### Initialization with DSL Parameter

```python
# Initialize with a DSL dictionary
dsl_dict = {
    "workflow": {
        "variant1": create_pipeline("var1"),
        "variant2": create_pipeline("var2")
    }
}

# Get or create the FlowManager instance with DSL
fm = FlowManager.instance(dsl=dsl_dict)

# Submit tasks directly to the loaded DSL
fm.submit_by_graph(task, "workflow", "variant1")
```

#### Testing

For testing purposes, you can reset the singleton instance:

```python
# Reset before each test
FlowManager.reset_instance()

# Create a fresh instance
fm = FlowManager.instance()
```

The thread-safe implementation ensures that the singleton pattern works correctly in multi-threaded environments, using a lock for thread safety during initialization.



## DSL Handling, Graph Validation, and FQNs

> **Note on Task vs. Job Distinction**: Tasks are units of work (data + metadata) that flow through the job graph, while jobs are the processing units that operate on tasks. This distinction is fundamental to understanding the Flow4AI execution model.

When a DSL component is added to `FlowManager` via `add_dsl()`:

1.  **DSL Transformation**: `dsl_graph.dsl_to_precedence_graph()` converts the user's DSL (composed of `Serial`, `Parallel`, and `JobABC` instances) into:
    *   A `PrecedenceGraph`: An adjacency list (dictionary) representing the graph structure using short job names.
    *   A `JobsDict`: A mapping from short job names to their corresponding `JobABC` objects.
2.  **Graph Validation**: `f4a_graph.validate_graph()` is called on the `PrecedenceGraph`. It checks for:
    *   Cycles.
    *   Invalid cross-graph references (ensuring nodes only link within their logical level).
    *   Presence of head and tail nodes, logging warnings if multiple are found.
3.  **Job Graph Assembly**: `JobFactory.create_job_graph()` takes the validated `PrecedenceGraph` and `JobsDict`.
    *   It links the `JobABC` instances by setting their `next_jobs` and `expected_inputs` attributes.
    *   **Automatic Head/Tail Jobs**: If the graph definition has multiple head nodes (no predecessors) or multiple tail nodes (no successors), `JobFactory` automatically inserts a `DefaultHeadJob` or `DefaultTailJob` respectively. This ensures the graph effectively has a single entry and exit point for the core execution logic.
4.  **FQName (Fully Qualified Name) Generation & Management**:
    *   Each job in the graph is assigned an FQN using `JobABC.create_FQName(graph_name, variant, short_job_name)`, resulting in a name like `graph_name$$variant$$short_job_name$$`.
    *   **Collision Avoidance**:
        *   If the *exact same DSL object instance* is re-added, `FlowManager` tries to detect this and reuse the original FQN.
        *   If *different DSL objects* are added with the same `graph_name` and `variant` (which would lead to FQN prefix clashes), `flowmanager_utils.find_unique_variant_suffix()` appends a numeric suffix (e.g., `_1`, `_2`) to the `variant` part of the FQN. This ensures that every distinct graph instance registered with `FlowManager` has a unique FQN.
    *   The `add_dsl` method returns the FQN of the graph's head job (which might be a `DefaultHeadJob`). This FQN is then used to submit tasks to this specific, uniquely identified graph instance.

```python
# Create a job graph and get its fully qualified name (fq_name)
fm = FlowManager()
fq_name = fm.add_dsl(dsl, "graph_name")

# The fq_name will look something like: 'graph_name$$$$first_job_name$$'
```

### 2. Submitting Tasks Using fq_name

- **Job Graph Lookup**: The `submit` method uses the fq_name to find the corresponding job graph
- **Requirement**: When multiple job graphs are loaded, you MUST provide the fq_name to identify which graph to use
- **Convenience**: If only one job graph has been added, the fq_name parameter can be omitted

```python
# CORRECT: Add DSL once and reuse the fq_name for submissions
fq_name = fm.add_dsl(dsl, "graph_name")

# Submit tasks using the fq_name as the key to the job graph
fm.submit(task1, fq_name)
fm.submit(task2, fq_name)
fm.submit([task3, task4], fq_name)  # Submit multiple tasks at once

# If only one DSL has been added, fq_name can be omitted
fm.submit(task5)  # Only works when there's just one job graph in the FlowManager
```

### 3. Avoiding Common Mistakes

```python
# INCORRECT: Adding the same DSL multiple times
fq_name1 = fm.add_dsl(dsl, "graph_name1")  # First addition
fq_name2 = fm.add_dsl(dsl, "graph_name2")  # Second addition - modifies already modified DSL!
```

- **One-time Addition**: Each DSL should only be added once to avoid double-transformation, though there is protection against this in the code.
- **Store the fq_name**: Always store and reuse the fq_name returned from `add_dsl`

## Tasks, Submission, State, and Results Management

### Task Definition and Parameter Formats
-   A `Task` is a dictionary subclass, automatically assigned a unique `task_id`.
-   Job parameters within a task can be specified using:
    -   **Short Form (Dot Notation)**: e.g., `"my_job.param_name": value`. `WrappingJob` converts this to the long form.
    -   **Long Form (Nested Dictionaries)**: e.g., `{"my_job": {"param_name": value}}`.
    -   For wrapped callables, special keys `args` (list) and `kwargs` (dict) can be used for positional and keyword arguments.

### Submission and Execution
-   Tasks are submitted via `fm.submit(task, fq_name)` or `fm.submit([task_list], fq_name)`.
-   `fm.wait_for_completion(timeout=X)` blocks until all tasks complete/error, or `X` seconds elapse. Returns `True` on full completion, `False` on timeout.
    -   The `JobABC.timeout` attribute (default 3000s) is a separate, per-job timeout for awaiting all its `expected_inputs`. If this is exceeded, the job errors out.
-   `fm.execute(task, dsl, ...)` is a high-level method combining `add_dsl`, `submit`, `wait_for_completion`, and result retrieval. It raises an `Exception` for job errors or a `TimeoutError` if `wait_for_completion` times out.
-   **Concurrency (`FlowManager`)**: Operates on a single `asyncio` event loop in a background thread, providing concurrency (cooperative multitasking) but not true multi-core parallelism. Parallel DSL paths (e.g., `A | B`) are run concurrently via `asyncio.gather`.

### Results and Error Handling
-   `fm.pop_results()` retrieves and clears results, returning `{'completed': {fq_name: [task_results...]}, 'errors': [error_details...]}`.
    -   Each `task_result` in the `'completed'` list contains:
        -   Direct output from the graph's tail job (e.g., `task_result["output_key"]`). If the tail job returns a non-dict, it's wrapped: `{"result": value}`.
        -   `JobABC.RETURN_JOB`: FQN of the job that produced this main result (usually the tail job).
        -   `JobABC.TASK_PASSTHROUGH_KEY`: The original task dictionary submitted.
        -   `JobABC.SAVED_RESULTS`: A dictionary of `{short_job_name: full_job_output_dict}` for any intermediate jobs that had `save_result=True`.
-   Errors from job execution (including `JobABC.timeout` for inputs) are caught and listed in `pop_results()['errors']`.
-   Exceptions raised within an `on_complete` callback (if provided to `FlowManager`) are *not* caught by `FlowManager`'s internal error handling.
-   `fm.get_counts()`: Returns cumulative `{'submitted': X, 'completed': Y, 'errors': Z}`.

## JobABC Subclasses vs Wrapped Functions

Flow4AI supports two primary methods for defining jobs in a job graph:

1. **JobABC Subclasses** - Object-oriented approach with inheritance
2. **Wrapped Functions** - Functional approach using plain functions


### When to Use Wrapped Functions

Wrapped functions were designed to enable seamless integration with existing frameworks and simplify the developer experience:

- **Framework Integration**: Easily wrap code from LangChain, LlamaIndex, or any other AI or data processing framework that users are already familiar with.

- **Simplicity First**: For users who prefer writing standard Python functions, wrapped functions provide a straightforward approach with no reduction in functionality compared to JobABC subclasses.

- **Minimal Context Dependencies**: Most transformation functions don't need access to job context data. When a job doesn't need to access inputs from predecessor jobs or task metadata, wrapped functions without the `j_ctx` parameter offer the cleanest implementation.

```python
# Example: Simple wrapped function without need for context
def process_document(document):
    # Process the document
    return {"processed_document": process_result}

# If context access is needed, use j_ctx parameter
def advanced_process(j_ctx):
    # Access task and inputs when needed
    task = j_ctx["task"]
    inputs = j_ctx["inputs"]
    return {"result": processed_data}
```

### When to Use JobABC Subclasses

For more complex scenarios, subclassing JobABC remains fully supported and is recommended when:

- You need direct access to built-in context methods like `get_inputs()` and `get_task()`
- Your job benefits from object-oriented design principles
- You're extending existing JobABC-based code

### Best Practice for Job Definition and DSL Construction

The recommended approach for defining job names and constructing DSL components is to use the `wrap()` function with a dictionary mapping names to job implementations. This method provides several advantages:

1. **Explicit Naming**: Each job gets a clear, explicit name that will be used as its short job name in the job graph
2. **Unified Treatment**: Both JobABC subclasses and regular functions are handled consistently
3. **Reference Convenience**: The resulting dictionary allows for easy job reference when constructing the DSL
4. **Code Readability**: The job graph structure becomes visually apparent in the DSL construction

```python
# First define or import your job implementations
analyzer2 = ProcessorJob("Analyzer2", "analyze")  # JobABC subclass
cache_manager = ProcessorJob("CacheManager", "cache")  # JobABC subclass
times = lambda x: {"result": x * 3}  # Simple function to be wrapped
transformer = ProcessorJob("Transformer", "transform")  # JobABC subclass
formatter = ProcessorJob("Formatter", "format")  # JobABC subclass
add = lambda x: {"result": x + 2}  # Simple function to be wrapped
square = lambda x: {"result": x * x}  # Simple function to be wrapped
aggregator = ProcessorJob("Aggregator", "aggregate")  # JobABC subclass
test_context = lambda j_ctx: {"result": process(j_ctx)}  # Function with context access

# Wrap all jobs in a dictionary with their short names
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

# Optionally configure job properties
jobs["times"].save_result = True
jobs["add"].save_result = True
jobs["square"].save_result = True

# Construct the DSL component using the named jobs
dsl:DSLComponent = (
    p(jobs["analyzer2"], jobs["cache_manager"], jobs["times"]) 
    >> jobs["transformer"] 
    >> jobs["formatter"] 
    >> (jobs["add"] | jobs["square"]) 
    >> jobs["test_context"]
    >> jobs["aggregator"] 
)
```

This approach works seamlessly for both JobABC subclasses and functions. When a JobABC subclass is "wrapped," it simply assigns the provided name without any negative side effects. For functions, it creates proper WrappingJob instances to integrate them into the job graph.

### Input Handling Differences

The main technical distinction between these two approaches is how they access inputs from predecessor jobs in the job graph. Importantly, only a small subset of wrapped functions typically need access to previous inputs or task metadata, making the wrapped function approach particularly clean for straightforward transformations:

#### JobABC Subclasses

JobABC subclasses implement an asynchronous `run` method and can directly access inputs from predecessor jobs using the built-in `get_inputs()` method:

```python
class MyCustomJob(JobABC):
    async def run(self, task):
        # Access inputs from predecessor jobs
        inputs = self.get_inputs()
        
        # Access a specific predecessor job's result by its short name
        predecessor_result = inputs.get("predecessor_job_name", {}).get("result", None)
        
        # Use async libraries and patterns for processing
        processed_data = await async_process(predecessor_result)
        
        # Return result
        return {"processed_data": processed_data}
```

**Important:** The `run` method is defined as `async` and should use asynchronous patterns. Avoid synchronous blocking operations that could affect performance.

**Important**: `get_inputs()` relies on proper job naming conventions. The `parse_job_name` method extracts short names from fully qualified ones using a specific format: `graph_name$$param_name$$job_name$$`. If a job name doesn't follow this pattern, it returns "UNSUPPORTED NAME FORMAT", which may cause input retrieval issues.

The `get_inputs()` method returns a dictionary with short job names as keys, making it easy to access upstream job results.

#### Wrapped Functions

For regular Python functions that are wrapped using the Flow4AI `wrap()` utility, inputs must be accessed through a special parameter named `j_ctx` (job context):

```python
def my_function(j_ctx):
    # Access the task data
    task = j_ctx["task"]
    
    # Access inputs from predecessor jobs
    inputs = j_ctx["inputs"]
    
    # Access a specific predecessor job's result
    predecessor_result = inputs.get("predecessor_job_name", {}).get("result", None)
    
    # Process and return result
    return {"processed_data": process(predecessor_result)}
```

The `j_ctx` parameter is automatically populated by the `WrappingJob` class when it executes the function. In the `WrappingJob.run()` method, it detects if the function accepts a parameter named `FN_CONTEXT` (which defaults to "j_ctx") and populates it with the necessary context information.

### Best Practices

1. For complex jobs with state or configuration, use **JobABC subclasses** and leverage the `get_inputs()` method.
2. For simple transformations or operations, use **wrapped functions** with the `j_ctx` parameter.
3. When refactoring between approaches, be aware of this fundamental difference in accessing inputs.
4. Always use the `wrap()` utility to properly integrate regular functions into the Flow4AI job graph system.

### Implementation Details

#### WrappingJob Context Passing

In `WrappingJob`, the `FN_CONTEXT` variable (defaulting to "j_ctx") is used to identify the special parameter that should receive the job context information. This is set up in the `run()` method:

```python
# From WrappingJob.run method
if self.FN_CONTEXT in sig.parameters:
    callable_params["kwargs"][self.FN_CONTEXT] = {}
    callable_params["kwargs"][self.FN_CONTEXT]["global"] = self.global_ctx
    callable_params["kwargs"][self.FN_CONTEXT]["task"] = params
    callable_params["kwargs"][self.FN_CONTEXT]["inputs"] = self.get_inputs()
```

Wrapped functions receive the same information that JobABC subclasses can access directly through their methods, just structured as a context dictionary parameter.

#### Job Naming Conventions

Job names in Flow4AI follow this format: `graph_name$$param_name$$job_name$$`

- When using `dsl_to_precedence_graph()`, this naming scheme is applied automatically
- The `add_dsl()` method handles this transformation and returns the fully qualified name
- Job names that don't follow this convention will cause "UNSUPPORTED NAME FORMAT" errors
- These naming conventions are crucial for proper input passing between jobs

```python
# Example of a fully qualified job name
'test_pipeline$$$$generator$$'  # graph_name$$param_name$$job_name$$
```

## Retrieving Results Using the fq_name

The FlowManager API provides several methods for retrieving results from job executions, all of which use the same fq_name that was returned from `add_dsl()` when creating the job graph:

### The Results Lifecycle

1. **Create job graph**: `fq_name = fm.add_dsl(dsl, "graph_name")`
2. **Submit tasks**: `fm.submit(task, fq_name)` 
3. **Wait for completion**: `fm.wait_for_completion()`
4. **Retrieve results**: `results = fm.pop_results()`
5. **Access results using fq_name**: `task_result = results['completed'][fq_name][0]`

### Popping Results with pop_results()

The `pop_results()` method retrieves and clears accumulated results:

```python
# Submit task(s) using the fq_name from add_dsl
fm.submit(task, fq_name)
# or fm.submit([task1, task2], fq_name)

# Wait for tasks to complete
fm.wait_for_completion()

# Pop results - this returns and clears the accumulated results
results = fm.pop_results()

# The results structure contains completed jobs and errors
print(results['completed'])  # Dictionary keyed by fq_name with results
print(results['errors'])     # List of tasks that encountered errors
```

### Accessing Tail Job Results Using fq_name

Results from the tail job (last job in the pipeline) are accessed using the same fq_name that was used during submission:

```python
# Get the fq_name when creating the job graph
fq_name = fm.add_dsl(dsl, "graph_name")

# After submitting and completing tasks, pop results
results = fm.pop_results()

# Access tail job results using the same fq_name as the key
tail_job_results = results['completed'][fq_name][0]  # For a single task

# For multiple tasks, each task result is in the list with the same fq_name key
first_task_results = results['completed'][fq_name][0]
second_task_results = results['completed'][fq_name][1]

# These results contain the direct output of the tail job
print(tail_job_results['sum'])      # Access a specific value from tail job
print(tail_job_results['count'])    # Access another specific value
```

### Accessing SAVED_RESULTS

When jobs have `save_result = True` set, their outputs are stored in a special `SAVED_RESULTS` field, still accessed using the fq_name:

```python
# Get results using the same fq_name used for submission
results = fm.pop_results()
saved_results = results['completed'][fq_name][0]['SAVED_RESULTS']

# Access results from specific jobs in the pipeline by their short names
generator_results = saved_results['generator']
transformer_results = saved_results['transformer']

# Access specific values from each job
print(generator_results['numbers'])
print(transformer_results['transformed'])
```

### Task Parameters Pass-Through

Task parameters are automatically passed through to the results for convenience, still accessed using the same fq_name:

```python
# Create a task with parameters
task = Task({
    'param1': 'value1',
    'param2': 'value2'
})

# Submit using the fq_name from add_dsl
fm.submit(task, fq_name)
fm.wait_for_completion()

# Pop and access results using the same fq_name
results = fm.pop_results()
task_params = results['completed'][fq_name][0]['task_pass_through']
print(task_params['param1'])  # Outputs: 'value1'
```

### Understanding the Results Structure

The overall structure of results from `pop_results()` is:

```
results = {
    'completed': {
        fq_name: [  # The same fq_name returned from add_dsl
            {  # First task result
                'RETURN_JOB': '...',
                'task_pass_through': Task(...),
                'SAVED_RESULTS': {...},
                # Direct outputs from the tail job
                'output_key1': value1,
                'output_key2': value2,
                ...
            },
            {  # Second task result (if multiple tasks were submitted)
                ...
            }
        ]
    },
    'errors': []
}
```

This consistency in using the same fq_name throughout the entire lifecycle (from job graph creation to result retrieval) ensures clarity and prevents confusion when working with multiple job graphs.
