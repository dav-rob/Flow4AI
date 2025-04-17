# JobChain Usage Guidelines

## Single JobChain Instance

JobChain is designed to be highly efficient and scalable with a single instance. Key points:

- Use only ONE JobChain instance per process/container
- Each JobChain can handle 10,000+ simultaneous jobs efficiently
- Typically run one JobChain instance per container/instance with 3 CPUs
- Multiple JobChains are NOT needed for parallel processing - the single instance handles this automatically

## Anti-Pattern

```python
# DON'T do this:
chain1 = JobChain(job1, processor)
chain2 = JobChain(job2, processor)  # Wrong! Don't create multiple chains
```

## Correct Usage

```python
# DO this:
flowmanagerMP = JobChain(job, processor)  # Single instance handles all parallel processing
```

The JobChain implementation is optimized for parallel execution within a single instance, making multiple instances unnecessary and potentially counterproductive.
