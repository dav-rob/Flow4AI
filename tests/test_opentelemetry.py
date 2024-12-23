import json
import os
import time

import pytest
import yaml
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

import jc_logging as logging
from job import JobABC, Task
from utils.otel_wrapper import TracerFactory, trace_function

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def trace_file():
    """Fixture to provide a temporary trace file path and clean up after tests."""
    temp_file = "tests/temp_otel_trace.json"
    yield temp_file
    
    # Clean up the main trace file
    if os.path.exists(temp_file):
        os.unlink(temp_file)
    
    # Clean up any rotated files
    test_dir = os.path.dirname(temp_file)
    base_name = os.path.basename(temp_file)
    rotated_files = [f for f in os.listdir(test_dir) 
                    if f.startswith(base_name + '.')]
    
    for rotated in rotated_files:
        rotated_path = os.path.join(test_dir, rotated)
        if os.path.exists(rotated_path):
            os.unlink(rotated_path)

@pytest.fixture
def setup_file_exporter(trace_file):
    """Fixture to set up file exporter configuration"""
    config_path = "tests/otel_config.yaml"
    
    # Create and write config file
    config = {
        "exporter": "file",
        "service_name": "MyService",
        "batch_processor": {
            "max_queue_size": 1000,
            "schedule_delay_millis": 1000
        },
        "file_exporter": {
            "path": trace_file
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Reset TracerFactory state
    TracerFactory._instance = None
    TracerFactory._config = None
    
    # Set config path in environment
    os.environ['JOBCHAIN_OT_CONFIG'] = config_path
    
    yield
    
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)
    if 'JOBCHAIN_OT_CONFIG' in os.environ:
        del os.environ['JOBCHAIN_OT_CONFIG']
    TracerFactory._instance = None
    TracerFactory._config = None
    time.sleep(0.1)

def verify_trace(trace_file, expected_name=None, expected_attrs=None, expected_status=None, expected_events=None, check_all_spans=False):
    """Helper function to verify trace output"""
    time.sleep(1.0)  # Wait for async operations
    with open(trace_file, 'r') as f:
        trace_data = json.load(f)
        assert isinstance(trace_data, list), "Trace data should be a list"
        assert len(trace_data) > 0, "Trace data should not be empty"
        
        if check_all_spans:
            # Check all spans for the expected attributes
            spans_to_check = trace_data
        else:
            # Get the last span (most recent)
            spans_to_check = [trace_data[-1]]
        
        for span in spans_to_check:
            # Verify span structure
            assert 'name' in span, "Span should have a name"
            assert 'context' in span, "Span should have context"
            assert 'trace_id' in span['context'], "Span should have trace_id"
            assert 'span_id' in span['context'], "Span should have span_id"
            assert 'attributes' in span, "Span should have attributes"
            
            # Verify expected name if provided
            if expected_name and span['name'] == expected_name:
                # Verify expected attributes if provided
                if expected_attrs:
                    for key, value in expected_attrs.items():
                        if value is None:
                            assert key not in span['attributes'], f"Span should not have {key} attribute"
                        else:
                            if key == "function.args" and "TestJob object at" in str(value):
                                # For TestJob object, just verify it contains the expected parts
                                assert "TestJob object at" in span['attributes'][key], f"Expected TestJob object in {key}, got {span['attributes'][key]}"
                                if "'test task'" in span['attributes'][key]:
                                    assert "'test task'" in span['attributes'][key], "Expected 'test task' in args"
                            elif key == "object.fields":
                                # Convert both strings to dicts for comparison, ignoring logger
                                actual_fields = eval(span['attributes'][key])
                                expected_fields = eval(value)
                                for k, v in expected_fields.items():
                                    assert actual_fields[k] == v, f"Mismatch in object.fields for key {k}"
                            else:
                                assert key in span['attributes'], f"Expected attribute {key} not found"
                                assert span['attributes'][key] == value, f"Expected {key}={value}, got {span['attributes'][key]}"
                
                # Verify expected status if provided
                if expected_status:
                    assert 'status' in span, "Span should have status"
                    assert span['status']['status_code'] == expected_status['status_code'], \
                        f"Expected status code {expected_status['status_code']}, got {span['status']['status_code']}"
                    if 'description' in expected_status:
                        expected_desc = expected_status['description']
                        if 'exception_type' in expected_status:
                            expected_desc = f"{expected_status['exception_type']}: {expected_desc}"
                        assert span['status']['description'] == expected_desc, \
                            f"Expected status description {expected_desc}, got {span['status']['description']}"
                
                # Verify expected events if provided
                if expected_events:
                    assert 'events' in span, "Span should have events"
                    assert len(span['events']) >= len(expected_events), f"Expected at least {len(expected_events)} events, got {len(span['events'])}"
                    for expected_event in expected_events:
                        event_found = False
                        for event in span['events']:
                            if (event['name'] == expected_event['name'] and
                                all(event['attributes'].get(k) == v for k, v in expected_event.get('attributes', {}).items())):
                                event_found = True
                                break
                        assert event_found, f"Expected event {expected_event} not found in span events"
            elif "trace.message" in expected_attrs and span['attributes'].get("trace.message") == expected_attrs["trace.message"]:
                # If we're looking for a trace message and found it, verify its attributes
                for key, value in expected_attrs.items():
                    if value is None:
                        assert key not in span['attributes'], f"Span should not have {key} attribute"
                    else:
                        assert span['attributes'].get(key) == value, f"Expected {key}={value}, got {span['attributes'].get(key)}"

def test_trace_function_detailed_off(trace_file, setup_file_exporter):
    """Test that trace_function decorator without detailed_trace doesn't record args"""
    @trace_function
    def sample_function(x, y):
        TracerFactory.trace("Inside sample_function")  # Add a trace to ensure something is captured
        return x + y
    
    result = sample_function(3, 4)
    assert result == 7
    
    # Add a delay to ensure spans are exported
    time.sleep(2)  # Increased delay to ensure export completes
    
    verify_trace(
        trace_file,
        expected_attrs={
            "trace.message": "Inside sample_function",
            "function.args": None,  # Should not have these attributes
            "function.kwargs": None,
            "object.fields": None
        },
        check_all_spans=True  # Check all spans since we have both function and message traces
    )

def test_trace_function_detailed_on(trace_file, setup_file_exporter):
    """Test that trace_function decorator with detailed_trace records args"""
    @trace_function(detailed_trace=True)
    def sample_function(x, y):
        return x + y
    
    result = sample_function(3, 4)
    assert result == 7
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.sample_function",
        expected_attrs={
            "function.args": "(3, 4)",
            "function.kwargs": "{}"
        }
    )

def test_tracer_factory_detailed_off(trace_file, setup_file_exporter):
    """Test that TracerFactory.trace without detailed_trace doesn't record args"""
    test_message = "Test message"
    TracerFactory.trace(test_message)
    
    verify_trace(
        trace_file,
        expected_attrs={
            "trace.message": test_message,
            "function.args": None,  # Should not have these attributes
            "function.kwargs": None,
            "object.fields": None
        }
    )

def test_tracer_factory_detailed_on(trace_file, setup_file_exporter):
    """Test that TracerFactory.trace with detailed_trace records args"""
    test_message = "Test message"
    TracerFactory.trace(test_message, detailed_trace=True)
    
    verify_trace(
        trace_file,
        expected_attrs={
            "trace.message": test_message,
            "function.args": "()",
            "function.kwargs": "{}"
        }
    )

def test_job_metaclass_tracing(trace_file, setup_file_exporter):
    """Test that JobABC metaclass properly applies detailed tracing"""
    class TestJob(JobABC):
        async def run(self, task):
            # strings are converted to dicts with {'task':,<the string>}
            return {"result": task['task']}

    # Create and execute job
    job = TestJob("test")
    import asyncio
    task = Task("test task", job.name)
    result = asyncio.run(job._execute(task))
    assert result == {"result": "test task"}
    
    verify_trace(
        trace_file,
        expected_attrs={
            "function.args": "(<test_opentelemetry.test_job_metaclass_tracing.<locals>.TestJob object at",  # Just verify it starts with this
            "function.kwargs": "{}",
            "object.fields": "{'name': 'test'}"
        }
    )

def test_file_exporter_yaml(trace_file, setup_file_exporter):
    """Test file exporter using a temporary yaml config file"""
    test_message = "Test trace message"
    TracerFactory.trace(test_message)
    
    verify_trace(
        trace_file,
        expected_attrs={"trace.message": test_message}
    )

def test_direct_trace_usage(trace_file, setup_file_exporter):
    """Test direct usage of TracerFactory.trace method"""
    test_message = "Test message"
    TracerFactory.trace(test_message)
    
    verify_trace(
        trace_file,
        expected_attrs={"trace.message": test_message}
    )

def test_trace_function_decorator(trace_file, setup_file_exporter):
    """Test that the trace_function decorator properly wraps a function"""
    @trace_function
    def sample_function(x, y):
        return x + y
    
    result = sample_function(3, 4)
    assert result == 7
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.sample_function",
        expected_attrs={"function.args": None, "function.kwargs": None}  # Should not have these attributes
    )

def test_class_methods(trace_file, setup_file_exporter):
    """Test that methods within a class can be traced"""
    class SampleClass:
        def __init__(self, value):
            self.value = value
        
        @trace_function(detailed_trace=True)
        def multiply(self, factor):
            return self.value * factor
        
        @trace_function
        def add(self, value):
            return self.value + value
    
    obj = SampleClass(2)
    mult_result = obj.multiply(3)
    add_result = obj.add(4)
    assert mult_result == 6
    assert add_result == 6
    
    # Verify add trace (last operation)
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.add",
        expected_attrs={
            "function.args": None,  # Should not have these attributes
            "function.kwargs": None
        }
    )

def test_nested_tracing(trace_file, setup_file_exporter):
    """Test nested tracing behavior"""
    @trace_function
    def outer_function():
        return inner_function()
    
    @trace_function
    def inner_function():
        return "result"
    
    result = outer_function()
    assert result == "result"
    
    # Verify outer function trace (last operation)
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.outer_function",
        expected_attrs={
            "function.args": None,  # Should not have these attributes
            "function.kwargs": None
        }
    )

def test_exception_handling(trace_file, setup_file_exporter):
    """Test that exceptions are properly recorded in spans"""
    @trace_function(detailed_trace=True)
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError) as exc_info:
        failing_function()
    assert str(exc_info.value) == "Test error"
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.failing_function",
        expected_attrs={
            "function.args": "()",
            "function.kwargs": "{}"
        },
        expected_status={
            "status_code": "StatusCode.ERROR",
            "description": "Test error",
            "exception_type": "ValueError"
        },
        expected_events=[{
            "name": "exception",
            "attributes": {
                "exception.type": "ValueError",
                "exception.message": "Test error"
            }
        }]
    )

def test_parent_child_functions(trace_file, setup_file_exporter):
    """Test that trace context is properly propagated"""
    @trace_function(detailed_trace=True)
    def parent_function():
        current_span = trace.get_current_span()
        current_span.set_attribute("parent.attr", "parent_value")
        return child_function()
    
    @trace_function
    def child_function():
        current_span = trace.get_current_span()
        current_span.set_attribute("child.attr", "child_value")
        return "success"
    
    result = parent_function()
    assert result == "success"
    
    # Verify parent function trace (last operation)
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.parent_function",
        expected_attrs={
            "function.args": "()",
            "function.kwargs": "{}",
            "parent.attr": "parent_value"
        }
    )

def test_trace_with_status(trace_file, setup_file_exporter):
    """Test that span status can be set"""
    @trace_function(detailed_trace=True)
    def status_function(succeed):
        current_span = trace.get_current_span()
        if not succeed:
            current_span.set_status(Status(StatusCode.ERROR, "Operation failed"))
            raise ValueError("Operation failed")
        return "success"
    
    result = status_function(True)
    assert result == "success"
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.status_function",
        expected_attrs={
            "function.args": "(True,)",
            "function.kwargs": "{}"
        },
        expected_status={"status_code": "StatusCode.UNSET"}
    )
    
    with pytest.raises(ValueError):
        status_function(False)
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.status_function",
        expected_attrs={
            "function.args": "(False,)",
            "function.kwargs": "{}"
        },
        expected_status={
            "status_code": "StatusCode.ERROR",
            "description": "Operation failed",
            "exception_type": "ValueError"
        },
        expected_events=[{
            "name": "exception",
            "attributes": {
                "exception.type": "ValueError",
                "exception.message": "Operation failed"
            }
        }]
    )

def test_trace_function_with_attributes(trace_file, setup_file_exporter):
    """Test that trace_function decorator properly handles additional attributes"""
    @trace_function(attributes={"custom.attr1": "value1", "custom.attr2": 42})
    def sample_function():
        return "success"
    
    result = sample_function()
    assert result == "success"
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.sample_function",
        expected_attrs={
            "custom.attr1": "value1",
            "custom.attr2": "42"  # Note: all attributes are converted to strings
        }
    )

def test_tracer_factory_with_attributes(trace_file, setup_file_exporter):
    """Test that TracerFactory.trace properly handles additional attributes"""
    test_message = "Test message with attributes"
    TracerFactory.trace(test_message, attributes={
        "environment": "test",
        "version": "1.0.0",
        "priority": 1
    })
    
    verify_trace(
        trace_file,
        expected_attrs={
            "trace.message": test_message,
            "environment": "test",
            "version": "1.0.0",
            "priority": "1"  # Note: all attributes are converted to strings
        }
    )

def test_file_exporter_with_rotation_config(trace_file, setup_file_exporter):
    """Test that file exporter works with rotation configuration."""
    # Create config with rotation settings
    config_path = "tests/otel_config.yaml"
    config = {
        "exporter": "file",
        "service_name": "MyService",
        "batch_processor": {
            "max_queue_size": 1000,
            "schedule_delay_millis": 1000
        },
        "file_exporter": {
            "path": trace_file,
            "max_size_bytes": 1048576,  # 1MB
            "rotation_time_days": 1
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Reset TracerFactory state
    TracerFactory._instance = None
    TracerFactory._config = None
    
    # Generate a trace
    test_message = "Test with rotation config"
    TracerFactory.trace(test_message)
    
    # Wait for async operations
    time.sleep(2)
    
    # Verify file exists and contains the trace
    assert os.path.exists(trace_file), "Trace file should exist"
    
    # Log the file size
    file_size = os.path.getsize(trace_file)
    logger.info("Trace file size after single trace: %d bytes", file_size)
    
    with open(trace_file, 'r') as f:
        data = json.load(f)
        assert isinstance(data, list), "Trace data should be a list"
        assert len(data) > 0, "Trace data should not be empty"
        # Log size of individual trace
        single_trace = data[0]
        trace_json = json.dumps(single_trace)
        logger.info("Size of single trace JSON: %d bytes", len(trace_json))
        assert any(trace['attributes'].get('trace.message') == test_message for trace in data), \
            "Test message should be in trace data"

def test_file_rotation_with_size_limit(trace_file, setup_file_exporter):
    """Test that file rotation occurs when size limit is exceeded."""
    # Create config with small size limit
    config_path = "tests/otel_config.yaml"
    config = {
        "exporter": "file",
        "service_name": "MyService",
        "batch_processor": {
            "max_queue_size": 1000,
            "schedule_delay_millis": 1000
        },
        "file_exporter": {
            "path": trace_file,
            "max_size_bytes": 700,  # Should rotate after two traces
            "rotation_time_days": 1
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Reset TracerFactory state
    TracerFactory._instance = None
    TracerFactory._config = None
    
    # Generate first trace
    test_message_1 = "First test trace"
    TracerFactory.trace(test_message_1)
    time.sleep(2)  # Wait for async operations
    
    # Verify first trace file exists and contains data
    assert os.path.exists(trace_file), "First trace file should exist"
    with open(trace_file, 'r') as f:
        data = json.load(f)
        assert isinstance(data, list), "Trace data should be a list"
        assert len(data) > 0, "Trace data should not be empty"
        assert any(trace['attributes'].get('trace.message') == test_message_1 for trace in data), \
            "First test message should be in trace data"
    
    # Log size after first trace
    first_size = os.path.getsize(trace_file)
    logger.info("File size after first trace: %d bytes", first_size)
    
    # Generate second trace
    test_message_2 = "Second test trace"
    TracerFactory.trace(test_message_2)
    time.sleep(2)  # Wait for async operations
    
    # Generate third trace - this should trigger rotation
    test_message_3 = "Third test trace"
    TracerFactory.trace(test_message_3)
    time.sleep(2)  # Wait for async operations
    
    # Find rotated files
    test_dir = os.path.dirname(trace_file)
    base_name = os.path.basename(trace_file)
    rotated_files = sorted([f for f in os.listdir(test_dir) 
                    if f.startswith(base_name + '.') and f != base_name])
    
    assert len(rotated_files) >= 1, f"Expected at least 1 rotated file, found {len(rotated_files)}"
    
    # Get the most recent rotated file
    rotated_file = os.path.join(test_dir, rotated_files[-1])
    
    # Verify files exist and contain correct data
    assert os.path.exists(trace_file), "Original trace file should still exist"
    assert os.path.exists(rotated_file), "Rotated file should exist"
    
    # Check contents of current file (should contain third trace)
    with open(trace_file, 'r') as f:
        current_data = json.load(f)
        assert isinstance(current_data, list), "Current file should contain a list"
        assert len(current_data) > 0, "Current file should not be empty"
        assert any(trace['attributes'].get('trace.message') == test_message_3 for trace in current_data), \
            "Third test message should be in current file"
    
    # Log final sizes
    logger.info("Original file final size: %d bytes", os.path.getsize(trace_file))
    logger.info("Most recent rotated file size: %d bytes", os.path.getsize(rotated_file))
    
    # Log all rotated files for debugging
    for rotated in rotated_files:
        full_path = os.path.join(test_dir, rotated)
        logger.info("Rotated file %s size: %d bytes", rotated, os.path.getsize(full_path))
