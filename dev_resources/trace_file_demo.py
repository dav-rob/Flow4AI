import asyncio
import atexit
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from job import Job
from job_chain import JobChain

# Set the OpenTelemetry configuration file
os.environ['JOBCHAIN_OT_CONFIG'] = str(Path(__file__).parent / 'trace_file_config.yaml')

# Configure logging - Set root logger to DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Register shutdown logging
def log_shutdown():
    logger.debug("Python interpreter shutdown started")
atexit.register(log_shutdown)

class DelayedJob(Job):
    """A simple job that delays for a specified time to demonstrate tracing"""
    def __init__(self, name: str, delay: float):
        super().__init__(name)
        self.delay = delay

    async def run(self, task) -> dict:
        """Execute job with specified delay"""
        task_id, delay = task  # Unpack the task data
        logger.info(f"Starting task {task_id} with delay {delay}s")
        await asyncio.sleep(delay)
        logger.info(f"Completed task {task_id}")
        return {"task_id": task_id, "status": "complete", "delay": delay}

def process_result(result: dict):
    """Simple result processor that logs the result"""
    logger.info(f"Processed result: {result}")

async def main():
    """Run multiple tasks with different delays to demonstrate parallel execution and tracing"""
    logger.debug("Starting main function")
    
    # Create a single job that can handle varying delays
    job = DelayedJob("Parallel Demo Job", 0)  # Delay will be specified per task
    
    # Create single JobChain instance
    job_chain = JobChain(job, process_result)
    
    # Submit tasks with different delays
    delays = [1.0, 2.0, 3.0]
    for delay in delays:
        for i in range(3):
            # Pass both task ID and delay as the task data
            job_chain.submit_task((f"Task-{i}-{delay}s", delay))
    
    # Mark chain as complete
    job_chain.mark_input_completed()
    
    # Wait for all tasks to complete
    # Total wait time slightly longer than longest task (3s) * number of tasks (3)
    await asyncio.sleep(10)
    logger.debug("Main function completed")

if __name__ == "__main__":
    """
    Run the demo and observe the traces in temp/trace_output.json.
    The traces will show:
    - Parallel execution of tasks with different delays using a single JobChain
    - Automatic tracing of the execute method
    - Task completion order based on delay times
    
    The trace output file will be created in temp/trace_output.json and can be
    inspected after the program completes.
    """
    try:
        logger.debug("Program starting")
        asyncio.run(main())
        logger.debug("Program execution completed")
    finally:
        logger.debug("Program entering shutdown phase")
        # Log OpenTelemetry trace file path
        trace_file = Path(__file__).parent / 'trace_output.json'
        logger.debug(f"OpenTelemetry trace file path: {trace_file}")
