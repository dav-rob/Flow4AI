"""Tests for FQ name collision handling in FlowManager."""

import pytest

from flow4ai import f4a_logging as logging
from flow4ai.dsl import DSLComponent, JobsDict, wrap
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC, Task

# Configure logging
logger = logging.getLogger(__name__)


class SimpleProducerJob(JobABC):
    """Job that produces a value specified at initialization time."""
    
    def __init__(self, name, value):
        super().__init__(name)
        self.value = value
        
    async def run(self, task):
        logger.info(f"Producer {self.name} producing value: {self.value}")
        return {"value": self.value}


class SimpleConsumerJob(JobABC):
    """Job that consumes input from a producer."""
    
    def __init__(self, name, expected_value=None):
        super().__init__(name)
        self.expected_value = expected_value
        
    async def run(self, task):
        # Get inputs from predecessor jobs
        inputs = self.get_inputs()
        logger.info(f"Consumer {self.name} received inputs: {inputs}")
        
        # Get value from producer - using short job name
        producer_value = inputs.get("producer", {}).get("value", None)
        
        return {
            "received_value": producer_value,
            "expected_value": self.expected_value,
            "match": producer_value == self.expected_value
        }


def test_fq_name_collision_resolution():
    """Test that FQ name collisions are properly resolved with unique variants."""
    
    # Create a FlowManager
    fm = FlowManager()
    
    # --- First DSL with producer="A" ---
    producer_a = SimpleProducerJob("producer", "A")
    consumer_a = SimpleConsumerJob("consumer", expected_value="A")
    
    jobs_a = wrap({
        "producer": producer_a,
        "consumer": consumer_a
    })
    
    # Create pipeline: producer_a >> consumer_a
    dsl_a = jobs_a["producer"] >> jobs_a["consumer"]
    
    # Add first DSL - should get standard FQ name
    logger.info("Adding first DSL (A)")
    fq_name_a = fm.add_dsl(dsl_a, "test_pipeline")
    logger.info(f"First DSL FQ name: {fq_name_a}")
    
    # --- Second DSL with producer="B" but same structure ---
    producer_b = SimpleProducerJob("producer", "B")  # Same job name but different value
    consumer_b = SimpleConsumerJob("consumer", expected_value="B")
    
    jobs_b = wrap({
        "producer": producer_b,
        "consumer": consumer_b
    })
    
    # Create pipeline with same structure: producer_b >> consumer_b
    dsl_b = jobs_b["producer"] >> jobs_b["consumer"]
    
    # Add second DSL - should get a unique variant suffix
    logger.info("Adding second DSL (B)")
    fq_name_b = fm.add_dsl(dsl_b, "test_pipeline")
    logger.info(f"Second DSL FQ name: {fq_name_b}")
    
    # Verify two different FQ names were generated
    assert fq_name_a != fq_name_b, "Different DSLs with same structure should get unique FQ names"
    
    # --- Submit Tasks ---
    # Create and submit task for first DSL
    task_a = Task({"id": "A"})
    logger.info(f"Submitting task A to DSL A with FQ name: {fq_name_a}")
    fm.submit(task_a, fq_name_a)
    success = fm.wait_for_completion()
    assert success, "Task A did not complete successfully"
    
    # Get and check results 
    results_a = fm.pop_results()
    logger.info(f"Results for task A: {results_a}")
    
    # Extract consumer result from task A
    consumer_result_a = None
    for job_name, job_results in results_a.get("completed", {}).items():
        if job_name == fq_name_a and job_results:
            consumer_result_a = job_results[0]
            break
            
    assert consumer_result_a is not None, "No result found for DSL A"
    assert consumer_result_a.get("received_value") == "A", "Consumer A should have received value 'A'"
    assert consumer_result_a.get("expected_value") == "A", "Consumer A expected value should be 'A'"
    assert consumer_result_a.get("match") == True, "Consumer A expected and received values should match"
    
    # Create and submit task for second DSL
    task_b = Task({"id": "B"})
    logger.info(f"Submitting task B to DSL B with FQ name: {fq_name_b}")
    fm.submit(task_b, fq_name_b)
    success = fm.wait_for_completion()
    assert success, "Task B did not complete successfully"
    
    # Get and check results
    results_b = fm.pop_results()
    logger.info(f"Results for task B: {results_b}")
    
    # Extract consumer result from task B
    consumer_result_b = None
    for job_name, job_results in results_b.get("completed", {}).items():
        if job_name == fq_name_b and job_results:
            consumer_result_b = job_results[0]
            break
            
    assert consumer_result_b is not None, "No result found for DSL B"
    assert consumer_result_b.get("received_value") == "B", "Consumer B should have received value 'B'"
    assert consumer_result_b.get("expected_value") == "B", "Consumer B expected value should be 'B'"
    assert consumer_result_b.get("match") == True, "Consumer B expected and received values should match"
    
    # --- Add a third DSL with same structure ---
    producer_c = SimpleProducerJob("producer", "C")
    consumer_c = SimpleConsumerJob("consumer", expected_value="C")
    
    jobs_c = wrap({
        "producer": producer_c,
        "consumer": consumer_c
    })
    
    # Create pipeline with same structure: producer_c >> consumer_c
    dsl_c = jobs_c["producer"] >> jobs_c["consumer"]
    
    # Add third DSL - should get a different unique variant suffix
    logger.info("Adding third DSL (C)")
    fq_name_c = fm.add_dsl(dsl_c, "test_pipeline")
    logger.info(f"Third DSL FQ name: {fq_name_c}")
    
    # Verify third FQ name is different from the first two
    assert fq_name_c != fq_name_a, "Third DSL should get a different FQ name than first DSL"
    assert fq_name_c != fq_name_b, "Third DSL should get a different FQ name than second DSL"
    
    # Create and submit task for third DSL
    task_c = Task({"id": "C"})
    logger.info(f"Submitting task C to DSL C with FQ name: {fq_name_c}")
    fm.submit(task_c, fq_name_c)
    success = fm.wait_for_completion()
    assert success, "Task C did not complete successfully"
    
    # Get and check results
    results_c = fm.pop_results()
    logger.info(f"Results for task C: {results_c}")
    
    # Extract consumer result from task C
    consumer_result_c = None
    for job_name, job_results in results_c.get("completed", {}).items():
        if job_name == fq_name_c and job_results:
            consumer_result_c = job_results[0]
            break
            
    assert consumer_result_c is not None, "No result found for DSL C"
    assert consumer_result_c.get("received_value") == "C", "Consumer C should have received value 'C'"
    assert consumer_result_c.get("expected_value") == "C", "Consumer C expected value should be 'C'"
    assert consumer_result_c.get("match") == True, "Consumer C expected and received values should match"
