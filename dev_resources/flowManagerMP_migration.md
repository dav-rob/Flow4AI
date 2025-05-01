# FlowManagerMP to FlowManager Migration Guide

This document tracks the migration status for tests that use FlowManagerMP to use FlowManager instead.

## Migration Status Legend

- [x] Test migrated to use FlowManager
- [!] Test partially migrated or has migration issues (see notes)
- [ ] Test not yet migrated
- [~] Test will not be migrated (see explanation)

## Tests to Migrate

The following tests use FlowManagerMP but don't have file names starting with "test_fmmp". These tests should be migrated to use FlowManager.

### test_aa.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_imports_are_working - Creates a FlowManagerMP instance to test imports

### test_concurrency.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_concurrency_by_expected_returns - Uses FlowManagerMP to test concurrency with result collection

### test_error_conditions.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_basic_error_handling - Tests error handling with FlowManagerMP (serial_processing=True)
  - [ ] test_timeout_handling - Tests timeout scenarios with FlowManagerMP (serial_processing=True)
  - [ ] test_process_termination - Tests process termination handling (not shown in code view)
  - [ ] test_invalid_input - Tests invalid input handling (not shown in code view)
  - [ ] test_resource_cleanup - Tests resource cleanup (not shown in code view)
  - [ ] test_error_in_result_processing - Tests result processing errors (not shown in code view)
  - [ ] test_memory_error_handling - Tests memory error handling (not shown in code view)
  - [ ] test_unpicklable_result - Tests unpicklable result scenarios (not shown in code view)

### test_job_graph.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_parallel_execution_multiple_jobs - Tests parallel execution with FlowManagerMP (serial_processing=True)
  - [ ] Other tests that may use FlowManagerMP (not shown in code view)

### test_job_loading.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - Tests to move to test_fmmp_parallel_execution.py:
    - [ ] test_head_jobs_in_flowmanagerMP_parallel - Uses FlowManagerMP with parallel processing (default)
  - Tests to migrate to use FlowManager (all use serial_processing=True):
    - [ ] test_head_jobs_in_flowmanagerMP_serial - Tests head jobs with serial processing
    - [ ] test_pydantic_jobs_in_flowmanagerMP_serial - Tests pydantic models with serial processing
    - [ ] test_multiple_head_jobs_in_flowmanagerMP_serial - Tests multiple head jobs with serial processing
    - [ ] test_multiple_tail_jobs_in_flowmanagerMP_serial - Tests multiple tail jobs with serial processing
    - [ ] test_simple_parallel_jobs_in_flowmanagerMP_serial - Tests parallel job graph structure (but uses serial_processing=True)
    - [ ] test_save_result - Tests saving results with serial processing

### test_logging_config.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_debug_logging_in_flowmanagerMP - Tests debug logging with FlowManagerMP

### test_task_passthrough.py
- [ ] Migrate test file to use FlowManager instead of FlowManagerMP
  - [ ] test_task_passthrough - Tests task parameter passthrough with FlowManagerMP

## Migration Steps

For each test file, the following steps should be taken:

1. Create a backup of the original test file if needed
2. Update imports to use FlowManager instead of FlowManagerMP
   ```python
   # From
   from flow4ai.flowmanagerMP import FlowManagerMP
   # To
   from flow4ai.flowmanager import FlowManager
   ```
3. Update test code to use FlowManager API
   - Update instantiations and method calls according to the FlowManager API
   - Update any test assertions to match FlowManager's behavior and outputs
4. Run the migrated tests to ensure they pass
5. Mark the test as migrated in this document

## API Differences

Key differences between FlowManagerMP and FlowManager:

- [Add key API differences here after analyzing both classes]
- [Note any initialization parameter differences]
- [Note any method signature changes]
- [Note any behavior changes that will affect tests]

## Migration Progress Tracking

Total tests to migrate: 7
Completed migrations: 0
Tests in progress: 0
Tests not to be migrated: 0
