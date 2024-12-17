import asyncio
from typing import List

import pytest
import jc_logging as logging

from jobs.llm_jobs import OpenAIJob


@pytest.mark.asyncio
async def test_openai_job_async_calls():
    """Test that OpenAIJob can make multiple asynchronous calls to GPT-4o-mini."""
    # Create an OpenAIJob instance
    job = OpenAIJob(properties={
        "api": {
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    })
    
    # Prepare multiple tasks
    tasks = [
        {"prompt": "What is 2+2?"},
        {"prompt": "What is the capital of France?"},
        {"prompt": "What is the color of the sky?"}
    ]
    
    # Record start time
    start_time = asyncio.get_event_loop().time()
    logging.info("Starting async OpenAI calls")
    
    # Create and gather all tasks
    async_tasks: List[asyncio.Task] = []
    for task in tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Calculate elapsed time
    elapsed_time = asyncio.get_event_loop().time() - start_time
    logging.info(f"All OpenAI calls completed in {elapsed_time:.2f} seconds")
    
    # Verify results
    assert len(results) == 3
    for result in results:
        assert isinstance(result, dict)
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0  # Ensure we got a non-empty response


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test that rate limiting configuration is respected."""
    # Create an OpenAIJob instance with strict rate limiting
    job = OpenAIJob(properties={
        "api": {
            "model": "gpt-4o-mini",
            "temperature": 0.7
        },
        "rate_limit": {
            "max_rate": 1,
            "time_period": 4
        }
    })
    
    # Prepare multiple tasks
    tasks = [
        {"prompt": "Count to 1"},
        {"prompt": "Count to 2"},
        {"prompt": "Count to 3"}
    ]
    
    # Record start time
    start_time = asyncio.get_event_loop().time()
    
    # Create and gather all tasks
    async_tasks: List[asyncio.Task] = []
    for task in tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Calculate elapsed time
    elapsed_time = asyncio.get_event_loop().time() - start_time
    logging.info(f"Rate limited calls completed in {elapsed_time:.2f} seconds")
    
    # Verify timing - with rate limit of 1 request per 4 seconds, 3 requests should take at least 8 seconds
    # (first request at t=0, second at t=4, third at t=8)
    assert elapsed_time >= 8.0, f"Expected at least 8 seconds, but took {elapsed_time} seconds"
    
    # Verify we got responses (either success or error) for all requests
    assert len(results) == 3
    for result in results:
        assert isinstance(result, dict)
        assert ("response" in result) or ("error" in result), "Expected either 'response' or 'error' in result"
