import asyncio
from typing import Any, Dict

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.jobs import OpenAIJob


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
    
    # Test with prompt format
    prompt_tasks = [
        {"prompt": "What is 2+2?"},
        {"prompt": "What is the capital of France?"},
        {"prompt": "What is the color of the sky?"}
    ]
    
    # Record start time
    start_time = asyncio.get_event_loop().time()
    logging.info("Starting async OpenAI calls with prompts")
    
    # Create and gather all tasks
    async_tasks: Dict[str, Any] = []
    for task in prompt_tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Calculate elapsed time
    elapsed_time = asyncio.get_event_loop().time() - start_time
    logging.info(f"All OpenAI prompt calls completed in {elapsed_time:.2f} seconds")
    
    # Verify prompt results
    assert len(results) == 3
    for result in results:
        assert isinstance(result, dict)
        assert ("response" in result) or ("error" in result), "Expected either 'response' or 'error' in result"
        if "response" in result:
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0

    # Test with messages format
    message_tasks = [
        {"messages": [{"role": "user", "content": "What is 2+2?"}]},
        {"messages": [{"role": "user", "content": "What is the capital of France?"}]},
        {"messages": [{"role": "user", "content": "What is the color of the sky?"}]}
    ]
    
    # Record start time for messages test
    start_time = asyncio.get_event_loop().time()
    logging.info("Starting async OpenAI calls with messages")
    
    # Create and gather all tasks
    async_tasks = []
    for task in message_tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Calculate elapsed time
    elapsed_time = asyncio.get_event_loop().time() - start_time
    logging.info(f"All OpenAI message calls completed in {elapsed_time:.2f} seconds")
    
    # Verify message results
    assert len(results) == 3
    for result in results:
        assert isinstance(result, dict)
        assert ("response" in result) or ("error" in result), "Expected either 'response' or 'error' in result"
        if "response" in result:
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0


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
    async_tasks: Dict[str, Any] = []
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


@pytest.mark.asyncio
async def test_openrouter_api():
    """Test that OpenAIJob can make multiple asynchronous calls using OpenRouter API with deepseek model."""
    # Create an OpenAIJob instance with OpenRouter configuration
    job = OpenAIJob(properties={
        "client": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": "OPENROUTER_API_KEY"  
        },
        "api": {
            "model": "deepseek/deepseek-chat",
            "temperature": 0.7
        }
    })
    
    # Prepare multiple tasks with proper message format
    tasks = [
        {"messages": [{"role": "user", "content": "What is 2+2?"}]},
        {"messages": [{"role": "user", "content": "What is the capital of France?"}]},
        {"messages": [{"role": "user", "content": "What is the color of the sky?"}]},
        {"prompt": "Count to 1"},
        {"prompt": "Count to 2"},
        {"prompt": "Count to 3"}
    ]
    
    # Record start time
    start_time = asyncio.get_event_loop().time()
    logging.info("Starting async OpenRouter calls")
    
    # Create and gather all tasks
    async_tasks: Dict[str, Any] = []
    for task in tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Calculate elapsed time
    elapsed_time = asyncio.get_event_loop().time() - start_time
    logging.info(f"All OpenRouter calls completed in {elapsed_time:.2f} seconds")
    
    # Verify results
    assert len(results) == 6
    for result in results:
        assert isinstance(result, dict)
        assert ("response" in result) or ("error" in result), "Expected either 'response' or 'error' in result"
