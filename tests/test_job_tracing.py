import inspect
from typing import Any, Dict

import pytest

from job import AbstractJob, Job, _is_traced
from utils.otel_wrapper import trace_function


class SimpleTestJob(AbstractJob):
    """A simple Job implementation for testing."""
    async def run(self, task) -> Dict[str, Any]:
        return {"task": task, "status": "complete"}


def test_job_execute_is_traced():
    """Test that AbstractJob's execute method is automatically traced"""
    job = SimpleTestJob("Test Job")
    assert isinstance(job, AbstractJob)
    assert _is_traced(job.__class__._execute)


def test_job_execute_no_trace_available():
    """Test that AbstractJob subclasses have access to untraced execute via executeNoTrace"""
    job = SimpleTestJob("Test Job")
    assert hasattr(job, 'executeNoTrace'), "Job should have executeNoTrace method"
    assert not _is_traced(job.__class__.executeNoTrace), "executeNoTrace should not be traced"


def test_job_subclass_gets_traced_execute():
    """Test that AbstractJob subclasses inherit the traced execute method"""
    class CustomJob(AbstractJob):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "success"}
    
    job = CustomJob("Test Job")
    assert _is_traced(job.__class__._execute)
    assert hasattr(job, 'executeNoTrace')
    assert not _is_traced(job.__class__.executeNoTrace)


def test_decorator_preserves_method_signature():
    """Test that the traced execute method preserves the original signature"""
    class TestJob(AbstractJob):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "complete"}
    
    # Get the signatures of the traced and untraced versions
    untraced_sig = inspect.signature(TestJob.executeNoTrace)
    traced_sig = inspect.signature(TestJob._execute)
    
    # Compare parameters and return annotation
    assert str(untraced_sig.parameters) == str(traced_sig.parameters), (
        "The traced execute method should preserve the parameter signature"
    )
    assert untraced_sig.return_annotation == traced_sig.return_annotation, (
        "The traced execute method should preserve the return type annotation"
    )


def test_job_factory_returns_traced_jobs():
    """Test that JobFactory returns properly traced Job instances"""
    from job import JobFactory

    # Test file-based job loading
    file_job = JobFactory.load_job({"type": "file", "params": {}})
    assert isinstance(file_job, AbstractJob)
    assert _is_traced(file_job.__class__._execute)
    assert hasattr(file_job, 'executeNoTrace')
    
    # Test datastore-based job loading
    datastore_job = JobFactory.load_job({"type": "datastore", "params": {}})
    assert isinstance(datastore_job, AbstractJob)
    assert _is_traced(datastore_job.__class__._execute)
    assert hasattr(datastore_job, 'executeNoTrace')


def test_existing_job_implementations():
    """Test that all existing Job implementations in the codebase have tracing"""
    def get_all_subclasses(cls):
        """Recursively get all subclasses of a class"""
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses
    
    # Get all AbstractJob subclasses (excluding our test classes)
    job_subclasses = {cls for cls in get_all_subclasses(AbstractJob)
                     if not cls.__module__.startswith('test_job_tracing')}
    
    # Check each subclass
    untraced_classes = []
    for cls in job_subclasses:
        if not _is_traced(cls._execute):
            untraced_classes.append(f"{cls.__module__}.{cls.__name__}")
    
    assert not untraced_classes, (
        f"Found Job subclasses without traced execute method: "
        f"{', '.join(untraced_classes)}\n"
        "All AbstractJob subclasses must have tracing on their execute method.\n"
        "This is required for proper monitoring of job execution."
    )


def test_execute_no_trace_matches_original():
    """Test that executeNoTrace matches the original implementation"""
    class TestJob(AbstractJob):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "result": "success"}
    
    job = TestJob("Test Job")
    
    # Get the source code of both methods
    execute_source = inspect.getsource(job.__class__.executeNoTrace)
    
    # The source code should contain key implementation details
    assert "async def" in execute_source
    assert "_execute(self, task)" in execute_source
    assert "self.has_all_dependencies()" in execute_source
    assert "self.run(task)" in execute_source
