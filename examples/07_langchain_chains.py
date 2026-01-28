"""
Example 7: LangChain Integration - Chains

Demonstrates more complex LangChain integration with Flow4AI:
- Using LangChain chains in parallel workflows
- Multiple LangChain operations coordinated by Flow4AI
- Practical use case: multi-perspective document analysis

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
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install -e \".[test]\"")


async def technical_analysis(document):
    """Analyze document from technical perspective."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical analyst. Analyze the following document from a technical perspective."),
        ("human", "{document}")
    ])
    
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    
    return {
        "perspective": "technical",
        "analysis": result.content
    }


async def business_analysis(document):
    """Analyze document from business perspective."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a business analyst. Analyze the following document from a business perspective focusing on value and ROI."),
        ("human", "{document}")
    ])
    
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    
    return {
        "perspective": "business",
        "analysis": result.content
    }


async def user_experience_analysis(document):
    """Analyze document from UX perspective."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a UX researcher. Analyze the following document from a user experience perspective."),
        ("human", "{document}")
    ])
    
    chain = prompt | llm
    result = await chain.ainvoke({"document": document})
    
    return {
        "perspective": "user_experience",
        "analysis": result.content
    }


async def synthesize_analysis(j_ctx):
    """Synthesize all analyses into a comprehensive summary."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    # Get inputs from previous jobs
    inputs = j_ctx["inputs"]
    technical = inputs.get("technical", {}).get("analysis", "N/A")
    business = inputs.get("business", {}).get("analysis", "N/A")
    ux = inputs.get("user_experience", {}).get("analysis", "N/A")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strategic advisor. Synthesize the following analyses into a cohesive executive summary."),
        ("human", "Technical Analysis:\n{technical}\n\nBusiness Analysis:\n{business}\n\nUX Analysis:\n{ux}")
    ])
    
    chain = prompt | llm
    result = await chain.ainvoke({
        "technical": technical,
        "business": business,
        "ux": ux
    })
    
    return {
        "executive_summary": result.content
    }


def main():
    """Run the LangChain chains example."""
    if not LANGCHAIN_AVAILABLE:
        print("\n❌ LangChain is not installed.")
        print("Install with: pip install -e \".[test]\"\n")
        return False
    
    print("\n" + "="*60)
    print("Example 7: LangChain Integration - Chains")
    print("="*60 + "\n")
    
    print("This example demonstrates:")
    print("- LangChain chains wrapped as Flow4AI jobs")
    print("- Parallel execution of multiple LangChain chains")
    print("- Multi-perspective analysis workflow")
    print("- Result synthesis using j_ctx\n")
    
    # Wrap LangChain chains as Flow4AI jobs
    jobs = wrap({
        "technical": technical_analysis,
        "business": business_analysis,
        "user_experience": user_experience_analysis,
        "synthesize": synthesize_analysis
    })
    
    # Configure jobs to save results
    jobs["technical"].save_result = True
    jobs["business"].save_result = True
    jobs["user_experience"].save_result = True
    
    # Create workflow: parallel analysis >> synthesis
    from flow4ai.dsl import p
    dsl = p(jobs["technical"], jobs["business"], jobs["user_experience"]) >> jobs["synthesize"]
    
    # Sample document
    document = """
    Flow4AI is a powerful Python framework for orchestrating complex AI workflows.
    It enables developers to build parallel processing pipelines with minimal code.
    The framework integrates seamlessly with popular AI libraries like LangChain,
    making it easy to scale LLM operations and manage concurrent API calls efficiently.
    """
    
    print(f"Document to analyze:\n{document[:150]}...\n")
    print("Running multi-perspective analysis in parallel...\n")
    
    # Execute workflow
    task = {
        "technical.document": document,
        "business.document": document,
        "user_experience.document": document
    }
    
    errors, results = FlowManager.run(dsl, task, "multi_perspective_analysis", timeout=60)
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    print("="*60)
    print("✅ Analysis Complete")
    print("="*60 + "\n")
    
    # Display intermediate analyses (from SAVED_RESULTS)
    saved_results = results.get("SAVED_RESULTS", {})
    
    if saved_results:
        print("Individual Perspectives:\n")
        for key, value in saved_results.items():
            if "analysis" in key:
                perspective = value.get("perspective", "unknown")
                analysis = value.get("analysis", "N/A")
                print(f"📊 {perspective.upper()} Perspective:")
                print(f"   {analysis[:100]}...")
                print()
    
    # Display synthesis
    executive_summary = results.get("executive_summary", "N/A")
    print("="*60)
    print("📝 EXECUTIVE SUMMARY:")
    print("="*60)
    print(executive_summary)
    print()
    
    print("="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ Three LangChain chains executed in parallel")
    print("✓ Flow4AI coordinated all LLM operations")
    print("✓ SAVED_RESULTS provided access to intermediate analyses")
    print("✓ Synthesis job used j_ctx to access all perspectives")
    print("✓ Real-world pattern for multi-agent analysis")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
