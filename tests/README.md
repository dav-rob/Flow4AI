# Test Suite Documentation

## Running Tests

### Running All Tests
To run all tests:
```bash
python3 -m pytest
```
Note: By default, performance-intensive tests (like those in `test_parallel_load.py`) will be skipped to ensure quick test execution during normal development.

### Running All Tests Including Performance Tests
To run all tests including performance tests:
```bash
python3 -m pytest --full-suite
```
This will execute all tests, including the normally skipped performance and parallel load tests.

### Running Specific Tests
When running specific test files or individual tests that are normally skipped (like parallel load tests), you must include the `--full-suite` flag:

```bash
# Running a specific test file with skipped tests
python3 -m pytest tests/test_parallel_load.py -v --full-suite

# Running a specific test function
python3 -m pytest tests/test_parallel_load.py::test_maximum_parallel_file_trace -v --full-suite
```

The `--full-suite` flag is only required when running tests that are normally skipped. Regular tests can be run individually without this flag:

```bash
# Running a regular test file
python3 -m pytest tests/test_job_loader.py -v

# Running a specific regular test
python3 -m pytest tests/test_job_loader.py::test_load_job -v
```

## Test Categories

### Regular Tests
These tests run by default and are designed to be quick and focused on core functionality:
- test_async_functionality.py
- test_error_conditions.py
- test_job_loader.py
- test_job_tracing.py
- test_logging.py
- test_opentelemetry.py
- test_parallel_execution.py
- test_queue_stress.py
- test_result_processing.py

### Performance Tests (Requires --full-suite)
These tests are skipped by default as they are time and resource-intensive:
- test_parallel_load.py

These tests are valuable for verifying system performance and stability but are separated to maintain fast test execution during normal development.

To add more files to the skipped tests list, update the following section in `conftest.py`:
```python
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--full-suite"):
        # Skip load tests by default
        for item in items:
            if "test_parallel_load.py" in str(item.fspath):
                item.add_marker(pytest.mark.skip(reason="Load test - use --full-suite to include"))
```
Additional test files can be added to the skip condition using the same pattern.
