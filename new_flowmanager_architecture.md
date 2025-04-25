# Flow4AI Architecture: Input Handling in Job Graphs

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

### Implementation Note

In `WrappingJob`, the `FN_CONTEXT` variable (defaulting to "j_ctx") is used to identify the special parameter that should receive the job context information. This is set up in the `run()` method:

```python
# From WrappingJob.run method
if self.FN_CONTEXT in sig.parameters:
    callable_params["kwargs"][self.FN_CONTEXT] = {}
    callable_params["kwargs"][self.FN_CONTEXT]["global"] = self.global_ctx
    callable_params["kwargs"][self.FN_CONTEXT]["task"] = params
    callable_params["kwargs"][self.FN_CONTEXT]["inputs"] = self.get_inputs()
```

This means that wrapped functions receive the same information that JobABC subclasses can access directly through their methods, just structured as a context dictionary parameter.
