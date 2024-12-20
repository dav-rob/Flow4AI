import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from job_loader import JobFactory
from jobs.llm_jobs import OpenAIJob

# Test configuration
TEST_JOBS_DIR = os.path.join(os.path.dirname(__file__), "test_jc_config/jobs")

@pytest.fixture
def job_factory():
    factory = JobFactory()
    # Load both the test jobs and the real jobs
    factory.load_custom_jobs_directory(TEST_JOBS_DIR)
    factory.load_custom_jobs_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs"))
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
