"""
Example 9: Syntax Details & Advanced Features

This example demonstrates critical Flow4AI concepts across three scenarios:
1.  **Job Syntax & Parameters**: JobABC vs. Wrapped functions, and how to access parameters.
2.  **Multiple Tail Jobs**: How to handle graphs with multiple end nodes and interpret results.
3.  **Intermediate Results & Lifecycle**: Using `save_result=True` and `on_complete` callbacks.
"""

import asyncio
from typing import Dict, Any
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p
from flow4ai.job import JobABC

# ==============================================================================
# Scenario 1: Syntax & Parameters
# ==============================================================================
def scenario_1_syntax_differences():
    print("\n=== Scenario 1: Syntax Differences (JobABC vs Wrapped) ===")
    
    # --- 1a. JobABC Subclass ---
    # Best for: Complex logic, maintaining state, inheritance
    class ClassBasedJob(JobABC):
        async def run(self, task):
            # NEW: Use get_params() for clean parameter access (matches function behavior)
            params = self.get_params()  # Returns {"val": 10} for this job
            val = params.get("val", 0)
            
            # OLD APPROACH (still works, but more verbose):
            # my_params = task.get("class_job", {})
            # val = my_params.get("val", 0)
            
            # Access upstream inputs via self.get_inputs()
            # (Empty dict here as this is a head node in this example)
            
            print(f"[ClassBasedJob] Using get_params(). val={val}")
            return {"result": val * 2}

    # --- 1b. Wrapped Function (Context Aware) ---
    # Best for: Simple transformations needing context or dynamic params
    def context_func(j_ctx, **kwargs):
        # OPTION A (**kwargs): Flow4AI automatically finds parameters matching this job
        # and passes them as kwargs.
        val = kwargs.get("val", 0)
        
        # OPTION B (j_ctx["task"]): Access the full raw task dict
        # task = j_ctx["task"]
        
        print(f"[ContextFunc] Auto-extracted kwargs. val={val}")
        return {"result": val + 10}

    # --- 1c. Wrapped Function (Simple) ---
    # Best for: Pure functions
    def simple_func(val):
        # Arguments are automatically mapped from task parameters
        print(f"[SimpleFunc] Direct argument mapping. val={val}")
        return {"result": val * 5}

    # Setup & Execution
    jobs = job({
        "class_job": ClassBasedJob("class_job"),
        "context_job": context_func,
        "simple_job": simple_func
    })
    
    # Simple parallel execution of all three
    dsl = p(jobs["class_job"], jobs["context_job"], jobs["simple_job"])
    
    task = {
        "class_job": {"val": 10},
        "context_job": {"val": 20},
        "simple_job": {"val": 30}
    }
    
    errors, results = FlowManager.run(dsl, task, "scenario_1")
    if not errors:
        # Results from parallel tail jobs are in the results dict keyed by job name
        print(f"Results: {results}")

# ==============================================================================
# Scenario 2: Multiple Tail Jobs & Result Structure
# ==============================================================================
def scenario_2_multiple_tails():
    print("\n=== Scenario 2: Multiple Tail Jobs & Result Structure ===")
    
    # A graph can split and end in multiple places.
    #      /--> Branch A (Tail)
    # Start
    #      \--> Branch B (Tail)
    
    def start_job(): 
        return {"data": 1}
    
    def branch_a(j_ctx):
        prev = j_ctx["inputs"]["start"]["data"]
        return {"a_result": prev + 100}
        
    def branch_b(j_ctx):
        prev = j_ctx["inputs"]["start"]["data"]
        return {"b_result": prev + 200}
        
    jobs = job({
        "start": start_job,
        "branch_a": branch_a,
        "branch_b": branch_b
    })
    
    # Define split
    dsl = jobs["start"] >> (jobs["branch_a"] | jobs["branch_b"])
    
    errors, results = FlowManager.run(dsl, {}, "scenario_2")
    
    if not errors:
        # When there are multiple tail jobs, 'results' is a dictionary containing all of them.
        # Key = Job Name, Value = Result Dict
        print("Graph ended with multiple tails.")
        
        if "branch_a" in results:
            print(f"Tail 'branch_a': {results['branch_a']}")
            
        if "branch_b" in results:
            print(f"Tail 'branch_b': {results['branch_b']}")
            
        # Note: If there was only ONE tail job, FlowManager.run returns its result directly
        # AND wrapped in the dict? Let's check the output.
        # The behavior is consistent: it returns a dict of results from the last executed layer/tails.

# ==============================================================================
# Scenario 3: Intermediate Results & Lifecycle (on_complete)
# ==============================================================================
def scenario_3_intermediate_and_lifecycle():
    print("\n=== Scenario 3: Intermediate Results & Lifecycle ===")
    
    def step_1(): return {"step": 1, "msg": "I am hidden unless saved"}
    def step_2(j_ctx): return {"step": 2, "msg": "I am intermediate"}
    def step_3(j_ctx): return {"step": 3, "msg": "I am the tail"}
    
    jobs = job({"step1": step_1, "step2": step_2, "step3": step_3})
    
    # 1. Accessing Intermediate Results
    # By default, only the tail result is returned. 
    # To see step_2's output in the final result, we set save_result=True.
    jobs["step2"].save_result = True
    
    # 2. Result Handling: on_complete vs pop_results()
    # You generally use ONE of these approaches:
    #   A) on_complete callback: Best for async/non-blocking handling (logging, streaming to DB).
    #   B) pop_results(): Best for blocking/synchronous workflows where you wait for everything.
    
    # We will demonstrate (A) here.
    
    # Instantiate FlowManager with the callback
    fm = FlowManager(on_complete=scenario3_callback)
    
    # Define DSL
    dsl = jobs["step1"] >> jobs["step2"] >> jobs["step3"]
    
    # Add the DSL to the manager
    fq_name = fm.add_dsl(dsl, "scenario_3")
    
    task = {"user_id": "user_123"} 
    
    print("   Submitting task to FlowManager instance...")
    fm.submit_task(task, fq_name)
    
    # For demonstration purposes, we wait here so the script doesn't exit.
    # In a real async app, you might be doing other things.
    fm.wait_for_completion() 
    
    # NOTE: Since we handled results in the callback, we don't strictly NEED pop_results().
    # However, FlowManager stores them until popped, so it's good practice to clear them 
    # if the manager instance is long-lived.
    fm.pop_results() 

def scenario3_callback(result):
    # The 'result' dict contains:
    # 1. The output of the tail job (here, 'step3')
    # 2. Metadata: 'task_pass_through' (original task), 'SAVED_RESULTS' (intermediate data)
    
    pass_through = result.get("task_pass_through", {})
    user_id = pass_through.get("user_id", "unknown")
    
    # Accessing the Tail Result (directly in the dict)
    step_val = result.get("step", "unknown")
    
    # Accessing Intermediate Results (in SAVED_RESULTS sub-dict)
    saved_step2 = result.get("SAVED_RESULTS", {}).get("step2", {})
    
    print(f"   [Callback] Workflow finished for user={user_id}")
    print(f"   [Callback] Tail Result (Step 3): {step_val}")
    print(f"   [Callback] Intermediate (Step 2): {saved_step2.get('msg', 'N/A')}")

if __name__ == "__main__":
    scenario_1_syntax_differences()
    scenario_2_multiple_tails()
    scenario_3_intermediate_and_lifecycle()
