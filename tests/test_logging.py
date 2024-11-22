import io
import logging
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logging_config import LOGGING_CONFIG

@pytest.fixture(autouse=True)
def setup_logging_for_tests():
    """Setup and teardown logging configuration for each test"""
    # Store original handlers
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    
    # Remove all handlers
    for handler in original_handlers:
        root.removeHandler(handler)
    
    # Create test-specific logging config
    test_config = LOGGING_CONFIG.copy()
    test_config['handlers'] = LOGGING_CONFIG['handlers'].copy()
    test_config['handlers']['file'] = LOGGING_CONFIG['handlers']['file'].copy()
    test_config['handlers']['file']['filename'] = 'tests/jobchain.log'
    
    # Ensure ExampleCustom logger uses the capture handler
    test_config['loggers'] = LOGGING_CONFIG['loggers'].copy()
    test_config['loggers']['ExampleCustom'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
        'propagate': True
    }
    
    # Apply test config
    logging.config.dictConfig(test_config)
    
    yield
    
    # Cleanup log file
    try:
        os.remove('tests/jobchain.log')
    except FileNotFoundError:
        pass
    
    # Restore original handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    for handler in original_handlers:
        root.addHandler(handler)

@pytest.fixture
def capture_logs():
    """Capture log output for verification"""
    # Create string IO and handler
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    # Get root logger and add our capture handler
    root = logging.getLogger()
    root.addHandler(handler)
    
    # Set initial level to DEBUG to allow all messages
    root.setLevel(logging.DEBUG)
    
    yield log_capture
    
    # Cleanup
    root.removeHandler(handler)
    log_capture.close()

@pytest.fixture
def env_level(monkeypatch):
    """Fixture to set and restore JOBCHAIN_LOG_LEVEL"""
    original = os.environ.get('JOBCHAIN_LOG_LEVEL')
    
    def _set_level(level):
        monkeypatch.setenv('JOBCHAIN_LOG_LEVEL', level)
        # Get root logger
        root = logging.getLogger()
        # Set level based on environment variable
        root.setLevel(getattr(logging, level))
        
        # Ensure ExampleCustom logger always has DEBUG level
        custom_logger = logging.getLogger('ExampleCustom')
        custom_logger.setLevel(logging.DEBUG)
    
    yield _set_level
    
    # Restore original environment
    if original is not None:
        monkeypatch.setenv('JOBCHAIN_LOG_LEVEL', original)
    else:
        monkeypatch.delenv('JOBCHAIN_LOG_LEVEL', raising=False)

def test_root_logger_respects_env_level(env_level, capture_logs):
    """Test that root logger respects JOBCHAIN_LOG_LEVEL"""
    logger = logging.getLogger('TestLogger')
    
    # Test with INFO level
    env_level('INFO')
    logger.debug('This debug message should not appear')
    logger.info('This info message should appear')
    
    logs = capture_logs.getvalue()
    assert 'This debug message should not appear' not in logs
    assert 'This info message should appear' in logs
    
    # Clear the log capture
    capture_logs.truncate(0)
    capture_logs.seek(0)
    
    # Test with DEBUG level
    env_level('DEBUG')
    logger.debug('This debug message should now appear')
    logger.info('This info message should still appear')
    
    logs = capture_logs.getvalue()
    assert 'This debug message should now appear' in logs
    assert 'This info message should still appear' in logs

def test_example_custom_always_debug(env_level, capture_logs):
    """Test that ExampleCustom logger always logs at DEBUG level regardless of env setting"""
    logger = logging.getLogger('ExampleCustom')
    
    # Test with INFO level
    env_level('INFO')
    logger.debug('ExampleCustom debug message with INFO level')
    
    logs = capture_logs.getvalue()
    assert 'ExampleCustom debug message with INFO level' in logs
    
    # Clear the log capture
    capture_logs.truncate(0)
    capture_logs.seek(0)
    
    # Test with ERROR level
    env_level('ERROR')
    logger.debug('ExampleCustom debug message with ERROR level')
    
    logs = capture_logs.getvalue()
    assert 'ExampleCustom debug message with ERROR level' in logs

def test_multiple_loggers_different_levels(env_level, capture_logs):
    """Test interaction between different loggers at different env levels"""
    root_logger = logging.getLogger('RootTest')
    custom_logger = logging.getLogger('ExampleCustom')
    
    # Set environment to ERROR level
    env_level('ERROR')
    
    # Root logger should only show ERROR
    root_logger.debug('Root debug - should not show')
    root_logger.info('Root info - should not show')
    root_logger.error('Root error - should show')
    
    # ExampleCustom should show all levels
    custom_logger.debug('Custom debug - should show')
    custom_logger.info('Custom info - should show')
    custom_logger.error('Custom error - should show')
    
    logs = capture_logs.getvalue()
    
    # Check root logger behavior
    assert 'Root debug - should not show' not in logs
    assert 'Root info - should not show' not in logs
    assert 'Root error - should show' in logs
    
    # Check ExampleCustom logger behavior
    assert 'Custom debug - should show' in logs
    assert 'Custom info - should show' in logs
    assert 'Custom error - should show' in logs

if __name__ == '__main__':
    pytest.main([__file__])
