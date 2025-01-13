import asyncio
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

import jobchain.jc_logging as logging
from jobchain.job_chain import JobChain
from jobchain.job_loader import ConfigLoader


# NB result_collector is used by the JobExecutorProcess and so has a different
#  process to the test so results need to be shared using results = manager.list()
#  its either this or write to file.
def result_collector(shared_results, result):
    logging.info(f"Result collector received: {result}")
    shared_results.append(result)

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
    
    # Get job instances from JobChain
    jobs = job_chain.job_map
    
    # Check for race conditions and state corruption in each job
    for job_name, job in jobs.items():
        logging.info(f"\nStats for {job_name}:")
        logging.info(f"Total tasks processed: {job.stats.processed_count}")
        logging.info(f"Maximum concurrent executions: {job.stats.max_concurrent}")
        logging.info(f"Unique tasks processed: {len(job.stats.processed_tasks)}")
        
        # Check for duplicate processing
        expected_tasks = set()
        if job_name.startswith('head'):
            expected_tasks = {f"{job_name}_{i}" for i in range(num_tasks_per_head)}
        else:
            # Middle and tail jobs should process all tasks
            for job_name in ['head1', 'head2', 'head3', 'head4']:
                expected_tasks.update({f"{job_name}_{i}" for i in range(num_tasks_per_head)})
        
        missing_tasks = expected_tasks - job.stats.processed_tasks
        extra_tasks = job.stats.processed_tasks - expected_tasks
        
        if missing_tasks:
            logging.error(f"{job_name} missing tasks: {missing_tasks}")
        if extra_tasks:
            logging.error(f"{job_name} has extra tasks: {extra_tasks}")
        
        assert not missing_tasks, f"{job_name} did not process all expected tasks"
        assert not extra_tasks, f"{job_name} processed unexpected tasks"
        
    # Analyze timing patterns
    for job_name, job in jobs.items():
        logging.info(f"\nTiming analysis for {job_name}:")
        for task_id, times in job.stats.processing_times.items():
            if len(times) > 1:
                logging.error(f"Task {task_id} was processed {len(times)} times!")
                logging.error(f"Processing times: {times}")