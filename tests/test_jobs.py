import asyncio
import os
import pytest
from typing import List
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
    
    # Create and gather all tasks
    async_tasks: List[asyncio.Task] = []
    for task in tasks:
        async_tasks.append(asyncio.create_task(job.run(task)))
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks)
    
    # Verify results
    assert len(results) == 3
    for result in results:
        assert isinstance(result, dict)
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0  # Ensure we got a non-empty response
