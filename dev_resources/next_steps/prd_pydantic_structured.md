# PRD: pydantic_structured.py

## Overview

**File:** `examples/integrations/pydantic_structured.py`
**Purpose:** Demonstrate structured data extraction from unstructured text using Pydantic models with Flow4AI parallel execution.

---

## Goals

1. Show how to extract validated, typed data from LLM outputs
2. Demonstrate parallel extraction from multiple texts
3. Use Pydantic `BaseModel` for schema definition
4. Integrate with OpenAI's structured output feature (or Instructor library)

---

## Flow4AI Semantics to Demonstrate

| Concept | How Used |
|---------|----------|
| `job()` | Wrap async extraction functions as Flow4AI jobs |
| `p()` | Run multiple extractions in parallel |
| `save_result` | (Optional) Store individual extraction results |
| Task routing | Pass different texts to each extraction job |

---

## Functional Requirements

### Input
- 3-4 sample text snippets embedded in the code (no external files)
- Example domain: product descriptions, person bios, or event announcements

### Processing  
- Define a Pydantic model (e.g., `ProductInfo` with name, price, features)
- Create async extraction functions that call LLM with structured output
- Wrap as Flow4AI jobs
- Execute in parallel

### Output
- Print validated Pydantic model instances
- Show extraction results in clear format

---

## Code Structure

```
# Section 1: Pydantic Models
class Product(BaseModel): ...

# Section 2: Extraction Jobs  
async def extract_product(text): ...

# Section 3: Main (succinct, focused on Flow4AI)
def main():
    # Sample texts
    # Create jobs
    # Build parallel workflow
    # Execute
    # Print results

# Section 4: Output Helpers
def _print_header(): ...
def _print_results(): ...
```

---

## Dependencies

```python
# Required
from pydantic import BaseModel
from langchain_openai import ChatOpenAI  # or instructor library

# Already in setup.py test extras:
# - langchain-openai ✓
# - pydantic ✓ (transitive)
```

**Decision Needed:** Use LangChain's `.with_structured_output()` or add `instructor` as dependency?

Recommendation: Use LangChain's built-in structured output to avoid new dependency.

---

## Sample Data (Embedded)

```python
SAMPLE_TEXTS = [
    "iPhone 15 Pro - $999 - Features: A17 chip, titanium design, 48MP camera",
    "Samsung Galaxy S24 Ultra - $1199 - Features: AI features, 200MP camera, S-Pen",
    "Google Pixel 8 - $699 - Features: Tensor G3 chip, 7 years updates, AI photo editing",
]
```

---

## Performance Requirements

- **Target execution time:** < 10 seconds (with `max_tokens=50`)
- **Test inclusion:** Include in core tests if < 10s
- **Token limit:** Use `max_tokens=50` since structured output is compact

**Important:** Structured output extraction is inherently fast because responses are short JSON, not prose.

---

## Verification Plan

1. Run example manually: `python examples/integrations/pydantic_structured.py`
2. Verify all 3 extractions complete successfully
3. Verify Pydantic validation works (types are correct)
4. Measure execution time
5. Add test to `test_examples.py` if < 10s

---

## Success Criteria

- [ ] Code is < 150 lines
- [ ] Uses correct Flow4AI semantics (`job()`, `p()`)
- [ ] Sample data embedded (no external files)
- [ ] Pydantic validation works
- [ ] Execution time < 10s
- [ ] Output is clear and educational
- [ ] Structure matches existing examples (header, main, helpers)

---

## Notes for Implementation

1. **Model:** Use `gpt-4o-mini` with `max_tokens=50`
2. **Structured output:** Use `.with_structured_output(Product)` method
3. **Error handling:** Show what happens if extraction fails validation
4. **Parallel execution:** Use `p(job1, job2, job3)` pattern
5. **Task input:** Route texts using `job_name.text` pattern
