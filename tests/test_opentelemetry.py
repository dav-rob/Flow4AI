import json
import os
import time

import pytest
import yaml
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from utils.otel_wrapper import TracerFactory, trace_function


@pytest.fixture
def trace_file():
    """Fixture to create and clean up a temporary trace file"""
    trace_file = "tests/temp_otel_trace.json"
    # Initialize trace file
    os.makedirs("tests", exist_ok=True)
    with open(trace_file, 'w') as f:
        json.dump([], f)
    yield trace_file
    # Cleanup
    if os.path.exists(trace_file):
        os.unlink(trace_file)

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

def verify_trace(trace_file, expected_name=None, expected_attrs=None, expected_status=None, expected_events=None):
    """Helper function to verify trace output"""
    time.sleep(1.0)  # Wait for async operations
    with open(trace_file, 'r') as f:
        trace_data = json.load(f)
        assert isinstance(trace_data, list), "Trace data should be a list"
        assert len(trace_data) > 0, "Trace data should not be empty"
        
        # Get the last span (most recent)
        span = trace_data[-1]
        
        # Verify span structure
        assert 'name' in span, "Span should have a name"
        assert 'context' in span, "Span should have context"
        assert 'trace_id' in span['context'], "Span should have trace_id"
        assert 'span_id' in span['context'], "Span should have span_id"
        assert 'attributes' in span, "Span should have attributes"
        
        # Verify expected name if provided
        if expected_name:
            assert span['name'] == expected_name, f"Expected span name {expected_name}, got {span['name']}"
        
        # Verify expected attributes if provided
        if expected_attrs:
            for key, value in expected_attrs.items():
                assert key in span['attributes'], f"Span should have {key} attribute"
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
        expected_attrs={"function.args": "(3, 4)", "function.kwargs": "{}"}
    )

def test_class_methods(trace_file, setup_file_exporter):
    """Test that methods within a class can be traced"""
    class SampleClass:
        def __init__(self, value):
            self.value = value
        
        @trace_function
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
        expected_attrs={"function.kwargs": "{}"}
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
        expected_attrs={"function.args": "()", "function.kwargs": "{}"}
    )

def test_exception_handling(trace_file, setup_file_exporter):
    """Test that exceptions are properly recorded in spans"""
    @trace_function
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError) as exc_info:
        failing_function()
    assert str(exc_info.value) == "Test error"
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.failing_function",
        expected_attrs={"function.args": "()", "function.kwargs": "{}"},
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
    @trace_function
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
    @trace_function
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
        expected_attrs={"function.args": "(True,)", "function.kwargs": "{}"},
        expected_status={"status_code": "StatusCode.UNSET"}
    )
    
    with pytest.raises(ValueError):
        status_function(False)
    
    verify_trace(
        trace_file,
        expected_name="test_opentelemetry.status_function",
        expected_attrs={"function.args": "(False,)", "function.kwargs": "{}"},
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
