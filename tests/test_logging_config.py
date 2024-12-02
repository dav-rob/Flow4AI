import os
import pytest
import jc_logging as logging

@pytest.fixture
def clear_log_file():
    """Clear the log file before each test."""
    if os.path.exists('jobchain.log'):
        os.remove('jobchain.log')
    yield
    if os.path.exists('jobchain.log'):
        os.remove('jobchain.log')

def test_logging_config_debug(clear_log_file):
    """Test that DEBUG level logging works when JOBCHAIN_LOG_LEVEL is set to DEBUG."""
    os.environ['JOBCHAIN_LOG_LEVEL'] = 'DEBUG'
    logging.setup_logging()  # Reload config with new log level
    
    # Create a logger and log a debug message
    logger = logging.getLogger('test')
    logger.debug('This is a debug message')
    
    # Check if the debug message appears in the log file
    with open('jobchain.log', 'r') as f:
        log_contents = f.read()
    assert 'This is a debug message' in log_contents

def test_logging_config_info(clear_log_file):
    """Test that DEBUG logs are filtered when JOBCHAIN_LOG_LEVEL is set to INFO."""
    os.environ['JOBCHAIN_LOG_LEVEL'] = 'INFO'
    logging.setup_logging()  # Reload config with new log level
    
    # Create a logger and log messages at different levels
    logger = logging.getLogger('test')
    logger.debug('This is a debug message')
    logger.info('This is an info message')
    
    # Check that only INFO message appears in the log file
    with open('jobchain.log', 'r') as f:
        log_contents = f.read()
    assert 'This is a debug message' not in log_contents
    assert 'This is an info message' in log_contents

if __name__ == '__main__':
    pytest.main([__file__])
