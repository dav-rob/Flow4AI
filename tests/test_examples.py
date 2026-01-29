"""
Test suite for verifying all examples in the examples/ directory execute correctly.

This ensures examples stay up-to-date with the codebase and work as documented.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def run_example(example_path):
    """
    Run an example file and capture its output.
    
    Args:
        example_path: Path to the example file relative to examples/ 
                     (e.g., 'tutorials/01_hello_workflow.py')
        
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    full_path = PROJECT_ROOT / "examples" / example_path
    
    result = subprocess.run(
        [sys.executable, str(full_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    return result.returncode, result.stdout, result.stderr


# =============================================================================
# Tutorial Tests
# =============================================================================

def test_hello_workflow():
    """Test that tutorials/01_hello_workflow.py executes successfully."""
    return_code, stdout, stderr = run_example("tutorials/01_hello_workflow.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output markers
    assert "Hello Workflow" in stdout or "Basic Workflow" in stdout
    assert "✅ Analysis complete!" in stdout
    assert "Word Count:" in stdout
    assert "Sentiment:" in stdout
    assert "Top Keywords:" in stdout


def test_parameters():
    """Test that tutorials/02_parameters.py executes successfully."""
    return_code, stdout, stderr = run_example("tutorials/02_parameters.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Tasks and Parameters" in stdout
    assert "Task Format Options" in stdout
    assert "Shorthand format" in stdout
    assert "Nested format" in stdout
    assert "Batch Processing" in stdout


def test_parallel_jobs():
    """Test that tutorials/03_parallel_jobs.py executes with significant parallel speedup."""
    return_code, stdout, stderr = run_example("tutorials/03_parallel_jobs.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Parallel" in stdout
    assert "FIRST submission" in stdout
    assert "FINAL submission" in stdout
    assert "FIRST completion" in stdout
    assert "FINAL completion" in stdout
    assert "Speedup:" in stdout
    assert "CONFIRMED" in stdout


def test_multiprocessing():
    """Test that tutorials/04_multiprocessing.py executes successfully with FlowManagerMP."""
    return_code, stdout, stderr = run_example("tutorials/04_multiprocessing.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Multiprocessing" in stdout
    assert "on_complete" in stdout.lower()
    assert "FIRST submission" in stdout
    assert "FINAL submission" in stdout  
    assert "FIRST completion" in stdout
    assert "FINAL completion" in stdout
    assert "primes" in stdout.lower()
    assert "FlowManagerMP" in stdout


def test_job_types():
    """Test that tutorials/05_job_types.py executes successfully."""
    return_code, stdout, stderr = run_example("tutorials/05_job_types.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Scenario 1" in stdout
    assert "Scenario 2" in stdout
    assert "Scenario 3" in stdout
    assert "ClassBasedJob" in stdout or "class_job" in stdout
    assert "Callback" in stdout


def test_data_flow():
    """Test that tutorials/06_data_flow.py executes successfully and demonstrates task_pass_through."""
    return_code, stdout, stderr = run_example("tutorials/06_data_flow.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Task Passthrough" in stdout or "Data Flow" in stdout
    assert "Order ORD-001" in stdout
    assert "Order ORD-002" in stdout
    assert "Order ORD-003" in stdout
    assert "Alice" in stdout
    assert "Bob" in stdout
    assert "Charlie" in stdout


def test_complex_pipelines():
    """Test that tutorials/07_complex_pipelines.py executes successfully with advanced features."""
    return_code, stdout, stderr = run_example("tutorials/07_complex_pipelines.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Complex" in stdout
    assert "✅ Workflow complete!" in stdout
    assert "SAVED_RESULTS" in stdout
    assert "task_pass_through" in stdout
    
    # Verify intermediate results are shown
    assert "times(5) = 10" in stdout
    assert "add(10) = 13" in stdout
    assert "square(7) = 49" in stdout
    
    # Verify key features are demonstrated
    assert "Mixed job types" in stdout


# =============================================================================
# Structure Tests
# =============================================================================

def test_directory_structure():
    """Verify that the expected directory structure exists."""
    examples_dir = PROJECT_ROOT / "examples"
    
    # Check directories exist
    assert (examples_dir / "tutorials").is_dir(), "tutorials/ directory missing"
    assert (examples_dir / "integrations").is_dir(), "integrations/ directory missing"
    assert (examples_dir / "README.md").exists(), "examples/README.md missing"
    
    # Check tutorial files exist
    tutorials = [
        "tutorials/01_hello_workflow.py",
        "tutorials/02_parameters.py",
        "tutorials/03_parallel_jobs.py",
        "tutorials/04_multiprocessing.py",
        "tutorials/05_job_types.py",
        "tutorials/06_data_flow.py",
        "tutorials/07_complex_pipelines.py",
    ]
    
    for tutorial in tutorials:
        assert (examples_dir / tutorial).exists(), f"Tutorial file missing: {tutorial}"
    
    # Check integration files exist
    integrations = [
        "integrations/langchain_simple.py",
        "integrations/langchain_chains.py",
    ]
    
    for integration in integrations:
        assert (examples_dir / integration).exists(), f"Integration file missing: {integration}"


def test_tutorials_have_proper_structure():
    """Verify that all tutorial files have proper structure."""
    examples_dir = PROJECT_ROOT / "examples"
    
    tutorials = [
        "tutorials/01_hello_workflow.py",
        "tutorials/02_parameters.py",
        "tutorials/03_parallel_jobs.py",
        "tutorials/04_multiprocessing.py",
        "tutorials/05_job_types.py",
        "tutorials/06_data_flow.py",
        "tutorials/07_complex_pipelines.py",
    ]
    
    for tutorial in tutorials:
        tutorial_path = examples_dir / tutorial
        
        # Read the file content
        with open(tutorial_path, 'r') as f:
            content = f.read()
        
        # Verify it has a docstring
        assert '"""' in content or "'''" in content, f"{tutorial} missing docstring"
        
        # Verify it has if __name__ == "__main__"
        assert 'if __name__ == "__main__"' in content, f"{tutorial} missing __main__ check"


# =============================================================================
# Integration Tests (Skipped by Default - Require API Keys)
# =============================================================================

# Check if LangChain is available
try:
    import langchain_core
    import langchain_openai
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def test_langchain_simple():
    """Test that integrations/langchain_simple.py executes correctly."""
    return_code, stdout, stderr = run_example("integrations/langchain_simple.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    assert "LangChain Integration" in stdout
    assert "Sentiment:" in stdout


def test_langchain_chains():
    """Test that integrations/langchain_chains.py executes correctly."""
    return_code, stdout, stderr = run_example("integrations/langchain_chains.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    assert "LangChain Integration" in stdout
    assert "Analysis Complete" in stdout

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
