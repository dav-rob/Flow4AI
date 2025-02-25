"""
Test utilities for JobChain tests.

This module contains simple job implementations that are used in tests.
These are not intended for production use.
"""
import asyncio
from typing import Any, Dict, Union

from jobchain import jc_logging as logging
from jobchain.job import JobABC, Task


class SimpleJob(JobABC):
    """A Job implementation that provides a simple default behavior."""
    
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """Run a simple job that logs and returns the task."""
        logging.info(f"Async JOB for {task}")
        await asyncio.sleep(1)  # Simulate network delay
        return {"task": task, "status": "complete"}


class SimpleJobFactory:
    """Factory class for creating Job instances with proper tracing."""
    
    @staticmethod
    def _load_from_file(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from file configuration."""
        logging.info(f"Loading job with params: {params}")
        return SimpleJob("File Job")

    @staticmethod
    def _load_from_datastore(params: Dict[str, Any]) -> JobABC:
        """Create a traced job instance from datastore."""
        logging.info(f"Loading job from datastore with params: {params}")
        return SimpleJob("Datastore Job")

    @staticmethod
    def load_job(job_context: Dict[str, Any]) -> JobABC:
        """Load a job instance with proper tracing based on context."""
        load_type = job_context.get("type", "").lower()
        params = job_context.get("params", {})

        if load_type == "file":
            return SimpleJobFactory._load_from_file(params)
        elif load_type == "datastore":
            return SimpleJobFactory._load_from_datastore(params)
        else:
            raise ValueError(f"Unsupported job type: {load_type}")
