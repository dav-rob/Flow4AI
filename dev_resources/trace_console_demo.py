import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from job import Job
from job_chain import JobChain

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

if __name__ == "__main__":
    """
    Run the demo and observe the traces in console output.
    The traces will show:
    - Parallel execution of tasks with different delays using a single JobChain
    - Automatic tracing of the execute method
    - Task completion order based on delay times
    """
    asyncio.run(main())
