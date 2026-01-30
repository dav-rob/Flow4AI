# PRD: FlowManagerMP Multi-Process Scaling

## Problem Statement

FlowManager is limited by Python's GIL - all async operations run on a single thread. FlowManagerMP uses multiprocessing to bypass this, achieving ~10x higher concurrency. However, it currently doesn't maximize hardware utilization.

**Goal:** Enable FlowManagerMP to spawn one process per CPU core for maximum parallelism.

## Background

| Component | Concurrency Model | Practical Limit |
|-----------|-------------------|-----------------|
| FlowManager | AsyncIO (single thread) | ~1000 tasks |
| FlowManagerMP | Multiprocessing | ~10,000 tasks |
| FlowManagerMP + Multi-core | One process per core | TBD (target: 100k+) |

## Proposed Solution

### Approach: Worker Pool per Core

```python
# Current FlowManagerMP (single process pool)
fm = FlowManagerMP()

# Proposed (multi-core)
fm = FlowManagerMP(
    workers_per_core=1,  # One worker process per CPU core
    cores=None,          # Auto-detect (os.cpu_count())
)
```

### Architecture

```
Main Process
    │
    ├── Core 0: FlowManagerMP Worker
    │       └── AsyncIO event loop (handles 1000 concurrent tasks)
    │
    ├── Core 1: FlowManagerMP Worker  
    │       └── AsyncIO event loop (handles 1000 concurrent tasks)
    │
    ├── Core 2: FlowManagerMP Worker
    │       └── AsyncIO event loop (handles 1000 concurrent tasks)
    │
    └── ... (N cores)
```

On an M4 Mac with 10 cores → potential for 10,000+ true parallel tasks.

## Prerequisites

1. **Complete PRD 1 (Throttled Submission)** - need monitoring before scaling
2. **Larger corpus** - need more than 3000 chunks to test at scale
3. **FlowManagerMP understanding** - review existing implementation

## Investigation Tasks

1. [ ] Review current FlowManagerMP implementation
2. [ ] Understand job distribution mechanism
3. [ ] Test current FlowManagerMP limits on M4 Mac
4. [ ] Research multiprocessing.Pool vs concurrent.futures.ProcessPoolExecutor

## Implementation Plan

### Phase 1: Benchmark Current FlowManagerMP

#### File: `examples/integrations/parallel_rag/rag_pipeline_mp.py` (NEW)
- Copy of rag_pipeline.py using FlowManagerMP
- Add benchmarking for 1000, 5000, 10000 chunks

#### File: `examples/integrations/parallel_rag/utils/download.py`
- Add more books to corpus (target: 10,000+ chunks)
- Possible sources: Project Gutenberg, Wikipedia dumps

### Phase 2: Multi-Core Implementation

#### File: `src/flow4ai/flowmanagermp.py`
- Add `cores` parameter
- Implement worker-per-core spawning
- Add load balancing across workers

### Phase 3: Documentation

#### File: `examples/integrations/parallel_rag/README.md`
- Document FlowManager vs FlowManagerMP differences
- Performance comparison tables
- When to use each

## Success Criteria

- [ ] FlowManagerMP handles 10,000+ tasks on M4 Mac
- [ ] Near-linear scaling with core count
- [ ] Clear documentation on when to use FlowManager vs FlowManagerMP

## Risks

1. **Serialization overhead** - passing tasks between processes has cost
2. **Memory usage** - each process has separate memory space
3. **Complexity** - debugging multi-process issues is harder

## Open Questions

1. What's the current FlowManagerMP architecture?
2. How does it handle job distribution?
3. What's the memory footprint per worker?
