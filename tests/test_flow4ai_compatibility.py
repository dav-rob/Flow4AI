"""
Tests to verify the dual-package compatibility between jobchain and flow4ai.
"""
import pytest
import sys
import warnings

def test_flow4ai_import():
    """Verify that flow4ai can be imported and provides the same core functionality as jobchain."""
    # Test importing from flow4ai
    from flow4ai import JobABC, JobChain, Flow4AI, jc_logging, f4a_logging
    
    # Verify that Flow4AI is an alias for JobChain
    assert Flow4AI is JobChain
    
    # Verify that f4a_logging is an alias for jc_logging
    assert f4a_logging is jc_logging

def test_jobchain_still_works():
    """Verify that importing from jobchain still works (but with deprecation warning)."""
    # We need to force reload the module to see the warning each time
    if 'jobchain' in sys.modules:
        del sys.modules['jobchain']
        
    # Capture the deprecation warning that should be emitted
    with pytest.warns(DeprecationWarning):
        import jobchain  # This should produce the warning

def test_flow4ai_creation():
    """Test that we can create a Flow4AI instance."""
    from flow4ai import Flow4AI
    from jobchain.jobs.default_jobs import DefaultHeadJob
    
    # Create a simple job
    job = DefaultHeadJob()
    
    # Create a Flow4AI instance (which is actually a JobChain instance)
    flow = Flow4AI(job)
    
    # Verify the Flow4AI instance was created and is a JobChain instance
    # Check for known methods that should be available on JobChain
    assert hasattr(flow, 'submit_task')
    assert hasattr(flow, 'mark_input_completed')
    assert hasattr(flow, 'get_job_names')
