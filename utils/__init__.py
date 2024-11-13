# Make utils a Python package
from .otel_wrapper import TracerFactory, trace_function

__all__ = ['TracerFactory', 'trace_function']
