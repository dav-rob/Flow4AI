"""
JobChain - A scalable AI job scheduling and execution platform
This package has been renamed to 'flow4ai'. Please update your imports.
"""

import warnings

# Emit a deprecation warning when importing from jobchain
warnings.warn(
    "The 'jobchain' package has been renamed to 'flow4ai'. "
    "Please update your imports to use 'flow4ai' instead of 'jobchain'.",
    DeprecationWarning, 
    stacklevel=2
)

from .job import JobABC
from .job_chain import JobChain
from . import jc_logging

__all__ = ['JobABC', 'JobChain', 'jc_logging']
