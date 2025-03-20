"""
Tests for the DSL (Domain Specific Language) module of JobChain.

This test suite covers:
- Wrapping callables with the wrap/w function
- Parallel composition using | operator and parallel/p function
- Serial composition using >> operator and serial/s function
- Graph evaluation with GraphCreator.evaluate
- WrappingJob functionality with mock LLM and data processing functions
- Integration with custom JobABC subclasses
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from jobchain.dsl import (Parallel, Serial, WrappingJob, evaluate, p, parallel,
                          s, serial, w, wrap)
from jobchain.job import JobABC


# Define mock functions for testing
def mock_llm_completion() -> str:
    """Mock LLM completion function that returns a fixed response."""
    return "This is a response from the LLM model."

def mock_data_extraction() -> dict:
    """Mock data extraction function that returns structured data."""
    return {"entities": ["Apple", "Google", "Microsoft"], "sentiment": "positive"}

def mock_text_processing() -> str:
    """Mock text processing function that transforms text."""
    return "Processed text output"

def mock_json_formatter() -> str:
    """Mock JSON formatter function that formats data as JSON."""
    return json.dumps({"formatted": True, "timestamp": "2025-03-19"})

# Custom JobABC subclass implementations
class LLMSummarizer(JobABC):
    """A custom JobABC implementation that simulates summarizing text."""
    
    def __init__(self, name="LLMSummarizer"):
        super().__init__(name)
    
    async def run(self, task):
        return {"summary": "This is a summary of the input text."}

class DataProcessor(JobABC):
    """A custom JobABC implementation that processes data."""
    
    def __init__(self, name="DataProcessor"):
        super().__init__(name)
    
    async def run(self, task):
        return {"processed_data": [1, 2, 3, 4, 5], "status": "success"}

class TestWrapping:
    """Tests for the wrap/w function and WrappingJob class."""
    
    def test_wrap_callable(self):
        """Test wrapping a callable object."""
        wrapped = wrap(mock_llm_completion)
        assert isinstance(wrapped, WrappingJob)
        assert wrapped.wrapped_obj == mock_llm_completion
    
    def test_wrap_job_object(self):
        """Test wrapping a JobABC object (should return the object unchanged)."""
        job = LLMSummarizer("test_summarizer")
        wrapped = wrap(job)
        assert wrapped is job  # Should return the same object
    
    def test_w_alias(self):
        """Test that w is an alias for wrap."""
        wrapped1 = wrap(mock_data_extraction)
        wrapped2 = w(mock_data_extraction)
        assert isinstance(wrapped1, WrappingJob)
        assert isinstance(wrapped2, WrappingJob)
        assert wrapped1.wrapped_obj == wrapped2.wrapped_obj


class TestParallelComposition:
    """Tests for parallel composition using | operator and parallel/p function."""
    
    def test_parallel_operator(self):
        """Test parallel composition using | operator with callables."""
        # Create parallel composition of two callables
        composition = wrap(mock_llm_completion) | wrap(mock_data_extraction)
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 2
        assert composition.components[0].wrapped_obj == mock_llm_completion
        assert composition.components[1].wrapped_obj == mock_data_extraction
    
    def test_parallel_with_job_objects(self):
        """Test parallel composition with JobABC objects."""
        # Create instances of custom JobABC subclasses
        llm_job = LLMSummarizer()
        data_job = DataProcessor()
        
        # Create parallel composition
        composition = llm_job | data_job
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 2
        assert composition.components[0] is llm_job
        assert composition.components[1] is data_job
    
    def test_parallel_function(self):
        """Test parallel composition using parallel function."""
        # Create parallel composition with three callables
        composition = parallel(mock_llm_completion, mock_data_extraction, mock_text_processing)
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 3
        callables = [mock_llm_completion, mock_data_extraction, mock_text_processing]
        for i, func in enumerate(callables):
            assert composition.components[i].wrapped_obj == func
    
    def test_p_alias(self):
        """Test that p is an alias for parallel."""
        funcs = [mock_llm_completion, mock_data_extraction]
        
        composition1 = parallel(funcs)
        composition2 = p(funcs)
        
        assert isinstance(composition1, Parallel)
        assert isinstance(composition2, Parallel)
        assert len(composition1.components) == len(composition2.components)
    
    def test_parallel_empty_list(self):
        """Test that parallel raises ValueError for empty list."""
        with pytest.raises(ValueError):
            parallel([])
    
    def test_parallel_single_item(self):
        """Test that parallel with a single item returns a wrapped item."""
        result = parallel([mock_llm_completion])
        assert isinstance(result, WrappingJob)
        assert result.wrapped_obj == mock_llm_completion
        
    def test_parallel_mixed_components(self):
        """Test parallel composition with a mix of JobABC subclasses and wrapped callables."""
        llm_job = LLMSummarizer()
        wrapped_func = wrap(mock_data_extraction)
        
        composition = llm_job | wrapped_func
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 2
        assert composition.components[0] is llm_job
        assert composition.components[1] is wrapped_func


class TestSerialComposition:
    """Tests for serial composition using >> operator and serial/s function."""
    
    def test_serial_operator(self):
        """Test serial composition using >> operator with callables."""
        # Create a serial pipeline that simulates text extraction followed by formatting
        composition = wrap(mock_text_processing) >> wrap(mock_json_formatter)
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 2
        assert composition.components[0].wrapped_obj == mock_text_processing
        assert composition.components[1].wrapped_obj == mock_json_formatter
    
    def test_serial_with_job_objects(self):
        """Test serial composition with JobABC objects."""
        # Create a pipeline that first summarizes and then processes data
        llm_job = LLMSummarizer()
        data_job = DataProcessor()
        
        # Create serial composition
        composition = llm_job >> data_job
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 2
        assert composition.components[0] is llm_job
        assert composition.components[1] is data_job
    
    def test_serial_function(self):
        """Test serial composition using serial function."""
        # Create a three-stage pipeline: extraction -> processing -> formatting
        composition = serial(mock_data_extraction, mock_text_processing, mock_json_formatter)
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 3
        funcs = [mock_data_extraction, mock_text_processing, mock_json_formatter]
        for i, func in enumerate(funcs):
            assert composition.components[i].wrapped_obj == func
    
    def test_s_alias(self):
        """Test that s is an alias for serial."""
        funcs = [mock_llm_completion, mock_json_formatter]
        
        composition1 = serial(funcs)
        composition2 = s(funcs)
        
        assert isinstance(composition1, Serial)
        assert isinstance(composition2, Serial)
        assert len(composition1.components) == len(composition2.components)
    
    def test_serial_empty_list(self):
        """Test that serial raises ValueError for empty list."""
        with pytest.raises(ValueError):
            serial([])
    
    def test_serial_single_item(self):
        """Test that serial with a single item returns a wrapped item."""
        result = serial(mock_llm_completion)
        assert isinstance(result, WrappingJob)
        assert result.wrapped_obj == mock_llm_completion
        
    def test_serial_mixed_components(self):
        """Test serial composition with a mix of JobABC subclasses and wrapped callables."""
        # Create a pipeline: wrapped callable -> JobABC subclass
        wrapped_func = wrap(mock_llm_completion)
        data_job = DataProcessor()
        
        composition = wrapped_func >> data_job
        
        assert isinstance(composition, Serial)
        assert len(composition.components) == 2
        assert composition.components[0] is wrapped_func
        assert composition.components[1] is data_job


class TestMixedComposition:
    """Tests for mixed serial and parallel compositions."""
    
    def test_mixed_operators(self):
        """Test mixed serial and parallel operators with callables."""
        # Create a complex workflow:
        # (LLM completion >> JSON formatting) | Data extraction
        serial_part = wrap(mock_llm_completion) >> wrap(mock_json_formatter)
        data_extraction_job = wrap(mock_data_extraction)
        composition1 = serial_part | data_extraction_job
        
        assert isinstance(composition1, Parallel)
        assert len(composition1.components) == 2
        assert isinstance(composition1.components[0], Serial)
        assert composition1.components[0].components[0].wrapped_obj == mock_llm_completion
        assert composition1.components[0].components[1].wrapped_obj == mock_json_formatter
        assert composition1.components[1].wrapped_obj == mock_data_extraction
        
        # Another complex workflow:
        # Text processing | (Data extraction >> JSON formatting)
        serial_comp = wrap(mock_data_extraction) >> wrap(mock_json_formatter)
        text_processing_job = wrap(mock_text_processing)
        composition2 = text_processing_job | serial_comp
        
        assert isinstance(composition2, Parallel)
        assert len(composition2.components) == 2
        assert composition2.components[0].wrapped_obj == mock_text_processing
        assert isinstance(composition2.components[1], Serial)
    
    def test_complex_llm_workflow(self):
        """Test a complex LLM and data processing workflow."""
        # Create a workflow that processes data in parallel and then feeds to an LLM
        # (Data extraction | Text processing) >> LLM summarizer
        
        parallel_processing = wrap(mock_data_extraction) | wrap(mock_text_processing)
        llm_summarizer = LLMSummarizer()
        
        workflow = parallel_processing >> llm_summarizer
        
        assert isinstance(workflow, Serial)
        assert len(workflow.components) == 2
        assert isinstance(workflow.components[0], Parallel)
        assert workflow.components[1] is llm_summarizer
        
    def test_mixed_job_types(self):
        """Test mixing custom JobABC subclasses with wrapped callables."""
        # Create a complex workflow with both custom jobs and wrapped callables
        # (LLM summarizer | Data processor) >> JSON formatter
        
        parallel_jobs = LLMSummarizer() | DataProcessor()
        formatter = wrap(mock_json_formatter)
        
        workflow = parallel_jobs >> formatter
        
        assert isinstance(workflow, Serial)
        assert len(workflow.components) == 2
        assert isinstance(workflow.components[0], Parallel)
        assert isinstance(workflow.components[0].components[0], LLMSummarizer)
        assert isinstance(workflow.components[0].components[1], DataProcessor)
        assert workflow.components[1] is formatter


class TestWrappingJob:
    """Tests for WrappingJob class with callable objects."""
    
    @pytest.mark.asyncio
    async def test_wrapping_job_run_with_callable(self):
        """Test that WrappingJob.run executes the callable and returns its result."""
        # Create a simple callable for testing
        mock_callable = MagicMock(return_value="callable result")
        
        # Create a WrappingJob with the callable
        job = WrappingJob(mock_callable, name="test_callable")
        
        # Prepare the task with the necessary structure
        task = {job.name: {}}
        
        # Set up context access to work in tests
        job.get_context = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the callable was executed
        mock_callable.assert_called_once()
        assert result == "callable result"
    
    @pytest.mark.asyncio
    async def test_wrapping_job_run_with_async_callable(self):
        """Test that WrappingJob.run works with async callables."""
        # Create a mock async callable
        mock_async_callable = AsyncMock(return_value="async result")
        
        # Create a WrappingJob with the async callable
        job = WrappingJob(mock_async_callable, name="test_async")
        
        # Prepare the task with necessary structure
        task = {job.name: {}}
        
        # Set up context access to work in tests
        job.get_context = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the async callable was executed
        mock_async_callable.assert_called_once()
        assert result == "async result"


@pytest.mark.asyncio
class TestGraphEvaluation:
    """Tests for graph evaluation with various job types."""
    
    async def test_evaluate_single_callable(self):
        """Test evaluating a single wrapped callable."""
        # Create a simple callable that returns a fixed value
        mock_callable = MagicMock(return_value="callable result")
        job = WrappingJob(mock_callable, name="test_callable")
        
        # Set up context access to work in tests
        job.get_context = MagicMock(return_value={job.name: {}})
        
        result = await evaluate(job)
        assert result == "callable result"
    
    async def test_evaluate_single_job(self):
        """Test evaluating a custom JobABC subclass."""
        job = LLMSummarizer()
        
        result = await evaluate(job)
        assert "summary" in result
    
    async def test_evaluate_parallel_callables(self):
        """Test evaluating a parallel composition of callables."""
        # Create mockable callables for testing
        mock_callable1 = MagicMock(return_value="result1")
        mock_callable2 = MagicMock(return_value="result2")
        
        job1 = WrappingJob(mock_callable1, name="callable1")
        job2 = WrappingJob(mock_callable2, name="callable2")
        
        # Set up context access to work in tests
        job1.get_context = MagicMock(return_value={job1.name: {}})
        job2.get_context = MagicMock(return_value={job2.name: {}})
        
        composition = job1 | job2
        
        result = await evaluate(composition)
        assert "Executed in parallel" in result
        assert "result1" in result
        assert "result2" in result
    
    async def test_evaluate_serial_callables(self):
        """Test evaluating a serial composition of callables."""
        # Create mockable callables for testing
        mock_callable1 = MagicMock(return_value="result1")
        mock_callable2 = MagicMock(return_value="result2")
        
        job1 = WrappingJob(mock_callable1, name="callable1")
        job2 = WrappingJob(mock_callable2, name="callable2")
        
        # Set up context access to work in tests
        job1.get_context = MagicMock(return_value={job1.name: {}})
        job2.get_context = MagicMock(return_value={job2.name: {}})
        
        composition = job1 >> job2
        
        result = await evaluate(composition)
        assert "Executed in series" in result
        assert "result1" in result
        assert "result2" in result
    
    async def test_evaluate_mixed_job_types(self):
        """Test evaluating a mixed composition of JobABC subclasses and wrapped callables."""
        # Create a complex workflow: 
        # (LLM summarizer | wrapped callable) >> Data processor
        
        mock_callable = MagicMock(return_value="callable result")
        callable_job = WrappingJob(mock_callable, name="mock_callable")
        callable_job.get_context = MagicMock(return_value={callable_job.name: {}})
        
        llm_job = LLMSummarizer()
        data_job = DataProcessor()
        
        # Build the composition
        parallel_stage = llm_job | callable_job
        workflow = parallel_stage >> data_job
        
        result = await evaluate(workflow)
        
        # Verify result structure
        assert "Executed in series" in result
        assert "Executed in parallel" in result
        assert "summary" in result
        assert "callable result" in result
        assert "processed_data" in result or "status" in result


if __name__ == "__main__":
    pytest.main(["-v", "test_dsl.py"])
