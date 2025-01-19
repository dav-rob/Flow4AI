import asyncio
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

import jobchain.jc_logging as logging
from jobchain.job import JobABC
from jobchain.job_chain import JobChain
from jobchain.job_loader import ConfigLoader


def returns_collector(shared_results, result):
    logging.info(f"Result collector received: {result[JobABC.TASK_PASSTHROUGH_KEY]['task']}, with result: {result['result']}")
    shared_results.append(result)


@pytest.mark.asyncio
async def test_concurrency_by_expected_returns():
    # Create a manager for sharing the results list between processes
    manager = mp.Manager()
    shared_results = manager.list()
    
    # Create a partial function with our shared results list
    collector = partial(returns_collector, shared_results)
    
    # Set config directory for test
    config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency_by_returns")
    ConfigLoader._set_directories([config_dir])
    
    # Create JobChain with parallel processing
    job_chain = JobChain(result_processing_function=collector)
    logging.info(f"Names of jobs in head job: {job_chain.get_job_graph_mapping()}")

    def submit_task(range_val:int):
        for i in range(range_val):
            job_chain.submit_task({'task': f'range {range_val}, item {i}'})

    def check_results():
        for result in shared_results:
            assert result['result'] == 'A.A.B.C.E.A.D.F.G'

        shared_results[:] = []  # Clear the shared_results using slice assignment
    

    submit_task(1)
    check_results()



    job_chain.mark_input_completed()

@pytest.mark.asyncio
async def test_concurrency_by_expected_returns_fails_hangs():
    # Create a manager for sharing the results list between processes
    manager = mp.Manager()
    shared_results = manager.list()
    
    # Create a partial function with our shared results list
    collector = partial(returns_collector, shared_results)
    
    # Set config directory for test
    config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency_by_returns")
    ConfigLoader._set_directories([config_dir])
    
    # Create JobChain with parallel processing
    job_chain = JobChain(result_processing_function=collector)
    logging.info(f"Names of jobs in head job: {job_chain.get_job_graph_mapping()}")

    def submit_task(range_val:int):
        for i in range(range_val):
            job_chain.submit_task({'task': f'range {range_val}, item {i}'})

    def check_results():
        for result in shared_results:
            assert result['result'] == 'A.A.B.C.E.A.D.F.G'

        shared_results[:] = []  # Clear the shared_results using slice assignment
    

    submit_task(7)
    check_results()



    job_chain.mark_input_completed()
