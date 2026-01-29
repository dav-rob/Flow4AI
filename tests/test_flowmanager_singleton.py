import time
import threading
import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import job
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC

# Configure logging
logger = logging.getLogger(__name__)


class TestJob(JobABC):
    """Simple test job for singleton testing."""
    async def run(self, task):
        return {"job_id": self.name, "task_data": task, "result": "success"}


def test_singleton_basic():
    """Test that FlowManager.instance() returns the same instance when called multiple times."""
    # Rule Applied: Base decisions on evidence
    
    # Reset the instance to ensure clean test state
    FlowManager.reset_instance()
    
    # Get instance 1
    fm1 = FlowManager.instance()
    
    # Get instance 2
    fm2 = FlowManager.instance()
    
    # Assert they are the same object
    assert fm1 is fm2, "FlowManager.instance() should return the same instance"
    
    # Verify both instances share the same state by modifying one
    test_job_instance = TestJob("test_job")
    dsl = job({"test_job": test_job_instance})
    
    fq_name = fm1.add_workflow(dsl, "test_graph")
    
    # Verify the DSL is accessible from both instances
    assert fq_name in fm1.job_graph_map
    assert fq_name in fm2.job_graph_map


def test_singleton_reset():
    """Test that FlowManager.reset_instance() clears the instance and allows creating a new one."""
    # Rule Applied: Base decisions on evidence
    
    # Get initial instance
    fm1 = FlowManager.instance()
    
    # Add a job to the instance
    test_job_instance = TestJob("reset_test_job")
    dsl = job({"reset_test_job": test_job_instance})
    fq_name = fm1.add_workflow(dsl, "reset_test_graph")
    
    # Reset the instance
    FlowManager.reset_instance()
    
    # Get a new instance
    fm2 = FlowManager.instance()
    
    # Assert they are different objects
    assert fm1 is not fm2, "After reset, FlowManager.instance() should return a new instance"
    
    # Verify the new instance has a clean state
    assert not hasattr(fm2, 'job_graph_map') or fq_name not in fm2.job_graph_map, "New instance should have clean state"


def test_singleton_thread_safety():
    """Test that FlowManager.instance() is thread-safe."""
    # Rule Applied: Break complex problems into simpler pieces
    
    # Reset the instance to ensure clean test state
    FlowManager.reset_instance()
    
    # List to store instances from different threads
    instances = []
    error_occurred = [False]
    
    def get_instance():
        try:
            instances.append(FlowManager.instance())
        except Exception as e:
            logger.error(f"Error getting instance: {e}")
            error_occurred[0] = True
    
    # Create threads that get the instance
    threads = [threading.Thread(target=get_instance) for _ in range(10)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Assert no errors occurred
    assert not error_occurred[0], "Errors occurred during thread execution"
    
    # Assert all instances are the same object
    first_instance = instances[0]
    for instance in instances[1:]:
        assert instance is first_instance, "All instances should be the same object"


def test_singleton_in_different_contexts():
    """Test that FlowManager.instance() works in different usage contexts."""
    # Rule Applied: DRY (Don't Repeat Yourself)
    
    # Reset the instance to ensure clean test state
    FlowManager.reset_instance()
    
    # Context 1: Adding and submitting a simple job
    def simple_function(j_ctx):
        # Access the input from the task context
        data = j_ctx.get('task', {})
        x = data.get('x', 0)
        return x * 2
    
    # Get the instance and configure it
    fm = FlowManager.instance()
    dsl1 = job({"simple_func": simple_function})
    fq_name1 = fm.add_workflow(dsl1, "context1")
    
    # Submit a task and verify results
    fm.submit_task({"x": 5}, fq_name1)
    success = fm.wait_for_completion()
    assert success, "Task should complete successfully"
    
    results = fm.pop_results()
    assert "context1$$$$simple_func$$" in results["completed"]
    assert results["completed"]["context1$$$$simple_func$$"][0]["result"] == 10
    
    # Context 2: In a different part of the application, reusing the same instance
    # but with a different DSL and task
    async def async_func(j_ctx):
        task = j_ctx.get('task', {})
        return {"original": task, "processed": "processed_" + str(task.get("data", ""))}
    
    # Create a test job
    async_job = TestJob("async_job")
    
    # Get the instance (should be the same one)
    fm2 = FlowManager.instance()
    assert fm is fm2, "Should get the same instance"
    
    # Add a new DSL with both functions separately
    dsl2 = job({"async_func": async_func})
    fq_name2 = fm2.add_workflow(dsl2, "context2")
    
    # Add the job separately
    dsl3 = job({"async_job": async_job})
    fq_name3 = fm2.add_workflow(dsl3, "context3")
    
    # Submit a task to the new DSL
    fm2.submit_task({"data": "test_data"}, fq_name2)
    success = fm2.wait_for_completion()
    assert success, "Task should complete successfully"
    
    # Verify all DSLs exist in the same instance
    assert fq_name1 in fm.job_graph_map
    assert fq_name2 in fm.job_graph_map
    assert fq_name3 in fm.job_graph_map
    
    # Get new results without affecting previous ones
    new_results = fm2.pop_results()
    assert "context2$$$$async_func$$" in new_results["completed"]
    
    # Verify state is properly shared
    assert fm.submitted_count == fm2.submitted_count
    assert fm.completed_count == fm2.completed_count


def test_singleton_parameters():
    """Test that FlowManager.instance() properly handles parameters."""
    # Rule Applied: Test code for correctness
    
    # Reset the instance to ensure clean test state
    FlowManager.reset_instance()
    
    # Define a completion callback
    callback_called = [False]
    def on_complete(result):
        callback_called[0] = True
    
    # Create instance with parameters
    fm = FlowManager.instance(on_complete=on_complete)
    
    # Create a simple job
    def simple_job(j_ctx):
        data = j_ctx.get('task', {})
        return data.get('x', 'default_value')
    
    # Add DSL and submit task
    dsl = job({"simple_job": simple_job})
    fq_name = fm.add_workflow(dsl, "param_test")
    fm.submit_task({"x": "test_value"}, fq_name)
    
    # Wait for completion
    fm.wait_for_completion()
    
    # Verify callback was called
    assert callback_called[0], "Callback should have been called"
    
    # Try to create a new instance with different parameters
    # This should not affect the existing instance since it's already created
    different_callback_called = [False]
    def different_callback(result):
        different_callback_called[0] = True
    
    fm2 = FlowManager.instance(on_complete=different_callback)
    
    # Verify it's the same instance
    assert fm is fm2, "Should get the same instance regardless of different parameters"
    
    # Submit another task
    fm2.submit_task({"x": "another_value"}, fq_name)
    fm2.wait_for_completion()
    
    # Verify the original callback was called, not the new one
    assert callback_called[0], "Original callback should have been called"
    assert not different_callback_called[0], "New callback should not have been called"


def test_wait_for_completion_no_tasks():
    """Test that FlowManager.wait_for_completion() doesn't hang when no tasks are submitted."""
    # Rule Applied: Test code for correctness and Base decisions on evidence
    
    # Reset the instance to ensure clean test state
    FlowManager.reset_instance()
    
    # Create instance
    fm = FlowManager.instance()
    
    # Create a simple job
    def simple_job(j_ctx):
        data = j_ctx.get('task', {})
        return data.get('x', 'default_value')
    
    # Add DSL but don't submit any tasks
    dsl = job({"simple_job": simple_job})
    fm.add_workflow(dsl, "no_tasks_test")
    
    # Log that we're calling wait_for_completion with no tasks
    logger.info("Calling wait_for_completion with no tasks submitted")
    
    # Wait for completion - this should return immediately since there are no tasks
    start_time = time.time()
    success = fm.wait_for_completion()
    end_time = time.time()
    
    # Log the elapsed time
    elapsed_time = end_time - start_time
    logger.info(f"wait_for_completion completed in {elapsed_time:.6f} seconds")
    
    # Verify success status
    assert success, "wait_for_completion should return True even when no tasks are submitted"
    
    # Verify that wait_for_completion returned quickly (didn't hang until timeout)
    assert elapsed_time < 1.0, f"wait_for_completion took {elapsed_time:.6f} seconds, which suggests it may be hanging"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
