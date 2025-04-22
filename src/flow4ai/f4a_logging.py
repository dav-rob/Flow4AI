"""
Logging configuration for Flow4AI.

Environment Variables:
    FLOW4AI_LOG_LEVEL: Set the logging level (e.g., 'DEBUG', 'INFO'). Defaults to 'INFO'.
    JOBCHAIN_LOG_HANDLERS: Set logging handlers. Options:
        - Not set or 'console': Log to console only (default)
        - 'console,file': Log to both console and file
        
Example:
    To enable both console and file logging:
    $ export JOBCHAIN_LOG_HANDLERS='console,file'
    
    To set debug level logging:
    $ export FLOW4AI_LOG_LEVEL='DEBUG'
"""


import os

# Initializing the flag here stops logging caching root levels to another value
# for reasons I'm not completely sure about.
WINDSURF_LOG_FLAG = None #None #"DEBUG"
os.environ['FLOW4AI_LOG_LEVEL'] = WINDSURF_LOG_FLAG or os.getenv('FLOW4AI_LOG_LEVEL', 'INFO')
import logging
from logging.config import dictConfig


def get_logging_config():
    """Get the logging configuration based on current environment variables."""
    
    
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
                'level': os.getenv('FLOW4AI_LOG_LEVEL', 'INFO'),
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': os.getenv('FLOW4AI_LOG_LEVEL', 'INFO'),
                'formatter': 'detailed',
                'filename': 'jobchain.log',
                'mode': 'a'
            }
        },
        'loggers': {
            'ExampleCustom': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level':  os.getenv('FLOW4AI_LOG_LEVEL', 'INFO'),
            # Set JOBCHAIN_LOG_HANDLERS='console,file' to enable both console and file logging
            'handlers': os.getenv('JOBCHAIN_LOG_HANDLERS', 'console').split(',')
        }
    }

def setup_logging():
    """Setup logging with current configuration."""
    config = get_logging_config()
    
    # Always create log file with header, actual logging will only happen if handlers use it
    if not os.path.exists('jobchain.log'):
        with open('jobchain.log', 'w') as f:
            f.write('# JobChain log file - This file is created empty and will be written to only when file logging is enabled\n')
    
    print(f"Logging level: {config['root']['level']}")
    # Apply configuration
    dictConfig(config)

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
