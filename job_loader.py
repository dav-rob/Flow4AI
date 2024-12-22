import importlib.util
import inspect
import os
import sys
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Type

import anyconfig

from job import JobABC, create_job_graph


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
    directories = [
            "./local/config",
            "/etc/myapp/config"
        ]
    _cached_configs: Dict[str, dict] = None
    
    @classmethod
    def load_configs_from_dirs(
        cls,
        directories: List[str] = ["./config", "/etc/myapp/config"],
        config_bases: List[str] = ['graphs', 'jobs', 'parameters', 'jobchain_all'],
        allowed_extensions: tuple = ('.yaml', '.yml', '.json')
    ) -> Dict[str, dict]:
        """
        Load configuration files from multiple directories.
        
        Args:
            directories: List of directory paths to search
            config_bases: List of configuration file base names to look for
            allowed_extensions: Tuple of allowed file extensions
        
        Returns:
            Dictionary with config_base as key and loaded config as value
        """
        configs: Dict[str, dict] = {}
        
        # Convert directories to Path objects
        dir_paths = [Path(str(d)) for d in directories]  # Handle both string and Path objects
        print(f"Looking for config files in directories: {dir_paths}")
        
        # For each config file we want to find
        for config_base in config_bases:
            print(f"Looking for {config_base} config file...")
            # Search through directories in order
            for dir_path in dir_paths:
                if not dir_path.exists():
                    print(f"Directory {dir_path} does not exist")
                    continue
                    
                # Look for matching files
                matches = [f for f in dir_path.glob(f"{config_base}.*") 
                        if f.suffix.lower() in allowed_extensions]
                print(f"Found matches in {dir_path}: {matches}")
                
                # If we found a match, load it and break the directory loop
                if matches:
                    try:
                        configs[config_base] = anyconfig.load(str(matches[0]))  # Convert Path to string for anyconfig
                        print(f"Loaded {matches[0]} with content: {configs[config_base]}")  # Debug print
                        break  # Stop searching other directories for this config
                    except Exception as e:
                        print(f"Error loading {matches[0]}: {e}")
                        continue
        
        print(f"Final configs: {configs}")
        return configs
    
    @classmethod
    def load_all_configs(cls) -> Dict[str, dict]:
        if cls._cached_configs is None:
            print(f"Loading all configs from directories: {cls.directories}")
            cls._cached_configs = cls.load_configs_from_dirs(cls.directories)
            print(f"Loaded configs: {cls._cached_configs}")
        return cls._cached_configs

    @classmethod
    def reload_configs(cls) -> Dict[str, dict]:
        """Force a reload of all configurations."""
        print("Reloading configs...")
        cls._cached_configs = None
        return cls.load_all_configs()
    
    @classmethod
    def get_graphs_config(cls) -> dict:
        """
        Get graphs configuration from either dedicated graphs file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        print(f"Getting graphs config from: {configs}")
        
        # Try to get from dedicated graphs file first
        if 'graphs' in configs:
            print(f"Found graphs config: {configs['graphs']}")
            return configs['graphs']
            
        # If not found, try to get from jobchain_all
        if 'jobchain_all' in configs and isinstance(configs['jobchain_all'], dict):
            print(f"Found graphs config in jobchain_all: {configs['jobchain_all'].get('graphs', {})}")
            return configs['jobchain_all'].get('graphs', {})
            
        # If nothing found, return empty dict
        print("No graphs config found")
        return {}

    @classmethod
    def get_jobs_config(cls) -> dict:
        """
        Get jobs configuration from either dedicated jobs file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        
        # Try to get from dedicated jobs file first
        if 'jobs' in configs:
            return configs['jobs']
            
        # If not found, try to get from jobchain_all
        if 'jobchain_all' in configs and isinstance(configs['jobchain_all'], dict):
            return configs['jobchain_all'].get('jobs', {})
            
        # If nothing found, return empty dict
        return {}

    @classmethod
    def get_parameters_config(cls) -> dict:
        """
        Get parameters configuration from either dedicated parameters file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        
        # Try to get from dedicated parameters file first
        if 'parameters' in configs:
            return configs['parameters']
            
        # If not found, try to get from jobchain_all
        if 'jobchain_all' in configs and isinstance(configs['jobchain_all'], dict):
            return configs['jobchain_all'].get('parameters', {})
            
        # If nothing found, return empty dict
        return {}
