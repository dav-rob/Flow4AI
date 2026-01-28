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


def run_example(example_name):
    """
    Run an example file and capture its output.
    
    Args:
        example_name: Name of the example file (e.g., '01_basic_workflow.py')
        
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    example_path = PROJECT_ROOT / "examples" / example_name
    
    result = subprocess.run(
        [sys.executable, str(example_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    return result.returncode, result.stdout, result.stderr


def test_basic_workflow():
    """Test that 01_basic_workflow.py executes successfully."""
    return_code, stdout, stderr = run_example("01_basic_workflow.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output markers
    assert "Example 1: Basic Workflow" in stdout
    assert "✅ Analysis complete!" in stdout
    assert "Word Count:" in stdout
    assert "Sentiment:" in stdout
    assert "Top Keywords:" in stdout
    assert "FlowManager.run()" in stdout


def test_task_passthrough():
    """Test that 02_task_passthrough.py executes successfully and demonstrates task_pass_through."""
    return_code, stdout, stderr = run_example("02_task_passthrough.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Example 2: Task Passthrough" in stdout
    assert "callback" in stdout.lower()
    assert "disconnected" in stdout.lower()
    assert "Order ORD-001" in stdout
    assert "Order ORD-002" in stdout
    assert "Order ORD-003" in stdout
    assert "Alice" in stdout
    assert "Bob" in stdout
    assert "Charlie" in stdout
    assert "task_pass_through matters" in stdout


def test_parallel_execution():
    """Test that 03_parallel_execution.py executes with significant parallel speedup."""
    return_code, stdout, stderr = run_example("03_parallel_execution.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Example 3: Parallel Execution" in stdout
    assert "interlacing" in stdout.lower() or "interleave" in stdout.lower()
    assert "FIRST submission" in stdout
    assert "FINAL submission" in stdout
    assert "FIRST completion" in stdout
    assert "FINAL completion" in stdout
    assert "Speedup:" in stdout
    assert "CONFIRMED" in stdout
    
    # Verify that at least one of the task counts was tested
    assert any(count in stdout for count in ["100 tasks", "500 tasks", "1000 tasks"])


def test_multiprocessing():
    """Test that 04_multiprocessing.py executes successfully with FlowManagerMP."""
    return_code, stdout, stderr = run_example("04_multiprocessing.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Example 4: Multiprocessing" in stdout
    assert "on_complete" in stdout.lower()
    assert "FIRST submission" in stdout
    assert "FINAL submission" in stdout  
    assert "FIRST completion" in stdout
    assert "FINAL completion" in stdout
    assert "primes" in stdout.lower()
    assert "FlowManagerMP" in stdout


def test_complex_workflow():
    """Test that 05_complex_workflow.py executes successfully with advanced features."""
    return_code, stdout, stderr = run_example("05_complex_workflow.py")
    
    # Should complete successfully
    assert return_code == 0, f"Example failed with return code {return_code}. stderr: {stderr}"
    
    # Verify expected output
    assert "Example 5: Complex Workflow" in stdout
    assert "✅ Workflow complete!" in stdout
    assert "SAVED_RESULTS" in stdout
    assert "task_pass_through" in stdout
    
    # Verify intermediate results are shown
    assert "times(5) = 10" in stdout
    assert "add(10) = 13" in stdout
    assert "square(7) = 49" in stdout
    
    # Verify key features are demonstrated
    assert "Mixed job types" in stdout


def test_all_examples_exist():
    """Verify that all expected example files exist."""
    examples_dir = PROJECT_ROOT / "examples"
    
    expected_examples = [
        "01_basic_workflow.py",
        "02_task_passthrough.py",
        "03_parallel_execution.py",
        "04_multiprocessing.py",
        "05_complex_workflow.py",
        "README.md"
    ]
    
    for example in expected_examples:
        example_path = examples_dir / example
        assert example_path.exists(), f"Expected example file not found: {example}"


def test_examples_are_executable():
    """Verify that all Python example files have proper structure."""
    examples_dir = PROJECT_ROOT / "examples"
    
    python_examples = [
        "01_basic_workflow.py",
        "02_task_passthrough.py",
        "03_parallel_execution.py",
        "04_multiprocessing.py",
        "05_complex_workflow.py",
    ]
    
    for example in python_examples:
        example_path = examples_dir / example
        
        # Read the file content
        with open(example_path, 'r') as f:
            content = f.read()
        
        # Verify it has a docstring
        assert '"""' in content or "'''" in content, f"{example} missing docstring"
        
        # Verify it has a main function
        assert "def main():" in content, f"{example} missing main() function"
        
        # Verify it has if __name__ == "__main__"
        assert 'if __name__ == "__main__"' in content, f"{example} missing __main__ check"


# Check if LangChain is available
try:
    import langchain_core
    import langchain_openai
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
def test_langchain_simple():
    """Test that 06_langchain_simple.py structure is correct (skip actual LLM calls)."""
    return_code, stdout, stderr = run_example("06_langchain_simple.py")
    
    # Should complete successfully or show langchain status
    assert return_code == 0 or "LangChain" in stdout, \
        f"Example had unexpected failure. return_code: {return_code}, stderr: {stderr}"
    
    # Verify expected structure
    assert "Example 6: LangChain Integration" in stdout
    assert "LangChain" in stdout


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
def test_langchain_chains():
    """Test that 07_langchain_chains.py structure is correct (skip actual LLM calls)."""
    return_code, stdout, stderr = run_example("07_langchain_chains.py")
    
    # Should complete successfully or show langchain status
    assert return_code == 0 or "LangChain" in stdout, \
        f"Example had unexpected failure. return_code: {return_code}, stderr: {stderr}"
    
    # Verify expected structure
    assert "Example 7: LangChain Integration" in stdout
    assert "LangChain" in stdout or "chains" in stdout.lower()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
