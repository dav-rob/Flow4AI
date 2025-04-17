import asyncio
import os
from unittest.mock import MagicMock

import pytest
import yaml

from flow4ai import f4a_logging as logging
from flow4ai.jc_graph import validate_graph
from flow4ai.job import JobABC, Task, job_graph_context_manager
from flow4ai.job_chain import JobChain  # Import JobChain
from flow4ai.job_loader import ConfigLoader, ConfigurationError, JobFactory

# Test configuration
TEST_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config"))

@pytest.fixture
def job_factory() -> JobFactory:
    factory = JobFactory()
    # Load both the test jobs and the real jobs
    #  the real jobs are always loaded by the factory
    factory.load_python_into_registries([TEST_CONFIG_DIR])
    return factory

def test_job_type_registration(job_factory: JobFactory):
    """Test that all expected job types are registered"""
    # Get all registered job types
    job_types = job_factory._job_types_registry
    
    # Expected job types from test directory
    assert "MockJob" in job_types, "MockJob should be registered"
    assert "MockFileReadJob" in job_types, "MockFileReadJob should be registered"
    assert "MockDatabaseWriteJob" in job_types, "MockDatabaseWriteJob should be registered"
    assert "DummyJob" in job_types, "DummyJob should be registered"
    
    # Expected job type from real jobs directory
    assert "OpenAIJob" in job_types, "OpenAIJob should be registered"


def test_pydantic_type_registration(job_factory: JobFactory):
    """Test that all expected pydantic models are registered"""
    # Configure JobFactory to use test_pydantic_config directory
    test_config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_pydantic_config")
    JobFactory.load_python_into_registries([test_config_dir])
    
    # Get all registered pydantic types
    pydantic_types = job_factory._pydantic_types_registry
    
    # Expected pydantic models from test directory
    assert "UserProfile" in pydantic_types, "UserProfile model should be registered"
    assert "JobMetadata" in pydantic_types, "JobMetadata model should be registered"
    assert "TaskConfig" in pydantic_types, "TaskConfig model should be registered"
    
    # Verify the registered models are actually pydantic BaseModel subclasses
    from pydantic import BaseModel
    assert issubclass(pydantic_types["UserProfile"], BaseModel)
    assert issubclass(pydantic_types["JobMetadata"], BaseModel)
    assert issubclass(pydantic_types["TaskConfig"], BaseModel)

@pytest.mark.asyncio
async def test_job_instantiation_and_execution(job_factory: JobFactory):
    """Test that jobs can be instantiated and run"""
    # Create a mock job instance
    mock_job = job_factory.create_job(
        name="test_mock_job",
        job_type="MockJob",
        job_def={"properties": {"test_param": "test_value"}}
    )
    mock_job.get_inputs = MagicMock(return_value={"test_job_input": "test_value"})
    
    # Verify job creation
    assert mock_job is not None
    assert mock_job.name == "test_mock_job"
    
    # Run the job with required inputs
    result = await mock_job.run(task={})
    assert result is not None
    assert mock_job.name in result

@pytest.mark.asyncio
async def test_openai_job_instantiation_and_execution(job_factory: JobFactory):
    """Test that OpenAIJob can be instantiated and run"""
    # Get the OpenAIJob class from the registry
    assert "OpenAIJob" in job_factory._job_types_registry, "OpenAIJob should be registered"
    OpenAIJobClass = job_factory._job_types_registry["OpenAIJob"]
    
    openai_job = job_factory.create_job(
        name="test_openai_job",
        job_type="OpenAIJob",
        job_def={
            "properties": {
                "api": {
                    "model": "gpt-4",
                    "temperature": 0.7
                },
                "rate_limit": {
                    "max_rate": 1,
                    "time_period": 4
                }
            }
        }
    )
    
    assert openai_job is not None
    assert openai_job.name == "test_openai_job"
    assert isinstance(openai_job, OpenAIJobClass), "Job should be an instance of OpenAIJob"
    
    # Run the job
    result = await openai_job.run({})
    assert result is not None
    assert "response" in result
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0

def test_config_loader_separate():
    """Test loading configurations from separate files"""
    # Get absolute paths
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config"))
    logging.info(f"\nTest config dir: {test_config_dir}")
    logging.info(f"Directory exists: {os.path.exists(test_config_dir)}")
    logging.info(f"Directory contents: {os.listdir(test_config_dir)}")
    
    # Reset ConfigLoader state and set directories
    ConfigLoader._cached_configs = None  # Reset cached configs
    ConfigLoader._set_directories([str(test_config_dir)])  # Convert to string for anyconfig
    logging.info(f"ConfigLoader directories: {ConfigLoader.directories}")
    
    # Test graphs config
    graphs_config = ConfigLoader.get_graphs_config()
    logging.info(f"Graphs config: {graphs_config}")
    assert graphs_config is not None
    with open(os.path.join(test_config_dir, "graphs.yaml"), 'r') as f:
        expected_graphs = yaml.safe_load(f)
    logging.info(f"Expected graphs: {expected_graphs}")
    assert graphs_config == expected_graphs
    
    # Test jobs config
    jobs_config = ConfigLoader.get_jobs_config()
    assert jobs_config is not None
    with open(os.path.join(test_config_dir, "jobs.yaml"), 'r') as f:
        expected_jobs = yaml.safe_load(f)
    assert jobs_config == expected_jobs
    
    # Test parameters config
    params_config = ConfigLoader.get_parameters_config()
    assert params_config is not None
    with open(os.path.join(test_config_dir, "parameters.yaml"), 'r') as f:
        expected_params = yaml.safe_load(f)
    assert params_config == expected_params
    
    # Validate each graph separately
    for graph_name, graph in graphs_config.items():
        validate_graph(graph, graph_name)

def test_config_loader_all():
    """Test loading configurations from a single combined file"""
    # Get absolute paths
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config_all"))
    logging.info(f"\nTest config dir: {test_config_dir}")
    logging.info(f"Directory exists: {os.path.exists(test_config_dir)}")
    logging.info(f"Directory contents: {os.listdir(test_config_dir)}")
    
    # Reset ConfigLoader state and set directories
    ConfigLoader._cached_configs = None  # Reset cached configs
    ConfigLoader._set_directories([str(test_config_dir)])  # Convert to string for anyconfig
    logging.info(f"ConfigLoader directories: {ConfigLoader.directories}")
    
    # Load the combined config file for comparison
    with open(os.path.join(test_config_dir, "jobchain_all.yaml"), 'r') as f:
        all_config = yaml.safe_load(f)
    logging.info(f"All config: {all_config}")
    
    # Test graphs config
    graphs_config = ConfigLoader.get_graphs_config()
    logging.info(f"Graphs config: {graphs_config}")
    assert graphs_config is not None
    assert graphs_config == all_config.get('graphs', {})
    
    # Test jobs config
    jobs_config = ConfigLoader.get_jobs_config()
    logging.info(f"Jobs config: {jobs_config}")
    assert jobs_config is not None
    assert jobs_config == all_config.get('jobs', {})
    
    # Test parameters config
    params_config = ConfigLoader.get_parameters_config()
    logging.info(f"Parameters config: {params_config}")
    assert params_config is not None
    assert params_config == all_config.get('parameters', {})
    
    # Validate each graph separately
    for graph_name, graph in graphs_config.items():
        validate_graph(graph, graph_name)

def test_create_head_jobs_from_config(job_factory: JobFactory):
    """Test that create_head_jobs_from_config creates the correct number of graphs with correct structure"""
    # Set up test config directory
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config"))
    logging.info(f"\nTest config dir: {test_config_dir}")
    logging.info(f"Directory exists: {os.path.exists(test_config_dir)}")
    logging.info(f"Directory contents: {os.listdir(test_config_dir)}")
    
    # Reset ConfigLoader state and set directories
    ConfigLoader._cached_configs = None  # Reset cached configs
    ConfigLoader._set_directories([str(test_config_dir)])  # Convert to string for anyconfig

    # Create head jobs
    head_jobs = JobFactory.get_head_jobs_from_config()
    
    # Should create 4 graphs:
    # - 2 from four_stage_parameterized (params1 and params2)
    # - 1 from three_stage (params1)
    # - 1 from three_stage_reasoning (no params)
    assert len(head_jobs) == 4, f"Expected 4 head jobs, got {len(head_jobs)}"
    
    # Get graph definitions for validation
    graphs_config = ConfigLoader.get_graphs_config()
    
    # Validate each head job's structure matches its graph definition
    for i, head_job in enumerate(head_jobs):
        print(f"\nJob Graph {i + 1}:")
        
        # Print all jobs in this graph using DFS
        visited = set()
        def print_job_graph(job):
            if job in visited:
                return
            visited.add(job)
            print(str(job))
            for child in job.next_jobs:
                print_job_graph(child)
        
        print_job_graph(head_job)
        print("----------------------")
        
        # Extract graph name and param group from job name
        job_parts = head_job.name.split("_")
        if len(job_parts) >= 3 and job_parts[0] in graphs_config:
            graph_name = job_parts[0]
            param_group = job_parts[1] if job_parts[1].startswith("params") else None
            
            # Get graph definition
            graph_def = graphs_config[graph_name]
            
            # Validate job structure matches graph definition
            def validate_job_structure(job, graph_def):
                # Get job's base name (without graph and param prefixes)
                base_job_name = "_".join(job.name.split("_")[2:]) if param_group else "_".join(job.name.split("_")[1:])
                
                # Check that next_jobs match graph definition
                expected_next = set(graph_def[base_job_name].get("next", []))
                actual_next = {next_job.name.split("_")[-1] for next_job in job.next_jobs}
                assert expected_next == actual_next, \
                    f"Mismatch in next_jobs for {job.name}. Expected: {expected_next}, Got: {actual_next}"
                
                # Recursively validate next jobs
                for next_job in job.next_jobs:
                    validate_job_structure(next_job, graph_def)
            
            validate_job_structure(head_job, graph_def)

def test_validate_all_jobs_in_graph():
    """Test that validation catches jobs referenced in graphs but not defined in jobs"""
    # Test with invalid configuration
    invalid_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config_invalid"))
    ConfigLoader._set_directories([invalid_config_dir])
    
    with pytest.raises(ValueError) as exc_info:
        ConfigLoader.load_all_configs()
    assert "Job 'nonexistent_job' referenced in 'next' field of job 'read_file' in graph 'four_stage_parameterized'" in str(exc_info.value)
    
    # Test with valid configuration
    valid_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config"))
    ConfigLoader._set_directories([valid_config_dir])
    
    try:
        ConfigLoader.load_all_configs()
    except ValueError as e:
        pytest.fail(f"Validation failed for valid configuration: {str(e)}")

def test_validate_all_parameters_filled():
    """Test that validation catches missing or invalid parameter configurations"""
    # Test with invalid parameter configuration
    invalid_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config_invalid_parameters"))
    ConfigLoader._set_directories([invalid_config_dir])
    
    with pytest.raises(ValueError) as exc_info:
        ConfigLoader.load_all_configs()
    
    error_msg = str(exc_info.value)
    # Should catch missing parameters for read_file in params1
    assert "Job 'read_file' in graph 'four_stage_parameterized' requires parameters {'filepath'} but has no entry in parameter group 'params1'" in error_msg
    
    # Test with valid configuration
    valid_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config"))
    ConfigLoader._set_directories([valid_config_dir])
    
    try:
        ConfigLoader.load_all_configs()
    except ValueError as e:
        pytest.fail(f"Validation failed for valid configuration: {str(e)}")



@pytest.mark.asyncio
async def test_job_execution_chain(caplog):
    """Test that all jobs in a graph are executed when _execute is called on the head job."""
    caplog.set_level('DEBUG')  # Set the logging level
    # Load custom job types
    JobFactory.load_python_into_registries([TEST_CONFIG_DIR])

    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config")])
    ConfigLoader.reload_configs()

    # Get head jobs from config
    head_jobs = JobFactory.get_head_jobs_from_config()

    # Get the first head job from four_stage_parameterized_params1
    head_job = [job for job in head_jobs if 'four_stage_parameterized$$params1$$read_file$$' in job.name][0]

    # Execute the head job
    job_set = JobABC.job_set(head_job)
    async with job_graph_context_manager(job_set):
        await asyncio.create_task(head_job._execute(Task({"task": "Test task"})))

    # Expected job names in the graph
    expected_jobs = {
        'four_stage_parameterized$$params1$$read_file$$',
        'four_stage_parameterized$$params1$$ask_llm$$',
        'four_stage_parameterized$$params1$$save_to_db$$',
        'four_stage_parameterized$$params1$$summarize$$'
    }

    # Check that all jobs were executed by verifying their presence in the log output
    for job_name in expected_jobs:
        assert f"{job_name} finished running" in caplog.text, f"Job {job_name} was not executed"

   

@pytest.mark.asyncio
async def test_head_jobs_in_jobchain_serial():
    """Test that head jobs from config can be executed in JobChain with serial processing"""
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config")])
    
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    
    # Submit tasks for each job
    for job in head_jobs:
        job_chain.submit_task({"task": "Test task"}, job_name=job)
    
    # Mark input as completed and wait for all tasks to finish
    job_chain.mark_input_completed()
    
    # Convert shared list to regular list for sorting
    results_list = list(results)
    
    # Verify results
    # We expect one result per head job
    assert len(results_list) == len(head_jobs), f"Expected {len(head_jobs)} results, got {len(results_list)}"
    
    # Sort results by job name to ensure deterministic ordering
    results_list.sort(key=lambda x: next(iter(x.keys())))
    
    # Each result should be a dictionary with job results
    for result in results_list:
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        
        # Verify parameter substitution for each graph type
        if 'four_stage_parameterized_params1_summarize' in result:
            result_str = str(result['four_stage_parameterized_params1_summarize'])
            # Verify save_to_db parameters
            assert 'postgres://user1:pass1@db1/mydb' in result_str, "Database URL not correctly substituted"
            assert 'table_a' in result_str, "Table name not correctly substituted"
            # Verify read_file parameters
            assert './file1.txt' in result_str, "Filepath not correctly substituted"
            
        elif 'three_stage_params1_summarize' in result:
            result_str = str(result['three_stage_params1_summarize'])
            # Verify save_to_db2 parameters are from the job definition
            assert 'sqlite://user2:pass2@db2/mydb' in result_str, "Database URL not correctly set"
            assert 'table_b' in result_str, "Table name not correctly set"


def process_result(result):
    """Process a result by appending it to the global results list and logging to file"""
    print(f"Got result: {result}")
    # Extract just the job-specific data, excluding task_pass_through and RETURN_JOB
    job_result = {k: v for k, v in result.items() if k not in ['task_pass_through', 'RETURN_JOB']}
    with open("count_parallel_results", "a") as f:
        f.write(str(job_result) + "\n")


@pytest.mark.asyncio
async def test_head_jobs_in_jobchain_parallel():
    """Test that head jobs from config can be executed in JobChain with parallel processing"""
    # Clean up any existing results file
    if os.path.exists("count_parallel_results"):
        os.remove("count_parallel_results")
        
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_jc_config")])
    
    # Create JobChain with parallel processing (default)
    job_chain = JobChain(job=None, result_processing_function=process_result)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    
    # Submit tasks for each job
    for job in head_jobs:
        job_chain.submit_task({"task": "Test task"}, job_name=job)
    
    # Mark input as completed and wait for all processing to finish
    job_chain.mark_input_completed()
    
    # Read results file and verify contents
    with open("count_parallel_results", "r") as f:
        results_list = [eval(line.strip()) for line in f.readlines()]
        assert len(results_list) == 4, f"Expected 4 results but got {len(results_list)}"
        
        # Each result should be a dictionary with job results
        for result in results_list:
            assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
            
            # Verify parameter substitution for each graph type
            if 'four_stage_parameterized_params1_summarize' in result:
                result_str = str(result['four_stage_parameterized_params1_summarize'])
                # Verify save_to_db parameters
                assert 'postgres://user1:pass1@db1/mydb' in result_str, "Database URL not correctly substituted"
                assert 'table_a' in result_str, "Table name not correctly substituted"
                # Verify read_file parameters
                assert './file1.txt' in result_str, "Filepath not correctly substituted"
                
            elif 'four_stage_parameterized_params2_summarize' in result:
                result_str = str(result['four_stage_parameterized_params2_summarize'])
                # Verify save_to_db parameters
                assert 'sqlite://user2:pass2@db2/mydb' in result_str, "Database URL not correctly substituted"
                assert 'table_b' in result_str, "Table name not correctly substituted"
                # Verify read_file parameters
                assert './file2.txt' in result_str, "Filepath not correctly substituted"
                
            elif 'three_stage_params1_summarize' in result:
                result_str = str(result['three_stage_params1_summarize'])
                # Verify save_to_db2 parameters are from the job definition
                assert 'sqlite://user2:pass2@db2/mydb' in result_str, "Database URL not correctly set"
                assert 'table_b' in result_str, "Table name not correctly set"
                
            elif 'three_stage_reasoning__summarize' in result:
                result_str = str(result['three_stage_reasoning__summarize'])
                # Verify save_to_db2 parameters are from the job definition
                assert 'sqlite://user2:pass2@db2/mydb' in result_str, "Database URL not correctly set"
                assert 'table_b' in result_str, "Table name not correctly set"
    
    # Clean up results file
    os.remove("count_parallel_results")

def process_prompts(result):
    """Process a result by appending it to the global results list and logging to file"""
    print(f"Got result: {result}")

@pytest.mark.asyncio
async def test_single_job_multiple_prompts():
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_single_job")])
    
    # Create JobChain with parallel processing (default)
    job_chain = JobChain(result_processing_function=process_prompts)

    prompts = ["what is the capital of france",
    "what is the capital of germany",
    "what is the capital of the UK",
    "what is the capital of the USA"
    ]

    for prompt in prompts:
        job_chain.submit_task({"prompt": prompt})
    
    # Mark input as completed and wait for all processing to finish
    job_chain.mark_input_completed()

@pytest.mark.asyncio
async def test_malformed_configuration():
    """Test that a malformed configuration file raises a clear error."""
    
    # Test malformed graphs config
    test_config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_malformed_config")
    ConfigLoader._set_directories([test_config_dir])
    
    with pytest.raises(ConfigurationError) as excinfo:
        ConfigLoader.load_all_configs()
        
    error_msg = str(excinfo.value)
    assert "Configuration is malformed" in error_msg
    assert "test_malformed_config/graphs.yaml" in error_msg
    
    # Test malformed jobs config
    test_config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_malformed_config_jobs")
    ConfigLoader._set_directories([test_config_dir])
    ConfigLoader._cached_configs = None  # Reset cached configs
    
    with pytest.raises(ConfigurationError) as excinfo:
        ConfigLoader.load_all_configs()
        
    error_msg = str(excinfo.value)
    assert "Configuration is malformed" in error_msg
    assert "test_malformed_config_jobs/jobs.yaml" in error_msg
    
    # Test malformed parameters config
    test_config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_malformed_config_params")
    ConfigLoader._set_directories([test_config_dir])
    ConfigLoader._cached_configs = None  # Reset cached configs
    
    with pytest.raises(ConfigurationError) as excinfo:
        ConfigLoader.load_all_configs()
        
    error_msg = str(excinfo.value)
    assert "Configuration is malformed" in error_msg
    assert "test_malformed_config_params/parameters.yaml" in error_msg

#@pytest.mark.skip("Skipping test due to working yet")
@pytest.mark.asyncio
async def test_pydantic_jobs_in_jobchain_serial():
    """Test that head jobs from config can be executed in JobChain with serial processing"""
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_pydantic_config")])

   
    results = []
    
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    
    # Submit tasks for each job
    for job in head_jobs:
        job_chain.submit_task({"prompt": "Create a male user."}, job_name=job)
        job_chain.submit_task({"prompt": "Create a female user."}, job_name=job)
    
    # Mark input as completed and wait for all tasks to finish
    job_chain.mark_input_completed()
    
    # Convert shared list to regular list for sorting
    results_list = list(results)
    
    # Verify results
    # We expect one result per head job
    assert len(results_list) == len(head_jobs)*2, f"Expected {len(head_jobs)} results, got {len(results_list)}"
    
    # Sort results by job name to ensure deterministic ordering
    results_list.sort(key=lambda x: next(iter(x.keys())))
    
    # Each result should be a dictionary with job results
    for result in results_list:
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        logging.info(f"Result: {result}")
        

@pytest.mark.asyncio
async def test_multiple_head_jobs_in_jobchain_serial(caplog):
    """Test that multiple head jobs from config can be executed in JobChain with serial processing
       The test uses a configuration with multiple parameters which means that multiple DefaultHeadJobs
       should be created.
    """
    # Enable debug logging
    caplog.set_level('DEBUG')
    
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_multiple_heads")])
    ConfigLoader.reload_configs()
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    logging.info(f"Identified head jobs: {head_jobs}")
    
    # Verify there is exactly two head job (the DefaultHeadJob), one for each parameter group
    assert len(head_jobs) == 2, f"Expected exactly two head jobs, got {len(head_jobs)}: {head_jobs}"

    for job in head_jobs:
        logging.info(f"DEBUG - Head job name: {job}")
        parsed_name = JobABC.parse_job_name(job)
        assert parsed_name == "DefaultHeadJob", \
            f"Parsed name mismatch. Expected 'DefaultHeadJob' got {parsed_name}"
        logging.info(f"Submitting task for job: {job}")
        job_chain.submit_task({"task": "Multi-head test task"}, job_name=job)
    
    # Mark input as completed and wait for all tasks to finish
    logging.info("Marking input as completed")
    job_chain.mark_input_completed()
    # JobChain automatically waits for completion when mark_input_completed is called
    logging.info("Job chain completed")
    
    # Log the results for debugging
    logging.info(f"Results count: {len(results)}")
    for i, result in enumerate(results):
        logging.info(f"Result {i}: {result}")
    
    # Check if we have any results
    if len(results) == 0:
        logging.error("No results received from job execution")
        assert False, "No results received from job execution"
    
    # Verify that multiple head nodes were detected
    assert "multiple head nodes" in caplog.text.lower(), "Multiple head nodes not detected in log"
    
    # Verify we got at least one result
    assert len(results) == 2, f"Expected two results, got {len(results)}"
    
    for result in results:
        logging.info(f"DEBUG - Result: {result}")
        # Verify the result contains the expected data
        assert "storage_url" in result, "Result missing storage_url field"
        assert "status" in result, "Result missing status field"
        assert result["status"] == "success", f"Expected status 'success', got '{result.get('status')}'"



@pytest.mark.asyncio
async def test_multiple_tail_jobs_in_jobchain_serial(caplog):
    """Test that multiple tail jobs from config can be executed in JobChain with serial processing"""
    # Enable debug logging
    caplog.set_level('DEBUG')
    
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_multiple_tails")])
    ConfigLoader.reload_configs()
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    logging.info(f"Identified head jobs: {head_jobs}")
    
    # Print head job name for debugging
    if head_jobs:
        logging.info(f"DEBUG - Head job name: {head_jobs[0]}")
    
    # Verify there is exactly one head job
    assert len(head_jobs) == 1, f"Expected exactly one head job, got {len(head_jobs)}: {head_jobs}"
    
    # Get the head job name
    head_job_name = head_jobs[0]
    logging.debug(f"Head job name: {head_job_name}")
    
    # Submit tasks for the head job
    logging.info(f"Submitting task for job: {head_job_name}")
    job_chain.submit_task({"task": "Multi-tail test task"}, job_name=head_job_name)
    
    # Mark input as completed and wait for all tasks to finish
    logging.info("Marking input as completed")
    job_chain.mark_input_completed()
    # JobChain automatically waits for completion when mark_input_completed is called
    logging.info("Job chain completed")
    
    # Log the results for debugging
    logging.info(f"Results count: {len(results)}")
    for i, result in enumerate(results):
        logging.info(f"Result {i}: {result}")
    
    # Check if we have any results
    if len(results) == 0:
        logging.error("No results received from job execution")
        assert False, "No results received from job execution"
    
    # Verify that multiple tail nodes were detected
    assert "multiple tail nodes" in caplog.text.lower(), "Multiple tail nodes not detected in log"
    
    # Verify we got at least one result from each tail job
    # Since we have a DefaultTailJob, we should get at least one result
    assert len(results) > 0, f"Expected at least one result, got {len(results)}"
    
    # Verify the results contain the expected data
    # The result should contain the DefaultTailJob information
    for result in results:
        assert "RETURN_JOB" in result, "Result missing RETURN_JOB field"
        assert "DefaultTailJob" in result["RETURN_JOB"], f"Expected DefaultTailJob in RETURN_JOB, got {result.get('RETURN_JOB')}"
        assert "task_pass_through" in result, "Result missing task_pass_through field"
        assert "processor_alpha" in result, "Result missing processor_alpha field"
        assert "processor_beta" in result, "Result missing processor_beta field"
        assert "accuracy" in result["processor_alpha"], "processor_alpha should contain returned values"
        assert "archived_items" in result["processor_beta"], "processor_beta should contain returned values"

@pytest.mark.asyncio
async def test_multiple_tail_jobs_2_parameters(caplog):
    """Test that multiple tail jobs from config can be executed in JobChain with serial processing"""
    # Enable debug logging
    caplog.set_level('DEBUG')
    
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_multiple_tails2")])
    ConfigLoader.reload_configs()
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    logging.info(f"Identified head jobs: {head_jobs}")
    
    # Verify there is exactly two head jobs
    assert len(head_jobs) == 2, f"Expected exactly two head jobs, got {len(head_jobs)}: {head_jobs}"

    for head_job_name in head_jobs:
        logging.debug(f"Head job name: {head_job_name}")
        # Submit tasks for the head job
        logging.info(f"Submitting task for job: {head_job_name}")
        job_chain.submit_task({"task": "Multi-tail test task"}, job_name=head_job_name)
    
    # Mark input as completed and wait for all tasks to finish
    logging.info("Marking input as completed")
    job_chain.mark_input_completed()
    # JobChain automatically waits for completion when mark_input_completed is called
    logging.info("Job chain completed")
    
    # Log the results for debugging
    logging.info(f"Results count: {len(results)}")
    for i, result in enumerate(results):
        logging.info(f"Result {i}: {result}")
    
    # Check if we have any results
    if len(results) == 0:
        logging.error("No results received from job execution")
        assert False, "No results received from job execution"
    
    # Verify that multiple tail nodes were detected
    assert "multiple tail nodes" in caplog.text.lower(), "Multiple tail nodes not detected in log"
    
    # Verify we got at least one result from each tail job
    # Since we have a DefaultTailJob, we should get at least one result
    assert len(results) > 0, f"Expected at least one result, got {len(results)}"
    
    # Verify the results contain the expected data
    # The result should contain the DefaultTailJob information
    for result in results:
        assert "RETURN_JOB" in result, "Result missing RETURN_JOB field"
        assert "DefaultTailJob" in result["RETURN_JOB"], f"Expected DefaultTailJob in RETURN_JOB, got {result.get('RETURN_JOB')}"
        assert "task_pass_through" in result, "Result missing task_pass_through field"
        assert "processor_alpha" in result, "Result missing processor_alpha field"
        assert "processor_beta" in result, "Result missing processor_beta field"
        assert "accuracy" in result["processor_alpha"], "processor_alpha should contain returned values"
        assert "archived_items" in result["processor_beta"], "processor_beta should contain returned values"


@pytest.mark.asyncio
async def test_simple_parallel_jobs_in_jobchain_serial(caplog):
    """Test that a simple parallel job graph with multiple independent jobs can be executed in JobChain"""
    # Enable debug logging
    caplog.set_level('DEBUG')
    
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_simple_parallel")])
    ConfigLoader.reload_configs()
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    logging.info(f"Identified head jobs: {head_jobs}")
    
    # Verify there is exactly one head job (the DefaultHeadJob)
    assert len(head_jobs) == 1, f"Expected exactly one head job, got {len(head_jobs)}: {head_jobs}"
    
    # Get the head job name and verify it's correctly formatted
    head_job_name = head_jobs[0]
    logging.debug(f"Head job name: {head_job_name}")
    parsed_name = JobABC.parse_job_name(head_job_name)
    assert parsed_name == "DefaultHeadJob", \
        f"Parsed name mismatch. Expected 'DefaultHeadJob' got {parsed_name}"
    
    # Submit tasks for the head job
    logging.info(f"Submitting task for job: {head_job_name}")
    job_chain.submit_task({"task": "Simple parallel test task"}, job_name=head_job_name)
    
    # Mark input as completed and wait for all tasks to finish
    logging.info("Marking input as completed")
    job_chain.mark_input_completed()
    # JobChain automatically waits for completion when mark_input_completed is called
    logging.info("Job chain completed")
    
    # Log the results for debugging
    logging.info(f"Results count: {len(results)}")
    for i, result in enumerate(results):
        logging.info(f"Result {i}: {result}")
    
    # Check if we have any results
    if len(results) == 0:
        logging.error("No results received from job execution")
        assert False, "No results received from job execution"
    
    # Verify that both multiple head nodes and multiple tail nodes were detected
    assert "multiple head nodes" in caplog.text.lower(), "Multiple head nodes not detected in log"
    assert "multiple tail nodes" in caplog.text.lower(), "Multiple tail nodes not detected in log"
    
    # Verify we got at least one result
    assert len(results) > 0, f"Expected at least one result, got {len(results)}"
    
    # Verify the result contains the DefaultTailJob information
    for result in results:
        assert "RETURN_JOB" in result, "Result missing RETURN_JOB field"
        assert "DefaultTailJob" in result["RETURN_JOB"], f"Expected DefaultTailJob in RETURN_JOB, got {result.get('RETURN_JOB')}"
        assert "task_pass_through" in result, "Result missing task_pass_through field"

@pytest.mark.asyncio
async def test_save_result():
    """Test that head jobs from config can be executed in JobChain with serial processing"""
    # Set config directory for test
    ConfigLoader._set_directories([os.path.join(os.path.dirname(__file__), "test_configs/test_save_result")])
    
    # Initialize results tracking
    results = []
    
    def result_processor(result):
        results.append(result)
        logging.info(f"Processed result: {result}")
    
    # Create JobChain with serial processing to ensure deterministic results
    job_chain = JobChain(job=None, result_processing_function=result_processor, serial_processing=True)
    
    # Get head jobs from config to know their names
    head_jobs = job_chain.get_job_names()
    
    # Submit tasks for each job
    for job in head_jobs:
        job_chain.submit_task({"task": "Test task"}, job_name=job)
    
    # Mark input as completed and wait for all tasks to finish
    job_chain.mark_input_completed()
    
    # Convert shared list to regular list for sorting
    results_list = list(results)
    
    # Verify results
    # We expect one result per head job
    assert len(results_list) == len(head_jobs), f"Expected {len(head_jobs)} results, got {len(results_list)}"
    
    # Sort results by job name to ensure deterministic ordering
    results_list.sort(key=lambda x: next(iter(x.keys())))
    
    # Each result should be a dictionary with job results
    for result in results_list:
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        tail_job_name = result.get('RETURN_JOB')
        tail_job_value = result.get("dummy_job_result")
        # Verify parameter substitution for each graph type
        if 'four_stage_parameterized$$params1$$summarize$$' == tail_job_name:
            # Verify save_to_db parameters
            assert 'postgres://user1:pass1@db1/mydb' in tail_job_value, "Database URL not correctly substituted"
            assert 'table_a' in tail_job_value, "Table name not correctly substituted"
            # Verify read_file parameters
            assert './file1.txt' in tail_job_value, "Filepath not correctly substituted"
            assert JobABC.SAVED_RESULTS not in result, f"{JobABC.SAVED_RESULTS} should not be in {result}"

        elif 'four_stage_parameterized$$params2$$summarize$$' == tail_job_name:
            saved_result_str = str(result[JobABC.SAVED_RESULTS]['save_to_db'])
            assert 'sqlite://user2:pass2@db2/mydb' in saved_result_str, "Database URL not correctly saved"
            assert 'table_b' in saved_result_str, "Table name not correctly saved"
            
        elif 'three_stage$$params1$$summarize$$' == tail_job_name:
            # Verify save_to_db2 parameters are from the job definition
            assert 'sqlite://user2:pass2@db2/mydb' in tail_job_value, "Database URL not correctly set"
            assert 'table_b' in tail_job_value, "Table name not correctly set"
            assert JobABC.SAVED_RESULTS not in result, f"{JobABC.SAVED_RESULTS} should not be in {result}"
            
        elif 'three_stage_reasoning$$params1$$summarize$$' == tail_job_name:
            saved_result_str = str(result[JobABC.SAVED_RESULTS]['save_to_db'])
            assert 'sqlite://user2:pass2@db2/mydb' in saved_result_str, "Database URL not correctly saved"
            assert 'table_b' in saved_result_str, "Table name not correctly saved"