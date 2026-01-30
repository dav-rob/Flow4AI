# PRD: Throttled Submission Pattern

**STATUS: IMPLEMENTED ✅**

## Results

| Chunks | Mode | Time | Rate | Status |
|--------|------|------|------|--------|
| 3033 | Parallel (all at once) | ∞ (hangs) | 0 | ❌ Fails |
| 3033 | **Throttled** | **12.39s** | **245/sec** | ✅ Works |

## Problem Statement

When submitting 3000+ tasks simultaneously to FlowManager, the system hangs - tasks are submitted but none complete. This is because FlowManager has a practical limit on concurrent tasks.

**Observed behavior:**
```
Submitted: 3033, Completed: 0, Post-processing: 0
```
(repeats indefinitely)

**Goal:** Enable processing of arbitrarily large task sets by throttling submission rate.

## Proposed Solution

### Approach: Monitor-and-Submit Loop

Instead of submitting all tasks upfront, monitor completion rate and submit in batches:

```python
# Current (hangs at scale)
for chunk in chunks:
    fm.submit_task(task, fq_name)
fm.wait_for_completion()

# Proposed (throttled)
batch_size = 250
submitted = 0
while submitted < len(chunks):
    # Submit a batch
    batch = chunks[submitted:submitted + batch_size]
    for chunk in batch:
        fm.submit_task(task, fq_name)
    submitted += len(batch)
    
    # Wait for some completions before submitting more
    while fm.get_pending_count() > batch_size:
        time.sleep(0.1)

fm.wait_for_completion()
```

### Key FlowManager APIs Needed

1. **Get pending task count** (may already exist):
   ```python
   fm.get_pending_count()  # Returns: submitted - completed
   ```

2. **Get completion stats without blocking**:
   ```python
   stats = fm.get_stats()
   # Returns: {"submitted": N, "completed": M, "errors": E}
   ```

## Investigation Tasks

1. [ ] Review FlowManager API for existing stats methods
2. [ ] Check if `pop_results()` can be used non-destructively
3. [ ] Test optimal batch_size for different scenarios

## Implementation Plan

### File Changes

#### 1. `src/flow4ai/flowmanager.py` (if needed)
- Add `get_stats()` or `get_pending_count()` method if not present

#### 2. `examples/integrations/parallel_rag/rag_pipeline.py`
- Add `run_indexing_pipeline_throttled()` function
- Implement monitor-and-submit loop

#### 3. `examples/integrations/parallel_rag/README.md`
- Document throttled pattern
- Add performance comparison

## Success Criteria

- [ ] 3000+ chunks complete successfully
- [ ] Performance within 2x of small-batch runs
- [ ] Clear documentation of pattern

## Open Questions

1. What's the optimal batch size? (250? 500?)
2. Should we expose throttle settings as CLI args?
3. Can we auto-detect the optimal batch size?
