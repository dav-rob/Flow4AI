# Result Processing in JobChain

Pickling restrictions on result_processing_function, mean that for parallel-mode result processing (default mode) the function should:

- not be local, it should be defined at module level (not inside another function),
- not contain unpicklable closure variables,
- not be a lambda.

For serial mode:
- No restrictions - can use any Python objects or resources

JobChain's result processing pickling restriction **only applies to the result_processing_function itself not to what happens inside the function**. This means your result processing function can freely perform any operations including file I/O, database operations, logging, etc. - as long as the function itself is defined at module level not locally, the function is not a lambda and does not contain unpicklable closure variables.

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
flowmanagerMP = JobChain(job, processor.process_result, serial_processing=True)
```


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


