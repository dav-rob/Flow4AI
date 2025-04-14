# jobchain_to_flow4ai Migration Plan

This document tracks the phased implementation of the jobchain_to_flow4ai migration.

## Implementation Status Legend

- [x] Feature fully implemented and working
- [!] Feature implemented but has issues (see notes)
- [ ] Feature not implemented
- [~] Feature skipped (see explanation)

## Migration Strategy

To make this migration manageable and minimize test breakage, we'll implement the changes in phases. Each phase builds on the previous one while maintaining test integrity where possible.

### Phase 1: Core Configuration & Setup Files
- [ ] Update `setup.py` with dual package support (both 'jobchain' and 'flow4ai')
- [ ] Create a compatibility layer in `src/__init__.py` that allows both import styles
- [ ] Create the `src/flow4ai` directory structure parallel to `src/jobchain`
- [ ] Copy core module files to the new structure (keeping both versions for now)
- [ ] Update documentation files to reflect the new name
- [ ] Add tests to verify dual-package compatibility

### Phase 2: Module File Duplication with Compatibility
- [ ] Rename the `jc_` prefix to `f4a_` in the new structure (e.g., `jc_logging.py` → `f4a_logging.py`)
- [ ] Update the package_data reference in `setup.py` to include both "jobchain" and "flow4ai"
- [ ] Create compatibility imports in the old structure to forward to the new structure
- [ ] Add deprecation warnings when using old imports
- [ ] Update the logging system to support both `jobchain.log` and `flow4ai.log`

### Phase 3: Class Names and Update Examples
- [ ] Create `Flow4AI` class that extends from `JobChain` for compatibility
- [ ] Update examples to use the new imports and class names
- [ ] Create a subset of tests that use the new imports
- [ ] Update environment variables to support both `JOBCHAIN_` and `FLOW4AI_` prefixes

### Phase 4: Gradual Test Migration
- [ ] Migrate tests in small batches (25% at a time)
- [ ] For each batch, update imports and class references
- [ ] Update configuration loading to support both `jobchain` and `flow4ai` directories
- [ ] Update test paths from `test_jc_config` to `test_f4a_config` while maintaining both

### Phase 5: Complete Migration and Cleanup
- [ ] Remove compatibility layers and transition fully to new names
- [ ] Update all remaining documentation
- [ ] Remove old directory structure and deprecated code
- [ ] Clean up dual configuration support

## Detailed Changes Required

### Package and Module Names
- [ ] Update `setup.py` to change package name from 'jobchain' to 'flow4ai'
- [ ] Rename the main package directory from `src/jobchain` to `src/flow4ai`
- [ ] Update the package_data reference in `setup.py` from "jobchain" to "flow4ai"
- [ ] Rename the `jc_` prefix in module names to `f4a_` (e.g., `jc_logging.py` to `f4a_logging.py`)

### Import Statements
- [ ] Update all absolute imports (e.g., `import jobchain.jc_logging as logging` to `import flow4ai.f4a_logging as logging`)
- [ ] Update all relative imports (e.g., `from . import jc_logging as logging` to `from . import f4a_logging as logging`)
- [ ] Update JobChain class imports (e.g., `from jobchain.job_chain import JobChain` to `from flow4ai.job_chain import JobChain`)

### Class Names
- [ ] Rename `JobChain` class to `Flow4AI` throughout the codebase
- [ ] Update all instantiations of `JobChain` to `Flow4AI` 
- [ ] Update documentation references from `JobChain` to `Flow4AI`

### Environment Variables and Configuration
- [ ] Rename environment variables from `JOBCHAIN_` prefix to `FLOW4AI_` prefix
- [ ] Update config file names from `jobchain_all.yaml` to `flow4ai_all.yaml`
- [ ] Update config directory search paths from `jobchain` to `flow4ai`

### Documentation
- [ ] Update all documentation files with new naming conventions
- [ ] Update all code examples in documentation to use new class and import names
- [ ] Update file headers and comments to reflect the new project name

### Logging System
- [ ] Rename log file from `jobchain.log` to `flow4ai.log`
- [ ] Update log message prefixes from `JobChain` to `Flow4AI`
- [ ] Update log initialization code to use new file names

### Test Files
- [ ] Update all test imports to use the new package name
- [ ] Update test paths that include `test_jc_config` to `test_f4a_config`
- [ ] Update all test assertions that reference `JobChain` to `Flow4AI`

### Configuration Loading
- [ ] Update config loading logic to search for `flow4ai` directories instead of `jobchain`
- [ ] Rename config bases from `jobchain_all` to `flow4ai_all`
- [ ] Update error messages related to config loading

### Examples
- [ ] Update all example imports from `jobchain` to `flow4ai`
- [ ] Update example documentation from `JobChain` to `Flow4AI`
- [ ] Update example instantiations from `job_chain = JobChain()` to `flow = Flow4AI()`
