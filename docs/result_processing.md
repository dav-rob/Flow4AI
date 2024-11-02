# Result Processing in JobChain

JobChain uses multiple processes to achieve efficient parallel execution. The result processing function must be "picklable" - it needs to be serializable so it can be sent between processes. This document explains the limitations and best practices for providing result processing functions to JobChain.

## Understanding Pickling Limitations

When you pass a result processing function to JobChain, it needs to be sent to a separate process. This means:

1. The function itself must be picklable
2. Any state the function depends on must be picklable
3. Any objects the function references must be picklable

## Valid Approaches

### 1. Standalone Functions

```python
def valid_result_processor(result):
    """This function can be pickled because it's defined at module level
    and only uses built-in Python functionality."""
    print(f"Processing result: {result}")
    # Only use local variables or module-level imports
    processed = result.upper()
    return processed

# This works
job_chain = JobChain(job, valid_result_processor)
```

### 2. Methods from Module-Level Class Instances

```python
class ResultProcessor:
    def __init__(self, prefix):
        # Only store picklable state
        self.prefix = prefix
    
    def process_result(self, result):
        print(f"{self.prefix}: {result}")

# Create instance at module level
processor = ResultProcessor("PREFIX")

# This works because both the instance and its state are picklable
job_chain = JobChain(job, processor.process_result)
```

## Invalid Approaches

### 1. Closures (Functions that Capture Local Variables)

```python
def create_processor(prefix):
    def process_result(result):  # Captures prefix from outer scope
        print(f"{prefix}: {result}")
    return process_result

# This will FAIL
processor = create_processor("PREFIX")
job_chain = JobChain(job, processor)  # Pickling error!
```

### 2. Lambda Functions

```python
# This will FAIL
processor = lambda result: print(f"Result: {result}")
job_chain = JobChain(job, processor)  # Pickling error!
```

### 3. Functions with Unpicklable State

```python
class UnpicklableProcessor:
    def __init__(self):
        # File handles can't be pickled
        self.log_file = open('log.txt', 'w')
    
    def process_result(self, result):
        self.log_file.write(str(result))

# This will FAIL
processor = UnpicklableProcessor()
job_chain = JobChain(job, processor.process_result)  # Pickling error!
```

## Common Scenarios and Solutions

### 1. Working with Files

```python
# BAD - File handle can't be pickled
log_file = open('log.txt', 'w')
def bad_processor(result):
    log_file.write(str(result))

# GOOD - Open file inside function
def good_processor(result):
    with open('log.txt', 'a') as f:
        f.write(str(result))
```

### 2. Working with Databases

```python
# BAD - Connection can't be pickled
db = create_database_connection()
def bad_processor(result):
    db.save(result)

# GOOD - Create connection inside function
def good_processor(result):
    with create_database_connection() as db:
        db.save(result)
```

### 3. Working with External Libraries

```python
# BAD - External object might not be picklable
processor = ComplexExternalObject()
def bad_processor(result):
    processor.process(result)

# GOOD - Create objects inside function
def good_processor(result):
    processor = ComplexExternalObject()
    processor.process(result)
```

## Testing for Pickling Support

You can test if your function will work with JobChain before using it:

```python
import pickle

def test_processor(func):
    """Test if a result processor function can be pickled."""
    try:
        # Try to pickle the function
        pickled = pickle.dumps(func)
        print("Function can be pickled!")
        
        # Try to unpickle and use it
        unpickled = pickle.loads(pickled)
        test_result = {"test": "data"}
        unpickled(test_result)
        print("Function works after unpickling!")
        return True
    except Exception as e:
        print(f"Function cannot be pickled: {e}")
        return False

# Example usage:
def my_processor(result):
    print(result)

test_processor(my_processor)  # Should pass

test_processor(lambda x: print(x))  # Should fail
```

## Best Practices

1. Keep result processing functions simple and self-contained
2. Define functions at module level
3. Only store picklable state in classes
4. Create resource handles (files, connections) inside the function
5. Test pickling support before using with JobChain
6. Use the provided example file (`examples/function_pickling_examples.py`) to verify your approach

## Performance Considerations

1. Heavy processing in the result function will block other results from being processed
2. Consider batching operations (e.g., database writes) for better performance
3. Resource-intensive operations should be handled asynchronously if possible

## Example

See `examples/function_pickling_examples.py` for complete examples of valid and invalid approaches to result processing functions, including:
- Standalone functions
- Class methods
- Closures (invalid)
- Lambdas (invalid)
- Functions with unpicklable state (invalid)
