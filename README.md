# Flow4AI

**Break complex tasks into parallel subtasks, then aggregate results.**

Flow4AI provides a simple DSL (Domain Specific Language) to define task graphs where work can be split into parallel branches and then combined. This is ideal for AI workflows where you want to analyze data from multiple angles and synthesize the results.

## Quick Start

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

# Define your processing steps as simple functions
def analyze(text):
    return f"Analysis of: {text}"

def summarize(j_ctx):
    # j_ctx provides access to inputs from previous jobs
    inputs = j_ctx["inputs"]
    analysis = inputs["analyze"]["result"]
    return f"Summary: {analysis}"

# Wrap functions as jobs and build a pipeline
jobs = wrap({"analyze": analyze, "summarize": summarize})
dsl = jobs["analyze"] >> jobs["summarize"]

# Execute
task = {"analyze.text": "Hello World"}
errors, result = FlowManager.run(dsl, task, graph_name="my_pipeline")
print(result["result"])  # "Summary: Analysis of: Hello World"
```

## DSL Operators

| Operator | Name | Description |
|----------|------|-------------|
| `>>` | Serial | Execute jobs in sequence. Output of first becomes input to second. |
| `\|` | Parallel | Execute jobs concurrently. Both receive the same input. |
| `p()` | Parallel | Function alternative to `\|`. Use for grouping: `p(job1, job2, job3)` |

## The Core Pattern: Divide and Aggregate

The key use case is breaking a large task into subtasks that run in parallel, then bringing results together:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap, p

# Step 1: Split work into parallel branches
def extract_keywords(text):
    return {"keywords": text.split()[:3]}

def analyze_sentiment(text):
    return {"sentiment": "positive"}

def count_words(text):
    return {"word_count": len(text.split())}

# Step 2: Aggregate results from all branches
def combine_results(j_ctx):
    inputs = j_ctx["inputs"]
    return {
        "keywords": inputs["keywords"]["keywords"],
        "sentiment": inputs["sentiment"]["sentiment"],
        "word_count": inputs["count"]["word_count"]
    }

# Build the graph
jobs = wrap({
    "keywords": extract_keywords,
    "sentiment": analyze_sentiment,
    "count": count_words,
    "combine": combine_results
})

# Parallel analysis branches >> aggregation
dsl = p(jobs["keywords"], jobs["sentiment"], jobs["count"]) >> jobs["combine"]

# Execute
task = {"keywords.text": "Hello world example", 
        "sentiment.text": "Hello world example",
        "count.text": "Hello world example"}
errors, result = FlowManager.run(dsl, task, graph_name="analyzer")

print(result["result"])
# {'keywords': ['Hello', 'world', 'example'], 'sentiment': 'positive', 'word_count': 3}
```

## FlowManager Examples

### Simple Linear Pipeline

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

square = lambda x: x ** 2
double = lambda x: x * 2

jobs = wrap({"square": square, "double": double})
dsl = jobs["square"] >> jobs["double"]

errors, result = FlowManager.run(dsl, {"square.x": 5}, "math_pipeline")
print(result["result"])  # 50 (5² × 2)
```

### Using FlowManager Instance

For more control over task submission and result handling:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

def process(value):
    return value * 2

jobs = wrap({"process": process})
dsl = jobs["process"]

fm = FlowManager()
fq_name = fm.add_dsl(dsl, "my_graph")

fm.submit_task({"process.value": 10}, fq_name)
fm.wait_for_completion()

results = fm.pop_results()
print(results["completed"][fq_name][0]["result"])  # 20
```

### Custom Job Classes

For complex jobs, extend `JobABC`:

```python
from flow4ai.job import JobABC
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

class DataProcessor(JobABC):
    async def run(self, task):
        # Access inputs from predecessor jobs
        inputs = self.get_inputs()
        
        # Your processing logic
        data = inputs.get("generator", {}).get("data", [])
        return {"processed": [x * 2 for x in data]}

class DataGenerator(JobABC):
    async def run(self, task):
        count = task.get("count", 5)
        return {"data": list(range(count))}

# Use in a pipeline
generator = DataGenerator("generator")
processor = DataProcessor("processor")

jobs = wrap({"generator": generator, "processor": processor})
dsl = jobs["generator"] >> jobs["processor"]

errors, result = FlowManager.run(dsl, {"count": 3}, "custom_jobs")
print(result["result"])  # {'processed': [0, 2, 4]}
```

### Saving Intermediate Results

Use `save_result = True` to capture outputs from any job:

```python
jobs = wrap({"step1": func1, "step2": func2, "step3": func3})
jobs["step1"].save_result = True
jobs["step2"].save_result = True

dsl = jobs["step1"] >> jobs["step2"] >> jobs["step3"]

errors, result = FlowManager.run(dsl, task, "pipeline")

# Access saved results
print(result["SAVED_RESULTS"]["step1"])
print(result["SAVED_RESULTS"]["step2"])
```

## FlowManagerMP (Multiprocessing)

For CPU-bound tasks requiring true parallelism across cores, use `FlowManagerMP`. Note that tasks and results must be picklable.

```python
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.dsl import wrap

def heavy_computation(x):
    return x ** 2

jobs = wrap({"compute": heavy_computation})
dsl = jobs["compute"]

fm = FlowManagerMP(dsl)
fq_name = fm.get_fq_names()[0]

fm.submit_task({"compute.x": 10}, fq_name)
fm.close_processes()  # Waits for completion and cleans up
```

## Task Parameter Formats

Two equivalent formats for passing parameters:

```python
# Short form (dot notation)
task = {"job_name.param": value}

# Long form (nested dict)
task = {"job_name": {"param": value}}
```

## Further Documentation

See the `/docs` directory for detailed documentation:
- `Flow4AI-api-instructions.md` - Comprehensive API reference
- `ARCHITECTURE.md` - System architecture details
