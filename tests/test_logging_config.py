import os
import pytest
from jobchain import jc_logging as logging
import asyncio
from jobchain import job as job
from jobchain import job_chain as job_chain

class DebugDelayedJob(job.JobABC):
    def __init__(self, name: str, delay: float):
        super().__init__(name)
        self.delay = delay
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self, task: job.Task) -> dict:
        """Execute a delayed job with both debug and info logging."""
        task_str = task.get('task', str(task))  # Get task string or full dict
        self.logger.debug(f"Starting task {task_str} with delay {self.delay}")
        self.logger.info(f"Processing task {task_str}")
        await asyncio.sleep(self.delay)
        self.logger.debug(f"Completed task {task_str}")
        return {"task": dict(task), "status": "complete"}

@pytest.fixture
def clear_log_file():
    """Clear the log file before each test."""
    if os.path.exists('jobchain.log'):
        os.remove('jobchain.log')
    yield
    if os.path.exists('jobchain.log'):
        os.remove('jobchain.log')
    # Clear any environment variables that might affect logging
    os.environ.pop('JOBCHAIN_LOG_HANDLERS', None)
    os.environ.pop('JOBCHAIN_LOG_LEVEL', None)

def test_logging_handlers_default(clear_log_file):
    """Test that by default, logs are only written to console and not to file."""
    logging.setup_logging()
    logger = logging.getLogger('test')
    logger.info('This is a test message')
    
    with open('jobchain.log', 'r') as f:
        lines = f.readlines()
    # Should only contain the header comment
    assert len(lines) == 1, "Log file should only contain header comment"
    assert lines[0].startswith('# JobChain log file'), "Log file should only contain header comment"

def test_logging_handlers_console_explicit(clear_log_file):
    """Test that when JOBCHAIN_LOG_HANDLERS='console', logs are not written to file."""
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console'
    logging.setup_logging()
    logger = logging.getLogger('test')
    logger.info('This is a test message')
    
    with open('jobchain.log', 'r') as f:
        lines = f.readlines()
    # Should only contain the header comment
    assert len(lines) == 1, "Log file should only contain header comment"
    assert lines[0].startswith('# JobChain log file'), "Log file should only contain header comment"

def test_logging_handlers_file(clear_log_file):
    """Test that when JOBCHAIN_LOG_HANDLERS includes 'file', logs are written to file."""
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console,file'
    logging.setup_logging()
    logger = logging.getLogger('test')
    test_message = 'This should be in the log file'
    logger.info(test_message)
    
    with open('jobchain.log', 'r') as f:
        lines = f.readlines()
    # Should contain both header and log message
    assert len(lines) > 1, "Log file should contain header and log messages"
    assert lines[0].startswith('# JobChain log file'), "First line should be header comment"
    assert any(test_message in line for line in lines[1:]), "Test message should be in log file"

def test_logging_config_debug(clear_log_file):
    """Test that DEBUG level logging works when JOBCHAIN_LOG_LEVEL is set to DEBUG."""
    os.environ['JOBCHAIN_LOG_LEVEL'] = 'DEBUG'
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console,file'  # Enable file logging for this test
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
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console,file'  # Enable file logging for this test
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

def test_debug_logging_in_job_chain(clear_log_file):
    """Test that both JobChain and Job debug logs are visible when JOBCHAIN_LOG_LEVEL=DEBUG."""
    os.environ['JOBCHAIN_LOG_LEVEL'] = 'DEBUG'
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console,file'  # Enable file logging for this test
    logging.setup_logging()  # Reload config with new log level

    # Create and run job chain with debug-enabled job
    job = DebugDelayedJob("Debug Test Job", 0.1)
    job_chain = job_chain.JobChain(job)

    # Submit tasks
    for i in range(3):
        job_chain.submit_task({'task': f'Task {i}'})  # Changed to use dict format
    job_chain.mark_input_completed()

    # Check log file contents
    with open('jobchain.log', 'r') as f:
        log_contents = f.read()
        log_lines = log_contents.splitlines()

    # Separate JobChain and DebugDelayedJob debug logs
    jobchain_debug_logs = [line for line in log_lines if '[DEBUG]' in line and 'JobChain' in line]
    delayed_job_debug_logs = [line for line in log_lines if '[DEBUG]' in line and 'DebugDelayedJob' in line]

    # Verify JobChain has debug logs
    assert len(jobchain_debug_logs) > 0, "No DEBUG logs found from JobChain"
    print("\nJobChain DEBUG logs:")
    for log in jobchain_debug_logs[:3]:  # Print first 3 for verification
        print(log)

    # Verify DebugDelayedJob has debug logs
    assert len(delayed_job_debug_logs) > 0, "No DEBUG logs found from DebugDelayedJob"
    print("\nDebugDelayedJob DEBUG logs:")
    for log in delayed_job_debug_logs[:3]:  # Print first 3 for verification
        print(log)

    # Verify specific debug messages from DebugDelayedJob
    delayed_job_debug_messages = [line.split('] ')[-1] for line in delayed_job_debug_logs]
    assert any('Starting task Task' in msg for msg in delayed_job_debug_messages)
    assert any('Completed task Task' in msg for msg in delayed_job_debug_messages)

    # Verify info logs are also present
    info_logs = [line for line in log_lines if '[INFO]' in line]
    assert any('Processing task Task' in line for line in info_logs)

def test_info_logging_in_job_chain(clear_log_file):
    """Test that DEBUG logs are filtered when JOBCHAIN_LOG_LEVEL=INFO."""
    os.environ['JOBCHAIN_LOG_LEVEL'] = 'INFO'
    os.environ['JOBCHAIN_LOG_HANDLERS'] = 'console,file'  # Enable file logging for this test
    logging.setup_logging()  # Reload config with new log level

    # Create and run job chain with debug-enabled job
    job = DebugDelayedJob("Info Test Job", 0.1)
    job_chain = job_chain.JobChain(job)

    # Submit tasks
    for i in range(3):
        job_chain.submit_task({'task': f'Task {i}'})  # Changed to use dict format
    job_chain.mark_input_completed()

    # Check log file contents
    with open('jobchain.log', 'r') as f:
        log_contents = f.read()
        log_lines = log_contents.splitlines()

    # Check for absence of DEBUG logs
    debug_logs = [line for line in log_lines if '[DEBUG]' in line]
    assert len(debug_logs) == 0, f"Found unexpected DEBUG logs:\n" + "\n".join(debug_logs[:3])

    # Verify INFO logs are present for both components
    jobchain_info_logs = [line for line in log_lines if '[INFO]' in line and 'JobChain' in line]
    delayed_job_info_logs = [line for line in log_lines if '[INFO]' in line and 'DebugDelayedJob' in line]

    # Verify JobChain info logs
    assert len(jobchain_info_logs) > 0, "No INFO logs found from JobChain"
    print("\nJobChain INFO logs:")
    for log in jobchain_info_logs[:3]:  # Print first 3 for verification
        print(log)

    # Verify DebugDelayedJob info logs
    assert len(delayed_job_info_logs) > 0, "No INFO logs found from DebugDelayedJob"
    print("\nDebugDelayedJob INFO logs:")
    for log in delayed_job_info_logs[:3]:  # Print first 3 for verification
        print(log)

    # Verify specific info messages from DebugDelayedJob
    delayed_job_info_messages = [line.split('] ')[-1] for line in delayed_job_info_logs]
    assert any('Processing task Task' in msg for msg in delayed_job_info_messages)

if __name__ == '__main__':
    pytest.main([__file__])
