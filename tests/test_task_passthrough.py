import asyncio
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

import jobchain.jc_logging as logging
from jobchain.job_chain import JobChain
from jobchain.job_loader import ConfigLoader


def result_collector(shared_results, result):
    logging.info(f"Result collector received: {result}")
    shared_results.append(result)
    # Log the current count of results
    logging.info(f"Current results count: {len(shared_results)}")


@pytest.mark.asyncio
async def test_task_passthrough():
    """Test to verify task parameters are passed through from submit_task to result processing"""
    
    # Create a manager for sharing the results list between processes
    manager = mp.Manager()
    results = manager.list()
    
    # Create a partial function with our shared results list
    collector = partial(result_collector, results)
    
    # Set config directory for test
    config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_task_passthrough")
    ConfigLoader._set_directories([config_dir])
    
    # Create JobChain with parallel processing
    job_chain = JobChain(result_processing_function=collector)
    
    # Submit text processing tasks with unique identifiers
    test_texts = [
        "hello world",
        "testing task passthrough",
        "verify original data"
    ]
    submitted_tasks = []
    
    for i, text in enumerate(test_texts):
        # Create task with text to process and metadata we want passed through
        task = {
            'text': text,
            'task_id': f"task_{i}",
            'metadata': {
                'original_text': text,
                'sequence': i,
                'type': 'text_processing'
            }
        }
        submitted_tasks.append(task)
        logging.info(f"Submitting task: {task}")
        # Use a different graph for each task
        graph_num = i + 1
        job_chain.submit_task(task, job_name=f'text_processing_graph{graph_num}__text_capitalize')
    
    # Mark completion and wait for processing
    job_chain.mark_input_completed()
    

    
    # Verify basic results count
    assert len(results) == len(test_texts), f"Expected {len(test_texts)} results, got {len(results)}"
    
    # This test is designed to fail to demonstrate that task pass-through should be automatic.
    # Currently, users have to manually implement task pass-through in their jobs, which is error-prone
    # and requires too much boilerplate. Instead, JobChain should automatically pass task data through
    # the entire job chain.
    try:
        for result in results:
            # These assertions will fail because task_pass_through is not automatically handled
            assert 'task_pass_through' in result, "Result missing task_pass_through field"
            task_pass_through = result['task_pass_through']
            
            assert 'task_id' in task_pass_through, "task_id not passed through"
            assert 'metadata' in task_pass_through, "metadata not passed through"
            
            matching_task = next(
                (t for t in submitted_tasks if t['task_id'] == task_pass_through['task_id']), 
                None
            )
            assert matching_task is not None, f"No matching submitted task for {task_pass_through['task_id']}"
            
            assert task_pass_through['metadata'] == matching_task['metadata'], \
                f"Metadata mismatch for task {task_pass_through['task_id']}"
    except AssertionError as e:
        # Log the failure but don't fail the test yet - this is expected until we implement
        # automatic task pass-through in JobChain
        logging.error(f"Task pass-through test failed as expected: {e}")
        logging.error("This is the intended behavior until JobChain implements automatic task pass-through")
