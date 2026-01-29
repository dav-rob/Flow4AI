# Flow4AI Examples

This directory contains working examples demonstrating Flow4AI's core features and capabilities, organized into two categories:

- **[tutorials/](./tutorials/)** - Learn Flow4AI syntax from simple to complex
- **[integrations/](./integrations/)** - Use Flow4AI with external frameworks (LangChain, OpenAI)

## Setup

### 1. Install Dependencies

For tutorials (basic Flow4AI):
```bash
pip install -e .
```

For integrations (requires external libraries):
```bash
pip install -e ".[test]"
```

### 2. Configure API Keys

Integration examples require API keys. Set up your environment:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# At minimum, you'll need:
# OPENAI_API_KEY=your_key_here
```

**Important**: The `.env` file is in `.gitignore` and will never be committed.

---

## Tutorials (Learning Flow4AI)

Start here! Work through these in order for the best learning experience:

```bash
cd /path/to/Flow4AI
python examples/tutorials/01_hello_workflow.py
python examples/tutorials/02_parameters.py       # CORE - read early!
python examples/tutorials/03_parallel_jobs.py
python examples/tutorials/04_multiprocessing.py
python examples/tutorials/05_job_types.py
python examples/tutorials/06_data_flow.py
python examples/tutorials/07_complex_pipelines.py
```

### Tutorial Descriptions

| # | File | Description |
|---|------|-------------|
| 01 | `hello_workflow.py` | Your first workflow: parallel analysis with result aggregation |
| 02 | `parameters.py` | **CORE!** Task formats, parameter injection, and batch processing |
| 03 | `parallel_jobs.py` | Submit 1000 concurrent tasks with FlowManager |
| 04 | `multiprocessing.py` | CPU-bound processing with FlowManagerMP |
| 05 | `job_types.py` | JobABC vs functions, multiple tails, intermediate results |
| 06 | `data_flow.py` | Understanding `task_pass_through` for batch correlation |
| 07 | `complex_pipelines.py` | Capstone: mixed job types, complex graphs, all features |

---

## Integrations (External Frameworks)

These examples show how Flow4AI orchestrates popular AI frameworks in parallel workflows:

```bash
# Requires OPENAI_API_KEY in .env
python examples/integrations/langchain_simple.py
python examples/integrations/langchain_chains.py
python examples/integrations/openai_native.py
```

### Integration Descriptions

| File | Description |
|------|-------------|
| `langchain_simple.py` | Wrap LangChain LLM calls as Flow4AI jobs |
| `langchain_chains.py` | Multi-perspective document analysis with parallel LangChain chains |
| `openai_native.py` | Native OpenAI integration with Flow4AI's `OpenAIJob` class |

**Key insight**: Flow4AI doesn't replace these frameworks—it **orchestrates** them, enabling parallel execution and complex pipelines with any AI library.

---

## Testing

All examples are tested automatically:

```bash
pytest tests/test_examples.py -v
```

This ensures examples stay up-to-date with the codebase and work as documented.
