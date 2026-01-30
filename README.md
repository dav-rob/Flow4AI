# Flow4AI

**Mix, Match, and Scale: The Universal AI Workflow Orchestrator**

Flow4AI is the glue that binds your AI ecosystem. **Combine the best features of LangChain, LlamaIndex, and your own custom Python logic** into unified, massively parallel pipelines. 

Whether you're processing thousands of documents, chaining complex LLM calls, or vectorizing datasets, Flow4AI handles the concurrency, dependency management, and error handling so you can focus on the logic.


## Table of Contents
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [The Core Pattern: Divide and Aggregate](#the-core-pattern-divide-and-aggregate)
- [Massive Parallelism](#massive-parallel-execution)
  - [Async Requirements](#async-requirements-for-parallel-code)
  - [Scaling to 1000+ Tasks](#scaling-to-1000-tasks)
- [Complex Workflows](#complex-workflow-example)
- [Working Examples](#working-examples)
- [Deep Dive: Functions vs Job Classes](#deep-dive-functions-vs-job-classes)

## Quick Start

> **Example Script**: [`examples/01_basic_workflow.py`](examples/01_basic_workflow.py)

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# Define your processing steps as simple Python functions
def analyze(text):
    return f"Analysis of: {text}"

def summarize(j_ctx):
    # j_ctx provides access to inputs from previous jobs
    inputs = j_ctx["inputs"]
    analysis = inputs["analyze"]["result"]
    return f"Summary: {analysis}"

# Turn functions into jobs and build a pipeline
jobs = job({"analyze": analyze, "summarize": summarize})
workflow = jobs["analyze"] >> jobs["summarize"]

# Execute
task = {"analyze.text": "Hello World"}
errors, result = FlowManager.run(workflow, task, graph_name="my_pipeline")
print(result["result"])  # "Summary: Analysis of: Hello World"
```

## Core Concepts

### Workflow
A **workflow** is your complete processing pipeline - a collection of jobs connected in parallel and serial configurations. Think of it as the blueprint that defines how your data flows through different processing steps.

### Job
A **job** is an individual unit of work within your workflow. Jobs are just Python functions (or classes) that Flow4AI runs in parallel when the workflow structure allows. Jobs process data and pass their results to downstream jobs.

### Task
A **task** represents a single, independent unit of data flowing through your workflow. When you submit multiple tasks, each one carries its own unique data through the entire workflow. This is what enables true parallel processing - thousands of tasks can execute simultaneously through the same workflow.


| Operator | Name | Description |
|----------|------|-------------|
| `>>` | Serial | Execute jobs in sequence. Output of first becomes input to second. |
| `|` | Parallel | Execute jobs concurrently. Both receive the same input. |
| `p()` | Parallel | Function alternative to `|`. Use for grouping: `p(job1, job2, job3)` |

## The Core Pattern: Divide and Aggregate

The key use case is breaking a large task into subtasks that run in parallel, then bringing results together:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p

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
jobs = job({
    "keywords": extract_keywords,
    "sentiment": analyze_sentiment,
    "count": count_words,
    "combine": combine_results
})

# Parallel analysis branches >> aggregation
workflow = p(jobs["keywords"], jobs["sentiment"], jobs["count"]) >> jobs["combine"]

# Execute
task = {"keywords.text": "Hello world example", 
        "sentiment.text": "Hello world example",
        "count.text": "Hello world example"}
errors, result = FlowManager.run(workflow, task, graph_name="analyzer")

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
from flow4ai.dsl import job

async def fetch_data(task_id):
    await asyncio.sleep(0.5)  # Simulate I/O
    return {"task_id": task_id, "status": "complete"}

jobs = job({"fetch": fetch_data})
fm = FlowManager()
fq_name = fm.add_workflow(jobs["fetch"], "parallel_workers")  # Renamed from add_dsl

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

### Async Requirements for Parallel Code

**Critical:** Flow4AI uses asyncio for concurrency. Blocking (sync) code will execute sequentially, not in parallel.

| Pattern | 5 Tasks | Speedup |
|---------|---------|--------|
| OpenAI Sync | 5.81s | 1x |
| **OpenAI Async** | 0.52s | **11.3x** |
| LangChain `invoke()` | 3.43s | 1x |
| **LangChain `ainvoke()`** | 1.33s | **2.6x** |

```python
# ❌ WRONG - blocks event loop, runs sequentially
def my_job(prompt):
    return OpenAI().chat.completions.create(...)  # Blocking!

# ✅ CORRECT - async enables parallel execution
async def my_job(prompt):
    return await AsyncOpenAI().chat.completions.create(...)
```

See [`examples/async/`](examples/async/) for detailed comparisons and benchmarks.

### Scaling to 1000+ Tasks

For large workloads (3000+ tasks), set `max_concurrent` to avoid overwhelming the event loop:

```python
# Automatic throttling - framework handles it internally
fm = FlowManager(max_concurrent=500)  # Safe default

# Or use submit_batch for clean iteration
fm.submit_batch(
    chunks,
    lambda chunk: {"embed.chunk_id": chunk.id, "embed.text": chunk.text},
    fq_name
)
```

| max_concurrent | Recommended For |
|----------------|-----------------|
| None (default) | Small workloads (< 500 tasks) |
| 500 | Safe default for any system |
| 1000+ | Modern laptops (M1+, i7+) - experiment |

Run `python examples/benchmarks/scale_test.py` to find optimal value for your system.

See [`examples/integrations/parallel_rag/`](examples/integrations/parallel_rag/) for a real-world example processing 3000+ document chunks with throttling.

### FlowManagerMP: Multi-process (CPU-Bound)

 **Example Script**: [`examples/04_multiprocessing.py`](examples/04_multiprocessing.py)

For CPU-intensive workloads requiring true parallelism across cores.

```python
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.dsl import job

def cpu_intensive(n):
    # CPU-bound computation (e.g., prime calculations)
    return {"result": sum(i for i in range(n) if all(i % j != 0 for j in range(2, int(i**0.5) + 1)))}

jobs = job({"compute": cpu_intensive})
fm = FlowManagerMP(jobs["compute"])
fq_name = fm.get_fq_names()[0]

# Process multiple CPU-intensive tasks across cores
for size in [1000, 5000, 10000]:
    fm.submit_task({"compute.n": size}, fq_name)

fm.close_processes()  # Waits for completion and cleans up
```

**Key Difference:** `FlowManager` uses async/await (single process, many concurrent tasks), while `FlowManagerMP` uses multiprocessing (multiple processes, true CPU parallelism).

## Complex Workflow Example

Combine job classes, functions, and lambdas in sophisticated workflows:

```python
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p
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

jobs = job({
    "analyzer": Analyzer("analyzer"),
    "times": times,
    "add": add,
    "aggregate": aggregate
})

jobs["times"].save_result = True
jobs["add"].save_result = True

# Complex workflow: parallel branches >> aggregation
workflow = p(jobs["analyzer"], jobs["times"]) >> (jobs["add"] | jobs["aggregate"])

errors, result = FlowManager.run(
    workflow, 
    {"times": {"fn.x": 5}, "add": {"fn.x": 10}},
    "complex_workflow"
)

print(result["SAVED_RESULTS"])     # Intermediate results
print(result["task_pass_through"])  # Original task data
```


## Working Examples

Complete, runnable examples are available in the [`examples/`](./examples/) directory, organized into two categories:

### Tutorials (Learn Flow4AI)

Work through these in order for the best learning experience:

| # | File | Description |
|---|------|-------------|
| 01 | [`hello_workflow.py`](examples/tutorials/01_hello_workflow.py) | Parallel analysis with result aggregation |
| 02 | [`parameters.py`](examples/tutorials/02_parameters.py) | **Core!** Task formats and parameter patterns |
| 03 | [`parallel_jobs.py`](examples/tutorials/03_parallel_jobs.py) | 1000 concurrent tasks with FlowManager |
| 04 | [`multiprocessing.py`](examples/tutorials/04_multiprocessing.py) | CPU-bound processing with FlowManagerMP |
| 05 | [`job_types.py`](examples/tutorials/05_job_types.py) | JobABC vs functions, syntax details |
| 06 | [`data_flow.py`](examples/tutorials/06_data_flow.py) | Task passthrough for batch correlation |
| 07 | [`complex_pipelines.py`](examples/tutorials/07_complex_pipelines.py) | Advanced workflows, mixed job types |

### Integrations (External Frameworks)

See how Flow4AI orchestrates popular AI libraries:

| File | Description |
|------|-------------|
| [`langchain_simple.py`](examples/integrations/langchain_simple.py) | LangChain LLM calls as Flow4AI jobs |
| [`langchain_chains.py`](examples/integrations/langchain_chains.py) | Parallel LangChain chains |
| [`openai_native.py`](examples/integrations/openai_native.py) | Native OpenAI integration |

Run any example:
```bash
python examples/tutorials/01_hello_workflow.py
```


## Deep Dive: Functions vs Job Classes

> **Example Script**: [`tutorials/05_job_types.py`](examples/tutorials/05_job_types.py)

Flow4AI offers two ways to define jobs. Both are equally capable — choose based on your preference:

1.  **Functions** (Recommended): Just write regular Python functions. This is the natural, Pythonic approach.
2.  **Job Classes**: Subclass `JobABC` for more structure — useful when building reusable library components.

### Accessing Data Inside Jobs

| Data You Need | Job Class (`JobABC`) | Function (with `j_ctx`) |
|---|---|---|
| **Parameters for *this* job** | `self.get_params()["key"]` | `kwargs["key"]` |
| **Predecessors' outputs** | `self.get_inputs()["job_name"]` | `j_ctx["inputs"]["job_name"]` |
| **Saved results** *(needs `.save_result=True`)* | `self.get_saved_results()["job_name"]` | `j_ctx["saved_results"]["job_name"]` |
| **Full task dictionary** | `self.get_task()` | `j_ctx["task"]` |

> **Note:** `get_inputs()` returns outputs from **immediate predecessors only**. For earlier jobs in a chain, use `get_saved_results()` (requires setting `.save_result=True` on those jobs).

**Examples:**

```python
# Job Class
class MyJob(JobABC):
    async def run(self, task):
        params = self.get_params()                    # Parameters for this job
        inputs = self.get_inputs()["prev_job"]        # Immediate predecessors
        saved = self.get_saved_results()["early_job"] # Earlier jobs (save_result=True)
        return {"result": params.get("val", 0) * 2}

# Function with j_ctx
def my_function(j_ctx, **kwargs):
    val = kwargs.get("val", 0)                        # Parameters for this job
    inputs = j_ctx["inputs"]["prev_job"]              # Immediate predecessors
    saved = j_ctx["saved_results"]["early_job"]       # Earlier jobs (save_result=True)
    return {"result": val * 2}
```

### Processing Results After Execution

Flow4AI provides two ways to access results: via an `on_complete` callback (async/streaming) or by calling `pop_results()` (synchronous/batch).

| Data You Need | Via `on_complete` callback | Via `pop_results()` |
|---|---|---|
| **Final result** | `result["key"]` | `results["completed"][fq_name][i]["key"]` |
| **Original task (passthrough)** | `result["task_pass_through"]` | `results["completed"][fq_name][i]["task_pass_through"]` |
| **Intermediate results** | `result["SAVED_RESULTS"]["job_name"]` | `results["completed"][fq_name][i]["SAVED_RESULTS"]["job_name"]` |
| **Errors** | N/A (callback not called) | `results["errors"]` |

**Task Passthrough:** Flow4AI automatically includes `task_pass_through` in every result, preserving the original task. This lets you correlate results back to specific inputs when processing batches.

**Intermediate Results:** Set `job.save_result = True` on any job to capture its output in `SAVED_RESULTS`.

**Examples:**

```python
# Setup: Enable intermediate result saving
jobs = job({"step1": func1, "step2": func2, "step3": func3})
jobs["step1"].save_result = True
jobs["step2"].save_result = True
workflow = jobs["step1"] >> jobs["step2"] >> jobs["step3"]

# Option A: on_complete callback (async, per-task)
def on_complete(result):
    original_task = result["task_pass_through"]       # Original task data
    step1_output = result["SAVED_RESULTS"]["step1"]   # Intermediate result
    final_output = result["result"]                   # Tail job result
    print(f"Completed task {original_task['id']}: {final_output}")

fm = FlowManager(on_complete=on_complete)
fq_name = fm.add_workflow(workflow, "pipeline")
fm.submit_task({"id": "task-1", "step1.x": 10}, fq_name)
fm.wait_for_completion()

# Option B: pop_results() (synchronous, batch)
fm = FlowManager()
fq_name = fm.add_workflow(workflow, "pipeline")
fm.submit_task({"id": "task-1", "step1.x": 10}, fq_name)
fm.wait_for_completion()
results = fm.pop_results()

for result in results["completed"][fq_name]:
    original_task = result["task_pass_through"]
    step1_output = result["SAVED_RESULTS"]["step1"]
    final_output = result["result"]
    print(f"Completed task {original_task['id']}: {final_output}")

for error in results["errors"]:
    print(f"Error: {error}")
```

Check out [`tutorials/05_job_types.py`](examples/tutorials/05_job_types.py) for more comprehensive examples including multiple tail jobs and advanced callback patterns.


## Further Documentation

See the `/docs` directory for detailed documentation:
- `Flow4AI-api-instructions.md` - Comprehensive API reference
- `ARCHITECTURE.md` - System architecture details
