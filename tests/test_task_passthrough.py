import asyncio
import multiprocessing as mp
import os
from functools import partial
from typing import Any, Dict

import pytest

import jobchain.jc_logging as logging
from jobchain.job_chain import JobChain
from jobchain.job_loader import ConfigLoader

test_tasks = [
        {
            'text': 'hello world',
            'task_id': 'task_0',
            'metadata': {
                'original_text': 'hello world',
                'sequence': 0,
                'type': 'text_processing',
                'priority': 'high',
                'tags': ['greeting', 'simple'],
                'timestamp': '2025-01-14T01:42:04Z',
                'nested': {
                    'source': 'user_input',
                    'language': 'en',
                    'confidence': 0.95,
                    'metrics': {
                        'word_count': 2,
                        'char_count': 11,
                        'complexity_score': 0.1
                    }
                }
            },
            'config': {
                'preserve_case': False,
                'max_length': 100,
                'filters': ['lowercase', 'trim']
            }
        },
        {
            'text': 'testing task passthrough',
            'task_id': 'task_1',
            'metadata': {
                'original_text': 'testing task passthrough',
                'sequence': 1,
                'type': 'text_processing',
                'priority': 'medium',
                'tags': ['test', 'complex'],
                'timestamp': '2025-01-14T01:42:04Z',
                'nested': {
                    'source': 'test_suite',
                    'language': 'en',
                    'confidence': 0.99,
                    'metrics': {
                        'word_count': 3,
                        'char_count': 23,
                        'complexity_score': 0.4
                    }
                }
            },
            'config': {
                'preserve_case': True,
                'max_length': 200,
                'filters': ['punctuation', 'normalize']
            }
        },
        {
            'text': 'verify original data',
            'task_id': 'task_2',
            'metadata': {
                'original_text': 'verify original data',
                'sequence': 2,
                'type': 'text_processing',
                'priority': 'low',
                'tags': ['verification', 'data'],
                'timestamp': '2025-01-14T01:42:04Z',
                'nested': {
                    'source': 'validation',
                    'language': 'en',
                    'confidence': 0.85,
                    'metrics': {
                        'word_count': 3,
                        'char_count': 19,
                        'complexity_score': 0.6
                    }
                }
            },
            'config': {
                'preserve_case': True,
                'max_length': 150,
                'filters': ['whitespace', 'special_chars']
            }
        }
    ]

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
    
    submitted_tasks = []
    
    for i, task in enumerate(test_tasks):
        submitted_tasks.append(task)
        logging.info(f"Submitting task: {task}")
        # Use a different graph for each task
        graph_num = i + 1
        job_chain.submit_task(task, job_name=f'text_processing_graph{graph_num}__text_capitalize')
    
    # Mark completion and wait for processing
    job_chain.mark_input_completed()
    

    
    # Verify basic results count
    assert len(results) == len(test_tasks), f"Expected {len(test_tasks)} results, got {len(results)}"
    
    logging.debug("Verifying task pass-through")
    # This test is designed to fail to demonstrate that task pass-through should be automatic.
    # Currently, users have to manually implement task pass-through in their jobs, which is error-prone
    # and requires too much boilerplate. Instead, JobChain should automatically pass task data through
    # the entire job chain.
    # try:
    for result in results:
        # Verify task_pass_through exists and contains all original task data
        assert 'task_pass_through' in result, "Result missing task_pass_through field"
        task_pass_through = result['task_pass_through']
        
        assert 'task_id' in task_pass_through, "task_id not passed through"
        assert 'metadata' in task_pass_through, "metadata not passed through"
        
        matching_task = next(
            (t for t in submitted_tasks if t['task_id'] == task_pass_through['task_id']), 
            None
        )
        assert matching_task is not None, f"No matching submitted task for {task_pass_through['task_id']}"
        
        # Verify all metadata fields are preserved exactly
        assert task_pass_through['metadata'] == matching_task['metadata'], \
            f"Metadata mismatch for task {task_pass_through['task_id']}"
        
        # Verify nested structures are preserved
        assert task_pass_through['metadata']['nested'] == matching_task['metadata']['nested'], \
            f"Nested metadata mismatch for task {task_pass_through['task_id']}"
        
        # Verify arrays are preserved
        assert task_pass_through['metadata']['tags'] == matching_task['metadata']['tags'], \
            f"Tags mismatch for task {task_pass_through['task_id']}"
        
        # Verify metrics are preserved
        assert task_pass_through['metadata']['nested']['metrics'] == matching_task['metadata']['nested']['metrics'], \
            f"Metrics mismatch for task {task_pass_through['task_id']}"
        
        # Verify config is passed through if present
        if 'config' in matching_task:
            assert 'config' in task_pass_through, "Config not passed through"
            assert task_pass_through['config'] == matching_task['config'], \
                f"Config mismatch for task {task_pass_through['task_id']}"
    # except AssertionError as e:
    #     # Log the failure but don't fail the test yet - this is expected until we implement
    #     # automatic task pass-through in JobChain
    #     logging.error(f"Task pass-through test failed as expected: {e}")
    #     logging.error("This is the intended behavior until JobChain implements automatic task pass-through")
