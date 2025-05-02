import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, JobsDict, wrap
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC, Task

# Configure logging
logger = logging.getLogger(__name__)


class SimpleJob(JobABC):
    """Example component that implements JobABC interface for testing."""
    def __init__(self, name):
        super().__init__(name)
    
    async def run(self, task):
        logger.info(f"Processing task in {self.name}")
        return {"result": f"Job {self.name} processed task"}


def test_add_dsl_resubmission():
    """Test that resubmitting the same DSL returns the original FQ name.
    
    This verifies our enhancement to the add_dsl method that tracks previously added DSLs
    and returns their FQ name without reprocessing them.
    """
    # Create job instances
    job1 = SimpleJob("job1")
    job2 = SimpleJob("job2")
    
    # Wrap jobs in a dictionary
    jobs = wrap({
        "job1": job1,
        "job2": job2
    })
    
    # Create a simple pipeline: job1 >> job2
    dsl = jobs["job1"] >> jobs["job2"]
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # First submission - should process normally
    logger.info("First DSL submission")
    fq_name1 = fm.add_dsl(dsl, "test_graph", "test")
    logger.info(f"Received FQ name: {fq_name1}")
    
    # Verify DSL is marked as already added
    assert hasattr(dsl, "_f4a_already_added")
    assert dsl._f4a_already_added is True
    
    # Verify head job has reference to source DSL
    head_job = fm.job_map[fq_name1]
    assert hasattr(head_job, "_f4a_source_dsl")
    assert head_job._f4a_source_dsl is dsl
    
    # Second submission with same DSL - should return original FQ name
    logger.info("Second DSL submission (same object)")
    fq_name2 = fm.add_dsl(dsl, "test_graph", "test")
    logger.info(f"Received FQ name: {fq_name2}")
    
    # Should be the same FQ name
    assert fq_name1 == fq_name2, f"Expected same FQ name: {fq_name1} != {fq_name2}"
    
    # Third submission with different graph name and variant
    # Since it's the same DSL object, should still return original FQ name
    logger.info("Third DSL submission (same object, different graph name)")
    fq_name3 = fm.add_dsl(dsl, "different_graph", "different")
    logger.info(f"Received FQ name: {fq_name3}")
    
    # Still should be the same FQ name
    assert fq_name1 == fq_name3, f"Expected same FQ name: {fq_name1} != {fq_name3}"


def test_dsl_submission_with_tasks():
    """Test submitting tasks to a reused DSL FQ name."""
    # Create job instances
    processor1 = SimpleJob("processor1")
    processor2 = SimpleJob("processor2")
    
    # Wrap jobs
    jobs = wrap({
        "processor1": processor1,
        "processor2": processor2
    })
    
    # Enable result saving
    jobs["processor1"].save_result = True
    jobs["processor2"].save_result = True
    
    # Create pipeline
    dsl = jobs["processor1"] >> jobs["processor2"]
    
    # Initialize FlowManager
    fm = FlowManager()
    
    # First submission
    fq_name = fm.add_dsl(dsl, "test_pipeline")
    
    # Create and submit a task
    task = Task({"input": "test data"})
    fm.submit(task, fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Task did not complete successfully"
    
    # Get results
    results = fm.pop_results()
    assert "completed" in results
    assert len(results["completed"]) > 0, "No completed results found"
    
    # Submit the same DSL again - should get same FQ name
    same_fq_name = fm.add_dsl(dsl, "different_name")
    assert fq_name == same_fq_name, "Did not get the same FQ name for resubmitted DSL"
    
    # Submit another task using the returned FQ name
    task2 = Task({"input": "more test data"})
    fm.submit(task2, same_fq_name)
    
    # Wait for completion
    success = fm.wait_for_completion()
    assert success, "Second task did not complete successfully"
    
    # Get results
    results2 = fm.pop_results()
    assert "completed" in results2
    assert len(results2["completed"]) > 0, "No completed results found for second task"


def test_new_dsl_with_same_structure():
    """Test that two DSLs with the same structure get the same FQ name based on job names.
    
    This test confirms current system behavior: FQ names are generated based on graph name
    and job names, not object identity.
    """
    # Create a FlowManager
    fm = FlowManager()
    
    # Create first DSL
    job1 = SimpleJob("job1")
    job2 = SimpleJob("job2")
    jobs1 = wrap({
        "job1": job1,
        "job2": job2
    })
    dsl1 = jobs1["job1"] >> jobs1["job2"]
    
    # Add first DSL
    logger.info("Adding first DSL")
    fq_name1 = fm.add_dsl(dsl1, "test_graph")
    logger.info(f"First DSL FQ name: {fq_name1}")
    
    # Create second DSL with same structure but different objects
    job3 = SimpleJob("job1")  # Same name but different object
    job4 = SimpleJob("job2")  # Same name but different object
    jobs2 = wrap({
        "job1": job3,
        "job2": job4
    })
    dsl2 = jobs2["job1"] >> jobs2["job2"]
    
    # Add second DSL
    logger.info("Adding second DSL with same structure but different objects")
    fq_name2 = fm.add_dsl(dsl2, "test_graph")
    logger.info(f"Second DSL FQ name: {fq_name2}")
    
    # Current behavior: Same FQ names because they're based on graph/job names
    assert fq_name1 == fq_name2, "DSLs with same structure should get same FQ names in current implementation"
    
    # Check the _f4a_source_dsl reference
    head_job = fm.job_map[fq_name2]
    assert hasattr(head_job, "_f4a_source_dsl")
    
    # The current implementation updates the reference to the most recently added DSL
    # with the same FQ name, which is dsl2 in this case
    assert head_job._f4a_source_dsl is dsl2
    assert head_job._f4a_source_dsl is not dsl1
    
    # Create a third DSL with different job name structure
    job5 = SimpleJob("processorA")
    job6 = SimpleJob("processorB")
    jobs3 = wrap({
        "processorA": job5,
        "processorB": job6
    })
    dsl3 = jobs3["processorA"] >> jobs3["processorB"]
    
    # Add third DSL
    logger.info("Adding third DSL with different job names")
    fq_name3 = fm.add_dsl(dsl3, "test_graph")
    logger.info(f"Third DSL FQ name: {fq_name3}")
    
    # FQ name should be different with different job names
    assert fq_name1 != fq_name3, "DSLs with different job names should get different FQ names"
