# Flow4AI

**Mix, Match, and Scale: The Universal AI Workflow Orchestrator**

Flow4AI is the glue that binds your AI ecosystem. **Combine the best features of LangChain, LlamaIndex, and your own custom Python logic** into unified, massively parallel pipelines. 

Whether you're processing thousands of documents, chaining complex LLM calls, or vectorizing datasets, Flow4AI handles the concurrency, dependency management, and error handling so you can focus on the logic.


## Table of Contents
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [The Core Pattern: Divide and Aggregate](#the-core-pattern-divide-and-aggregate)
- [Massive Parallelism](#massive-parallel-execution)
- [Complex Workflows](#complex-workflow-example)
- [Task Passthrough and Intermediate Results](#task-passthrough-and-intermediate-results)
- [Working Examples](#working-examples)
- [Deep Dive: Job Syntax & Parameters](#deep-dive-job-syntax-parameters)

## Quick Start

> **Example Script**: [`examples/01_basic_workflow.py`](examples/01_basic_workflow.py)

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

## Core Concepts

### Workflow
A **workflow** is your complete processing pipeline - a collection of jobs connected in parallel and serial configurations. Think of it as the blueprint that defines how your data flows through different processing steps.

### Job
A **job** is an individual unit of work within your workflow. Each job can run independently and in parallel with other jobs when the workflow structure allows it. Jobs process data and pass their results to downstream jobs.

### Task
A **task** represents a single, independent unit of data flowing through your workflow. When you submit multiple tasks, each one carries its own unique data through the entire workflow. This is what enables true parallel processing - thousands of tasks can execute simultaneously through the same workflow.


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


## Massive Parallel Execution

Flow4AI excels at running **thousands of tasks in parallel**. Choose the right manager for your workload:

### FlowManager: Multi-threaded (I/O-Bound)

 **Example Script**: [`examples/03_parallel_execution.py`](examples/03_parallel_execution.py)

Perfect for API calls, database queries, file I/O, and network operations.

```python
import asyncio
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

async def fetch_data(task_id):
    await asyncio.sleep(0.5)  # Simulate I/O
    return {"task_id": task_id, "status": "complete"}

jobs = wrap({"fetch": fetch_data})
fm = FlowManager()
fq_name = fm.add_dsl(jobs["fetch"], "parallel_workers")

# Submit 1000 tasks - all execute concurrently
import time
start = time.perf_counter()

for i in range(1000):
    fm.submit_task({"fetch.task_id": f"task_{i}"}, fq_name)

fm.wait_for_completion()
elapsed = time.perf_counter() - start

print(f"1000 tasks completed in {elapsed:.2f}s")
print(f"Sequential would take: {1000 * 0.5:.0f}s")
print(f"Speedup: {(1000 * 0.5) / elapsed:.0f}x")
# Typical output: ~1-2 seconds (100-500x speedup!)
```

### FlowManagerMP: Multi-process (CPU-Bound)

 **Example Script**: [`examples/04_multiprocessing.py`](examples/04_multiprocessing.py)

For CPU-intensive workloads requiring true parallelism across cores.

```python
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.dsl import wrap

def cpu_intensive(n):
    # CPU-bound computation (e.g., prime calculations)
    return {"result": sum(i for i in range(n) if all(i % j != 0 for j in range(2, int(i**0.5) + 1)))}

jobs = wrap({"compute": cpu_intensive})
fm = FlowManagerMP(jobs["compute"])
fq_name = fm.get_fq_names()[0]

# Process multiple CPU-intensive tasks across cores
for size in [1000, 5000, 10000]:
    fm.submit_task({"compute.n": size}, fq_name)

fm.close_processes()  # Waits for completion and cleans up
```

**Key Difference:** `FlowManager` uses async/await (single process, many concurrent tasks), while `FlowManagerMP` uses multiprocessing (multiple processes, true CPU parallelism).

## Complex Workflow Example

Combine JobABC classes, functions, and lambdas in sophisticated workflows:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap, p
from flow4ai.job import JobABC

class Analyzer(JobABC):
    async def run(self, task):
        return "analysis_result"

def aggregate(j_ctx):
    # Access all previous job results
    inputs = j_ctx["inputs"]
    task = j_ctx["task"]
    return {"all_inputs": inputs, "original_task": task}

# Mix job types
times = lambda x: x * 2
add = lambda x: x + 3

jobs = wrap({
    "analyzer": Analyzer("analyzer"),
    "times": times,
    "add": add,
    "aggregate": aggregate
})

jobs["times"].save_result = True
jobs["add"].save_result = True

# Complex workflow: parallel branches >> aggregation
dsl = p(jobs["analyzer"], jobs["times"]) >> (jobs["add"] | jobs["aggregate"])

errors, result = FlowManager.run(
    dsl, 
    {"times": {"fn.x": 5}, "add": {"fn.x": 10}},
    "complex_workflow"
)

print(result["SAVED_RESULTS"])     # Intermediate results
print(result["task_pass_through"])  # Original task data
```


## Task Passthrough and Intermediate Results

### Task Passthrough

> **Example Script**: [`examples/02_task_passthrough.py`](examples/02_task_passthrough.py)

When processing multiple tasks with different data, results need access to the **original task data**. Flow4AI automatically includes `task_pass_through` in every result, preserving the complete original task.

**Why it matters:** Each task carries independent data (customer orders, documents, API requests). Your result processing functions need to correlate results back to specific inputs.

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap

def process_order(order_id, amount):
    tax = amount * 0.08
    return {"tax": tax, "total": amount + tax}

jobs = wrap({"process": process_order})
fm = FlowManager()
fq_name = fm.add_dsl(jobs["process"], "orders")

# Submit multiple orders with different data
orders = [
    {"process.order_id": "ORD-001", "process.amount": 100.00},
    {"process.order_id": "ORD-002", "process.amount": 250.50},
]

for order in orders:
    fm.submit_task(order, fq_name)

fm.wait_for_completion()
results = fm.pop_results()

# Access original task data via task_pass_through
for result in results["completed"][fq_name]:
    original_order_id = result["task_pass_through"]["process.order_id"]
    total = result["result"]["total"]
    print(f"Order {original_order_id}: ${total:.2f}")
```

### Accessing Intermediate Results

Use `save_result = True` to capture outputs from any job in your workflow. These are available in the final result's `SAVED_RESULTS` dictionary.

```python
jobs = wrap({"step1": func1, "step2": func2, "step3": func3})
jobs["step1"].save_result = True
jobs["step2"].save_result = True

dsl = jobs["step1"] >> jobs["step2"] >> jobs["step3"]
errors, result = FlowManager.run(dsl, task, "pipeline")

# Access intermediate results
print(result["SAVED_RESULTS"]["step1"])  # Output from step1
print(result["SAVED_RESULTS"]["step2"])  # Output from step2
print(result["result"])                   # Final output from step3
```



## Working Examples

Complete, runnable examples are available in the [`examples/`](./examples/) directory:

- **01_basic_workflow.py** - Parallel analysis with result aggregation
- **02_task_passthrough.py** - Task data preservation and batch processing  
- **03_parallel_execution.py** - 1000 concurrent tasks with FlowManager
- **04_multiprocessing.py** - CPU-bound processing with FlowManagerMP
- **05_complex_workflow.py** - Interdependent jobs exchanging data.
- **07_langchain_chains.py** - Integrating LangChain chains
- **08_openai_job_chains.py** - Native OpenAI job chains (Performance benchmark)
- **09_syntax_details.py** - Syntax guide for JobABC vs ordinary python Functions

Run any example:
```bash
python examples/01_basic_workflow.py
```


### Deep Dive: Job Syntax & Parameters

> **Example Script**: [`examples/09_syntax_details.py`](examples/09_syntax_details.py)

Flow4AI offers two ways to define jobs, each with different syntax for accessing data:

1.  **Wrapped Functions** (Functional, Simple): Best for straightforward transformations.
    -   Parameters passed as **arguments** (e.g., `def func(x, y):`).
    -   Access context via `j_ctx` argument (e.g., `def func(j_ctx, **kwargs):`).
2.  **JobABC Subclasses** (Object-Oriented, Powerful): Best for complex logic and state.
    -   Access inputs via `self.get_inputs()`.
    -   Access full task dictionary via `task` argument in `run()`.

Check out [`examples/09_syntax_details.py`](examples/09_syntax_details.py) for a comprehensive guide on these differences and how to handle nested task parameters correctly. It also covers advanced topics like:
-   Handling multiple tail jobs.
-   Accessing intermediate results.
-   Using `on_complete` callbacks.


## Further Documentation

See the `/docs` directory for detailed documentation:
- `Flow4AI-api-instructions.md` - Comprehensive API reference
- `ARCHITECTURE.md` - System architecture details
