import importlib.util
import inspect
import os
import sys
from glob import glob
from pathlib import Path
from typing import Any, Collection, Dict, List, Type

import anyconfig

import jc_logging as logging
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

    @classmethod
    def create_head_jobs_from_config(cls) -> Collection[JobABC]:
        job_graphs: list[JobABC] = []
        graphs_config = ConfigLoader.get_graphs_config()
        graph_names = list(graphs_config.keys())
        for graph_name in graph_names:
            graph_def = graphs_config[graph_name]
            job_names_in_graph = list(graph_def.keys())
            param_groups_for_graph_name = ConfigLoader.get_parameters_config().get(graph_name, {})
            if param_groups_for_graph_name:
                param_jobs_graphs: List[JobABC] = cls.create_job_graph_using_parameters(graph_def, graph_name,
                                                                                        param_groups_for_graph_name,
                                                                                        job_names_in_graph)
                job_graphs += param_jobs_graphs
            else:
                job_graph_no_params: JobABC = cls.create_job_graph_no_params(graph_def, graph_name,
                                                                                     job_names_in_graph)
                job_graphs.append(job_graph_no_params)
        return job_graphs

    @classmethod
    def create_job_graph_using_parameters(cls, graph_def, graph_name, param_groups_for_graph_name,
                                          job_names_in_graph) -> List[JobABC]:
        job_graphs: list[JobABC] = []
        params_for_graph_name = list(param_groups_for_graph_name.keys())
        for param_name in params_for_graph_name:
            job_instances: dict[str, JobABC] = {}
            for graph_job_name in job_names_in_graph:
                raw_job_def: Dict[str, Any] = ConfigLoader.get_jobs_config()[graph_job_name]
                if ConfigLoader.is_parameterized_job(raw_job_def):
                    job_def: Dict[str, Any] = ConfigLoader.fill_job_with_parameters(raw_job_def, graph_name, param_name)
                else:
                    job_def = raw_job_def
                unique_job_name = graph_name + "_" + param_name + "_" + graph_job_name
                job_type: str = job_def["type"]
                job: JobABC = cls.create_job(unique_job_name, job_type, job_def)
                job_instances[graph_job_name] = job
            job_graph: JobABC = create_job_graph(graph_def, job_instances)
            job_graphs.append(job_graph)
        return job_graphs

    @classmethod
    def create_job_graph_no_params(cls, graph_def, graph_name, job_names_in_graph)-> JobABC:
        job_instances: dict[str, JobABC] = {}
        for graph_job_name in job_names_in_graph:
                job_def: Dict[str, Any] = ConfigLoader.get_jobs_config()[graph_job_name]
                unique_job_name = graph_name + "_" + "_" + graph_job_name
                job_type: str = job_def["type"]
                job: JobABC = cls.create_job(unique_job_name, job_type, job_def)
                job_instances[graph_job_name] = job
        job_graph: JobABC = create_job_graph(graph_def, job_instances)
        return job_graph


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
        logging.info(f"Looking for config files in directories: {dir_paths}")

        # For each config file we want to find
        for config_base in config_bases:
            logging.info(f"Looking for {config_base} config file...")
            # Search through directories in order
            for dir_path in dir_paths:
                if not dir_path.exists():
                    logging.info(f"Directory {dir_path} does not exist")
                    continue

                # Look for matching files
                matches = [f for f in dir_path.glob(f"{config_base}.*")
                           if f.suffix.lower() in allowed_extensions]
                logging.info(f"Found matches in {dir_path}: {matches}")

                # If we found a match, load it and break the directory loop
                if matches:
                    try:
                        configs[config_base] = anyconfig.load(str(matches[0]))  # Convert Path to string for anyconfig
                        logging.info(f"Loaded {matches[0]} with content: {configs[config_base]}")  # Debug print
                        break  # Stop searching other directories for this config
                    except Exception as e:
                        logging.error(f"Error loading {matches[0]}: {e}")
                        continue

        logging.info(f"Final configs: {configs}")
        return configs

    @classmethod
    def _extract_config_section(cls, configs: Dict[str, dict], section_name: str) -> dict:
        """
        Extract a configuration section from either a dedicated file or jobchain_all.
        
        Args:
            configs: Dictionary containing all configurations
            section_name: Name of the section to extract (e.g., 'graphs', 'jobs', 'parameters')
            
        Returns:
            Dictionary containing the configuration section, or empty dict if not found
        """
        # Try to get from dedicated file first
        if section_name in configs:
            return configs[section_name]

        # If not found, try to get from jobchain_all
        if 'jobchain_all' in configs and isinstance(configs['jobchain_all'], dict):
            return configs['jobchain_all'].get(section_name, {})

        # If nothing found, return empty dict
        return {}

    @classmethod
    def _find_parameterized_fields(cls, job_config: dict) -> set:
        """
        Find all parameterized fields in a job configuration.
        A field is parameterized if its value starts with '$'.
        
        Args:
            job_config: Job configuration dictionary
            
        Returns:
            Set of parameterized field names
        """
        params = set()

        def search_dict(d):
            for k, v in d.items():
                if isinstance(v, dict):
                    search_dict(v)
                elif isinstance(v, str) and v.startswith('$'):
                    params.add(v[1:])  # Remove the '$' prefix

        search_dict(job_config.get('properties', {}))
        return params

    @classmethod
    def validate_configs(cls, configs: Dict[str, dict]) -> None:
        """
        Validate that:
        1. All jobs referenced in graphs exist in jobs configuration
        2. All parameterized jobs have corresponding parameter values
        3. Each graph structure is valid (no cycles, proper head/tail nodes, valid references)
        
        Args:
            configs: Dictionary containing all configurations
            
        Raises:
            ValueError: If validation fails
        """
        graphs_config = cls._extract_config_section(configs, 'graphs')
        jobs_config = cls._extract_config_section(configs, 'jobs')
        parameters_config = cls._extract_config_section(configs, 'parameters')

        if not graphs_config or not jobs_config:
            return

        # First validate that all jobs in graphs exist
        defined_jobs = set(jobs_config.keys())

        for graph_name, graph_def in graphs_config.items():
            for job_name, job_def in graph_def.items():
                if job_name not in defined_jobs:
                    raise ValueError(
                        f"Job '{job_name}' referenced in graph '{graph_name}' is not defined in jobs configuration")

                # Check jobs in 'next' field
                next_jobs = job_def.get('next', [])
                for next_job in next_jobs:
                    if next_job not in defined_jobs:
                        raise ValueError(
                            f"Job '{next_job}' referenced in 'next' field of job '{job_name}' in graph '{graph_name}' is not defined in jobs configuration")
                    
            # After verifying all jobs exist, validate graph structure
            from jc_graph import validate_graph
            validate_graph(graph_def, graph_name)

        # Now validate parameters
        for graph_name, graph_def in graphs_config.items():
            # Find all parameterized jobs in this graph
            graph_parameterized_jobs = {}
            for job_name in graph_def.keys():
                job_config = jobs_config[job_name]
                params = cls._find_parameterized_fields(job_config)
                if params:
                    graph_parameterized_jobs[job_name] = params

            # If graph has parameterized jobs, it must have parameters
            if graph_parameterized_jobs:
                if graph_name not in parameters_config:
                    raise ValueError(
                        f"Graph '{graph_name}' contains parameterized jobs {list(graph_parameterized_jobs.keys())} but has no entry in parameters configuration")

                graph_params = parameters_config[graph_name]

                # Validate parameter groups
                for group_name in graph_params.keys():
                    if not group_name.startswith('params'):
                        raise ValueError(
                            f"Invalid parameter group name '{group_name}' in graph '{graph_name}'. Parameter groups must start with 'params'")

                # Validate that all parameters are filled for each group
                for group_name, group_params in graph_params.items():
                    for job_name, required_params in graph_parameterized_jobs.items():
                        if job_name not in group_params:
                            raise ValueError(
                                f"Job '{job_name}' in graph '{graph_name}' requires parameters {required_params} but has no entry in parameter group '{group_name}'")

                        # Each job should have a list of parameter sets
                        job_param_sets = group_params[job_name]
                        if not isinstance(job_param_sets, list):
                            raise ValueError(
                                f"Parameters for job '{job_name}' in graph '{graph_name}', group '{group_name}' should be a list of parameter sets")

                        # Check each parameter set
                        for param_set in job_param_sets:
                            missing_params = required_params - set(param_set.keys())
                            if missing_params:
                                raise ValueError(
                                    f"Parameter set for job '{job_name}' in graph '{graph_name}', group '{group_name}' is missing required parameters: {missing_params}")

            # If graph has no parameterized jobs, it should not have parameters
            elif graph_name in parameters_config:
                raise ValueError(
                    f"Graph '{graph_name}' has no parameterized jobs but has an entry in parameters configuration")

    @classmethod
    def load_all_configs(cls) -> Dict[str, dict]:
        """Load all configurations and validate them"""
        cls._cached_configs = cls.load_configs_from_dirs(cls.directories)
        cls.validate_configs(cls._cached_configs)
        return cls._cached_configs

    @classmethod
    def reload_configs(cls) -> Dict[str, dict]:
        """Force a reload of all configurations."""
        logging.info("Reloading configs...")
        cls._cached_configs = None
        return cls.load_all_configs()

    @classmethod
    def get_graphs_config(cls) -> dict:
        """
        Get graphs configuration from either dedicated graphs file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        return cls._extract_config_section(configs, 'graphs')

    @classmethod
    def get_jobs_config(cls) -> dict:
        """
        Get jobs configuration from either dedicated jobs file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        return cls._extract_config_section(configs, 'jobs')

    @classmethod
    def get_parameters_config(cls) -> dict:
        """
        Get parameters configuration from either dedicated parameters file or jobchain_all.
        Returns empty dict if no configuration is found.
        """
        configs = cls.load_all_configs()
        return cls._extract_config_section(configs, 'parameters')

    @classmethod
    def is_parameterized_job(cls, raw_job_def):
        """
        Check if a job definition contains parameterized fields.
        
        Args:
            raw_job_def: Raw job definition from jobs.yaml
            
        Returns:
            bool: True if job has parameterized fields, False otherwise
        """
        if not isinstance(raw_job_def, dict):
            return False
            
        # Use existing method to find parameterized fields
        params = cls._find_parameterized_fields(raw_job_def)
        return len(params) > 0

    @classmethod
    def fill_job_with_parameters(cls, job_config: dict, graph_name: str, param_group: str) -> dict:
        """
        Fill a job configuration with parameters from parameters.yaml.
        
        Args:
            job_config: Raw job configuration from jobs.yaml
            graph_name: Name of the graph containing the job
            param_group: Name of the parameter group to use
            
        Returns:
            dict: Job configuration with parameters filled in
        """
        # Deep copy the job config to avoid modifying the original
        import copy
        filled_config = copy.deepcopy(job_config)
        
        # Get parameters for this job from parameters.yaml
        params_config = cls.get_parameters_config()
        if graph_name not in params_config or param_group not in params_config[graph_name]:
            raise ValueError(f"No parameters found for graph '{graph_name}' and group '{param_group}'")
            
        # Get the job name by finding which job in the parameters matches this config
        job_name = None
        for job in params_config[graph_name][param_group].keys():
            if job_config == cls.get_jobs_config()[job]:
                job_name = job
                break
                
        if job_name is None:
            raise ValueError(f"Could not find job in parameters for graph '{graph_name}' and group '{param_group}'")
            
        # Get parameter values for this job
        param_sets = params_config[graph_name][param_group][job_name]
        if not param_sets or not isinstance(param_sets, list):
            raise ValueError(f"Invalid parameter sets for job '{job_name}' in graph '{graph_name}', group '{param_group}'")
            
        # Use the first parameter set (as defined in the spec)
        param_values = param_sets[0]
        
        def replace_params(obj, params):
            if isinstance(obj, dict):
                return {k: replace_params(v, params) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_params(item, params) for item in obj]
            elif isinstance(obj, str) and obj.startswith('$'):
                param_name = obj[1:]  # Remove '$' prefix
                if param_name not in params:
                    raise ValueError(f"Parameter '{param_name}' not found in parameter set")
                return params[param_name]
            return obj
            
        # Replace all parameterized values in the config
        filled_config = replace_params(filled_config, param_values)
        return filled_config
