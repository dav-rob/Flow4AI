# PRD: llamaindex_rag.py

## Overview

**File:** `examples/integrations/llamaindex_rag.py`
**Purpose:** Demonstrate a simple RAG (Retrieval Augmented Generation) pipeline using LlamaIndex with Flow4AI orchestration.

---

## Goals

1. Show basic RAG pattern: index documents → retrieve → generate answer
2. Demonstrate LlamaIndex integration with Flow4AI
3. Use in-memory document storage (no external vector DB)
4. Keep it minimal - a "hello world" of RAG

---

## Flow4AI Semantics to Demonstrate

| Concept | How Used |
|---------|----------|
| `job()` | Wrap LlamaIndex operations as Flow4AI jobs |
| `>>` | Chain indexing → retrieval → generation |
| `j_ctx["inputs"]` | Pass index between stages |
| `j_ctx["params"]` | Access query from task input |
| `save_result` | Store retrieval results for inspection |

---

## Functional Requirements

### Input
- 3-5 sample documents embedded as strings in code
- Domain: company FAQ, product documentation, or recipe collection
- User query embedded in code

### Processing
1. **Index Stage:** Create LlamaIndex VectorStoreIndex from documents
2. **Query Stage:** Execute query against index
3. **Generation Stage:** LLM generates answer using retrieved context

### Output
- Retrieved document chunks
- Generated answer
- Source attribution

---

## Code Structure

```
# Section 1: Sample Documents
DOCUMENTS = [
    "Flow4AI is a Python framework for AI workflow orchestration...",
    "Flow4AI supports parallel execution via the p() function...",
    "Flow4AI uses job() to wrap async functions as workflow nodes...",
]

# Section 2: RAG Jobs
async def create_index(docs):
    """Create LlamaIndex vector store from documents."""
    ...

async def query_index(j_ctx):
    """Query the index and retrieve relevant docs."""
    ...

async def generate_answer(j_ctx):
    """Generate answer using retrieved context."""
    ...

# Section 3: Main
def main():
    # Create workflow: index >> query >> generate
    # Execute with sample query
    # Display results

# Section 4: Output Helpers
def _print_header(): ...
def _print_results(): ...
```

---

## Dependencies

```python
# LlamaIndex core
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.node_parser import SentenceSplitter

# LlamaIndex embeddings (uses OpenAI by default)
from llama_index.embeddings.openai import OpenAIEmbedding

# LlamaIndex LLM
from llama_index.llms.openai import OpenAI
```

**New Dependencies Required:**
```
llama-index-core
llama-index-embeddings-openai
llama-index-llms-openai
```

**Decision Needed:** Add LlamaIndex to `setup.py` extras?

**Recommendation:** Create new `[llamaindex]` extras group:
```python
extras_require = {
    "test": [...],
    "llamaindex": [
        "llama-index-core",
        "llama-index-embeddings-openai", 
        "llama-index-llms-openai",
    ],
}
```

---

## Sample Documents (Embedded)

```python
DOCUMENTS = [
    """Flow4AI is a Python framework for orchestrating AI workflows. It provides
    a clean DSL for defining parallel and sequential job graphs, making it easy
    to coordinate multiple LLM calls efficiently.""",
    
    """The job() function wraps Python async functions as Flow4AI jobs. Jobs can
    be connected using >> for sequential execution or p() for parallel execution.
    Each job receives task input and can access upstream results via j_ctx.""",
    
    """Flow4AI integrates with LangChain by wrapping LangChain chains as async
    functions. This allows parallel execution of multiple chains with automatic
    coordination and result aggregation.""",
    
    """The FlowManager.run() method executes workflows with configurable timeouts.
    It returns (errors, results) tuple where results contains outputs from all
    leaf nodes in the workflow graph.""",
]

QUERY = "How do I connect jobs in Flow4AI?"
```

---

## Performance Requirements

- **Target execution time:** 10-20 seconds
  - Embedding creation: ~2-5s (depends on embedding model)
  - Query + generation: ~3-5s
- **Test inclusion:** ⚠️ **LIKELY > 10s - Flag for review**
- **Token limit:** Use `max_tokens=150` for generation

**IMPORTANT:** This example may exceed 10s due to:
1. Embedding API calls for document indexing
2. Embedding API call for query
3. LLM generation call

**Optimization options to consider:**
- Use smaller/faster embedding model
- Pre-compute embeddings (defeats demo purpose)
- Reduce number of documents
- Use local embeddings (adds dependency complexity)

---

## Test Strategy

Since this example is likely > 10s:

1. **Skip in core tests** using `@pytest.mark.skip` or `--deselect`
2. **Include in full suite** only
3. **Flag to user** for optimization review

```python
# In test_examples.py
@pytest.mark.skip(reason="RAG example > 10s - run in full suite only")
def test_llamaindex_rag():
    ...
```

---

## Verification Plan

1. Install LlamaIndex: `pip install llama-index-core llama-index-embeddings-openai llama-index-llms-openai`
2. Run example manually: `python examples/integrations/llamaindex_rag.py`
3. Verify index creation succeeds
4. Verify query returns relevant documents
5. Verify answer generation works
6. Measure execution time
7. Add test to `test_examples.py` (with skip for core tests)

---

## Success Criteria

- [ ] Code is < 200 lines (RAG needs more code)
- [ ] Uses correct Flow4AI semantics
- [ ] Sample documents embedded (no external files)
- [ ] RAG pipeline works end-to-end
- [ ] Answer cites retrieved sources
- [ ] Dependencies documented
- [ ] Test added (skipped in core tests)
- [ ] Structure matches existing examples

---

## Notes for Implementation

1. **In-memory storage:** Use LlamaIndex's default in-memory vector store
2. **Embedding model:** Default OpenAI `text-embedding-ada-002` is fine
3. **LLM model:** Use `gpt-4o-mini` with `max_tokens=150`
4. **Settings:** Configure LlamaIndex Settings globally at script start
5. **Error handling:** Check for OPENAI_API_KEY, print helpful message if missing
6. **Index passing:** Store index in result dict, access via `j_ctx["inputs"]`

---

## Potential Speed Optimizations (For Future)

If user wants to speed this up later:

1. **Use local embeddings:** `llama-index-embeddings-huggingface` with small model
2. **Pre-computed demo:** Ship with pre-computed embeddings (defeats learning purpose)
3. **Fewer documents:** Reduce to 2 docs minimum
4. **Smaller chunks:** Reduce chunk size to minimize embedding calls
5. **Mock mode:** Add flag to skip actual API calls for testing

---

## Workflow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Documents  │ >>> │ Create Index│ >>> │ Query Index │ >>> │ Generate    │
│  (embedded) │     │ (LlamaIndex)│     │ (retrieve)  │     │ Answer      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │
                           v                   v                   v
                     VectorStoreIndex    Retrieved Chunks    Final Answer
```
