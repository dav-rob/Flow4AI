import os
import sys
from pathlib import Path
import logging

import pytest
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from job_loader import JobFactory, ConfigLoader
from jobs.llm_jobs import OpenAIJob
from jc_graph import validate_graph

# Test configuration
TEST_JOBS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_jc_config/jobs"))

@pytest.fixture
def job_factory():
    factory = JobFactory()
    # Load both the test jobs and the real jobs
    #  the real jobs are always loaded by the factory
    factory.load_custom_jobs_directory(TEST_JOBS_DIR)
    #factory.load_custom_jobs_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs"))
    return factory

def test_job_type_registration(job_factory):
    """Test that all expected job types are registered"""
    # Get all registered job types
    job_types = job_factory._job_types
    
    # Expected job types from test directory
    assert "MockJob" in job_types, "MockJob should be registered"
    assert "MockFileReadJob" in job_types, "MockFileReadJob should be registered"
    assert "MockDatabaseWriteJob" in job_types, "MockDatabaseWriteJob should be registered"
    assert "DummyJob" in job_types, "DummyJob should be registered"
    
    # Expected job type from real jobs directory
    assert "OpenAIJob" in job_types, "OpenAIJob should be registered"

@pytest.mark.asyncio
async def test_job_instantiation_and_execution(job_factory):
    """Test that jobs can be instantiated and run"""
    # Create a mock job instance
    mock_job = job_factory.create_job(
        name="test_mock_job",
        job_type="MockJob",
        properties={"test_param": "test_value"}
    )
    
    # Verify job creation
    assert mock_job is not None
    assert mock_job.name == "test_mock_job"
    
    # Run the job with required inputs
    result = await mock_job.run(inputs={"test_input": "test_value"})
    assert result is not None
    assert mock_job.name in result

@pytest.mark.asyncio
async def test_openai_job_instantiation_and_execution(job_factory):
    """Test that OpenAIJob can be instantiated and run"""
    # Get the OpenAIJob class from the registry
    assert "OpenAIJob" in job_factory._job_types, "OpenAIJob should be registered"
    OpenAIJobClass = job_factory._job_types["OpenAIJob"]
    
    openai_job = job_factory.create_job(
        name="test_openai_job",
        job_type="OpenAIJob",
        properties={
            "model": "gpt-3.5-turbo",
            "api": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello!"}
                ],
                "temperature": 0.7
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
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_jc_config"))
    logging.info(f"\nTest config dir: {test_config_dir}")
    logging.info(f"Directory exists: {os.path.exists(test_config_dir)}")
    logging.info(f"Directory contents: {os.listdir(test_config_dir)}")
    
    # Reset ConfigLoader state and set directories
    ConfigLoader._cached_configs = None  # Reset cached configs
    ConfigLoader.directories = [str(test_config_dir)]  # Convert to string for anyconfig
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
    test_config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_jc_config2"))
    logging.info(f"\nTest config dir: {test_config_dir}")
    logging.info(f"Directory exists: {os.path.exists(test_config_dir)}")
    logging.info(f"Directory contents: {os.listdir(test_config_dir)}")
    
    # Reset ConfigLoader state and set directories
    ConfigLoader._cached_configs = None  # Reset cached configs
    ConfigLoader.directories = [str(test_config_dir)]  # Convert to string for anyconfig
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
