# Load Management - Next Steps

This directory contains PRDs for scaling Flow4AI beyond single-batch parallelism.

## Background

When running the parallel_rag example with 3033 chunks, FlowManager hangs - tasks are submitted but none complete. With 100-1000 chunks, it works perfectly (~4.6s for 1000 embeddings).

**Root cause:** FlowManager has a practical limit on concurrent tasks due to:
- Python's GIL (single-threaded execution)
- AsyncIO event loop capacity
- External API rate limits (OpenAI)

## Observed Limits

| Manager | Hardware | Approximate Limit |
|---------|----------|-------------------|
| FlowManager | Intel Mac | ~1000 concurrent |
| FlowManagerMP | Intel Mac | ~10,000 concurrent |
| FlowManager | M4 Mac | TBD (higher) |
| FlowManagerMP | M4 Mac | TBD (higher) |

## PRDs (Sequentially)

### 1. [Throttled Submission Pattern](prd_throttled_submission.md) ✅
Monitor load and submit jobs incrementally to stay within limits.
**Status:** IMPLEMENTED - 3033 chunks in 12.39s (245/sec)

### 2. [FlowManagerMP Multi-Process Scaling](prd_flowmanagermp_scaling.md)
Extend FlowManagerMP to spawn processes per CPU core for maximum parallelism.
**Status:** Not started

## Progress Log

| Date | Activity |
|------|----------|
| 2026-01-30 | Discovered 3000+ chunk hanging issue |
| 2026-01-30 | Created load-management branch |
| 2026-01-30 | Created PRDs |
| 2026-01-30 | **Implemented throttled submission - 3033 chunks in 12.39s!** |
