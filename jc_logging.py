import logging
import os
from logging.config import dictConfig

def get_logging_config():
    """Get the logging configuration based on current environment variables."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': os.getenv('JOBCHAIN_LOG_LEVEL', 'INFO'),
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
            'level': os.getenv('JOBCHAIN_LOG_LEVEL', 'INFO'),
            'handlers': ['console', 'file']
        }
    }

def setup_logging():
    """Setup logging with current configuration."""
    # Create log file if it doesn't exist
    if not os.path.exists('jobchain.log'):
        with open('jobchain.log', 'w') as f:
            pass
    
    # Apply configuration
    dictConfig(get_logging_config())

# Apply configuration when module is imported
setup_logging()

# Re-export everything we need from logging
getLogger = logging.getLogger
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
dictConfig = dictConfig  # Re-export dictConfig directly
StreamHandler = logging.StreamHandler  # Re-export StreamHandler
Formatter = logging.Formatter  # Re-export Formatter
