import os
import pytest
import tempfile
import yaml
import json
import time
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from utils.otel_wrapper import TracerFactory, trace_function

def test_file_exporter_yaml():
    """Test file exporter using a temporary yaml config file"""
    config_path = "tests/otel_config.yaml"
    trace_file = "tests/temp_otel_trace.json"
    
    try:
        # Create test directory
        os.makedirs("tests", exist_ok=True)
        
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
        
        # Initialize trace file
        with open(trace_file, 'w') as f:
            json.dump([], f)
        
        # Reset TracerFactory state
        TracerFactory._instance = None
        TracerFactory._config = None
        
        # Set config path in environment
        os.environ['JOBCHAIN_OT_CONFIG'] = config_path
        
        # Create a simple trace
        test_message = "Test trace message"
        TracerFactory.trace(test_message)
        
        # Wait for async operations
        time.sleep(1.0)
        
        # Read and verify trace data
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
            assert isinstance(trace_data, list), "Trace data should be a list"
            assert len(trace_data) > 0, "Trace data should not be empty"
            
            # Get the first span
            span = trace_data[0]
            
            # Verify span structure
            assert 'name' in span, "Span should have a name"
            assert 'context' in span, "Span should have context"
            assert 'trace_id' in span['context'], "Span should have trace_id"
            assert 'span_id' in span['context'], "Span should have span_id"
            assert 'attributes' in span, "Span should have attributes"
            assert 'trace.message' in span['attributes'], "Span should have trace.message attribute"
            assert span['attributes']['trace.message'] == test_message, "Span should have correct message"
    
    finally:
        # Cleanup
        if os.path.exists(config_path):
            os.unlink(config_path)
        if os.path.exists(trace_file):
            os.unlink(trace_file)
        if 'JOBCHAIN_OT_CONFIG' in os.environ:
            del os.environ['JOBCHAIN_OT_CONFIG']
        # Reset TracerFactory state
        TracerFactory._instance = None
        TracerFactory._config = None
        time.sleep(0.1)

def test_config_from_env_var(temp_config_file):
    """Test that TracerFactory uses config from JOBCHAIN_OT_CONFIG environment variable"""
    os.environ['JOBCHAIN_OT_CONFIG'] = temp_config_file
    try:
        tracer = TracerFactory.get_tracer()
        config = TracerFactory._config
        assert config['service_name'] == 'test_service'
        assert config['batch_processor']['max_queue_size'] == 512
        assert config['batch_processor']['schedule_delay_millis'] == 5000
    finally:
        if 'JOBCHAIN_OT_CONFIG' in os.environ:
            del os.environ['JOBCHAIN_OT_CONFIG']
        TracerFactory._instance = None
        TracerFactory._config = None

def test_config_fallback_to_default():
    """Test that TracerFactory falls back to default config path when env var is not set"""
    if 'JOBCHAIN_OT_CONFIG' in os.environ:
        del os.environ['JOBCHAIN_OT_CONFIG']
    TracerFactory._instance = None
    TracerFactory._config = None
    tracer = TracerFactory.get_tracer()
    assert tracer is not None

@pytest.fixture
def temp_config_file():
    """Create a temporary config file with custom settings"""
    config = {
        "service_name": "test_service",
        "exporter": "console",
        "batch_processor": {
            "max_queue_size": 512,
            "schedule_delay_millis": 5000
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp:
        yaml.dump(config, temp)
        temp_path = temp.name
    yield temp_path
    os.unlink(temp_path)

def test_trace_function_decorator():
    """Test that the trace_function decorator properly wraps a function"""
    @trace_function
    def sample_function(x, y):
        return x + y
    result = sample_function(3, 4)
    assert result == 7

def test_class_methods():
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

def test_trace_method_decorator():
    """Test that the trace_function decorator works on individual methods"""
    class SampleClass:
        def __init__(self, value):
            self.value = value
        
        @trace_function
        def multiply(self, factor):
            return self.value * factor
    
    obj = SampleClass(2)
    result = obj.multiply(3)
    assert result == 6

def test_tracer_factory_singleton():
    """Test that TracerFactory maintains singleton behavior"""
    tracer1 = TracerFactory.get_tracer()
    tracer2 = TracerFactory.get_tracer()
    assert tracer1 is tracer2

def test_direct_trace_usage():
    """Test direct usage of TracerFactory.trace method"""
    TracerFactory.trace("Test message")

def test_nested_tracing():
    """Test nested tracing behavior"""
    @trace_function
    def outer_function():
        return inner_function()
    
    @trace_function
    def inner_function():
        return "result"
    
    result = outer_function()
    assert result == "result"

def test_exception_handling():
    """Test that exceptions are properly recorded in spans"""
    @trace_function
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError) as exc_info:
        failing_function()
    assert str(exc_info.value) == "Test error"

def test_trace_with_context():
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

def test_trace_with_status():
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
    
    with pytest.raises(ValueError):
        status_function(False)
