"""
Flow4AI - A scalable AI job scheduling and execution platform
"""

from . import f4a_logging

__all__ = ['JobABC', 'FlowManagerMP', 'f4a_logging']

# Lazily load submodules to avoid circular imports
def __getattr__(name):
    if name == 'FlowManagerMP':
        from .flowmanagerMP import FlowManagerMP
        return FlowManagerMP
    if name == 'JobABC':
        from .job import JobABC
        return JobABC
    raise AttributeError(f"module {__name__} has no attribute {name}")
