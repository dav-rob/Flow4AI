import pytest

from flow4ai.flowmanager_base import FlowManagerABC
from flow4ai.utils.otel_wrapper import TracerFactory

# set the TracerFactory up with the TestTracerProvider so the TracerProvider
#  can be overridden by code which normally isn't possible.
TracerFactory.set_test_mode(True)
FlowManagerABC.RAISE_ON_ERROR = True


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "isolated: marks tests to run in isolation"
    )

def pytest_addoption(parser):
    parser.addoption(
        "--full-suite",
        action="store_true",
        default=False,
        help="run full test suite including load tests"
    )
    parser.addoption(
        "--isolated",
        action="store_true",
        default=False,
        help="run only tests marked as isolated"
    )

def pytest_collection_modifyitems(config, items):
    # Handle isolated tests
    # if config.getoption("--isolated"):
    #     selected = []
    #     deselected = []
    #     for item in items:
    #         if item.get_closest_marker("isolated"):
    #             selected.append(item)
    #         else:
    #             deselected.append(item)
    #     config.hook.pytest_deselected(items=deselected)
    #     items[:] = selected
    #     return
    # else:
    #     # Skip isolated tests when not running with --isolated
    #     for item in items:
    #         if item.get_closest_marker("isolated"):
    #             item.add_marker(pytest.mark.skip(reason="Isolated test - use --isolated to run"))

    # Handle full suite option
    if not config.getoption("--full-suite"):
        # Skip load tests by default
        for item in items:
            if "test_fmmp_parallel_load.py" in str(item.fspath) or item.function.__name__ == "test_parallel_load":
                item.add_marker(pytest.mark.skip(reason="Load test - use --full-suite to include"))
