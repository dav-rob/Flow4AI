# Flow4AI Development Guide

## Commands
- Test: `python -m pytest`
- Single test: `python -m pytest tests/path_to_test.py::test_name -v`
- Full test suite: `python -m pytest --full-suite` (includes performance tests)
- Debug logs: `python -m pytest -s` or `FLOW4AI_LOG_LEVEL=DEBUG python -m pytest -v -s`
- Type checking: `mypy src/flow4ai`

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

## Architecture
Always read docs/ARCHITECTURE.md before anything other than simple command execution.