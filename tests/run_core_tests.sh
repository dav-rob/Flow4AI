#!/bin/bash
# Core tests - fast smoke tests (~30s)
# Run these to quickly verify the framework is working correctly
#
# Usage: ./tests/run_core_tests.sh
#        or: pytest tests/test_dsl_graph.py tests/test_flowmanager.py tests/test_examples.py -v

set -e

# Change to project root (script is in tests/)
cd "$(dirname "$0")/.."

echo "========================================"
echo "Running Flow4AI Core Tests (~12s)"
echo "========================================"

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run core tests with fast timeout (excludes integration tests with API calls)
python -m pytest \
    tests/test_dsl_graph.py \
    tests/test_flowmanager.py \
    tests/test_examples.py \
    --deselect tests/test_examples.py::test_langchain_simple \
    --deselect tests/test_examples.py::test_langchain_chains \
    --deselect tests/test_examples.py::test_pydantic_structured \
    --deselect tests/test_examples.py::test_model_comparison \
    --deselect tests/test_examples.py::test_llamaindex_rag \
    -v --tb=short -x \
    "$@"

echo ""
echo "✅ Core tests passed!"
echo ""
echo "To run full suite: pytest tests/"
