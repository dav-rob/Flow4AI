import asyncio
import functools
import logging
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Type, TypeVar

from utils.otel_wrapper import trace_function


def _is_traced(method):
    """Helper function to check if a method is traced."""
    return hasattr(method, '_is_traced') and method._is_traced


def _mark_traced(method):
    """Helper function to mark a method as traced."""
    method._is_traced = True
    return method


def traced_job(cls: Type) -> Type:
    """
    Class decorator that ensures the execute method is traced.
    This is automatically applied to all Job subclasses.
    """
    if hasattr(cls, 'execute'):
        original_execute = cls.execute
        traced_execute = trace_function(original_execute)
        traced_execute = _mark_traced(traced_execute)
        # Store original as executeNoTrace
        cls.executeNoTrace = original_execute
        # Replace execute with traced version
        cls.execute = traced_execute
    return cls


class UntracedJob(ABC):
    """
    Abstract base class for jobs that don't require tracing.
    WARNING: This class should only be used in special cases where tracing is not desired.
    For normal usage, inherit from Job instead which ensures proper tracing.
    """
    def __init__(self, name: str, prompt: str, model: str):
        self.name = name
        self.prompt = prompt
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def execute(self, task) -> Dict[str, Any]:
        """Execute the job on the given task. Must be implemented by subclasses."""
        pass


class JobMeta(ABCMeta):
    """Metaclass that automatically applies the traced_job decorator to all Job subclasses."""
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != 'Job':  # Don't decorate the Job class itself
            return traced_job(cls)
        return cls


class Job(UntracedJob, metaclass=JobMeta):
    """
    Base class for all job implementations. Automatically applies tracing to
    execute method to ensure proper monitoring.
    
    Example:
        class MyJob(Job):
            async def execute(self, task):
                return {"result": "success"}
    
    The execute method will automatically be traced, and the original untraced
    version will be available as executeNoTrace if needed.
    """
    @abstractmethod
    async def execute(self, task) -> Dict[str, Any]:
        """
        Execute the job on the given task. Must be implemented by subclasses.
        This method is automatically traced in all subclasses.
        """
        pass


class SimpleJob(Job):
    """A Job implementation that provides a simple default behavior."""
    
    async def execute(self, task) -> Dict[str, Any]:
        """Execute a simple job that logs and returns the task."""
        self.logger.info(f"Async JOB for {task}")
        await asyncio.sleep(1)  # Simulate network delay
        return {"task": task, "status": "complete"}


class JobFactory:
    """Factory class for creating Job instances with proper tracing."""
    
    @staticmethod
    def _load_from_file(params: Dict[str, Any]) -> Job:
        """Create a traced job instance from file configuration."""
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job with params: {params}")
        return SimpleJob("File Job", "Sample prompt from file", "gpt-3.5-turbo")

    @staticmethod
    def _load_from_datastore(params: Dict[str, Any]) -> Job:
        """Create a traced job instance from datastore."""
        logger = logging.getLogger('JobFactory')
        logger.info(f"Loading job from datastore with params: {params}")
        return SimpleJob("Datastore Job", "Sample prompt from datastore", "gpt-3.5-turbo")

    @staticmethod
    def load_job(job_context: Dict[str, Any]) -> Job:
        """Load a job instance with proper tracing based on context."""
        load_type = job_context.get("type", "").lower()
        params = job_context.get("params", {})

        if load_type == "file":
            return JobFactory._load_from_file(params)
        elif load_type == "datastore":
            return JobFactory._load_from_datastore(params)
        else:
            raise ValueError(f"Unsupported job type: {load_type}")
