import inspect
import json
import os
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Sequence

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter, SpanExporter,
                                            SpanExportResult)

# Explicitly define exports
__all__ = ['TracerFactory', 'trace_function', 'AsyncFileExporter']

class AsyncFileExporter(SpanExporter):
    """Asynchronous file exporter for OpenTelemetry spans."""
    
    def __init__(self, filepath: str):
        """Initialize the exporter with the target file path.
        
        Args:
            filepath: Path to the file where spans will be exported
        """
        self.filepath = os.path.expanduser(filepath)
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._export_lock = Lock()
        
        # Initialize file with empty array if it doesn't exist
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)
        
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
        """Export spans to file.
        
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

# Singleton TracerFactory
class TracerFactory:
    _instance = None
    _config = None
    _lock = Lock()
    
    @classmethod
    def _load_config(cls, yaml_file=None):
        """Load configuration from YAML file.
        
        Args:
            yaml_file: Optional path override for the YAML configuration file
        Returns:
            dict: Configuration dictionary
        """
        if cls._config is None:
            import yaml

            # Get config path from environment variable or use default
            config_path = yaml_file or os.environ.get('JOBCHAIN_OT_CONFIG', "resources/otel_config.yaml")
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
                    provider = TracerProvider()
                    
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
            return AsyncFileExporter(file_path)
        else:
            raise ValueError("Unsupported exporter type")

    @classmethod
    def trace(cls, message: str):
        """Trace a message with OpenTelemetry tracing.
        
        Args:
            message: The message to trace
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
                    span.set_attribute("function.args", str(tuple(args)))
                    span.set_attribute("function.kwargs", str(kwargs))
                    if args and hasattr(args[0], "__dict__"):
                        span.set_attribute("object.fields", str(vars(args[0])))
                    print(message)
                
                # Clean up
                del frame
                del caller_frame
                return
        
        # Fallback if not in a function context
        with tracer.start_as_current_span("trace_message") as span:
            span.set_attribute("trace.message", message)
            print(message)

# Decorator for OpenTelemetry tracing
def trace_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        tracer = TracerFactory.get_tracer()
        span_name = f"{func.__module__}.{func.__name__}"
        with tracer.start_as_current_span(span_name) as span:
            # Record function arguments
            span.set_attribute("function.args", str(args))
            span.set_attribute("function.kwargs", str(kwargs))
            if args and hasattr(args[0], "__dict__"):
                span.set_attribute("object.fields", str(vars(args[0])))
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                span.record_exception(e)
                raise

    return wrapper
