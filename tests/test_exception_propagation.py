import pytest
import time
import flow4ai.f4a_logging as logging
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC

logger = logging.getLogger(__name__)

class ErrorTestJob(JobABC):
    """Job that deliberately raises an exception for testing."""
    def __init__(self):
        super().__init__(name="ErrorTestJob")
    
    async def run(self, task):
        logger.info("ErrorTestJob.run() - About to raise deliberate error")
        raise RuntimeError("Deliberate error for testing exception propagation")

def test_exception_propagation():
    """Test that exceptions are properly propagated after cleanup."""
    logger.info("Starting exception propagation test")
    
    results = []
    errors = []
    
    def collect_result(result):
        logger.info(f"Collecting result: {result} (type: {type(result)})")
        if isinstance(result, Exception):
            logger.info(f"Adding exception to errors list: {result}")
            errors.append(result)
        else:
            logger.info(f"Adding result to results list")
            results.append(result)
    
    # Initialize FlowManagerMP with the job directly
    fm = FlowManagerMP(ErrorTestJob(), collect_result, serial_processing=True)
    
    # Get the head job's name
    head_jobs = fm.get_head_jobs()
    assert len(head_jobs) > 0, "No head jobs found in the flow manager"
    job_name = head_jobs[0].name
    logger.info(f"Using job with name: {job_name}")
    
    # Submit a task
    fm.submit_task({"test": "exception propagation"})
    logger.info("Task submitted")
    
    # Explicitly check that exception is propagated after cleanup
    try:
        # This should trigger the exception chain
        logger.info("Calling close_processes() - expecting exception to be propagated")
        fm.close_processes()
        # If we get here, the exception wasn't propagated as expected
        pytest.fail("Expected RuntimeError wasn't raised")
    except RuntimeError as e:
        # This is the expected behavior - exception is propagated after cleanup
        logger.info(f"Successfully caught expected exception after cleanup: {str(e)}")
        # Check for the generic error message from wait_for_completion
        assert "Flow execution completed with" in str(e)
        assert "error(s)" in str(e)
        
        # Now also check that the detailed error was collected by the result collector
        logger.info(f"Errors collected: {errors}")
        assert len(errors) > 0, "No errors were collected by the result collector"
        # Check that at least one collected error contains the detailed message
        assert any("Deliberate error for testing exception propagation" in str(err) for err in errors), \
            "Detailed error message not found in collected errors"
