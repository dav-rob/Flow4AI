
from typing import Any, Dict

from jobchain.dsl import DSLComponent, JobsDict, p, wrap
from jobchain.job import JobABC
from jobchain.taskmanager import TaskManager


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
    fq_name =tm.add_dsl(dsl, jobs, "test_execute_job_graph_from_dsl")
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

    def collate(j_ctx):
        inputs = j_ctx["inputs"]
        output = f"{inputs['once']['result']} {inputs['ina']['result']}"
        return output

    def completion_callback(result):
        assert result == "once upon a time in a galaxy far far away"
            
    jobs = wrap({
        "once": once,
        "ina": ina,
        "collate": collate
    })

    dsl =(jobs["once"] | jobs["ina"] ) >> jobs["collate"]
        
    tm = TaskManager(completion_callback=completion_callback)
    fq_name =tm.add_dsl(dsl, jobs, "test_completion_callback")
    print(fq_name)
    task = {"once": {"fn.x": "once "}, "ina": {"fn.x": "in a "}}
    tm.submit(task,fq_name)
    tm.wait_for_completion()

        
    