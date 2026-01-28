"""
Example 6: LangChain Integration - Simple

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
from flow4ai.dsl import wrap

# Load environment variables from .env file
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install -e \".[test]\"")


async def analyze_sentiment_langchain(text):
    """Use LangChain's ChatOpenAI to analyze sentiment."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    # Create LangChain LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create prompt
    messages = [
        HumanMessage(content=f"Analyze the sentiment of this text and respond with only one word (positive, negative, or neutral): {text}")
    ]
    
    # Invoke LLM
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
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    messages = [
        HumanMessage(content=f"Summarize this text in one short sentence: {text}")
    ]
    
    response = await llm.ainvoke(messages)
    
    return {
        "text": text,
        "summary": response.content.strip(),
        "model": "gpt-4o-mini"
    }


def main():
    """Run the LangChain integration example."""
    if not LANGCHAIN_AVAILABLE:
        print("\n❌ LangChain is not installed.")
        print("Install with: pip install -e \".[test]\"\n")
        return False
    
    print("\n" + "="*60)
    print("Example 6: LangChain Integration - Simple")
    print("="*60 + "\n")
    
    print("This example demonstrates Flow4AI + LangChain integration:")
    print("- LangChain ChatOpenAI wrapped as Flow4AI jobs")
    print("- Async compatibility between frameworks")
    print("- Parallel LLM calls managed by Flow4AI\n")
    
    # Wrap LangChain functions as Flow4AI jobs
    jobs = wrap({
        "sentiment": analyze_sentiment_langchain,
        "summarize": summarize_langchain
    })
    
    # Create parallel workflow: analyze sentiment AND summarize
    dsl = jobs["sentiment"] | jobs["summarize"]
    
    # Sample text
    text = """
    Flow4AI is an amazing framework that makes building AI workflows incredibly simple.
    The combination with LangChain opens up powerful possibilities for orchestrating
    complex LLM operations in parallel.
    """
    
    print(f"Text to analyze:\n{text[:100]}...\n")
    print("Running parallel LangChain operations...\n")
    
    # Execute workflow
    task = {
        "sentiment.text": text,
        "summarize.text": text
    }
    
    errors, results = FlowManager.run(dsl, task, "langchain_analysis")
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    # Extract results
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
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
