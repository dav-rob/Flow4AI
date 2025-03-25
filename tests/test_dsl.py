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

from jobchain import jc_logging as logging
from jobchain.dsl import (Parallel, Serial, p, parallel, s,
                          serial, w, wrap)
from jobchain.jobs.wrapping_job import WrappingJob
from jobchain.job import JobABC
from tests.test_utils.graph_evaluation import evaluate

logger = logging.getLogger(__name__)


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
        assert wrapped.callable == mock_llm_completion
    
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
        assert wrapped1.callable == wrapped2.callable
        
    def test_wrap_named_callable_kwargs(self):
        """Test wrapping a callable with a name using kwargs syntax."""
        wrapped = wrap(extractor=mock_data_extraction)
        assert isinstance(wrapped, WrappingJob)
        assert wrapped.callable == mock_data_extraction
        assert wrapped.name == "extractor"
        
    def test_wrap_named_callable_dict(self):
        """Test wrapping a callable with a name using dict syntax."""
        wrapped = wrap({"formatter": mock_json_formatter})
        assert isinstance(wrapped, WrappingJob)
        assert wrapped.callable == mock_json_formatter
        assert wrapped.name == "formatter"
        
    def test_wrap_job_object_with_name(self):
        """Test wrapping a JobABC object with a name (should set name and return the object)."""
        job = LLMSummarizer()
        wrapped = wrap(custom_summarizer=job)
        assert wrapped is job  # Should return the same object
        assert wrapped.name == "custom_summarizer"  # But with updated name
        
        # Test dict syntax as well
        job2 = DataProcessor()
        wrapped2 = wrap({"data_proc": job2})
        assert wrapped2 is job2
        assert wrapped2.name == "data_proc"
        
    def test_wrap_composite_with_name(self):
        """Test wrapping Serial/Parallel objects with names (should return object unchanged)."""
        # Create Serial and Parallel objects
        serial_obj = serial(mock_llm_completion, mock_text_processing)
        parallel_obj = parallel(mock_data_extraction, mock_json_formatter)
        
        # Wrap them with names
        wrapped_serial = wrap(pipeline=serial_obj)
        wrapped_parallel = wrap({"processors": parallel_obj})
        
        # Should return the same objects
        assert wrapped_serial is serial_obj
        assert wrapped_parallel is parallel_obj
        
    def test_wrap_multiple_objects(self):
        """Test wrapping multiple objects at once."""
        # Wrap multiple objects using kwargs syntax
        wrapped = wrap(
            extractor=mock_data_extraction,
            formatter=mock_json_formatter,
            processor=mock_text_processing
        )
        
        # Result should be a dictionary with wrapped objects
        assert isinstance(wrapped, dict)
        assert len(wrapped) == 3
        assert isinstance(wrapped["extractor"], WrappingJob)
        assert isinstance(wrapped["formatter"], WrappingJob)
        assert isinstance(wrapped["processor"], WrappingJob)
        assert wrapped["extractor"].callable == mock_data_extraction
        assert wrapped["formatter"].callable == mock_json_formatter
        assert wrapped["processor"].callable == mock_text_processing
        assert wrapped["extractor"].name == "extractor"
        assert wrapped["formatter"].name == "formatter"
        assert wrapped["processor"].name == "processor"
        
    def test_wrap_multiple_objects_dict(self):
        """Test wrapping multiple objects using dictionary syntax."""
        # Create a mix of different object types
        job1 = LLMSummarizer()
        job2 = DataProcessor()
        serial_obj = serial(mock_llm_completion, mock_text_processing)
        
        # Wrap them all in a dictionary
        wrapped = wrap({
            "summarizer": job1,
            "data_processor": job2,
            "formatter": mock_json_formatter,
            "pipeline": serial_obj
        })
        
        # Check the results
        assert isinstance(wrapped, dict)
        assert len(wrapped) == 4
        
        # JobABC instances should be the same objects with names set
        assert wrapped["summarizer"] is job1
        assert wrapped["summarizer"].name == "summarizer"
        assert wrapped["data_processor"] is job2
        assert wrapped["data_processor"].name == "data_processor"
        
        # Callable should be wrapped
        assert isinstance(wrapped["formatter"], WrappingJob)
        assert wrapped["formatter"].callable == mock_json_formatter
        assert wrapped["formatter"].name == "formatter"
        
        # Serial object should be returned as is
        assert wrapped["pipeline"] is serial_obj
        
    def test_wrap_single_item_in_collection(self):
        """Test that wrapping a single item in a collection returns just that item."""
        # With kwargs syntax
        wrapped1 = wrap(processor=mock_text_processing)
        assert isinstance(wrapped1, WrappingJob)
        assert wrapped1.name == "processor"
        
        # With dict syntax
        wrapped2 = wrap({"extractor": mock_data_extraction})
        assert isinstance(wrapped2, WrappingJob)
        assert wrapped2.name == "extractor"


class TestParallelComposition:
    """Tests for parallel composition using | operator and parallel/p function."""
    
    def test_parallel_operator(self):
        """Test parallel composition using | operator with callables."""
        # Create parallel composition of two callables
        composition = wrap(mock_llm_completion) | wrap(mock_data_extraction)
        
        assert isinstance(composition, Parallel)
        assert len(composition.components) == 2
        assert composition.components[0].callable == mock_llm_completion
        assert composition.components[1].callable == mock_data_extraction
    
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
            assert composition.components[i].callable == func
    
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
        assert result.callable == mock_llm_completion
        
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
        assert composition.components[0].callable == mock_text_processing
        assert composition.components[1].callable == mock_json_formatter
    
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
            assert composition.components[i].callable == func
    
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
        assert result.callable == mock_llm_completion
        
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

@pytest.mark.asyncio
class TestGraphEvaluation:
    """Tests for graph evaluation with various job types."""
    
    async def test_evaluate_single_callable(self):
        """Test evaluating a single wrapped callable."""
        # Create a simple callable that returns a fixed value
        mock_callable = MagicMock(return_value="callable result")
        job = WrappingJob(mock_callable, name="test_callable")
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value={job.name: {}})
        
        result = await evaluate(job)
        assert result == "0) callable result"
    
    async def test_evaluate_single_job(self):
        """Test evaluating a custom JobABC subclass."""
        job = LLMSummarizer()
        
        result = await evaluate(job)
        logger.info(result)
        assert "summary" in result
    
    async def test_evaluate_parallel_callables(self):
        """Test evaluating a parallel composition of callables."""
        # Create mockable callables for testing
        mock_callable1 = MagicMock(return_value="result1")
        mock_callable2 = MagicMock(return_value="result2")
        
        job1 = WrappingJob(mock_callable1, name="callable1")
        job2 = WrappingJob(mock_callable2, name="callable2")
        
        # Set up context access to work in tests
        job1.get_task = MagicMock(return_value={job1.name: {}})
        job2.get_task = MagicMock(return_value={job2.name: {}})
        
        composition = job1 | job2
        
        result = await evaluate(composition)
        logger.info(result)
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
        job1.get_task = MagicMock(return_value={job1.name: {}})
        job2.get_task = MagicMock(return_value={job2.name: {}})
        
        composition = job1 >> job2
        
        result = await evaluate(composition)
        logger.info(result)
        assert "Executed in series" in result
        assert "result1" in result
        assert "result2" in result
    
    async def test_evaluate_mixed_job_types(self):
        """Test evaluating a mixed composition of JobABC subclasses and wrapped callables."""
        # Create a complex workflow: 
        # (LLM summarizer | wrapped callable) >> Data processor
        
        mock_callable = MagicMock(return_value="callable result")
        callable_job = WrappingJob(mock_callable, name="mock_callable")
        callable_job.get_task = MagicMock(return_value={callable_job.name: {}})
        
        llm_job = LLMSummarizer()
        data_job = DataProcessor()
        
        # Build the composition
        parallel_stage = llm_job | callable_job
        workflow = parallel_stage >> data_job
        
        result = await evaluate(workflow)
        logger.info(result)
        
        # Verify result structure
        assert "Executed in series" in result
        assert "Executed in parallel" in result
        assert "summary" in result
        assert "callable result" in result
        assert "processed_data" in result or "status" in result
        
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
        assert composition1.components[0].components[0].callable == mock_llm_completion
        assert composition1.components[0].components[1].callable == mock_json_formatter
        assert composition1.components[1].callable == mock_data_extraction
        
        # Another complex workflow:
        # Text processing | (Data extraction >> JSON formatting)
        serial_comp = wrap(mock_data_extraction) >> wrap(mock_json_formatter)
        text_processing_job = wrap(mock_text_processing)
        composition2 = text_processing_job | serial_comp
        
        assert isinstance(composition2, Parallel)
        assert len(composition2.components) == 2
        assert composition2.components[0].callable == mock_text_processing
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
        
    @pytest.mark.asyncio
    async def test_with_lambdas(self):
        """Test complex composition with lambdas, JobABC instances, and functions."""
        # Create lambda functions
        lambda1 = lambda x: f"Lambda1 processed: {x}"
        lambda2 = lambda x: f"Lambda2 processed: {x}"
        lambda3 = lambda x: {"lambda3_result": x}
        
        # Create JobABC instances
        llm_job = LLMSummarizer() #return {"summary": "This is a summary of the input text."}
        data_job = DataProcessor() # return {"processed_data": [1, 2, 3, 4, 5], "status": "success"}
        
        # Create a complex composition with lambdas, JobABC instances, and functions
        # (lambda1 | data_job) >> (lambda2 >> mock_text_processing) >> (llm_job | lambda3)
        lambda1_job = wrap(lambda1)
        lambda2_job = wrap(lambda2)
        lambda3_job = wrap(lambda3)
        text_proc_job = wrap(mock_text_processing) # return "Processed text output"
        
        first_stage = lambda1_job | data_job
        second_stage = lambda2_job >> text_proc_job
        third_stage = llm_job | lambda3_job
        
        composition = first_stage >> second_stage >> third_stage
        
        # Set up context access for the wrapped jobs with appropriate parameters
        lambda1_job.get_task = MagicMock(return_value={lambda1_job.name: {"fn.args": ["input_data1"]}})
        lambda2_job.get_task = MagicMock(return_value={lambda2_job.name: {"fn.args": ["input_data2"]}})
        lambda3_job.get_task = MagicMock(return_value={lambda3_job.name: {"fn.args": ["input_data3"]}})
        text_proc_job.get_task = MagicMock(return_value={}) # text_proc_job.name: {}
        
        # Execute the workflow
        result = await evaluate(composition)
        logger.info(result)
        
        # Verify the result contains expected components
        assert "Executed in series" in result
        assert "Executed in parallel" in result
        assert "Lambda1 processed" in result
        assert "Lambda2 processed" in result
        assert "{'lambda3_result': 'input_data3'}" in result
        assert "Processed text output" in result
        assert "This is a summary of the input text." in result
        
    @pytest.mark.asyncio
    async def test_combining_everything(self):
        """Test combining everything together in a complex graph structure.
        
        Based on the example: p(w("T1") >> w(1), "T2", 3) >> w(4) | w(s(5, "T3", w(6)))
        """
        # Create functions and JobABC instances to use in the graph
        fn1 = lambda x: f"Function 1: {x}"
        fn2 = lambda x: f"Function 2: {x}"
        fn3 = lambda x: {"result": f"Function 3 result with {x}"}
        fn4 = lambda x: f"Function 4: {x}"
        fn5 = lambda x: f"Function 5: {x}"
        fn6 = lambda x: f"Function 6: {x}"
        
        llm_job = LLMSummarizer("T2")
        data_job = DataProcessor("T3")
        
        # Create the complex graph structure
        # p(w("T1") >> w(1), "T2", 3) >> w(4) | w(s(5, "T3", w(6)))
        fn1_job = wrap(fn1)
        fn1_job.name = "T1"
        fn2_job = wrap(fn2)
        fn3_job = wrap(fn3)
        fn4_job = wrap(fn4)
        fn5_job = wrap(fn5)
        fn6_job = wrap(fn6)
        
        # Build the graph in parts
        part1 = fn1_job >> fn2_job
        part2 = parallel(part1, llm_job, fn3_job)
        part3 = part2 >> fn4_job
        part4 = serial(fn5_job, data_job, fn6_job)
        
        # Combine into final graph
        graph = part3 | wrap(part4)
        
        # Set up context access for all WrappingJob instances
        for job in [fn1_job, fn2_job, fn3_job, fn4_job, fn5_job, fn6_job]:
            job.get_task = MagicMock(return_value={job.name: {"fn.args": ["test_input"]}})
        
        # Execute the workflow
        result = await evaluate(graph)
        
        # Verify the result contains expected components
        assert "Executed in parallel" in result
        assert "Executed in series" in result
        
    @pytest.mark.asyncio
    async def test_precedence_graph(self):
        """Test creating a precedence graph based on the example:
        graph = w(1) >> ((p(5,4,3) >> 7 >> 9) | (w(2) >> 6 >> 8>> 10)) >> w(11)
        """
        # Create functions and JobABC instances to use in the graph
        fn1 = lambda x: f"Function 1: {x}"
        fn2 = lambda x: f"Function 2: {x}"
        fn3 = lambda x: f"Function 3: {x}"
        fn4 = lambda x: f"Function 4: {x}"
        fn5 = lambda x: f"Function 5: {x}"
        fn6 = lambda x: f"Function 6: {x}"
        fn7 = lambda x: f"Function 7: {x}"
        fn8 = lambda x: f"Function 8: {x}"
        fn9 = lambda x: f"Function 9: {x}"
        fn10 = lambda x: f"Function 10: {x}"
        fn11 = lambda x: f"Function 11: {x}"
        
        # Create the WrappingJob instances
        job1 = wrap(fn1)
        job2 = wrap(fn2)
        job3 = wrap(fn3)
        job4 = wrap(fn4)
        job5 = wrap(fn5)
        job6 = wrap(fn6)
        job7 = wrap(fn7)
        job8 = wrap(fn8)
        job9 = wrap(fn9)
        job10 = wrap(fn10)
        job11 = wrap(fn11)
        
        # Build the complex graph structure: w(1) >> ((p(5,4,3) >> 7 >> 9) | (w(2) >> 6 >> 8>> 10)) >> w(11)
        parallel_part1 = parallel(job5, job4, job3)
        serial_part1 = parallel_part1 >> job7 >> job9
        
        serial_part2 = job2 >> job6 >> job8 >> job10
        
        middle_part = serial_part1 | serial_part2
        
        # Complete graph
        graph = job1 >> middle_part >> job11
        
        # Set up context access for all WrappingJob instances
        for job in [job1, job2, job3, job4, job5, job6, job7, job8, job9, job10, job11]:
            job.get_task = MagicMock(return_value={job.name: {"fn.args": ["test_input"]}})
        
        # Execute the workflow
        result = await evaluate(graph)
        
        # Verify the result contains expected components
        assert "Executed in series" in result
        assert "Executed in parallel" in result


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
        job.get_task = MagicMock(return_value=task)
        
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
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the async callable was executed
        mock_async_callable.assert_called_once()
        assert result == "async result"
    
    @pytest.mark.asyncio
    async def test_wrapped_function_with_multiple_args(self):
        """Test wrapped function that accepts multiple positional arguments."""
        # Create a function that processes multiple arguments
        def process_multiple_args(a, b, c):
            return {"sum": a + b + c, "product": a * b * c}
        
        # Mock the function to verify calls
        mock_func = MagicMock(side_effect=process_multiple_args)
        
        # Create a WrappingJob with the function
        job = WrappingJob(mock_func, name="multi_arg_func")
        
        # Prepare task with positional arguments
        task = {"multi_arg_func": {"fn.args": [5, 7, 3]}}
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the function was called with correct arguments
        mock_func.assert_called_once_with(5, 7, 3)
        
        # Check the results
        assert result["sum"] == 15  # 5 + 7 + 3
        assert result["product"] == 105  # 5 * 7 * 3
    
    @pytest.mark.asyncio
    async def test_wrapped_function_with_custom_objects(self):
        """Test wrapped function that accepts custom object arguments."""
        # Define a custom class
        class CustomData:
            def __init__(self, value, name):
                self.value = value
                self.name = name
                
            def process(self):
                return self.value * 2
        
        # Create a function that works with custom objects
        def process_custom_objects(data_obj, multiplier):
            processed_value = data_obj.process() * multiplier
            return {
                "name": data_obj.name,
                "processed_value": processed_value
            }
        
        # Mock the function to verify calls
        mock_func = MagicMock(side_effect=process_custom_objects)
        
        # Create custom object instance
        custom_obj = CustomData(10, "test_object")
        
        # Create a WrappingJob with the function
        job = WrappingJob(mock_func, name="custom_obj_func")
        
        # Prepare task with custom object as argument
        task = {"custom_obj_func": {"fn.args": [custom_obj, 3]}}
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the function was called with correct arguments
        mock_func.assert_called_once_with(custom_obj, 3)
        
        # Check the results - custom object's process method returns 20 (10*2), then multiplied by 3
        assert result["name"] == "test_object"
        assert result["processed_value"] == 60  # (10*2) * 3
    
    @pytest.mark.asyncio
    async def test_wrapped_function_with_kwargs(self):
        """Test wrapped function that accepts keyword arguments."""
        # Create a function that processes keyword arguments
        def config_formatter(prefix="", **settings):
            formatted = {}
            for key, value in settings.items():
                formatted[f"{prefix}{key}"] = value
            return formatted
        
        # Mock the function to verify calls
        mock_func = MagicMock(side_effect=config_formatter)
        
        # Create a WrappingJob with the function
        job = WrappingJob(mock_func, name="config_formatter")
        
        # Prepare task with keyword arguments - two ways to provide kwargs
        task = {
            "config_formatter": {
                # Method 1: Using fn.kwargs dictionary
                "fn.kwargs": {
                    "prefix": "setting_", 
                    "color": "blue", 
                    "size": "large", 
                    "enabled": True
                }
            }
        }
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the function was called with correct keyword arguments
        mock_func.assert_called_once_with(
            prefix="setting_", 
            color="blue", 
            size="large", 
            enabled=True
        )
        
        # Check the results contain properly formatted settings
        assert result == {
            "setting_color": "blue",
            "setting_size": "large",
            "setting_enabled": True
        }
        
    @pytest.mark.asyncio
    async def test_wrapped_function_with_fn_prefix_kwargs(self):
        """Test wrapped function with kwargs using fn. prefix notation."""
        # Create a function that processes keyword arguments
        def config_processor(mode, timeout=30, debug=False):
            return {
                "config": {
                    "mode": mode,
                    "timeout": timeout,
                    "debug": debug
                }
            }
        
        # Mock the function to verify calls
        mock_func = MagicMock(side_effect=config_processor)
        
        # Create a WrappingJob with the function
        job = WrappingJob(mock_func, name="processor")
        
        # Prepare task with fn. prefix notation for kwargs
        task = {
            "processor": {
                # Method 2: Using fn. prefix for individual parameters
                "fn.mode": "production",
                "fn.timeout": 60,
                "fn.debug": True
            }
        }
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the function was called with correct keyword arguments
        mock_func.assert_called_once_with(
            mode="production", 
            timeout=60, 
            debug=True
        )
        
        # Check the results
        assert result["config"]["mode"] == "production"
        assert result["config"]["timeout"] == 60
        assert result["config"]["debug"] is True
    
    @pytest.mark.asyncio
    async def test_wrapped_lambda_with_multiple_args(self):
        """Test wrapped lambda function with multiple arguments."""
        # Create a lambda function that processes multiple arguments
        # Lambda that calculates statistics from a list of numbers
        stats_lambda = lambda numbers, calc_median=False, round_to=2: {
            "mean": round(sum(numbers) / len(numbers), round_to),
            "min": min(numbers),
            "max": max(numbers),
            "median": round(sorted(numbers)[len(numbers) // 2], round_to) if calc_median else None
        }
        
        # We need to use MagicMock with side_effect to verify lambda calls
        mock_func = MagicMock(side_effect=stats_lambda)
        
        # Create a WrappingJob with the lambda
        job = WrappingJob(mock_func, name="stats_calculator")
        
        # Prepare task with arguments for the lambda
        task = {
            "stats_calculator": {
                "fn.args": [[10, 15, 7, 22, 8, 11]],  # List of numbers as first arg
                "fn.kwargs": {
                    "calc_median": True,
                    "round_to": 1
                }
            }
        }
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the lambda was called with correct arguments
        mock_func.assert_called_once_with(
            [10, 15, 7, 22, 8, 11], 
            calc_median=True, 
            round_to=1
        )
        
        # Check the results
        assert result["mean"] == 12.2  # (10+15+7+22+8+11)/6 = 73/6 = 12.166... rounded to 12.2
        assert result["min"] == 7
        assert result["max"] == 22
        assert result["median"] == 11.0  # Median of [7, 8, 10, 11, 15, 22] is 11 (rounded to 11.0)
        
    @pytest.mark.asyncio
    async def test_wrapped_function_with_args_and_kwargs(self):
        """Test wrapped function with both positional args and keyword args."""
        # Create a function that handles both args and kwargs
        def format_document(template, *sections, meta=None, **attributes):
            # Create document with template, sections and attributes
            document = {
                "template": template,
                "sections": list(sections),
                "meta": meta or {},
            }
            # Add all attributes
            for key, value in attributes.items():
                document[key] = value
            return document
        
        # Mock the function to verify calls
        mock_func = MagicMock(side_effect=format_document)
        
        # Create a WrappingJob with the function
        job = WrappingJob(mock_func, name="doc_formatter")
        
        # Prepare task with both args and kwargs
        task = {
            "doc_formatter": {
                "fn.args": ["report", "Introduction", "Methods", "Results"],
                "fn.kwargs": {
                    "meta": {"version": "1.0", "author": "Test User"},
                    "title": "Annual Report",
                    "date": "2025-03-22",
                    "draft": True
                }
            }
        }
        
        # Set up context access to work in tests
        job.get_task = MagicMock(return_value=task)
        
        # Execute the job
        result = await job.run(task)
        
        # Verify the function was called with correct args and kwargs
        mock_func.assert_called_once_with(
            "report", "Introduction", "Methods", "Results",
            meta={"version": "1.0", "author": "Test User"},
            title="Annual Report",
            date="2025-03-22",
            draft=True
        )
        
        # Check the results
        assert result["template"] == "report"
        assert result["sections"] == ["Introduction", "Methods", "Results"]
        assert result["meta"] == {"version": "1.0", "author": "Test User"}
        assert result["title"] == "Annual Report"
        assert result["date"] == "2025-03-22"
        assert result["draft"] is True


class TestComplexDSLExpressions:
    """Tests for complex, highly nested DSL expressions."""
    
    @pytest.mark.asyncio
    async def test_complex_nested_dsl_with_mixed_params(self):
        """Test a highly nested, complex DSL expression with various parameter types."""
        # Define a series of functions with different parameter patterns
        
        # Simple function that takes multiple args
        def math_op(a, b, c):
            return {"result": a * b + c}
        
        # Function with custom object parameter
        class DataPoint:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                
            def distance(self):
                return (self.x**2 + self.y**2)**0.5
        
        def process_data_point(point, scaling_factor=1.0):
            return {"distance": point.distance() * scaling_factor}
        
        # Function with kwargs
        def config_builder(**settings):
            return {"config": settings}
        
        # Lambda with multiple args
        format_lambda = lambda text, prefix="", suffix="": f"{prefix}{text}{suffix}"
        
        # Function with args and kwargs
        def transform_data(data, *transforms, metadata=None, **options):
            result = data.copy() if isinstance(data, dict) else {"value": data}
            
            for transform in transforms:
                if transform == "uppercase" and isinstance(result.get("value"), str):
                    result["value"] = result["value"].upper()
                elif transform == "double":
                    for key in result:
                        if isinstance(result[key], (int, float)):
                            result[key] *= 2
            
            if metadata:
                result["metadata"] = metadata
                
            for key, value in options.items():
                result[f"option_{key}"] = value
                
            return result
        
        # Mock results for each function to avoid needing to evaluate them
        # This allows us to test the parameter passing mechanism directly
        math_op_result = "{'result': 38}" # 5 * 7 + 3 = 38
        process_data_point_result = "{'distance': 10.0}" # 5 * 2.0 = 10.0
        format_lambda_result = "<< test >>"
        config_builder_result = "{'config': {'mode': 'testing', 'debug': True}}"
        transform_data_result = "{'value': 'SAMPLE', 'score': 20, 'metadata': {'source': 'test'}, 'option_format': 'json', 'option_version': 2}"
        
        # Create a custom data point
        data_point = DataPoint(3, 4)  # 3-4-5 triangle, distance = 5
        
        # Create the complex task with parameters for all the jobs
        task = {
            # Parameters for math_op
            "math_op": {
                "fn.args": [5, 7, 3]
            },
            # Parameters for process_data_point
            "process_data_point": {
                "fn.args": [data_point],
                "fn.kwargs": {"scaling_factor": 2.0}
            },
            # Parameters for format_lambda
            "format_lambda": {
                "fn.args": ["test"],
                "fn.prefix": "<< ",
                "fn.suffix": " >>"
            },
            # Parameters for config_builder
            "config_builder": {
                "fn.kwargs": {
                    "mode": "testing",
                    "debug": True
                }
            },
            # Parameters for transform_data
            "transform_data": {
                "fn.args": [{"value": "sample", "score": 10}, "uppercase", "double"],
                "fn.kwargs": {
                    "metadata": {"source": "test"},
                    "format": "json",
                    "version": 2
                }
            }
        }
        
        # Create a complex nested DSL expression
        # This combines serial, parallel compositions with different job types and parameter patterns
        math_op_job = WrappingJob(math_op, name="math_op")
        process_data_point_job = WrappingJob(process_data_point, name="process_data_point")
        format_lambda_job = WrappingJob(format_lambda, name="format_lambda")
        config_builder_job = WrappingJob(config_builder, name="config_builder")
        transform_data_job = WrappingJob(transform_data, name="transform_data")
        
        # We don't mock the run methods because we want to test actual execution
        # Instead we'll verify the results match our expectations based on the provided parameters
        
        # Create the complex DSL graph with our DSL operators
        complex_dsl = (
            # Start with a simple function taking multiple args
            math_op_job>> 
            # Then parallel branch with custom object and lambda
            p(
                # Branch 1: Process with custom object
                process_data_point_job,
                # Branch 2: Lambda with format args
                format_lambda_job >> 
                # Branch 2a: Nested with kwargs
                config_builder_job
            ) >> 
            # Finally, combine with function taking args and kwargs
            transform_data_job
        )
        
        # Set up tasks for each job
        math_op_job.get_task = MagicMock(return_value=task)
        process_data_point_job.get_task = MagicMock(return_value=task)
        format_lambda_job.get_task = MagicMock(return_value=task)
        config_builder_job.get_task = MagicMock(return_value=task)
        transform_data_job.get_task = MagicMock(return_value=task)
        
        # Execute each job individually to verify parameter passing
        math_result = await math_op_job.run({})
        process_result = await process_data_point_job.run({})
        format_result = await format_lambda_job.run({})
        config_result = await config_builder_job.run({})
        transform_result = await transform_data_job.run({})
        
        # Verify that get_task was called for each job
        math_op_job.get_task.assert_called()
        process_data_point_job.get_task.assert_called()
        format_lambda_job.get_task.assert_called()
        config_builder_job.get_task.assert_called()
        transform_data_job.get_task.assert_called()
        
        # Verify each function processed its parameters correctly
        # Check math_op result: should be 5 * 7 + 3 = 38
        assert math_result == {"result": 38}
        
        # Check process_data_point result: 5 (distance) * 2.0 (scaling_factor) = 10.0
        assert process_result == {"distance": 10.0}
        
        # Check format_lambda result: "<< test >>"
        assert format_result == "<< test >>"
        
        # Check config_builder result
        assert config_result == {"config": {"mode": "testing", "debug": True}}
        
        # Verify transform_data result - this shows the parameter handling for args and kwargs
        assert "value" in transform_result
        assert transform_result["value"] == "SAMPLE"  # Uppercase transform
        assert transform_result["score"] == 20  # Double transform
        assert transform_result["metadata"] == {"source": "test"}
        assert transform_result["option_format"] == "json"
        assert transform_result["option_version"] == 2
        
        # Now evaluate the full complex DSL graph
        # This tests that parameters are correctly passed through the entire graph
        # Use the built-in evaluate function to test the graph execution
        result_string = await evaluate(complex_dsl)
        logger.info(f"\n {result_string}")
        
        # Since evaluate returns a string representation, we just verify it completed
        # The individual tests above already verified the parameter handling works correctly
        assert result_string is not None
        assert isinstance(result_string, str)
        assert "Executed in parallel" in result_string
        assert "Executed in series" in result_string
        assert math_op_result in result_string
        assert process_data_point_result in result_string
        assert format_lambda_result in result_string
        assert config_builder_result in result_string
        assert transform_data_result in result_string





if __name__ == "__main__":
    pytest.main(["-v", "test_dsl.py"])
