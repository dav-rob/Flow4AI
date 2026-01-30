# Async Code Requirements

Flow4AI uses asyncio for parallel execution. To achieve true parallelism, your jobs must use **async** patterns.

## Why Async Matters

Blocking (synchronous) code prevents parallelism by blocking the event loop.

| Pattern | 5 Tasks | Speedup |
|---------|---------|---------|
| OpenAI Sync | 5.81s | 1x (baseline) |
| **OpenAI Async** | 0.52s | **11.3x** |
| LangChain `invoke()` | 3.43s | 1x (baseline) |
| **LangChain `ainvoke()`** | 1.33s | **2.6x** |

## Quick Reference

### OpenAI

```python
# ❌ WRONG - blocks event loop
from openai import OpenAI
def my_job(prompt):
    return OpenAI().chat.completions.create(...)

# ✅ CORRECT - async client
from openai import AsyncOpenAI
async def my_job(prompt):
    return await AsyncOpenAI().chat.completions.create(...)
```

### LangChain

```python
# ❌ WRONG - blocking
def analyze(doc):
    return chain.invoke({"doc": doc})

# ✅ CORRECT - async
async def analyze(doc):
    return await chain.ainvoke({"doc": doc})
```

### Wrapping Sync Code

If no async version exists, use `asyncio.to_thread()`:

```python
import asyncio
import requests

async def fetch_url(url):
    # Runs sync code in thread pool
    return await asyncio.to_thread(requests.get, url)
```

## Test Scripts

Run these to verify async behavior:

```bash
python examples/async/03_openai_async_vs_sync.py
python examples/async/04_langchain_async_vs_sync.py
```
