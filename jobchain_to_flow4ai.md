# jobchain_to_flow4ai Features

This document tracks the implementation status of jobchain_to_flow4ai features

## Implementation Status Legend

- [x] Feature fully implemented and working
- [!] Feature implemented but has issues (see notes)
- [ ] Feature not implemented
- [~] Feature skipped (see explanation)

## jobchain_to_flow4ai Features

### Package and Module Names
- [x] Update `setup.py` to change package name from 'jobchain' to 'flow4ai'
- [x] Rename the main package directory from `src/jobchain` to `src/flow4ai`
- [x] Update the package_data reference in `setup.py` from "jobchain" to "flow4ai"
- [x] Rename the `jc_` prefix in module names to `f4a_` (e.g., `f4a_logging.py` to `f4a_logging.py`)

### Import Statements
- [x] Update all absolute imports (e.g., `import jobchain.f4a_logging as logging` to `import flow4ai.f4a_logging as logging`)
- [x] Update all relative imports (e.g., `from . import f4a_logging as logging` to `from . import f4a_logging as logging`)
- [x] Update JobChain class imports (e.g., `from jobchain.flowmanagerMP import JobChain` to `from flow4ai.flowmanagerMP import JobChain`)

### Class Names
- [x] Rename `JobChain` class to `FlowManagerMP` throughout the codebase
- [x] Update all instantiations of `JobChain` to `FlowManagerMP` 
- [ ] Update documentation references from `JobChain` to `FlowManagerMP`

### Environment Variables and Configuration
- [ ] Rename environment variables from `JOBCHAIN_` prefix to `FLOW4AI_` prefix
- [ ] Update config file names from `jobchain_all.yaml` to `flow4ai_all.yaml`
- [ ] Update config directory search paths from `jobchain` to `flow4ai`

### Documentation
- [ ] Update all documentation files with new naming conventions
- [ ] Update all code examples in documentation to use new class and import names
- [ ] Update file headers and comments to reflect the new project name

### Logging System
- [ ] Rename log file from `flow4ai.log` to `flow4ai.log`
- [x] Update log message prefixes from `JobChain` to `FlowManagerMP`
- [ ] Update log initialization code to use new file names

### Test Files
- [x] Update all test imports to use the new package name
- [ ] Update test paths that include `test_jc_config` to `test_f4a_config`
- [ ] Update all test assertions that reference `JobChain` to `FlowManagerMP`

### Configuration Loading 
- [ ] Update config loading logic to search for `flow4ai` directories instead of `jobchain`
- [ ] Rename config bases from `jobchain_all` to `flow4ai_all`
- [ ] Update error messages related to config loading

### Examples
- [ ] Update all example imports from `jobchain` to `flow4ai`
- [ ] Update example documentation from `JobChain` to `FlowManagerMP`
- [x] Update example instantiations from `flowmanagerMP = JobChain()` to `flow = FlowManagerMP()`
