# Flow4AI Development Guide

## Commands
- Test suite ( ~2.5 mins): `python -m pytest`
- **Core tests (~11s)**: `./run_core_tests.sh` - use for quick smoke testing during refactoring
- Single test: `python -m pytest tests/path_to_test.py::test_name -v`
- Full test suite: `python -m pytest --full-suite` (includes performance tests)
- Debug logs: `python -m pytest -s` or `FLOW4AI_LOG_LEVEL=DEBUG python -m pytest -v -s`
- Type checking: `mypy src/flow4ai`

## ⚠️ CRITICAL: No Complex sed Scripts
**DO NOT create "god-like" sed one-liners for bulk code changes.** They break silently and waste hours debugging. Instead:
1. Use proper file editing tools (replace_file_content, multi_replace_file_content)
2. Update files **one by one**
3. Run `./run_core_tests.sh` after each batch of changes
4. If you can't explain the sed command in one sentence, don't use it

## Code Style
- **Naming**: Classes=CamelCase, Methods/functions/variables=snake_case, Constants=UPPERCASE
- **Imports**: Standard lib → Third-party → Local (relative imports), grouped alphabetically
- **Type hints**: Required for all functions/methods, variables and return types
- **Docstrings**: Google-style with Args sections
- **Error handling**: Specific exceptions with detailed messages
- **Logging**: Use `flow4ai.f4a_logging` module, not standard logging

## JobABC Rules
- NEVER override `_execute` method, only implement `run` method
- The `run` method must accept a task parameter and return a dictionary
- Use properties to access configuration parameters
- Always call super().__init__ with name and properties parameters

## Framework Documentation
Always read README.md and before any serious work, it contains the usability core of the framework, how it is meant to feel to use to developers, /examples folder contains many examples of how to use the framework.  Read docs/ARCHITECTURE.md for architectural overview about how the code internals are put together.