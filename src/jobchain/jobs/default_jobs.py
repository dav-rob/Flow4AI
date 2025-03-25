import copy
from typing import Any, Dict, Union

from jobchain import jc_logging as logging
from jobchain.job import JobABC, Task

logger = logging.getLogger(__name__)


class DefaultHeadJob(JobABC):
    """A Job implementation that provides a simple default behavior."""
    
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Run a simple job that logs and returns the task."""
        logger.info(f"Default head JOB for {task}")
        return {}

class DefaultTailJob(JobABC):
    """A Job implementation that provides a simple default behavior."""
    
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Run a simple job that logs and returns the task."""
        logger.info(f"Default tail JOB for {task}")
        inputs_with_short_job_name = self.get_inputs()
        return inputs_with_short_job_name