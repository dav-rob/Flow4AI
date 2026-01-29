# Flow4AI Integration Examples - Next Steps

## Overview

This document summarizes research on potential integration examples for Flow4AI and outlines the implementation plan.

## Approved Implementation Order

1. **pydantic_structured.py** - Structured output extraction with Pydantic/Instructor
2. **model_comparison.py** - Multi-model parallel queries and comparison
3. **llamaindex_rag.py** - Simple RAG pipeline with LlamaIndex

## Key Design Principles

1. **Succinctness** - Each example ~100-150 lines, clear and focused
2. **Self-Contained** - Sample data embedded in code, no external files
3. **Flow4AI Semantics** - Demonstrate correct use of `job()`, `p()`, `>>`, `j_ctx`, `save_result`
4. **Fast Tests** - Use `max_tokens` where possible; skip slow tests (>10s) in core tests
5. **Production Patterns** - Show real-world applicable patterns

## Test Strategy

- Examples < 10s: Include in `run_core_tests.sh`
- Examples > 10s: Skip in core tests, run only in full suite
- Flag slow examples for potential optimization review

## PRD Documents

See individual PRD files in this folder:
- `prd_pydantic_structured.md`
- `prd_model_comparison.md`
- `prd_llamaindex_rag.md`

## Research Reference

Full research is available in the artifacts directory:
`/Users/davidroberts/.gemini/antigravity/brain/e88f14a8-8255-4db4-bdb7-8b6fb32baee0/integration_examples_research.md`
