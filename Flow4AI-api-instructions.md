# Flow4AI API Instructions

This document provides instructions for using the Flow4AI API to execute job graphs, focusing on the `FlowManager` class in `src/flow4ai/flowmanager.py`.

## API Usage

The following sections describe how to use the Flow4AI API, starting with simple usage patterns and progressing to more complex scenarios.

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
task = {"square.x": 5}  # Task with input for square job
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
dsl = jobs["generator"] >> (jobs["square"] | jobs["double"]) >> jobs["combiner"]

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

## Clarification and Improvements

While working with the Flow4AI API, I've identified several areas for clarification and potential improvements:

### Clarifications Needed

1. **Error Handling**: The documentation could better explain how errors in jobs are propagated and handled. The `execute` method raises exceptions, but what happens when using `submit` and `wait_for_completion`?

2. **Task Parameters vs. Job Names**: The naming convention for task parameters is not always clear. Sometimes parameters use dot notation (e.g., `"square.x": 5`), and other times they don't (e.g., `"start": 1`). When should each format be used?

3. **FQ_Name Generation**: The rules for generating fully qualified names (FQ names) could be clearer. How does collision detection and resolution work when adding multiple DSLs with the same graph name and variant?

4. **Return Value Processing**: There's inconsistency in how return values are accessed. Sometimes through `result["result"]`, sometimes from saved results like `result["SAVED_RESULTS"]["job_name"]`.

5. **Context Variable Usage**: The documentation could provide more examples of accessing the job context (`j_ctx`) and explain all the available properties.

6. **Handling Timeouts**: The behavior when tasks exceed the timeout in `wait_for_completion` could be clearer. Are results partial or lost entirely?

7. **Multiple Submit Behavior**: When submitting multiple tasks with the same DSL, are they processed in parallel or sequentially? How is this affected by the implementation (async vs threading)?

### Potential Improvements

1. **Consistent Result Access API**: Standardize how results are accessed from jobs. Consider a more intuitive API for retrieving results.

2. **Enhanced Error Reporting**: Provide more detailed error information, including stack traces and the context in which errors occurred.

3. **Progress Monitoring**: Add methods to monitor the progress of long-running tasks, not just completion status.

4. **Interactive Dashboards**: Implement web-based dashboards for visualizing job graphs and their execution status.

5. **DSL Validation**: Add more robust validation of DSL components before execution to catch configuration errors early.

6. **Result Streaming**: Allow streaming of results as they become available rather than waiting for all tasks to complete.

7. **Persistent Job Graphs**: Support serialization and persistence of job graphs for reuse across application restarts.

8. **Type Annotations**: Enhance type annotations throughout the codebase to improve IDE support and catch type-related errors earlier.

9. **Cancellation Support**: Add the ability to cancel submitted tasks that are still pending or in progress.

10. **Documentation Improvements**: 
    - Add more code examples for common patterns
    - Document all parameters for each method
    - Create diagrams showing the lifecycle of tasks and jobs
    - Provide performance tips and best practices

11. **Synchronous API Option**: Consider providing a simpler synchronous API for cases where asynchronous execution isn't needed.

12. **Execution Hooks**: Add pre/post execution hooks at the job and graph levels for cross-cutting concerns like logging and metrics.
