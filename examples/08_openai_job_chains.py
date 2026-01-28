"""
Example 8: Pure OpenAIJob Chains (Performance Comparison)

This is a functional replica of Example 7 (LangChain Chains), but using
Flow4AI's native OpenAIJob. It is used to benchmark performance and demonstrate
that Flow4AI's native jobs are efficient.

Prerequisites:
    export OPENAI_API_KEY=your_key_here
"""

import asyncio
import time
import os
from dotenv import load_dotenv
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import parallel
from flow4ai.jobs import OpenAIJob

# Load environment variables
load_dotenv()

# Define specialized jobs equivalent to the LangChain chains

class TechnicalAnalysisJob(OpenAIJob):
    """Analyze document from technical perspective."""
    
    async def run(self, task):
        import time
        start = time.time()
        
        if "technical" in task:
            document = task.get("technical", {}).get("document")
        else:
             # Fallback if task is flattened or different
             document = task.get("document")
        
        # Construct messages with system prompt defined in the job
        messages = [
            {"role": "system", "content": "You are a technical analyst. Analyze the following document from a technical perspective."},
            {"role": "user", "content": document}
        ]
        
        # Prepare task for parent OpenAIJob
        # We enforce model and temp to match Example 07 exactly
        api_task = {
            "messages": messages,
            "model": "gpt-4o-mini",
            "temperature": 0
        }
        
        print(f"   ⏱️  Technical: Starting API call")
        api_start = time.time()
        
        # Call parent run which handles the API call
        result = await super().run(api_task)
        
        duration = time.time() - api_start
        print(f"   ⏱️  Technical: API call took {duration:.3f}s")
        print(f"   ⏱️  Technical: Total took {time.time() - start:.3f}s")
        
        if "error" in result:
            return result
            
        return {
            "perspective": "technical",
            "analysis": result.get("response")
        }

class BusinessAnalysisJob(OpenAIJob):
    """Analyze document from business perspective."""
    
    async def run(self, task):
        import time
        start = time.time()
        if "business" in task:
            document = task.get("business", {}).get("document")
        else:
            document = task.get("document")
        
        messages = [
            {"role": "system", "content": "You are a business analyst. Analyze the following document from a business perspective focusing on value and ROI."},
            {"role": "user", "content": document}
        ]
        
        api_task = {
            "messages": messages,
            "model": "gpt-4o-mini",
            "temperature": 0
        }
        
        print(f"   ⏱️  Business: Starting API call")
        api_start = time.time()
        result = await super().run(api_task)
        
        print(f"   ⏱️  Business: API call took {time.time() - api_start:.3f}s")
        print(f"   ⏱️  Business: Total took {time.time() - start:.3f}s")
        
        if "error" in result:
            return result

        return {
            "perspective": "business",
            "analysis": result.get("response")
        }

class UXAnalysisJob(OpenAIJob):
    """Analyze document from UX perspective."""
    
    async def run(self, task):
        import time
        start = time.time()
        if "user_experience" in task:
            document = task.get("user_experience", {}).get("document")
        else:
            document = task.get("document")
        
        messages = [
            {"role": "system", "content": "You are a UX researcher. Analyze the following document from a user experience perspective."},
            {"role": "user", "content": document}
        ]
        
        api_task = {
            "messages": messages,
            "model": "gpt-4o-mini",
            "temperature": 0
        }
        
        print(f"   ⏱️  UX: Starting API call")
        api_start = time.time()
        result = await super().run(api_task)
        
        print(f"   ⏱️  UX: API call took {time.time() - api_start:.3f}s")
        print(f"   ⏱️  UX: Total took {time.time() - start:.3f}s")
        
        if "error" in result:
            return result

        return {
            "perspective": "user_experience",
            "analysis": result.get("response")
        }

class SynthesisJob(OpenAIJob):
    """Synthesize all analyses into a comprehensive summary."""
    
    async def run(self, j_ctx):
        import time
        start = time.time()
        
        # Flow4AI passes context differently than simple dict task
        # Current FlowManager implementation passes inputs in the task dict if direct
        # But for synthesis we need inputs from multiple parents
        
        # When using DSL, j_ctx contains inputs from previous jobs
        inputs = j_ctx.get("inputs", {})
        
        technical = inputs.get("technical", {}).get("analysis", "N/A")
        business = inputs.get("business", {}).get("analysis", "N/A")
        ux = inputs.get("user_experience", {}).get("analysis", "N/A")
        
        prompt_content = f"Technical Analysis:\n{technical}\n\nBusiness Analysis:\n{business}\n\nUX Analysis:\n{ux}"
        
        messages = [
            {"role": "system", "content": "You are a strategic advisor. Synthesize the following analyses into a cohesive executive summary."},
            {"role": "user", "content": prompt_content}
        ]
        
        api_task = {
            "messages": messages,
            "model": "gpt-4o-mini",
            "temperature": 0
        }
        
        print(f"   ⏱️  Synthesis: Starting API call")
        api_start = time.time()
        result = await super().run(api_task)
        
        print(f"   ⏱️  Synthesis: API call took {time.time() - api_start:.3f}s")
        print(f"   ⏱️  Synthesis: Total took {time.time() - start:.3f}s")
        
        if "error" in result:
            return result

        return {
            "executive_summary": result.get("response")
        }


def run_parallel_chains_openai():
    # Define tasks (Jobs)
    # We must reset unique names if re-running or ensure new instances
    technical = TechnicalAnalysisJob("technical")
    business = BusinessAnalysisJob("business")
    ux = UXAnalysisJob("user_experience")
    
    synthesize = SynthesisJob("synthesis")
    

    
    # Define the DSL graph by providing the head nodes
    # When multiple head nodes exist, we use parallel() to group them
    dsl = parallel(technical, business, ux) >> synthesize

    document = """
    Flow4AI is a powerful Python framework for orchestrating complex AI workflows.
    It enables developers to build parallel processing pipelines with ease,
    handling dependencies, concurrency, and error management automatically.
    Built on top of asyncio, it provides a clean DSL for defining job graphs
    and manages the execution lifecycle robustly, making it ideal for scalable
    LLM applications. The system supports both simple task chains and complex
    DAGs (Directed Acyclic Graphs), allowing for sophisticated data processing
    architectures. Flow4AI abstracts away the complexity of async programming,
    making it easy to scale LLM operations and manage concurrent API calls efficiently.
    """
    
    print(f"Text to analyze:\n{document[:100]}...\n")
    print("Running multi-perspective analysis in parallel (OpenAIJob)...\n")
    
    # Execute workflow
    # Note: DSL task input routing works by matching job names
    task = {
        "technical": {"document": document},
        "business": {"document": document},
        "user_experience": {"document": document}
    }
    
    import time
    workflow_start = time.time()
    print(f"⏱️  Starting workflow execution at {time.strftime('%H:%M:%S')}\n")
    
    # Run with 60s timeout mostly to act as a failsafe
    errors, results = FlowManager.run(dsl, task, "multi_perspective_analysis_openai", timeout=60)
    
    workflow_time = time.time() - workflow_start
    print(f"\n⏱️  Total workflow execution time: {workflow_time:.3f}s\n")
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
        
    print("============================================================")
    print("✅ Analysis Complete")
    print("============================================================")
    
    # Extract results
    summary = results.get("synthesis", {}).get("executive_summary", "No summary generated")
    
    print("\nExecutive Summary:")
    print("============================================================")
    print(summary)
    print("============================================================")
    
    return True

if __name__ == "__main__":
    run_parallel_chains_openai()
