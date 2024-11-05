# Result Processing in JobChain

The most important thing to understand about JobChain's result processing is that **the pickling restriction only applies to the result_processing_function itself and its closure variables, not to what happens inside the function**. This means your result processing function can freely perform any operations including file I/O, database operations, logging, etc. - as long as the function itself is defined at module level.

## Quick Start

Most pickling problems can be solved with simple changes:

```python
# ❌ Won't work - closure captures unpicklable state
db = create_database_connection()
def process_result(result):
    db.save(result)  # db is a closure variable

# ✅ Will work - creates resources inside function
def process_result(result):
    db = create_database_connection()  # Created inside function
    db.save(result)

# ✅ Will also work - uses serial mode for unpicklable state
class Processor:
    def __init__(self):
        self.db = create_database_connection()
    
    def process_result(self, result):
        self.db.save(result)

processor = Processor()
job_chain = JobChain(job, processor.process_result, serial_processing=True)
```

## Requirements

For parallel mode (default):
1. Function must be defined at module level (not inside another function)
2. No unpicklable closure variables
3. Not a lambda

For serial mode:
- No restrictions - can use any Python objects or resources

## Best Practices

1. Keep the function definition simple:
```python
def process_result(result):
    # Complex operations are fine here
    with open('log.txt', 'w') as f:
        f.write(str(result))
    db = create_database_connection()
    db.save(result)
```

2. Use serial mode if you need shared state:
```python
class ResultAggregator:
    def __init__(self):
        self.results = []
        self.db = create_database_connection()
    
    def process_result(self, result):
        self.results.append(result)
        self.db.save(result)

aggregator = ResultAggregator()
job_chain = JobChain(job, aggregator.process_result, serial_processing=True)
```

