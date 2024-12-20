import importlib.util
import inspect
import os
import sys
from glob import glob
from pathlib import Path
from typing import Any, Dict, Type

import anyconfig

from job import JobABC


class JobValidationError(Exception):
    """Raised when a custom job fails validation"""
    pass

class CustomJobLoader:

    @staticmethod
    def validate_job_class(job_class: Type) -> bool:
        """
        Validate that a class meets the requirements to be a valid job:
        - Inherits from JobABC
        - Has required methods
        - Has required attributes
        """
        # Check if it's a class and inherits from JobABC
        if not (inspect.isclass(job_class) and issubclass(job_class, JobABC)):
            return False
        
        # Check for required async run method
        if not hasattr(job_class, 'run'):
            return False
        
        # Check if run method is async
        run_method = getattr(job_class, 'run')
        if not inspect.iscoroutinefunction(run_method):
            return False
        
        return True

    @classmethod
    def load_custom_jobs(cls, custom_jobs_dir: str) -> Dict[str, Type[JobABC]]:
        """
        Load all custom job classes from the specified directory
        """
        custom_jobs = {}
        custom_jobs_path = Path(custom_jobs_dir)

        if not custom_jobs_path.exists():
            raise FileNotFoundError(f"Custom jobs directory not found: {custom_jobs_dir}")

        # Add the custom jobs directory to Python path
        sys.path.append(str(custom_jobs_path))

        # Scan for Python files
        for file_path in custom_jobs_path.glob("**/*.py"):
            if file_path.name.startswith("__"):
                continue

            try:
                # Load the module
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, str(file_path))
                if spec is None or spec.loader is None:
                    continue
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all classes in the module that inherit from JobABC
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module.__name__:
                        try:
                            if cls.validate_job_class(obj):
                                custom_jobs[name] = obj
                        except Exception as e:
                            raise JobValidationError(
                                f"Error validating job class {name} in {file_path}: {str(e)}"
                            )

            except Exception as e:
                raise ImportError(
                    f"Error loading custom job from {file_path}: {str(e)}"
                )

        return custom_jobs

class JobFactory:
    _job_types: Dict[str, Type[JobABC]] = {}
    _default_jobs_dir: str = os.path.join(os.path.dirname(__file__), "jobs")
    
    @classmethod
    def load_custom_jobs_directory(cls, custom_jobs_dir: str):
        """
        Load and register all custom jobs from a directory
        """
        loader = CustomJobLoader()
        # Create an iterable of directories, including the default and any custom directory.
        jobs_dirs = [cls._default_jobs_dir] + ([custom_jobs_dir] if custom_jobs_dir else [])
        for jobs_dir in jobs_dirs:
          custom_jobs = loader.load_custom_jobs(jobs_dir)
          # Register all valid custom jobs
          for job_name, job_class in custom_jobs.items():
              cls.register_job_type(job_name, job_class)
              print(f"Registered custom job: {job_name}")

    @classmethod
    def create_job(cls, name: str, job_type: str, properties: Dict[str, Any]) -> JobABC:
        if job_type not in cls._job_types:
            raise ValueError(f"Unknown job type: {job_type}")
        return cls._job_types[job_type](name, properties)

    @classmethod
    def register_job_type(cls, type_name: str, job_class: Type[JobABC]):
        cls._job_types[type_name] = job_class

class ConfigLoader:
    @classmethod
    def load_config(cls, base_name: str) -> dict:
        # Find all files matching the pattern
        matches = glob(f"{base_name}.*")
        if not matches:
            raise FileNotFoundError(f"No configuration file found matching {base_name}.*")
        # Use the first match
        return anyconfig.load(matches[0])

    @classmethod
    def get_graphs_config(cls) -> dict:
        return cls.load_config("graphs")

    @classmethod
    def get_jobs_config(cls) -> dict:
        return cls.load_config("jobs")

    @classmethod
    def get_parameters_config(cls) -> dict:
        return cls.load_config("parameters")
