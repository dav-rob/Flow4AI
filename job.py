import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict


class Job(ABC):
    def __init__(self, name: str, prompt: str, model: str):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, task) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass

class SimpleJob(Job):
    """A Job implementation that provides a simple default behavior."""
    async def execute(self, task) -> Dict[str, Any]:
        self.logger.info(f"Async JOB for {task}")
        await asyncio.sleep(1)  # Simulate network delay
        return f"JOB of {task} complete"

class JobFactory:
    @staticmethod
    def _load_from_file(params: Dict[str, Any]) -> Job:
        # Placeholder for loading job from file
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job with params: {params}")
        return SimpleJob("File Job", "Sample prompt from file", "gpt-3.5-turbo")

    @staticmethod
    def _load_from_datastore(params: Dict[str, Any]) -> Job:
        # Placeholder for loading job from datastore
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job from datastore with params: {params}")
        return SimpleJob("Datastore Job", "Sample prompt from datastore", "gpt-3.5-turbo")

    @staticmethod
    def load_job(job_context: Dict[str, Any]) -> Job:
        load_type = job_context.get("type", "").lower()
        params = job_context.get("params", {})

        if load_type == "file":
            return JobFactory._load_from_file(params)
        elif load_type == "datastore":
            return JobFactory._load_from_datastore(params)
        else:
            raise ValueError(f"Unsupported job type: {load_type}")
