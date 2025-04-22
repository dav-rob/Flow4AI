# Make utils a Python package
from .otel_wrapper import TracerFactory, trace_function
from .timing import timing_decorator

__all__ = ['TracerFactory', 'trace_function', 'timing_decorator']
