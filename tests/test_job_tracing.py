import inspect
from typing import Any, Dict

from job import JobABC, _has_own_traced_execute, _is_traced


class Level1Job(JobABC):
    """First level in the inheritance hierarchy."""
    async def run(self, task) -> Dict[str, Any]:
        return {"task": task, "level": 1}


class Level2Job(Level1Job):
    """Second level in the inheritance hierarchy."""
    async def run(self, task) -> Dict[str, Any]:
        return {"task": task, "level": 2}


class Level3Job(Level2Job):
    """Third level in the inheritance hierarchy."""
    async def run(self, task) -> Dict[str, Any]:
        return {"task": task, "level": 3}


def test_deep_hierarchy_tracing():
    """Test that only JobABC._execute is traced, not its subclasses."""
    # Create instances of each level
    level1_job = Level1Job("Level 1")
    level2_job = Level2Job("Level 2")
    level3_job = Level3Job("Level 3")

    # Count how many classes have their own traced _execute
    def count_own_traced_execute(job):
        count = 0
        cls = job.__class__
        while cls != object:
            if _has_own_traced_execute(cls):
                count += 1
            cls = cls.__base__
        return count

    # Each instance should only have one class with its own traced _execute
    # (JobABC)
    assert count_own_traced_execute(level1_job) == 1, "Should only have one class with own traced _execute"
    assert count_own_traced_execute(level2_job) == 1, "Should only have one class with own traced _execute"
    assert count_own_traced_execute(level3_job) == 1, "Should only have one class with own traced _execute"


class SimpleTestJob(JobABC):
    """A simple Job implementation for testing."""
    async def run(self, task) -> Dict[str, Any]:
        return {"task": task, "status": "complete"}


def test_abstractjob_execute_is_traced():
    """Test that JobABC's execute method is traced"""
    # Create a test job instance
    job = SimpleTestJob("Test Job")
    
    # Get the actual JobABC class
    abstract_job_cls = JobABC
    
    # Verify JobABC's _execute is traced
    assert _has_own_traced_execute(abstract_job_cls), "JobABC should have its own traced _execute"
    
    # Verify the subclass doesn't have its own traced _execute
    assert not _has_own_traced_execute(job.__class__), "Subclass should not have its own traced _execute"


def test_job_execute_no_trace_available():
    """Test that JobABC subclasses have access to untraced execute via executeNoTrace"""
    job = SimpleTestJob("Test Job")
    assert hasattr(job, 'executeNoTrace'), "Job should have executeNoTrace method"
    assert not _is_traced(job.__class__.executeNoTrace), "executeNoTrace should not be traced"


def test_subclass_execute_not_traced():
    """Test that JobABC subclasses do not have their own traced execute methods"""
    class CustomJob(JobABC):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "success"}
    
    job = CustomJob("Test Job")
    assert not _has_own_traced_execute(job.__class__), "Subclass should not have its own traced _execute"
    assert hasattr(job, 'executeNoTrace'), "Should still have executeNoTrace method"


def test_decorator_preserves_method_signature():
    """Test that the traced execute method preserves the original signature"""
    class TestJob(JobABC):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "status": "complete"}
    
    # Get the signatures of the traced and untraced versions
    untraced_sig = inspect.signature(TestJob.executeNoTrace)
    traced_sig = inspect.signature(JobABC._execute)
    
    # Compare parameters and return annotation
    assert str(untraced_sig.parameters) == str(traced_sig.parameters), (
        "The traced execute method should preserve the parameter signature"
    )
    assert untraced_sig.return_annotation == traced_sig.return_annotation, (
        "The traced execute method should preserve the return type annotation"
    )


def test_job_factory_returns_untraced_jobs():
    """Test that JobFactory returns properly untraced Job instances"""
    from job import JobFactory

    # Test file-based job loading
    file_job = JobFactory.load_job({"type": "file", "params": {}})
    assert isinstance(file_job, JobABC)
    assert not _has_own_traced_execute(file_job.__class__), "Factory-created jobs should not have their own traced _execute"
    assert hasattr(file_job, 'executeNoTrace')
    
    # Test datastore-based job loading
    datastore_job = JobFactory.load_job({"type": "datastore", "params": {}})
    assert isinstance(datastore_job, JobABC)
    assert not _has_own_traced_execute(datastore_job.__class__), "Factory-created jobs should not have their own traced _execute"
    assert hasattr(datastore_job, 'executeNoTrace')


def test_job_implementations_not_traced():
    """Test that Job implementations do not have their own traced execute methods"""
    def get_all_subclasses(cls):
        """Recursively get all subclasses of a class"""
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_all_subclasses(subclass))
        return subclasses
    
    # Get all JobABC subclasses (excluding our test classes)
    job_subclasses = {cls for cls in get_all_subclasses(JobABC)
                     if not cls.__module__.startswith('test_job_tracing')}
    
    # Check each subclass
    traced_classes = []
    for cls in job_subclasses:
        if _has_own_traced_execute(cls):
            traced_classes.append(f"{cls.__module__}.{cls.__name__}")
    
    assert not traced_classes, (
        f"Found Job subclasses with their own traced execute method: "
        f"{', '.join(traced_classes)}\n"
        "Job subclasses should not have their own traced execute method.\n"
        "Only JobABC should have tracing."
    )


def test_execute_no_trace_matches_original():
    """Test that executeNoTrace matches the original implementation"""
    class TestJob(JobABC):
        async def run(self, task) -> Dict[str, Any]:
            return {"task": task, "result": "success"}
    
    job = TestJob("Test Job")
    
    # Get the source code of both methods
    execute_source = inspect.getsource(job.__class__.executeNoTrace)
    
    # The source code should contain key implementation details
    assert "async def" in execute_source
    assert "_execute(self, task" in execute_source  # More flexible check that works with type hints
    assert "self.has_finished()" in execute_source
    assert "self.do_finishing_actions()" in execute_source
    assert "self.do_intermediate_actions()" in execute_source
