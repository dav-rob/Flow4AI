"""
Logging configuration for JobChain.
**DEPRECATED**: This module is deprecated. Please use flow4ai.f4a_logging instead.

Environment Variables:
    JOBCHAIN_LOG_LEVEL: Set the logging level (e.g., 'DEBUG', 'INFO'). Defaults to 'INFO'.
    JOBCHAIN_LOG_HANDLERS: Set logging handlers. Options:
        - Not set or 'console': Log to console only (default)
        - 'console,file': Log to both console and file
        
Example:
    To enable both console and file logging:
    $ export JOBCHAIN_LOG_HANDLERS='console,file'
    
    To set debug level logging:
    $ export JOBCHAIN_LOG_LEVEL='DEBUG'
"""


import os
import warnings
import sys

# Import all names from flow4ai.f4a_logging
from flow4ai.f4a_logging import *

# Emit deprecation warning
warnings.warn(
    "The 'jobchain.jc_logging' module is deprecated. "
    "Please use 'flow4ai.f4a_logging' instead.",
    DeprecationWarning,
    stacklevel=2
)


# All functionality is now imported from flow4ai.f4a_logging

# All functionality is now imported from flow4ai.f4a_logging
