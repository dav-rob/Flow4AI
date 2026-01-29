#!/bin/bash
# Core tests - fast smoke tests (~30s)
# Run these to quickly verify the framework is working correctly
#
# Usage: ./run_core_tests.sh
#        or: pytest tests/test_dsl_graph.py tests/test_flowmanager.py tests/test_examples.py -v

set -e

echo "========================================"
echo "Running Flow4AI Core Tests (~30s)"
echo "========================================"

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run core tests with fast timeout (excludes LangChain integration tests)
python -m pytest \
    tests/test_dsl_graph.py \
    tests/test_flowmanager.py \
    tests/test_examples.py \
    --deselect tests/test_examples.py::test_langchain_simple \
    --deselect tests/test_examples.py::test_langchain_chains \
    -v --tb=short -x \
    "$@"

echo ""
echo "✅ Core tests passed!"
echo ""
echo "To run full suite: pytest tests/"
