#!/bin/bash
# Run all integration examples (requires API keys)
# This runs all integration examples that make actual API calls
#
# Usage: ./tests/run_all_examples.sh
#
# Prerequisites:
#   export OPENAI_API_KEY=your_key_here
#   export OPENROUTER_API_KEY=your_key_here  # Optional, for model_comparison
#   pip install -e ".[test,llamaindex]"

set -e

echo "========================================"
echo "Running All Flow4AI Integration Examples"
echo "========================================"

# Change to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo ""
echo "--- LangChain Simple ---"
python examples/integrations/langchain_simple.py

echo ""
echo "--- LangChain Chains ---"
python examples/integrations/langchain_chains.py

echo ""
echo "--- Pydantic Structured ---"
python examples/integrations/pydantic_structured.py

echo ""
echo "--- Model Comparison ---"
python examples/integrations/model_comparison.py

echo ""
echo "--- LlamaIndex RAG ---"
python examples/integrations/llamaindex_rag.py

echo ""
echo "========================================"
echo "✅ All integration examples completed!"
echo "========================================"
