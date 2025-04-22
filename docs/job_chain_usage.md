# FlowManagerMP Usage Guidelines

## Single FlowManagerMP Instance

FlowManagerMP is designed to be highly efficient and scalable with a single instance. Key points:

- Use only ONE FlowManagerMP instance per process/container
- Each FlowManagerMP can handle 10,000+ simultaneous jobs efficiently
- Typically run one FlowManagerMP instance per container/instance with 3 CPUs
- Multiple FlowManagerMPs are NOT needed for parallel processing - the single instance handles this automatically

## Anti-Pattern

```python
# DON'T do this:
flowmanagerMP1 = FlowManagerMP()
flowmanagerMP2 = FlowManagerMP()  # Wrong! Don't create multiple chains
```

## Correct Usage

```python
# DO this:
flowmanagerMP = FlowManagerMP()  # Single instance handles all parallel processing
```

The FlowManagerMP implementation is optimized for parallel execution within a single instance, making multiple instances unnecessary and potentially counterproductive.
