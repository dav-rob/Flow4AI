import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Collection, Dict, List, Type

import yaml

from . import jc_logging as logging
from .job import JobABC, create_job_graph


class JobValidationError(Exception):
    """Raised when a custom job fails validation"""
    pass


class ConfigurationError(Exception):
    """Exception raised when configuration is malformed."""
    pass


class JobLoader:

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
    def load_jobs(cls, jobs_dir: str) -> Dict[str, Type[JobABC]]:
        """
        Load all custom job classes from the specified directory
        """
        jobs = {}
        jobs_path = Path(jobs_dir)

        if not jobs_path.exists():
            logging.info(f"Jobs directory not found: {jobs_dir}")
            return jobs

        # Add the custom jobs directory to Python path
        logging.debug(f"Python path before: {sys.path}")
        sys.path.append(str(jobs_path))
        logging.info(f"Added {jobs_path} to Python path")
        logging.debug(f"Python path after: {sys.path}")

        # Scan for Python files
        for file_path in jobs_path.glob("**/*.py"):
            if file_path.name.startswith("__"):
                continue

            logging.info(f"Loading jobs from {file_path}")
            try:
                # Load the module
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, str(file_path))
                if spec is None or spec.loader is None:
                    logging.warning(f"Could not create module spec for {file_path}")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all classes in the module that inherit from JobABC
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module.__name__:
                        try:
                            if cls.validate_job_class(obj):
                                logging.info(f"Found valid job class: {name}")
                                jobs[name] = obj
                        except Exception as e:
                            logging.error(f"Error validating job class {name} in {file_path}: {str(e)}")
                            raise JobValidationError(
                                f"Error validating job class {name} in {file_path}: {str(e)}"
                            )

            except Exception as e:
                logging.error(f"Error loading custom job from {file_path}: {str(e)}")
                raise ImportError(
                    f"Error loading custom job from {file_path}: {str(e)}"
                )

        return jobs


class JobFactory:
    _job_types: Dict[str, Type[JobABC]] = {}
    # Default jobs directory is always checked first
    _default_jobs_dir: str = os.path.join(os.path.dirname(__file__), "jobs") # site-package directory when this is a package
    _cached_job_graphs: List[JobABC] = None

    @classmethod
    def load_jobs_into_registry(cls, custom_jobs_dirs: list[str] = None):
        """
        Load and register all custom jobs from specified config directories.
        Will look for jobs in the 'jobs' subdirectory of each config directory.
        Loads jobs from all directories.

        Args:
            custom_jobs_dirs: List of config directory paths. Jobs will be loaded from the 'jobs' subdirectory
                            of each config directory.
        """
        loader = JobLoader()
        # Create an iterable of job directories, including the default and any custom directories
        jobs_dirs = [cls._default_jobs_dir]
        if custom_jobs_dirs:
            # Add local jobs directories from each config directory
            for config_dir in custom_jobs_dirs:
                jobs_dir = os.path.join(config_dir, "jobs")
                if os.path.exists(jobs_dir):
                    jobs_dirs.append(jobs_dir)
            
        found_valid_jobs = False
        for jobs_dir in jobs_dirs:
            custom_jobs = loader.load_jobs(jobs_dir)
            if custom_jobs:
                found_valid_jobs = True
                # Register all valid custom jobs
                for job_name, job_class in custom_jobs.items():
                    cls.register_job_type(job_name, job_class)
                    print(f"Registered custom job: {job_name}")
        
        if not found_valid_jobs:
            # This is a critical error as we need at least one valid job directory
            raise FileNotFoundError(f"No valid jobs found in any of the directories: {jobs_dirs}")

    @classmethod
    def create_job(cls, name: str, job_type: str, job_def: Dict[str, Any]) -> JobABC:
        if job_type not in cls._job_types:
            logging.error(f"*** Unknown job type: {job_type} ***")
            raise ValueError(f"Unknown job type: {job_type}")
        
        properties = job_def.get('properties', {})
        if not properties:
            logging.info(f"No properties specified for job {name} of type {job_type}")
            
        return cls._job_types[job_type](name, properties)

    @classmethod
    def register_job_type(cls, type_name: str, job_class: Type[JobABC]):
        cls._job_types[type_name] = job_class

    @classmethod
    def get_head_jobs_from_config(cls) -> Collection[JobABC]:
        """Create job graphs from configuration, using cache if available"""
        if cls._cached_job_graphs is None:
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
            cls._cached_job_graphs = job_graphs
        return cls._cached_job_graphs

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
                unique_job_name = graph_name + "_" + param_name + "_" + graph_job_name + "__"
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
                unique_job_name = graph_name + "_" + "_" + graph_job_name +"__"
                job_type: str = job_def["type"]
                job: JobABC = cls.create_job(unique_job_name, job_type, job_def)
                job_instances[graph_job_name] = job
        job_graph: JobABC = create_job_graph(graph_def, job_instances)
        return job_graph


class ConfigLoader:
    # Directories are searched in order. If a valid jobchain directory is found,
    # the search stops and uses that directory.
    # TODO: Nice to have - Add support for merging configurations from multiple directories
    #       if required in the future.
    directories: List[str] = [
        os.path.join(os.getcwd(), "jobchain"),  # jobchain directory in current working directory
        os.path.join(os.path.expanduser("~"), "jobchain"),  # ~/jobchain
        "/etc/jobchain"  
    ]
    _cached_configs: Dict[str, dict] = None

    @classmethod
    def _set_directories(cls, directories):
        """Set the directories and clear the cache"""
        cls.directories = directories
        cls._cached_configs = None

    @classmethod
    def __setattr__(cls, name, value):
        """Clear cache when directories are changed"""
        super().__setattr__(name, value)
        if name == 'directories':
            cls._cached_configs = None

    @classmethod
    def load_configs_from_dirs(
            cls,
            directories: List[str] = [],
            config_bases: List[str] = ['graphs', 'jobs', 'parameters', 'jobchain_all'],
            allowed_extensions: tuple = ('.yaml', '.yml', '.json')
    ) -> Dict[str, dict]:
        """
        Load configuration files from directories. Will search directories in order and stop
        at the first valid jobchain directory found.
        
        Args:
            directories: List of directory paths to search
            config_bases: List of configuration file base names to look for
            allowed_extensions: Tuple of allowed file extensions
        
        Returns:
            Dictionary with config_base as key and loaded config as value
            
        Raises:
            FileNotFoundError: If no valid jobchain directory is found in any of the directories
            ConfigurationError: If configuration files are malformed
        """
        configs: Dict[str, dict] = {}
        config_files: Dict[str, str] = {}  # Track which file each config came from

        # Convert directories to Path objects
        dir_paths = [Path(str(d)) for d in directories]
        logging.info(f"Looking for config files in directories: {dir_paths}")

        found_valid_dir = False
        for dir_path in dir_paths:
            if not dir_path.exists():
                logging.info(f"Directory not found, skipping: {dir_path}")
                continue

            # Check if any config files exist in this directory
            has_configs = False
            for config_base in config_bases:
                for ext in allowed_extensions:
                    if (dir_path / f"{config_base}{ext}").exists():
                        has_configs = True
                        break
                if has_configs:
                    break

            if has_configs:
                found_valid_dir = True
                logging.info(f"Found valid jobchain directory: {dir_path}")
                # Load configs from this directory only
                for config_base in config_bases:
                    for ext in allowed_extensions:
                        config_path = dir_path / f"{config_base}{ext}"
                        if config_path.exists():
                            try:
                                with open(config_path) as f:
                                    configs[config_base] = yaml.safe_load(f)
                                    config_files[config_base] = str(config_path)
                            except yaml.YAMLError as e:
                                error_msg = "Configuration is malformed. Unable to proceed with job execution.\n\n" \
                                        "-------------------------------------------------------\n" \
                                        "          Configuration file malformed - cannot continue\n" \
                                        "-------------------------------------------------------\n" \
                                        f"File: {config_path}\n" \
                                        f"Error details: {str(e)}\n" \
                                        "-------------------------------------------------------"
                                raise ConfigurationError(error_msg) from e
                break  # Stop searching after finding first valid directory

        if not found_valid_dir:
            raise FileNotFoundError(f"No valid jobchain directory found in search paths: {dir_paths}")

        # Store file paths in configs
        configs['__files__'] = config_files
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
    def _validate_graph_structure(cls, graph_def: dict, defined_jobs: set, graph_name: str) -> None:
        """
        Validate the structure of a job graph.
        - Checks for cycles
        - Ensures all referenced jobs exist
        - Validates head/tail nodes
        
        Args:
            graph_def: Graph definition from configuration
            defined_jobs: Set of all defined job names
            graph_name: Name of the graph being validated
            
        Raises:
            ValueError: If validation fails
        """
        # First validate all jobs exist and are properly connected
        for job, job_def in graph_def.items():
            if job not in defined_jobs:
                raise ValueError(f"Job '{job}' in graph '{graph_name}' is not defined")
            for next_job in job_def.get('next', []):
                if next_job not in defined_jobs:
                    raise ValueError(f"Job '{next_job}' referenced in 'next' field of job '{job}' in graph '{graph_name}' is not defined in jobs configuration")
                    
        # Build adjacency list after validating jobs
        adjacency = {job: job_def.get('next', []) for job, job_def in graph_def.items()}
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
                    
            rec_stack.remove(node)
            return False
            
        # Run cycle detection from each unvisited node
        for job in adjacency:
            if job not in visited:
                if has_cycle(job):
                    raise ValueError(f"Cycle detected in graph '{graph_name}'")
                    
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
            ConfigurationError: If configuration is malformed (e.g. wrong types, missing required fields)
        """
        try:
            graphs_config = cls._extract_config_section(configs, 'graphs')
            jobs_config = cls._extract_config_section(configs, 'jobs')
            parameters_config = cls._extract_config_section(configs, 'parameters')
            config_files = configs.get('__files__', {})

            if not graphs_config or not jobs_config:
                return

            # First validate that all jobs in graphs exist
            defined_jobs = set(jobs_config.keys())

            # Track which config we're currently validating
            current_config = 'jobs'
            
            # Validate jobs config structure
            for job_name, job_config in jobs_config.items():
                if not isinstance(job_config, dict):
                    raise TypeError(f"Job '{job_name}' configuration must be a dictionary")
                
            current_config = 'graphs'
            for graph_name, graph_def in graphs_config.items():
                # Validate graph structure (no cycles, etc)
                print(f"\nChecking {graph_name} for cycles...")
                cls._validate_graph_structure(graph_def, defined_jobs, graph_name)
                print("No cycles detected")

                # Find all parameterized jobs in this graph
                graph_parameterized_jobs = {}
                for job_name in graph_def.keys():
                    job_config = jobs_config[job_name]
                    params = cls._find_parameterized_fields(job_config)
                    if params:
                        graph_parameterized_jobs[job_name] = params

                # If graph has parameterized jobs, it must have parameters
                if graph_parameterized_jobs:
                    current_config = 'parameters'
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

                            # Validate each parameter set
                            for param_set in job_param_sets:
                                missing_params = required_params - set(param_set.keys())
                                if missing_params:
                                    raise ValueError(
                                        f"Parameter set for job '{job_name}' in graph '{graph_name}', group '{group_name}' is missing required parameters: {missing_params}")

                print(f"Graph {graph_name} passed all validations")

        except (AttributeError, TypeError, KeyError) as e:
            # Get the relevant file path based on which config we were validating
            error_file = config_files.get(current_config, 'unknown file')
            error_msg = "Configuration is malformed. Unable to proceed with job execution.\n\n" \
                        "-------------------------------------------------------\n" \
                        "          Configuration file malformed - cannot continue\n" \
                        "-------------------------------------------------------\n" \
                        f"File: {error_file}\n" \
                        f"Error details: {str(e)}\n" \
                        "-------------------------------------------------------"
            raise ConfigurationError(error_msg) from e

    @classmethod
    def load_all_configs(cls) -> Dict[str, dict]:
        """Load all configurations and validate them"""
        if cls._cached_configs is None:
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
