# Flow4AI Examples

This directory contains working examples demonstrating Flow4AI's core features and capabilities.

## Running the Examples

Each example can be run independently:

```bash
cd /path/to/Flow4AI
python examples/01_basic_workflow.py
python examples/02_task_passthrough.py
python examples/03_parallel_execution.py
python examples/04_multiprocessing.py
python examples/05_complex_workflow.py
```

## Example Descriptions

### 01_basic_workflow.py
**Basic Workflow with Parallel Analysis**

Demonstrates:
- Defining jobs as simple functions
- Building workflows with serial (`>>`) and parallel (`|`, `p()`) operators
- Parallel execution of multiple analysis jobs
- Result aggregation
- Accessing intermediate results with `SAVED_RESULTS`

### 02_task_passthrough.py
**Task Passthrough for Independent Data**

Demonstrates:
- Submitting multiple tasks with different data
- Why `task_pass_through` is essential for batch processing
- Accessing original task data in results
- Correlating results with specific task inputs

### 03_parallel_execution.py
**Parallel Execution with FlowManager**

Demonstrates:
- Multi-threaded parallel execution with FlowManager
- Submitting up to 1000 concurrent tasks
- Proof of parallelism via execution time
- Ideal use cases (I/O-bound tasks)

### 04_multiprocessing.py
**Multiprocessing with FlowManagerMP**

Demonstrates:
- True parallelism across CPU cores with FlowManagerMP
- CPU-bound task processing
- Proper cleanup with `close_processes()`
- Performance benefits for computational workloads

### 05_complex_workflow.py
**Complex Workflow with Advanced Features**

Demonstrates:
- Mixed job types (JobABC classes, functions, lambdas)
- Complex parallel branches with `p()` operator
- Serial execution chains with `>>`
- `SAVED_RESULTS` for intermediate data access
- `task_pass_through` for original task data
- Context functions with `j_ctx` parameter

### 06_langchain_simple.py
**LangChain Integration - Simple**

Demonstrates:
- Integrating LangChain with Flow4AI workflows
- Wrapping LangChain LLM calls as Flow4AI jobs
- Parallel execution of multiple LangChain operations
- Async compatibility between frameworks

Prerequisites:
```bash
pip install -e ".[test]"  # Installs langchain dependencies
export OPENAI_API_KEY=your_key_here
```

### 07_langchain_chains.py
**LangChain Integration - Chains**

Demonstrates:
- Using LangChain chains in parallel workflows
- Multi-perspective document analysis (technical, business, UX)
- Parallel execution of multiple LangChain operations
- Result synthesis using j_ctx
- Real-world multi-agent analysis pattern

Prerequisites:
```bash
pip install -e ".[test]"
export OPENAI_API_KEY=your_key_here
```

## Testing

All examples are tested automatically:

```bash
pytest tests/test_examples.py -v
```

This ensures examples stay up-to-date with the codebase and work as documented.
