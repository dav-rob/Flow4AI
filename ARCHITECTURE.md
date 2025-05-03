# Flow4AI Architecture: Key Concepts

> **Terminology Clarification**: Throughout this document, "job graph" refers specifically to the technical implementation of execution flow, while "workflow" describes the higher-level business process being automated. A job graph is the concrete realization of a workflow in the Flow4AI system.

## FlowManager: Singleton Pattern

The `FlowManager` class operates as a singleton for managing job graphs and tasks:

- **Single Instance**: Only one instance of `FlowManager` is created per application, you can call the constructor multiple times in different files and it will return the same instance with all state remembered
- **State Management**: The FlowManager maintains internal state about job graphs, tasks, and results
- **Multiple Submissions**: A single FlowManager instance can handle multiple DSLs and task submissions
- **Stateful Counters**: Task counts (completed, errors) are cumulative across all submit operations

```python
# CORRECT: Create a single FlowManager instance
fm = FlowManager()

# Add multiple DSLs to the same manager
fq_name1 = fm.add_dsl(dsl1, "graph_one")
fq_name2 = fm.add_dsl(dsl2, "graph_two")

# Submit tasks to different DSLs
fm.submit(task1, fq_name1)
fm.submit(task2, fq_name2)

# Wait for all tasks to complete
fm.wait_for_completion()
```

```python
# INCORRECT: Creating multiple FlowManager instances
fm1 = FlowManager()  # First instance
fm2 = FlowManager()  # Second instance - unnecessary and can lead to issues
```

## DSL Handling and the Fully Qualified Name (fq_name)

> **Note on Task vs. Job Distinction**: Tasks are units of work (data + metadata) that flow through the job graph, while jobs are the processing units that operate on tasks. This distinction is fundamental to understanding the Flow4AI execution model.

When adding a DSL to FlowManager, important transformations occur that create a fully qualified name (fq_name):

### 1. Creating and Storing a Job Graph

- **DSL Transformation**: The `add_dsl` method calls `dsl_to_precedence_graph`, which transforms the DSL into a graph structure
- **Job Naming**: During transformation, each job is assigned a fully qualified name in the format: `graph_name$$param_name$$job_name$$`
- **Return Value**: The `add_dsl` method returns the fully qualified name (fq_name) of the head job in the graph
- **Key Function**: This fq_name serves as a unique key to identify and access the job graph
- **Graph Name and Head Job Name**: The name of the entire job graph equals the name of the head job in a logical sense for workflow management purposes, not necessarily reflecting all physical implementation details

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

- **One-time Addition**: Each DSL should only be added once to avoid double-transformation
- **Store the fq_name**: Always store and reuse the fq_name returned from `add_dsl`

## Tasks and Submission Patterns

The `Task` class is a dictionary subclass with a unique identifier:

```python
# Creating a task (dictionary with extra functionality)
task1 = Task({"param1": value1, "param2": value2})

# The task_id attribute is automatically generated
print(task1.task_id)  # UUID string for identifying this task
```

FlowManager supports two submission patterns:

### Pattern 1: Individual Submission with Sequential Waiting

```python
# Submit and process tasks one by one
fm.submit(task1, fq_name)
success1 = fm.wait_for_completion()
results1 = fm.pop_results()  # Get results for task1 only

fm.submit(task2, fq_name)
success2 = fm.wait_for_completion()
results2 = fm.pop_results()  # Get results for task2 only
```

### Pattern 2: Batch Submission with Single Wait

```python
# Submit multiple tasks at once
tasks = [task1, task2, task3]  # List of Task objects
fm.submit(tasks, fq_name)      # Submit all at once

# Wait for all submitted tasks to complete
success = fm.wait_for_completion()
results = fm.pop_results()      # Get results for all tasks
```

## State and Results Management

Key methods for managing state and results:

- **wait_for_completion()**: Blocks until all submitted tasks complete (returns boolean success)
- **pop_results()**: Returns and clears accumulated results (completed jobs and errors)
- **get_counts()**: Returns cumulative counts of submitted, completed, and error tasks

```python
# Task counts are cumulative across all submit operations
counts = fm.get_counts()  # Returns {"submitted": X, "completed": Y, "errors": Z}
```

## JobABC Subclasses vs Wrapped Functions

Flow4AI supports two primary methods for defining jobs in a job graph:

1. **JobABC Subclasses** - Object-oriented approach with inheritance
2. **Wrapped Functions** - Functional approach using plain functions

### Input Handling Differences

One of the key architectural differences between these two approaches is how they access inputs from predecessor jobs in the job graph:

#### JobABC Subclasses

JobABC subclasses can directly access inputs from predecessor jobs using the built-in `get_inputs()` method:

```python
class MyCustomJob(JobABC):
    async def run(self, task):
        # Access inputs from predecessor jobs
        inputs = self.get_inputs()
        
        # Access a specific predecessor job's result by its short name
        predecessor_result = inputs.get("predecessor_job_name", {}).get("result", None)
        
        # Process and return result
        return {"processed_data": process(predecessor_result)}
```

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
