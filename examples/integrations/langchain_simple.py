"""
LangChain Integration - Simple

Demonstrates using LangChain within Flow4AI workflows:
- Wrap LangChain LLM calls as Flow4AI jobs
- Shows async compatibility between frameworks
- Simple text processing with ChatOpenAI

Prerequisites:
    pip install -e ".[test]"  # Installs langchain-core and langchain-openai
    export OPENAI_API_KEY=your_key_here
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job

# Load environment variables from .env file
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install -e \".[test]\"")


# =============================================================================
# LangChain Jobs - Async functions that wrap LangChain LLM calls
# =============================================================================

async def analyze_sentiment_langchain(text):
    """Use LangChain's ChatOpenAI to analyze sentiment."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=100)
    
    messages = [
        HumanMessage(content=f"Analyze the sentiment of this text and respond with only one word (positive, negative, or neutral): {text}")
    ]
    
    response = await llm.ainvoke(messages)
    
    return {
        "text": text,
        "sentiment": response.content.strip().lower(),
        "model": "gpt-4o-mini"
    }


async def summarize_langchain(text):
    """Use LangChain's ChatOpenAI to create a summary."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=100)
    
    messages = [
        HumanMessage(content=f"Summarize this text in one short sentence: {text}")
    ]
    
    response = await llm.ainvoke(messages)
    
    return {
        "text": text,
        "summary": response.content.strip(),
        "model": "gpt-4o-mini"
    }


# =============================================================================
# Main - Core Flow4AI + LangChain integration
# =============================================================================

def main():
    """Run the LangChain integration example."""
    if not LANGCHAIN_AVAILABLE:
        print("\n❌ LangChain is not installed.")
        print("Install with: pip install -e \".[test]\"\n")
        return False
    
    _print_header()
    
    # Sample text to analyze
    text = """
    Flow4AI is an amazing framework that makes building AI workflows incredibly simple.
    The combination with LangChain opens up powerful possibilities for orchestrating
    complex LLM operations in parallel.
    """
    
    # Wrap LangChain async functions as Flow4AI jobs
    jobs = job({
        "sentiment": analyze_sentiment_langchain,
        "summarize": summarize_langchain
    })
    
    # Create parallel workflow: both jobs run concurrently
    workflow = jobs["sentiment"] | jobs["summarize"]
    
    # Task routes input to each job by name
    task = {
        "sentiment.text": text,
        "summarize.text": text
    }
    
    # Execute the workflow
    errors, results = FlowManager.run(workflow, task, "langchain_analysis", timeout=60)
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    _print_results(results)
    return True


# =============================================================================
# Output Helpers - Terminal display formatting
# =============================================================================

def _print_header():
    """Print example header and description."""
    print("\n" + "="*60)
    print("LangChain Integration - Simple")
    print("="*60 + "\n")
    print("This example demonstrates Flow4AI + LangChain integration:")
    print("- LangChain ChatOpenAI wrapped as Flow4AI jobs")
    print("- Async compatibility between frameworks")
    print("- Parallel LLM calls managed by Flow4AI\n")


def _print_results(results):
    """Print results and observations."""
    sentiment_result = results.get("sentiment", {})
    summary_result = results.get("summarize", {})
    
    print("="*60)
    print("✅ Results:")
    print("="*60)
    print(f"\nSentiment: {sentiment_result.get('sentiment', 'N/A')}")
    print(f"  Model: {sentiment_result.get('model', 'N/A')}")
    print(f"\nSummary: {summary_result.get('summary', 'N/A')}")
    print(f"  Model: {summary_result.get('model', 'N/A')}")
    
    print("\n" + "="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ LangChain functions work seamlessly as Flow4AI jobs")
    print("✓ Both LLM calls executed in parallel (not sequential)")
    print("✓ Flow4AI handles async coordination automatically")
    print("✓ Easy to integrate any LangChain component")
    print("="*60 + "\n")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
