"""
Tests for the DSL (Domain Specific Language) module of JobChain.

This test suite covers:
- Wrapping objects with the wrap/w function
- Parallel composition using | operator and parallel/p function
- Serial composition using >> operator and serial/s function
- Graph evaluation with GraphCreator.evaluate
- WrappingJob functionality
"""

import pytest

from jobchain.dsl import (Parallel, Serial, WrappingJob, evaluate, p, parallel,
                          s, serial, w, wrap)
from jobchain.job import JobABC


class TestWrapping:
    """Tests for the wrap/w function and WrappingJob class."""
    
    def test_wrap_regular_object(self):
        """Test wrapping a regular object."""
        obj = "test_object"
        wrapped = wrap(obj)
        assert isinstance(wrapped, WrappingJob)
        assert wrapped.wrapped_object == obj
    
    def test_wrap_job_object(self):
        """Test wrapping a JobABC object (should return the object unchanged)."""
        class TestJob(JobABC):
            async def run(self, task):
                return {"result": "test"}
        
        job = TestJob("test_job")
        wrapped = wrap(job)
        assert wrapped is job  # Should return the same object
    
    def test_w_alias(self):
        """Test that w is an alias for wrap."""
        obj = "test_object"
        wrapped1 = wrap(obj)
        wrapped2 = w(obj)
        assert isinstance(wrapped1, WrappingJob)
        assert isinstance(wrapped2, WrappingJob)
        assert wrapped1.wrapped_object == wrapped2.wrapped_object


class TestParallelComposition:
    """Tests for parallel composition using | operator and parallel/p function."""
    
    def test_parallel_operator(self):
        """Test parallel composition using | operator."""
        obj1 = "test1"
        obj2 = "test2"
        
        # Create parallel composition
        composition = wrap(obj1) | wrap(obj2)
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 2
        assert composition.components[0].wrapped_object == obj1
        assert composition.components[1].wrapped_object == obj2
    
    def test_parallel_function(self):
        """Test parallel composition using parallel function."""
        # Instead of passing a list, we need to pass individual objects
        obj1 = "test1"
        obj2 = "test2"
        obj3 = "test3"
        
        # Create parallel composition
        composition = parallel([obj1, obj2, obj3])
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 3
        objects = [obj1, obj2, obj3]
        for i, obj in enumerate(objects):
            assert composition.components[i].wrapped_object == obj
    
    def test_p_alias(self):
        """Test that p is an alias for parallel."""
        obj1 = "test1"
        obj2 = "test2"
        
        composition1 = parallel([obj1, obj2])
        composition2 = p([obj1, obj2])
        
        assert isinstance(composition1, Parallel)
        assert isinstance(composition2, Parallel)
        assert len(composition1.components) == len(composition2.components)
    
    def test_parallel_empty_list(self):
        """Test that parallel raises ValueError for empty list."""
        with pytest.raises(ValueError):
            parallel([])
    
    def test_parallel_single_item(self):
        """Test that parallel with a single item returns a wrapped item."""
        obj = "test"
        result = parallel([obj])
        assert isinstance(result, WrappingJob)
        assert result.wrapped_object == obj


class TestSerialComposition:
    """Tests for serial composition using >> operator and serial/s function."""
    
    def test_serial_operator(self):
        """Test serial composition using >> operator."""
        obj1 = "test1"
        obj2 = "test2"
        
        # Create serial composition
        composition = wrap(obj1) >> wrap(obj2)
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 2
        assert composition.components[0].wrapped_object == obj1
        assert composition.components[1].wrapped_object == obj2
    
    def test_serial_function(self):
        """Test serial composition using serial function."""
        obj1 = "test1"
        obj2 = "test2"
        obj3 = "test3"
        
        # Create serial composition
        composition = serial([obj1, obj2, obj3])
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 3
        objects = [obj1, obj2, obj3]
        for i, obj in enumerate(objects):
            assert composition.components[i].wrapped_object == obj
    
    def test_s_alias(self):
        """Test that s is an alias for serial."""
        obj1 = "test1"
        obj2 = "test2"
        
        composition1 = serial([obj1, obj2])
        composition2 = s([obj1, obj2])
        
        assert isinstance(composition1, Serial)
        assert isinstance(composition2, Serial)
        assert len(composition1.components) == len(composition2.components)
    
    def test_serial_empty_list(self):
        """Test that serial raises ValueError for empty list."""
        with pytest.raises(ValueError):
            serial([])
    
    def test_serial_single_item(self):
        """Test that serial with a single item returns a wrapped item."""
        obj = "test"
        result = serial([obj])
        assert isinstance(result, WrappingJob)
        assert result.wrapped_object == obj


class TestMixedComposition:
    """Tests for mixed serial and parallel compositions."""
    
    def test_mixed_operators(self):
        """Test mixed serial and parallel operators."""
        obj1 = "test1"
        obj2 = "test2"
        obj3 = "test3"
        
        # (obj1 >> obj2) | obj3
        composition1 = (wrap(obj1) >> wrap(obj2)) | wrap(obj3)
        assert isinstance(composition1, Parallel)
        assert len(composition1.components) == 2
        assert isinstance(composition1.components[0], Serial)
        
        # For the second test, we need to modify our approach
        # First create a serial composition
        serial_comp = wrap(obj2) >> wrap(obj3)
        # Then create a parallel composition with a wrapped object and the serial composition
        composition2 = wrap(obj1) | serial_comp
        # Verify it's a parallel composition with 2 components
        assert isinstance(composition2, Parallel)
        assert len(composition2.components) == 2
        # Verify first component is the wrapped object
        assert isinstance(composition2.components[0], WrappingJob)
        assert composition2.components[0].wrapped_object == obj1


class TestWrappingJob:
    """Tests for WrappingJob class."""
    
    @pytest.mark.asyncio
    async def test_wrapping_job_run(self):
        """Test that WrappingJob.run returns the string representation of the wrapped object."""
        obj = "test_object"
        job = WrappingJob(obj)
        
        result = await job.run({})
        assert result == str(obj)
    
    def test_wrapping_job_repr(self):
        """Test that WrappingJob.__repr__ returns the name."""
        obj = "test_object"
        job = WrappingJob(obj)
        
        assert repr(job) == job.name


@pytest.mark.asyncio
class TestGraphEvaluation:
    """Tests for graph evaluation."""
    
    async def test_evaluate_single_job(self):
        """Test evaluating a single job."""
        obj = "test_object"
        job = wrap(obj)
        
        result = await evaluate(job)
        assert result == str(obj)
    
    async def test_evaluate_parallel(self):
        """Test evaluating a parallel composition."""
        obj1 = "test1"
        obj2 = "test2"
        
        composition = wrap(obj1) | wrap(obj2)
        
        result = await evaluate(composition)
        assert "Executed in parallel" in result
        assert str(obj1) in result
        assert str(obj2) in result
    
    async def test_evaluate_serial(self):
        """Test evaluating a serial composition."""
        obj1 = "test1"
        obj2 = "test2"
        
        composition = wrap(obj1) >> wrap(obj2)
        
        result = await evaluate(composition)
        assert "Executed in series" in result
        assert str(obj1) in result
        assert str(obj2) in result
    
    async def test_evaluate_mixed(self):
        """Test evaluating a mixed composition."""
        obj1 = "test1"
        obj2 = "test2"
        obj3 = "test3"
        
        composition = (wrap(obj1) | wrap(obj2)) >> wrap(obj3)
        
        result = await evaluate(composition)
        assert "Executed in series" in result
        assert "Executed in parallel" in result
        assert str(obj1) in result
        assert str(obj2) in result
        assert str(obj3) in result


if __name__ == "__main__":
    pytest.main(["-v", "test_dsl.py"])
