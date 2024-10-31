import logging.config
import os

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
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
            'level': 'INFO',
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
        'handlers': ['console']
    }
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
