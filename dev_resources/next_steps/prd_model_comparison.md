# PRD: model_comparison.py

## Overview

**File:** `examples/integrations/model_comparison.py`
**Purpose:** Query multiple LLM providers simultaneously and compare their responses, showcasing Flow4AI's parallel execution strength.

---

## Goals

1. Demonstrate querying multiple LLM providers in parallel
2. Show how to aggregate and compare results from parallel jobs
3. Highlight Flow4AI's core value: efficient parallel orchestration
4. Provide a practical pattern for model evaluation

---

## Flow4AI Semantics to Demonstrate

| Concept | How Used |
|---------|----------|
| `job()` | Wrap provider-specific async functions as jobs |
| `p()` | Run all model queries in parallel |
| `>>` | Chain parallel results to comparison job |
| `j_ctx["inputs"]` | Access outputs from multiple upstream jobs |
| `save_result` | Store individual model responses for inspection |

---

## Functional Requirements

### Input
- Single prompt/question embedded in code
- Example: "Explain quantum computing in one sentence"

### Processing
- Query 3 different models in parallel:
  - OpenAI GPT-4o-mini
  - Anthropic Claude Haiku (if key available)
  - Google Gemini Flash (via OpenRouter or direct)
- Collect all responses
- Compare/summarize differences

### Output
- Display each model's response
- Show timing for each
- Highlight differences or consensus

---

## Code Structure

```
# Section 1: Model Query Jobs
async def query_openai(prompt): ...
async def query_anthropic(prompt): ...
async def query_gemini(prompt): ...

# Section 2: Comparison Job
async def compare_responses(j_ctx): ...

# Section 3: Main
def main():
    # Single prompt
    # Create jobs for each provider
    # Build workflow: p(openai, anthropic, gemini) >> compare
    # Execute
    # Display results

# Section 4: Output Helpers
def _print_header(): ...
def _print_comparison(): ...
```

---

## Dependencies

```python
# OpenAI - already available
from langchain_openai import ChatOpenAI

# Anthropic - may need langchain-anthropic
from langchain_anthropic import ChatAnthropic

# Gemini - can use OpenRouter to avoid new dependency
# OR langchain-google-genai
```

**Decision Needed:** 
- Use direct provider SDKs or LangChain wrappers?
- Use OpenRouter for Anthropic/Gemini to minimize dependencies?

**Recommendation:** Use OpenRouter for non-OpenAI models to keep dependencies minimal. This also demonstrates OpenRouter integration.

---

## Provider Configuration

```python
# OpenAI (direct)
llm_openai = ChatOpenAI(model="gpt-4o-mini", max_tokens=100)

# Anthropic via OpenRouter
llm_claude = ChatOpenAI(
    model="anthropic/claude-3-haiku",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    max_tokens=100
)

# Gemini via OpenRouter
llm_gemini = ChatOpenAI(
    model="google/gemini-2.0-flash-lite-001",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    max_tokens=100
)
```

---

## Graceful Degradation

The example should work with partial API key availability:
- OpenAI key → always required (primary)
- OpenRouter key → optional (for Claude/Gemini)

If OpenRouter is missing, run only OpenAI and skip the comparison to a simpler "single model" demo.

```python
if OPENROUTER_AVAILABLE:
    workflow = p(openai_job, claude_job, gemini_job) >> compare_job
else:
    workflow = openai_job  # Graceful fallback
    print("Note: Set OPENROUTER_API_KEY for multi-model comparison")
```

---

## Sample Prompt (Embedded)

```python
PROMPT = "Explain quantum computing in one sentence for a 10-year-old."
```

---

## Performance Requirements

- **Target execution time:** ~5-8 seconds (3 parallel calls)
- **Test inclusion:** Include in core tests (parallel should be fast)
- **Token limit:** Use `max_tokens=100` for all models

**Note:** This example should be FAST because all calls run in parallel. Expected time is roughly equal to the slowest single call, not sum of all calls.

---

## Verification Plan

1. Run example manually: `python examples/integrations/model_comparison.py`
2. Verify all available models respond
3. Verify graceful degradation if OpenRouter key missing
4. Measure execution time (should be ~5-8s, NOT 15-20s)
5. Add test to `test_examples.py`

---

## Success Criteria

- [ ] Code is < 150 lines
- [ ] Uses correct Flow4AI semantics (`job()`, `p()`, `>>`, `j_ctx`)
- [ ] Queries run in parallel (verify via timing)
- [ ] Graceful degradation without OpenRouter key
- [ ] Clear output showing each model's response
- [ ] Execution time < 10s
- [ ] Structure matches existing examples

---

## Notes for Implementation

1. **Parallel visualization:** Print start/end times to show parallel execution
2. **OpenRouter setup:** Include headers for HTTP-Referer and X-Title
3. **Error handling:** Catch failures from individual providers, don't fail entire workflow
4. **Comparison logic:** Simple side-by-side display, no complex analysis needed
5. **Environment check:** Verify API keys at startup, print helpful messages
