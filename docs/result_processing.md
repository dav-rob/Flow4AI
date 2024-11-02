# Result Processing in JobChain

JobChain uses multiple processes to achieve efficient parallel execution. This means that the result processing function must be "picklable" - it needs to be serializable so it can be sent between processes. However, JobChain also provides a serial mode for cases where the result processing function cannot be pickled.

## Parallel Mode (Default)

In parallel mode, JobChain uses separate processes for task execution and result processing, providing better performance but requiring picklable functions.

```python
def valid_result_processor(result):
    """This function can be pickled because it's defined at module level."""
    print(f"Processing result: {result}")
    return result.upper()

# This works in parallel mode
job_chain = JobChain(job, valid_result_processor)
```

### Requirements for Parallel Mode

1. The function must be picklable
2. Any closure variables must be picklable
3. Any global variables used must be picklable

## Serial Mode

For cases where your result processing function cannot be pickled (e.g., it uses file handles or database connections), you can use serial mode:

```python
class UnpicklableState:
    def __init__(self):
        self.log_file = open('log.txt', 'w')  # File handle can't be pickled
    
    def process_result(self, result):
        self.log_file.write(str(result) + '\n')

# Create processor with unpicklable state
processor = UnpicklableState()

# Use serial mode for unpicklable functions
job_chain = JobChain(job, processor.process_result, serial_processing=True)
```

### How Serial Mode Works

1. All processing happens in the main process
2. No pickling is required
3. Can use any Python objects or resources
4. Trade-off is reduced parallelism

## Choosing Between Modes

### Use Parallel Mode When:
- Your result processing function is simple and self-contained
- You need maximum performance
- You're processing large numbers of tasks
- Your function only uses picklable resources

### Use Serial Mode When:
- Your function uses unpicklable resources (file handles, database connections)
- Your function depends on complex object state
- You need to maintain shared state between results
- Performance is less critical

## Best Practices

### 1. Keep Functions Simple in Parallel Mode

```python
# GOOD - Simple, picklable function
def good_processor(result):
    return result.upper()

# BAD - Uses unpicklable resources
def bad_processor(result):
    with open('log.txt', 'w') as f:  # File handle can't be pickled
        f.write(str(result))
```

### 2. Create Resources Inside Functions

```python
# GOOD - Create resources when needed
def good_processor(result):
    with open('log.txt', 'a') as f:
        f.write(str(result))

# BAD - Tries to share resource
log_file = open('log.txt', 'w')  # This won't work in parallel mode
def bad_processor(result):
    log_file.write(str(result))
```

### 3. Use Serial Mode for Complex State

```python
class ResultAggregator:
    def __init__(self):
        self.results = []
        self.total = 0
    
    def process_result(self, result):
        self.results.append(result)
        self.total += result['value']

# Use serial mode to maintain shared state
aggregator = ResultAggregator()
job_chain = JobChain(job, aggregator.process_result, serial_processing=True)
```

### 4. Test Pickling Support

```python
import pickle

def test_processor(func):
    """Test if a result processor function can be pickled."""
    try:
        pickle.dumps(func)
        print("Function can be pickled!")
        return True
    except Exception as e:
        print(f"Function cannot be pickled: {e}")
        print("Use serial_processing=True for this function")
        return False
```

## Example: Database Operations

### Parallel Mode Approach
```python
def parallel_processor(result):
    # Create connection inside function
    with create_database_connection() as db:
        db.save(result)
```

### Serial Mode Approach
```python
class DatabaseProcessor:
    def __init__(self):
        # Keep connection open
        self.db = create_database_connection()
    
    def process_result(self, result):
        self.db.save(result)

processor = DatabaseProcessor()
job_chain = JobChain(job, processor.process_result, serial_processing=True)
```

## Performance Considerations

1. Parallel Mode:
   - Better for CPU-bound tasks
   - Better for large numbers of tasks
   - Better when results can be processed independently

2. Serial Mode:
   - Better for I/O-bound tasks
   - Better when maintaining shared state
   - Better when using unpicklable resources
   - May be slower for large numbers of tasks

## Example

See `examples/function_pickling_examples.py` for complete examples of both modes and when to use each.
