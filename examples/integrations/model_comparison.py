"""
Model Comparison - Multi-Model Parallel Queries

Demonstrates querying multiple LLM providers simultaneously and comparing
their responses, showcasing Flow4AI's parallel execution strength:
- Query OpenAI, Claude, and Gemini in parallel
- Use j_ctx to aggregate and compare responses
- Graceful degradation if some API keys are missing

Prerequisites:
    pip install -e ".[test]"
    export OPENAI_API_KEY=your_key_here
    export OPENROUTER_API_KEY=your_key_here  # Optional, for Claude/Gemini
"""

import asyncio
import os
import time
from dotenv import load_dotenv

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p

# Load environment variables from .env file
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install -e \".[test]\"")

# Check which API keys are available
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


# =============================================================================
# Sample Prompt - Embedded query
# =============================================================================

PROMPT = "Explain quantum computing in one sentence for a 10-year-old."


# =============================================================================
# Model Query Jobs - Async functions that query different providers
# =============================================================================

async def query_openai(prompt: str) -> dict:
    """Query OpenAI GPT-4o-mini."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    start = time.time()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=100)
    
    messages = [HumanMessage(content=prompt)]
    response = await llm.ainvoke(messages)
    
    return {
        "model": "gpt-4o-mini",
        "provider": "OpenAI",
        "response": response.content.strip(),
        "time_ms": int((time.time() - start) * 1000)
    }


async def query_claude(prompt: str) -> dict:
    """Query Claude via OpenRouter."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    if not OPENROUTER_KEY:
        return {"error": "OPENROUTER_API_KEY not set", "skipped": True}
    
    start = time.time()
    llm = ChatOpenAI(
        model="anthropic/claude-3-haiku-20240307",
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_KEY,
        max_tokens=100,
        default_headers={
            "HTTP-Referer": "https://github.com/flow4ai",
            "X-Title": "Flow4AI Model Comparison"
        }
    )
    
    messages = [HumanMessage(content=prompt)]
    response = await llm.ainvoke(messages)
    
    return {
        "model": "claude-3-haiku",
        "provider": "Anthropic (via OpenRouter)",
        "response": response.content.strip(),
        "time_ms": int((time.time() - start) * 1000)
    }


async def query_gemini(prompt: str) -> dict:
    """Query Gemini via OpenRouter."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    if not OPENROUTER_KEY:
        return {"error": "OPENROUTER_API_KEY not set", "skipped": True}
    
    start = time.time()
    llm = ChatOpenAI(
        model="google/gemini-2.0-flash-lite-001",
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_KEY,
        max_tokens=100,
        default_headers={
            "HTTP-Referer": "https://github.com/flow4ai",
            "X-Title": "Flow4AI Model Comparison"
        }
    )
    
    messages = [HumanMessage(content=prompt)]
    response = await llm.ainvoke(messages)
    
    return {
        "model": "gemini-2.0-flash-lite",
        "provider": "Google (via OpenRouter)",
        "response": response.content.strip(),
        "time_ms": int((time.time() - start) * 1000)
    }


async def compare_responses(j_ctx) -> dict:
    """Aggregate and compare all model responses.
    
    Uses j_ctx["inputs"] to access outputs from all parallel jobs.
    """
    inputs = j_ctx["inputs"]
    
    responses = []
    for key in ["openai", "claude", "gemini"]:
        result = inputs.get(key, {})
        if result.get("skipped"):
            continue
        if "response" in result:
            responses.append(result)
    
    # Calculate stats
    total_time = sum(r.get("time_ms", 0) for r in responses)
    avg_time = total_time // len(responses) if responses else 0
    
    return {
        "responses": responses,
        "model_count": len(responses),
        "avg_time_ms": avg_time,
        "prompt": PROMPT
    }


# =============================================================================
# Main - Core Flow4AI + Multi-Model integration
# =============================================================================

def main():
    """Run the model comparison example."""
    if not LANGCHAIN_AVAILABLE:
        print("\n❌ LangChain is not installed.")
        print("Install with: pip install -e \".[test]\"\n")
        return False
    
    _print_header()
    
    # Create query jobs for each provider
    jobs = job({
        "openai": query_openai,
        "claude": query_claude,
        "gemini": query_gemini,
        "compare": compare_responses,
    })
    
    # Pattern: parallel queries >> comparison
    # All providers queried concurrently, then compare aggregates results
    workflow = p(jobs["openai"], jobs["claude"], jobs["gemini"]) >> jobs["compare"]
    
    # Same prompt routed to all jobs
    task = {
        "openai.prompt": PROMPT,
        "claude.prompt": PROMPT,
        "gemini.prompt": PROMPT,
    }
    
    # Execute the workflow
    start_time = time.time()
    errors, results = FlowManager.run(workflow, task, "model_comparison", timeout=30)
    total_time = time.time() - start_time
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    _print_results(results, total_time)
    return True


# =============================================================================
# Output Helpers - Terminal display formatting
# =============================================================================

def _print_header():
    """Print example header and description."""
    print("\n" + "="*60)
    print("Model Comparison - Parallel Multi-Model Queries")
    print("="*60 + "\n")
    print("This example demonstrates:")
    print("- Querying multiple LLM providers in parallel")
    print("- OpenAI direct + Claude/Gemini via OpenRouter")
    print("- Aggregating and comparing responses\n")
    
    if not OPENROUTER_KEY:
        print("⚠️  OPENROUTER_API_KEY not set - only OpenAI will be queried")
        print("   Set this key to compare Claude and Gemini responses\n")


def _print_results(results, total_time):
    """Print model responses and comparison."""
    print("="*60)
    print("✅ Comparison Complete")
    print("="*60 + "\n")
    
    print(f"Prompt: \"{results.get('prompt', '')}\"")
    print(f"Models queried: {results.get('model_count', 0)}")
    print(f"Total wall time: {total_time:.2f}s (parallel execution)\n")
    
    print("-"*60)
    
    for resp in results.get("responses", []):
        print(f"\n🤖 {resp.get('model', 'Unknown')} ({resp.get('provider', '')})")
        print(f"   Time: {resp.get('time_ms', 0)}ms")
        print(f"   Response: {resp.get('response', 'N/A')}")
    
    print("\n" + "="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ All model queries ran in parallel")
    print(f"✓ Wall time ({total_time:.2f}s) ≈ slowest single call, not sum")
    print("✓ Compare job aggregated results via j_ctx['inputs']")
    print("✓ Graceful degradation when API keys missing")
    print("="*60 + "\n")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
