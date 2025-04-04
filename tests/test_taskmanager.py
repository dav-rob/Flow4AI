import asyncio
import time
from typing import Any, Dict

import jobchain.jc_logging as logging
from jobchain.dsl import DSLComponent, JobsDict, p, wrap
from jobchain.job import JobABC
from jobchain.taskmanager import TaskManager

# Configure logging
logger = logging.getLogger(__name__)


class ProcessorJob(JobABC):
    """Example component that implements JobABC interface."""
    def __init__(self, name, process_type):
        super().__init__(name)
        self.process_type = process_type
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return f"Processor {self.name} of type {self.process_type}"


def test_execute_job_graph_from_dsl():
    """
    Test a complex DSL with a mix of JobABC and functions and lambdas.
    """
    times = lambda x: x*2
    add = lambda x: x+3
    square = lambda x: x**2
    
    def test_context(j_ctx):
        task = j_ctx["task"]
        inputs = j_ctx["inputs"]
        return {"task": task, "inputs": inputs}
        
    analyzer2 = ProcessorJob("Analyzer2", "analyze")
    transformer = ProcessorJob("Transformer", "transform")
    aggregator = ProcessorJob("Aggregator", "aggregate")
    formatter = ProcessorJob("Formatter", "format")
    cache_manager = ProcessorJob("CacheManager", "cache")

    jobs:JobsDict = wrap({
            "analyzer2": analyzer2,
            "cache_manager": cache_manager,
            "times": times,
            "transformer": transformer,
            "formatter": formatter,
            "add": add,
            "square": square,
            "aggregator": aggregator,
            "test_context": test_context
        })

    jobs["times"].save_result = True
    jobs["add"].save_result = True
    jobs["square"].save_result = True

    dsl:DSLComponent = (
        p(jobs["analyzer2"], jobs["cache_manager"], jobs["times"]) 
        >> jobs["transformer"] 
        >> jobs["formatter"] 
        >> (jobs["add"] | jobs["square"]) 
        >> jobs["test_context"]
        >> jobs["aggregator"] 
    )
        
    tm = TaskManager()
    fq_name =tm.add_dsl(dsl, "test_execute_job_graph_from_dsl")
    print(fq_name)
    task = {"times": {"fn.x": 1}, "add": {"fn.x": 2}, "square": {"fn.x": 3}}
    tm.submit(task,fq_name)
    success = tm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Print results
    print("Task counts:", tm.get_counts())
    results = tm.pop_results()
    
    print("\nCompleted tasks:")
    for job_name, job_results in results["completed"].items():
        for result_data in job_results:
            print(f"- {job_name}: {result_data['result']}")
    
    print("\nErrors:")
    if results["errors"]:
        error_messages = []
        for job_name, job_errors in results["errors"].items():
            for error_data in job_errors:
                error_msg = f"- {job_name}: {error_data['error']}"
                print(error_msg)
                error_messages.append(error_msg)
        
        # Raise exception with all errors
        raise Exception("Errors occurred during job execution:\n" + "\n".join(error_messages))
    
    print("\nResults:")
    print(results["completed"].values())
    result_dict = list(results["completed"].values())[0][0] # [0]= first job
    assert result_dict["result"] == "Processor test_execute_job_graph_from_dsl$$$$aggregator$$ of type aggregate"
    assert result_dict["task_pass_through"] == task
    assert result_dict["SAVED_RESULTS"] == {"times": 2, "add": 5, "square": 9}
    

def test_completion_callback():
    once = lambda x: x + "upon a time"
    ina = lambda x: x + "galaxy far far away"

    async def collate(j_ctx):
        await asyncio.sleep(2)
        inputs = j_ctx["inputs"]
        output = f"{inputs['once']['result']} {inputs['ina']['result']}"
        return output

    def post_processor(result):
        assert result["result"] == "once upon a time in a galaxy far far away"
            
    jobs = wrap({
        "once": once,
        "ina": ina,
        "collate": collate
    })

    dsl =(jobs["once"] | jobs["ina"] ) >> jobs["collate"]
        
    tm = TaskManager(on_complete=post_processor)
    fq_name =tm.add_dsl(dsl, "test_completion_callback")
    print(fq_name)
    task = {"once": {"fn.x": "once "}, "ina": {"fn.x": "in a "}}
    tm.submit(task,fq_name)
    tm.wait_for_completion()

class DelayedJob(JobABC):
    async def run(self, task):
        short_name = self.parse_job_name(self.name)
        delay = task[short_name]
        logger.debug(f"Executing DelayedJob for {task} with delay {delay}")
        await asyncio.sleep(delay)
        return {"status": f"{self.name} complete"}

def create_tm(graph_name:str):
    jobs = {"delayed": DelayedJob("delayed")}
    dsl = jobs["delayed"]
    tm = TaskManager(on_complete=lambda x: logger.debug(f"received {x}"))
    fq_name = tm.add_dsl(dsl, graph_name)
    return tm, fq_name

def execute_tm_with_delay(delay, task_count=10):
    tm, fq_name = create_tm("test_parallel_execution" + str(delay))
    task = {"delayed": delay}
    start_time = time.perf_counter()
    for i in range(task_count):
        tm.submit(task, fq_name)
    tm.wait_for_completion()
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    logger.info(f"*** Execution time for {task_count} tasks = {execution_time}")
    return execution_time, tm

def test_parallel_execution():
    execution_time, tm = execute_tm_with_delay(1.0)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.5

    execution_time, tm = execute_tm_with_delay(2.0)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5


def test_parallel_load():
    logger.info("Executing parallel load tasks = 500")
    execution_time, tm = execute_tm_with_delay(1.0, 500)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.4

    logger.info("Executing parallel load tasks = 1000")
    execution_time, tm = execute_tm_with_delay(1.0, 1000)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 1.8

    logger.info("Executing parallel load tasks = 2000")
    execution_time, tm = execute_tm_with_delay(1.0, 2000)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 2.5

    logger.info("Executing parallel load tasks = 5000")
    execution_time, tm = execute_tm_with_delay(1.0, 5000)
    result_count = tm.get_counts()
    assert result_count["errors"] == 0, f"{result_count['errors']} errors occurred during job execution"
    assert execution_time < 4.0





