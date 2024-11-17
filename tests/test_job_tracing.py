import pytest
import inspect
from typing import Dict, Any
from job import Job, UntracableJob, _is_traced
from utils.otel_wrapper import trace_function


def test_untracable_job_allows_no_decorator():
    """Test that UntracableJob subclasses don't require the decorator"""
    class UnTracedJob(UntracableJob):
        async def execute(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "complete"}
    
    job = UnTracedJob("Test Job", "Test prompt", "test-model")
    assert isinstance(job, UntracableJob)
    assert not _is_traced(UnTracedJob.execute)


class SimpleTestJob(Job):
    """A simple Job implementation for testing."""
    async def execute(self, task) -> Dict[str, Any]:
        return {"task": task, "status": "complete"}


def test_job_execute_is_traced():
    """Test that Job's execute method is automatically traced"""
    job = SimpleTestJob("Test Job", "Test prompt", "test-model")
    assert isinstance(job, Job)
    assert _is_traced(job.__class__.execute)


def test_job_execute_no_trace_available():
    """Test that Job subclasses have access to untraced execute via executeNoTrace"""
    job = SimpleTestJob("Test Job", "Test prompt", "test-model")
    assert hasattr(job, 'executeNoTrace'), "Job should have executeNoTrace method"
    assert not _is_traced(job.__class__.executeNoTrace), "executeNoTrace should not be traced"


def test_job_subclass_gets_traced_execute():
    """Test that Job subclasses inherit the traced execute method"""
    class CustomJob(Job):
        async def execute(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "success"}
    
    job = CustomJob("Test Job", "Test prompt", "test-model")
    assert _is_traced(job.__class__.execute)
    assert hasattr(job, 'executeNoTrace')
    assert not _is_traced(job.__class__.executeNoTrace)


def test_job_requires_execute_implementation():
    """Test that Job subclasses must implement execute"""
    with pytest.raises(TypeError) as exc_info:
        class IncompleteJob(Job):
            pass
        
        job = IncompleteJob("Test Job", "Test prompt", "test-model")
    
    assert "execute" in str(exc_info.value)


def test_decorator_preserves_method_signature():
    """Test that the traced execute method preserves the original signature"""
    class BaseJob(UntracableJob):
        async def execute(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "complete"}
    
    class TracedJob(Job):
        async def execute(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "complete"}
    
    # Get the signatures
    base_sig = inspect.signature(BaseJob.execute)
    traced_sig = inspect.signature(TracedJob.execute)
    
    # Compare parameters and return annotation
    assert str(base_sig.parameters) == str(traced_sig.parameters), (
        "The traced execute method should preserve the parameter signature"
    )
    assert base_sig.return_annotation == traced_sig.return_annotation, (
        "The traced execute method should preserve the return type annotation"
    )


def test_job_factory_returns_traced_jobs():
    """Test that JobFactory always returns properly traced Job instances"""
    from job import JobFactory
    
    # Test file-based job loading
    file_job = JobFactory.load_job({"type": "file", "params": {}})
    assert isinstance(file_job, Job)
    assert _is_traced(file_job.__class__.execute)
    assert hasattr(file_job, 'executeNoTrace')
    assert not _is_traced(file_job.__class__.executeNoTrace)
    
    # Test datastore-based job loading
    datastore_job = JobFactory.load_job({"type": "datastore", "params": {}})
    assert isinstance(datastore_job, Job)
    assert _is_traced(datastore_job.__class__.execute)
    assert hasattr(datastore_job, 'executeNoTrace')
    assert not _is_traced(datastore_job.__class__.executeNoTrace)


def test_existing_job_implementations():
    """Test that all existing Job implementations in the codebase have tracing"""
    def get_all_subclasses(cls):
        """Recursively get all subclasses of a class"""
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses
    
    # Get all Job subclasses (excluding our test classes)
    job_subclasses = {cls for cls in get_all_subclasses(Job)
                     if not cls.__module__.startswith('test_job_tracing')}
    
    # Check each subclass
    untraced_classes = []
    for cls in job_subclasses:
        if not _is_traced(cls.execute):
            untraced_classes.append(f"{cls.__module__}.{cls.__name__}")
    
    assert not untraced_classes, (
        f"Found Job subclasses without traced execute method: "
        f"{', '.join(untraced_classes)}\n"
        "All Job subclasses must have tracing on their execute method.\n"
        "This is required for proper monitoring of job execution.\n"
        "Please ensure these classes properly inherit from Job."
    )


def test_execute_no_trace_matches_original():
    """Test that executeNoTrace matches the original implementation"""
    class TestJob(Job):
        async def execute(self, task) -> Dict[str, Any]:
            return {"task": task, "result": "success"}
    
    job = TestJob("Test Job", "Test prompt", "test-model")
    
    # Get the source code of both methods
    execute_source = inspect.getsource(job.__class__.executeNoTrace)
    
    # The source code should be similar (ignoring decorators and whitespace)
    assert "async def" in execute_source
    assert "return {" in execute_source
    assert '"task": task' in execute_source
    assert '"result": "success"' in execute_source
