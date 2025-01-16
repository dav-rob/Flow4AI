import asyncio
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

import jobchain.jc_logging as logging
from jobchain.job_chain import JobChain
from jobchain.job_loader import ConfigLoader


# NB this result_collector is used by the JobExecutorProcess and so has a different
#  process to the test so results need to be shared using results = manager.list()
#  its either this or write to file.
def result_collector(shared_results, result):
    logging.info(f"Result collector received: {result}")
    shared_results.append(result)


# We have tried many many different ways to create race conditions in JobChain
#   this is the remains of one of those ways.  Ways have been tried with 
#   thousands of submitted tasks, to no avail.  Currently, this file is a place-
#   holder until we find a test case.  Currently no race conditions, though the 
#   code does not seem immune to them on first inspection.
@pytest.mark.asyncio
async def test_concurrent_state_corruption():
    """Test to demonstrate state corruption under concurrent load"""
    
    # Create a manager for sharing the results list between processes
    manager = mp.Manager()
    results = manager.list()
    
    # Create a partial function with our shared results list
    collector = partial(result_collector, results)
    
    # Set config directory for test
    config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency")
    ConfigLoader._set_directories([config_dir])
    
    # Create JobChain with parallel processing
    job_chain = JobChain(result_processing_function=collector)
    
    # Submit multiple tasks rapidly to each head
    num_tasks_per_head = 5
    total_tasks = num_tasks_per_head * 4  # 4 head jobs
    
    for i in range(num_tasks_per_head):
        for job_name in job_chain.get_job_names():
            task = {
                'task_id': f"{job_name}_{i}",
                'data': f"task_{job_name}_{i}"
            }
            logging.debug(f"Submitting task: {task}")
            job_chain.submit_task(task, job_name=job_name)
    
    # Mark completion and wait for processing
    job_chain.mark_input_completed()
    
    # Verify results
    assert len(results) == total_tasks, f"Expected {total_tasks} results, got {len(results)}"

    def returns_collector(shared_results, result):
        logging.info(f"Result collector received: {result}")
        shared_results.append(result)
    
    @pytest.mark.asyncio
    async def test_concurrency_by_expected_returns():
        # Create a manager for sharing the results list between processes
        manager = mp.Manager()
        results = manager.list()
        
        # Create a partial function with our shared results list
        collector = partial(returns_collector, results)
        
        # Set config directory for test
        config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency2")
        ConfigLoader._set_directories([config_dir])
        
        # Create JobChain with parallel processing
        job_chain = JobChain(result_processing_function=collector)