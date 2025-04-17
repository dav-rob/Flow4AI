import inspect
import json
import os
from functools import wraps
from importlib import resources
from threading import Lock
from typing import Any, Dict, Optional, Sequence

import yaml
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter, SpanExporter,
                                            SpanExportResult)

# Explicitly define exports
__all__ = ['TracerFactory', 'trace_function', 'AsyncFileExporter']
DEFAULT_OTEL_CONFIG = "otel_config.yaml"

class AsyncFileExporter(SpanExporter):
    """Asynchronous file exporter for OpenTelemetry spans with log rotation support."""
    
    def __init__(self, filepath: str, max_size_bytes: int = None, rotation_time_days: int = None):
        """Initialize the exporter with the target file path and rotation settings.
        
        Args:
            filepath: Path to the file where spans will be exported
            max_size_bytes: Maximum file size in bytes before rotation
            rotation_time_days: Number of days before rotating file
        """
        self.filepath = os.path.expanduser(filepath)
        self.max_size_bytes = max_size_bytes
        self.rotation_time_days = rotation_time_days
        self.last_rotation_time = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._export_lock = Lock()
        
        # Initialize file with empty array if it doesn't exist
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
                
        # Record initial rotation time
        if self.rotation_time_days:
            self.last_rotation_time = os.path.getmtime(self.filepath)
    
    def _should_rotate(self, additional_size: int = 0) -> bool:
        """Check if file should be rotated based on size or time.
        
        Args:
            additional_size: Additional size in bytes that will be added
        """
        if not os.path.exists(self.filepath):
            return False
            
        should_rotate = False
        
        # Check size-based rotation
        if self.max_size_bytes:
            current_size = os.path.getsize(self.filepath)
            if (current_size + additional_size) >= self.max_size_bytes:
                should_rotate = True
                
        # Check time-based rotation
        if self.rotation_time_days and self.last_rotation_time:
            current_time = os.path.getmtime(self.filepath)
            days_elapsed = (current_time - self.last_rotation_time) / (24 * 3600)
            if days_elapsed >= self.rotation_time_days:
                should_rotate = True
                
        return should_rotate
    
    def _rotate_file(self):
        """Rotate the current file if it exists."""
        if not os.path.exists(self.filepath):
            return
            
        # Generate rotation suffix based on timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_path = f"{self.filepath}.{timestamp}"
        
        # Rotate the file
        os.rename(self.filepath, rotated_path)
        
        # Create new empty file
        with open(self.filepath, 'w') as f:
            json.dump([], f)
            
        # Update rotation time
        self.last_rotation_time = os.path.getmtime(self.filepath)
    
    def _serialize_span(self, span: ReadableSpan) -> dict:
        """Convert a span to a JSON-serializable dictionary.
        
        Args:
            span: The span to serialize
        Returns:
            dict: JSON-serializable representation of the span
        """
        return {
            'name': span.name,
            'context': {
                'trace_id': format(span.context.trace_id, '032x'),
                'span_id': format(span.context.span_id, '016x'),
            },
            'parent_id': format(span.parent.span_id, '016x') if span.parent else None,
            'start_time': span.start_time,
            'end_time': span.end_time,
            'attributes': dict(span.attributes),
            'events': [
                {
                    'name': event.name,
                    'timestamp': event.timestamp,
                    'attributes': dict(event.attributes)
                }
                for event in span.events
            ],
            'status': {
                'status_code': str(span.status.status_code),
                'description': span.status.description
            }
        }

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to file with rotation support.
        
        Args:
            spans: Sequence of spans to export
        Returns:
            SpanExportResult indicating success or failure
        """
        try:
            with self._export_lock:
                # Create serializable span data
                span_data = [self._serialize_span(span) for span in spans]
                
                # Read existing spans
                try:
                    with open(self.filepath, 'r') as f:
                        try:
                            existing_spans = json.load(f)
                        except json.JSONDecodeError:
                            existing_spans = []
                except FileNotFoundError:
                    existing_spans = []
                
                # Calculate size of new data
                new_data = existing_spans + span_data
                new_data_str = json.dumps(new_data, indent=2)
                additional_size = len(new_data_str.encode('utf-8'))
                
                # Check rotation after calculating new size
                if self._should_rotate(additional_size - os.path.getsize(self.filepath) if os.path.exists(self.filepath) else 0):
                    self._rotate_file()
                    existing_spans = []
                
                # Append new spans
                existing_spans.extend(span_data)
                
                # Write all spans back to file
                temp_file = f"{self.filepath}.tmp"
                try:
                    with open(temp_file, 'w') as f:
                        json.dump(existing_spans, f, indent=2)
                    # Atomic replace
                    os.replace(temp_file, self.filepath)
                finally:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error exporting spans to file: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        pass

class TestTracerProvider(TracerProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TestTracerProvider, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            
    def get_tracer(
        self,
        instrumenting_module_name: str,
        instrumenting_library_version: str = None,
        schema_url: str = None,
        attributes: dict = None,
    ) -> trace.Tracer:
        """Get a tracer for use in tests.
        
        Args:
            instrumenting_module_name: The name of the instrumenting module
            instrumenting_library_version: Optional version of the instrumenting module
            schema_url: Optional URL of the OpenTelemetry schema
            attributes: Optional attributes to add to the tracer
            
        Returns:
            A tracer instance for use in tests
        """
        return super().get_tracer(
            instrumenting_module_name,
            instrumenting_library_version,
            schema_url,
            attributes,
        )

# Singleton TracerFactory
class TracerFactory:
    _instance = None
    _config = None
    _lock = Lock()
    _is_test_mode = False
    
    @classmethod
    def set_test_mode(cls, enabled: bool = True):
        """Enable or disable test mode.
        
        Args:
            enabled: Whether to enable test mode
        """
        cls._is_test_mode = enabled
        cls._instance = None  # Reset instance to force recreation with new provider
    
    @classmethod
    def _load_config(cls, yaml_file=None):
        """Load configuration from YAML file.
        
        Args:
            yaml_file: Optional path override for the YAML configuration file
        Returns:
            dict: Configuration dictionary
        """
       # First try yaml_file parameter
        config_path = yaml_file
        if not config_path:
            # Then try environment variable
            config_path = os.environ.get('JOBCHAIN_OT_CONFIG', "")
        
        if not config_path:
            # Finally use default path from package resources
            try:
                with resources.path('flow4ai.resources', DEFAULT_OTEL_CONFIG) as path:
                    config_path = str(path)
            except Exception as e:
                raise RuntimeError(f"Could not find {DEFAULT_OTEL_CONFIG} in package resources: {e}")
        
        with open(config_path, 'r') as file:
                cls._config = yaml.safe_load(file)
        return cls._config
    
    @classmethod
    def get_tracer(cls, config=None):
        """Get or create the tracer instance.
        
        Args:
            config: Optional configuration override. If not provided, loads from file.
        Returns:
            Tracer instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    # Use provided config or load from file
                    cfg = config if config is not None else cls._load_config()
                    
                    # Use TestTracerProvider in test mode
                    provider = TestTracerProvider() if cls._is_test_mode else TracerProvider()
                    
                    # Configure main exporter
                    main_exporter = cls._configure_exporter(cfg['exporter'])
                    batch_processor = BatchSpanProcessor(
                        main_exporter,
                        max_queue_size=cfg['batch_processor']['max_queue_size'],
                        schedule_delay_millis=cfg['batch_processor']['schedule_delay_millis']
                    )
                    provider.add_span_processor(batch_processor)
                    
                    trace.set_tracer_provider(provider)
                    cls._instance = trace.get_tracer(cfg["service_name"])
        return cls._instance

    @staticmethod
    def _configure_exporter(exporter_type):
        """Configure the appropriate exporter based on type.
        
        Args:
            exporter_type: Type of exporter to configure
        Returns:
            Configured exporter instance
        """
        if exporter_type == "otlp":
            return OTLPSpanExporter()  # OTEL_EXPORTER_OTLP_... environment variables apply here
        elif exporter_type == "console":
            return ConsoleSpanExporter()  # OTEL_EXPORTER_CONSOLE_... environment variables apply here
        elif exporter_type == "file":
            # Load config to get file path
            config = TracerFactory._load_config()
            file_path = config.get('file_exporter', {}).get('path', "~/.JobChain/otel_trace.json")
            max_size_bytes = config.get('file_exporter', {}).get('max_size_bytes')
            rotation_time_days = config.get('file_exporter', {}).get('rotation_time_days')
            return AsyncFileExporter(file_path, max_size_bytes, rotation_time_days)
        else:
            raise ValueError("Unsupported exporter type")

    @classmethod
    def trace(cls, message: str, detailed_trace: bool = False, attributes: Optional[Dict[str, Any]] = None):
        """Trace a message with OpenTelemetry tracing.
        
        Args:
            message: The message to trace
            detailed_trace: Whether to include detailed tracing information (args, kwargs, object fields)
            attributes: Optional dictionary of additional attributes to add to the span
        """
        tracer = cls.get_tracer()
        
        # Get the calling frame
        frame = inspect.currentframe()
        if frame:
            caller_frame = frame.f_back
            if caller_frame:
                # Get function info
                func_name = caller_frame.f_code.co_name
                module_name = inspect.getmodule(caller_frame).__name__ if inspect.getmodule(caller_frame) else "__main__"
                
                # Get local variables including 'self' if it exists
                local_vars = caller_frame.f_locals
                args = []
                kwargs = {}
                
                # If this is a method call (has 'self')
                if 'self' in local_vars:
                    args.append(local_vars['self'])
                    # Add other arguments if they exist
                    if len(local_vars) > 1:
                        # Filter out 'self' and get remaining arguments
                        args.extend([v for k, v in local_vars.items() if k != 'self'])
                
                span_name = f"{module_name}.{func_name}"
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("trace.message", message)
                    if detailed_trace:
                        span.set_attribute("function.args", str(tuple(args)))
                        span.set_attribute("function.kwargs", str(kwargs))
                        if args and hasattr(args[0], "__dict__"):
                            span.set_attribute("object.fields", str(vars(args[0])))
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, str(value))
                    print(message)
                
                # Clean up
                del frame
                del caller_frame
                return
        
        # Fallback if not in a function context
        with tracer.start_as_current_span("trace_message") as span:
            span.set_attribute("trace.message", message)
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            print(message)

# Decorator for OpenTelemetry tracing
def trace_function(func=None, *, detailed_trace: bool = False, attributes: Optional[Dict[str, Any]] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = TracerFactory.get_tracer()
            span_name = f"{func.__module__}.{func.__name__}"
            with tracer.start_as_current_span(span_name) as span:
                # Record function arguments only if detailed_trace is True
                if detailed_trace:
                    span.set_attribute("function.args", str(args))
                    span.set_attribute("function.kwargs", str(kwargs))
                    if args and hasattr(args[0], "__dict__"):
                        span.set_attribute("object.fields", str(vars(args[0])))
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)
