"""
Logging configuration for Flow4AI (formerly JobChain).

Environment Variables:
    FLOW4AI_LOG_LEVEL: Set the logging level (e.g., 'DEBUG', 'INFO'). Defaults to 'INFO'.
    FLOW4AI_LOG_HANDLERS: Set logging handlers. Options:
        - Not set or 'console': Log to console only (default)
        - 'console,file': Log to both console and file
        
    For backward compatibility, these environment variables are also supported:
    JOBCHAIN_LOG_LEVEL, JOBCHAIN_LOG_HANDLERS
        
Example:
    To enable both console and file logging:
    $ export FLOW4AI_LOG_HANDLERS='console,file'
    
    To set debug level logging:
    $ export FLOW4AI_LOG_LEVEL='DEBUG'
"""


import os

# Initializing the flag here stops logging caching root levels to another value
# for reasons I'm not completely sure about.
WINDSURF_LOG_FLAG = None #None #"DEBUG"

# Support both old and new environment variable names
# For backward compatibility in tests, if JOBCHAIN_LOG_LEVEL is explicitly set, use it
jobchain_log_level = os.getenv('JOBCHAIN_LOG_LEVEL')
flow4ai_log_level = os.getenv('FLOW4AI_LOG_LEVEL')

log_level = (WINDSURF_LOG_FLAG or 
            (jobchain_log_level if jobchain_log_level else flow4ai_log_level) or 
            'INFO')

log_handlers = (os.getenv('JOBCHAIN_LOG_HANDLERS') or 
               os.getenv('FLOW4AI_LOG_HANDLERS') or 
               'console')

# Set both old and new variables for backwards compatibility
os.environ['FLOW4AI_LOG_LEVEL'] = log_level
os.environ['JOBCHAIN_LOG_LEVEL'] = log_level

import logging
from logging.config import dictConfig


def get_logging_config():
    """Get the logging configuration based on current environment variables."""
    # Get log level from environment variables
    # For backward compatibility in tests, if JOBCHAIN_LOG_LEVEL is explicitly set, use it
    jobchain_log_level = os.getenv('JOBCHAIN_LOG_LEVEL')
    flow4ai_log_level = os.getenv('FLOW4AI_LOG_LEVEL')
    
    log_level = (jobchain_log_level if jobchain_log_level else flow4ai_log_level) or 'INFO'
    
    # Support both log files
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'flow4ai_file': {
                'class': 'logging.FileHandler',
                'level': log_level,
                'formatter': 'detailed',
                'filename': 'flow4ai.log',
                'mode': 'a'
            },
            'jobchain_file': {
                'class': 'logging.FileHandler',
                'level': log_level,
                'formatter': 'detailed',
                'filename': 'jobchain.log',
                'mode': 'a'
            }
        },
        'loggers': {
            'ExampleCustom': {
                'level': 'DEBUG',
                'handlers': ['console', 'flow4ai_file', 'jobchain_file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            # Parse handlers setting and map 'file' to both file handlers for compatibility
            'handlers': _get_handlers()
        }
    }

def _get_handlers():
    """Parse handlers setting and map 'file' to both file handlers for compatibility."""
    # Get log handlers from environment variables (with Flow4AI taking precedence)
    handlers_str = (os.getenv('FLOW4AI_LOG_HANDLERS') or 
                  os.getenv('JOBCHAIN_LOG_HANDLERS', 'console'))
    
    print(f"DEBUG - Handlers string: {handlers_str}")
    
    handlers = handlers_str.split(',')
    
    # Replace 'file' with both file handlers for compatibility 
    if 'file' in handlers:
        handlers.remove('file')
        handlers.extend(['flow4ai_file', 'jobchain_file'])
    
    print(f"DEBUG - Final handlers: {handlers}")
    
    return handlers

def setup_logging():
    """Setup logging with current configuration."""
    # CRITICAL: Force reload environment variables before generating config
    # This ensures that environment variables set after module import are still picked up
    global log_level
    
    # For backward compatibility in tests, if JOBCHAIN_LOG_LEVEL is explicitly set, use it
    jobchain_log_level = os.getenv('JOBCHAIN_LOG_LEVEL')
    flow4ai_log_level = os.getenv('FLOW4AI_LOG_LEVEL')
    
    log_level = (WINDSURF_LOG_FLAG or 
                (jobchain_log_level if jobchain_log_level else flow4ai_log_level) or 
                'INFO')
    
    print(f"DEBUG - FLOW4AI_LOG_LEVEL: {os.getenv('FLOW4AI_LOG_LEVEL')}")
    print(f"DEBUG - JOBCHAIN_LOG_LEVEL: {os.getenv('JOBCHAIN_LOG_LEVEL')}")
    print(f"DEBUG - log_level: {log_level}")
    
    # Set both variables for backward compatibility
    os.environ['FLOW4AI_LOG_LEVEL'] = log_level
    os.environ['JOBCHAIN_LOG_LEVEL'] = log_level
    
    # Now get config with updated environment variables
    config = get_logging_config()
    
    # Always create log files with headers, actual logging will only happen if handlers use them
    if not os.path.exists('flow4ai.log'):
        with open('flow4ai.log', 'w') as f:
            f.write('# Flow4AI log file - This file is created empty and will be written to only when file logging is enabled\n')
    
    if not os.path.exists('jobchain.log'):
        with open('jobchain.log', 'w') as f:
            f.write('# JobChain log file - This file is created empty and will be written to only when file logging is enabled\n')
    
    print(f"Logging level: {config['root']['level']}")
    print(f"DEBUG - Handlers: {config['root']['handlers']}")
    
    # Apply configuration
    dictConfig(config)
    
    # Extra verification
    root_logger = logging.getLogger()
    print(f"DEBUG - Root logger level after config: {root_logger.level}")

# Apply configuration when module is imported
setup_logging()

# Re-export everything from logging
# Constants
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

# Functions
getLogger = logging.getLogger
basicConfig = logging.basicConfig
shutdown = logging.shutdown
debug = logging.debug
info = logging.info
warning = logging.warning
error = logging.error
critical = logging.critical
exception = logging.exception
log = logging.log

# Classes
Logger = logging.Logger
Handler = logging.Handler
Formatter = logging.Formatter
Filter = logging.Filter
LogRecord = logging.LogRecord

# Handlers
StreamHandler = logging.StreamHandler
FileHandler = logging.FileHandler
NullHandler = logging.NullHandler

# Configuration
dictConfig = dictConfig  # Already imported from logging.config
fileConfig = logging.config.fileConfig

# Exceptions
exception = logging.exception
captureWarnings = logging.captureWarnings

# Additional utilities
getLevelName = logging.getLevelName
makeLogRecord = logging.makeLogRecord
