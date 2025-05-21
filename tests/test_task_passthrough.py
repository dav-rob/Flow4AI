import json
import os
import tempfile
from functools import partial
from typing import Any, Dict

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job_loader import ConfigLoader

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

def result_collector(results_file: str, result: Dict[str, Any]) -> None:
    """Collect results by appending to a JSON file.
    
    Args:
        results_file: Path to the file storing results
        result: Result dictionary to append
    """
    logging.info(f"Result collector received: {result}")
    try:
        # Initialize file with empty list if it doesn't exist
        if not os.path.exists(results_file):
            with open(results_file, 'w') as f:
                json.dump([], f)
        
        # Read existing results
        with open(results_file, 'r') as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                # Handle case where file exists but is empty
                results = []
        
        # Transform result to expected format
        transformed_result = result.copy()
        transformed_result['processed_text'] = transformed_result.pop('text')
        
        # Append new result
        results.append(transformed_result)
        
        # Write back all results
        with open(results_file, 'w') as f:
            json.dump(results, f)
            
        logging.info(f"Current results count: {len(results)}")
    except Exception as e:
        logging.error(f"Error collecting result: {e}")
        raise


def test_task_passthrough():
    """Test to verify task parameters are passed through from submit_task to result processing"""
    
    # Create a temporary file for storing results
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        results_file = temp_file.name
        
        try:
            # Create a partial function with our results file
            collector = partial(result_collector, results_file)
            
            # Set config directory for test
            config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_task_passthrough")
            ConfigLoader._set_directories([config_dir])
            
            # Create FlowManagerMP with parallel processing
            flowmanagerMP = FlowManagerMP(result_processing_function=collector)
            
            # Submit text processing tasks with unique identifiers
            submitted_tasks = []

            head_jobs = flowmanagerMP.get_job_names()
            
            for i, task in enumerate(test_tasks):
                submitted_tasks.append(task)
                logging.info(f"Submitting task: {task}")
                # Use a different graph for each task
                graph_num = i + 1
                flowmanagerMP.submit_task(task, fq_name=f'text_processing_graph{graph_num}$$$$text_capitalize$$')
            
            # Mark completion and wait for processing
            flowmanagerMP.mark_input_completed()
            
            # Read results from file
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Verify basic results count
            assert len(results) == len(test_tasks), f"Expected {len(test_tasks)} results, got {len(results)}"
            
            logging.debug("Verifying task pass-through")
            
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
                
                # Verify processed text field exists
                assert 'processed_text' in result, "Result missing processed_text field"
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(results_file)
            except Exception as e:
                logging.warning(f"Failed to delete temporary file {results_file}: {e}")


def test_multiple_task_submissions():
    """Test submitting each task through each head job multiple times"""
    
    # Create a temporary file for storing results
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        results_file = temp_file.name
        
        try:
            # Create a partial function with our results file
            collector = partial(result_collector, results_file)
            
            # Set config directory for test
            config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_task_passthrough")
            ConfigLoader._set_directories([config_dir])
            
            # Create FlowManagerMP with parallel processing
            flowmanagerMP = FlowManagerMP(result_processing_function=collector)
            
            # Get all head jobs
            head_jobs = flowmanagerMP.get_job_names()
            
            # Submit text processing tasks with unique identifiers
            num_iterations = 2
            submitted_tasks = []

            # Submit each task through each head job multiple times
            for task in test_tasks:
                for head_job in head_jobs:
                    for iteration in range(num_iterations):
                        # Create a new task with unique ID for this iteration
                        task_copy = task.copy()
                        task_copy['task_id'] = f"{task['task_id']}_head{head_job}_iter{iteration}"
                        submitted_tasks.append(task_copy)
                        logging.info(f"Submitting task {task_copy['task_id']} to head job {head_job}")
                        flowmanagerMP.submit_task(task_copy, fq_name=head_job)
            
            # Mark completion and wait for processing
            flowmanagerMP.mark_input_completed()
            
            # Read results from file
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Calculate expected number of tasks
            expected_tasks = len(test_tasks) * len(head_jobs) * num_iterations
            assert len(results) == expected_tasks, f"Expected {expected_tasks} results, got {len(results)}"
            
            logging.debug("Verifying task pass-through for multiple submissions")
            
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
                
                # Verify metadata fields are preserved exactly
                assert task_pass_through['metadata'] == matching_task['metadata'], \
                    f"Metadata mismatch for task {task_pass_through['task_id']}"
                
                # Verify processed text field exists
                assert 'processed_text' in result, "Result missing processed_text field"
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(results_file)
            except:
                pass
