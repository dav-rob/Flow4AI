"""
Flow4AI - A scalable AI job scheduling and execution platform
(Formerly known as JobChain)
"""

import sys
import warnings

# Import our new modules first
from .job import JobABC  # Will just re-export jobchain.job for now
from .job_chain import JobChain  # Will just re-export jobchain.job_chain for now
from . import f4a_logging  # Our new renamed module
from . import f4a_graph  # Our new renamed module

# Create an alias for Flow4AI (will eventually replace JobChain)
Flow4AI = JobChain

# For backward compatibility with jobchain imports
import jobchain.jc_logging
jc_logging = f4a_logging

# Export our API
__all__ = ['JobABC', 'JobChain', 'Flow4AI', 'f4a_logging', 'f4a_graph', 'jc_logging']

# Emit a deprecation warning when directly importing from jobchain
warnings.warn(
    "The 'jobchain' package has been renamed to 'flow4ai'. "
    "Please update your imports to use 'flow4ai' instead of 'jobchain'.",
    DeprecationWarning, 
    stacklevel=2
)
