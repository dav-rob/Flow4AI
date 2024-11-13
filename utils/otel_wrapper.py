from functools import wraps
from threading import Lock
import inspect

import yaml
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
    OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)

# Explicitly define exports
__all__ = ['TracerFactory', 'trace_function']

# Singleton TracerFactory
class TracerFactory:
    _instance = None
    _config = None
    _lock = Lock()
    
    @classmethod
    def _load_config(cls, yaml_file="resources/otel_config.yaml"):  # Updated path
        """Load configuration from YAML file.
        
        Args:
            yaml_file: Path to the YAML configuration file
        Returns:
            dict: Configuration dictionary
        """
        if cls._config is None:
            with open(yaml_file, 'r') as file:
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
                    exporter = cls._configure_exporter(cfg['exporter'])
                    batch_processor = BatchSpanProcessor(
                        exporter,
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
