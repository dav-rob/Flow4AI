import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--full-suite",
        action="store_true",
        default=False,
        help="run full test suite including load tests"
    )

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--full-suite"):
        # Skip load tests by default
        for item in items:
            if "test_parallel_load.py" in str(item.fspath):
                item.add_marker(pytest.mark.skip(reason="Load test - use --full-suite to include"))
