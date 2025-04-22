from typing import Any, Dict

from flow4ai.dsl import DSLComponent, JobsDict, p, wrap
from flow4ai.dsl_graph import dsl_to_precedence_graph, visualize_graph
from flow4ai.f4a_graph import validate_graph
from flow4ai.flowmanager import FlowManager
from flow4ai.job import JobABC
from tests.test_utils.graph_evaluation import print_diff


class ProcessorJob(JobABC):
    """Example component that implements JobABC interface."""
    def __init__(self, name, process_type):
        super().__init__(name)
        self.process_type = process_type
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return f"Processor {self.name} of type {self.process_type}"

def test_complex_JobABC_subclass():
    """Test a complex DSL with direct JobABC subclasses"""
    # Create various ProcessorJob instances (MockJobABC subclasses)
    preprocessor = ProcessorJob("Preprocessor", "preprocess")
    analyzer1 = ProcessorJob("Analyzer1", "analyze")
    analyzer2 = ProcessorJob("Analyzer2", "analyze")
    transformer = ProcessorJob("Transformer", "transform")
    aggregator = ProcessorJob("Aggregator", "aggregate")
    formatter = ProcessorJob("Formatter", "format")
    cache_manager = ProcessorJob("CacheManager", "cache")
    logger = ProcessorJob("Logger", "log")
    init = ProcessorJob("Init", "init")
    
    # Create a complex DSL with various combinations of wrapping and direct usage
    # Main pipeline has a preprocessor followed by parallel analyzers, then transforms and formats
    # Side pipeline handles caching and logging which can run in parallel with the main pipeline
    main_pipeline = preprocessor >> p(analyzer1, analyzer2) >> transformer >> formatter
    side_pipeline = init >> p(cache_manager, logger)
    
    # Combine pipelines and add an aggregator at the end
    dsl: DSLComponent = p(main_pipeline, side_pipeline) >> aggregator
    
    print(f"DSL: Complex expression with ProcessorJob instances combined with p() and >>")
    
    # Convert to adjacency list
    graph, jobs = dsl_to_precedence_graph(dsl)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Preprocessor": {"next": ["Analyzer1", "Analyzer2"]},
        "Init": {"next": ["CacheManager", "Logger"]},
        "Analyzer1": {"next": ["Transformer"]},
        "Analyzer2": {"next": ["Transformer"]},
        "CacheManager": {"next": ["Aggregator"]},
        "Logger": {"next": ["Aggregator"]},
        "Transformer": {"next": ["Formatter"]},
        "Formatter": {"next": ["Aggregator"]},
        "Aggregator": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "test_complex_JobABC_subclass")
    
    validate_graph(graph, name="test_complex_JobABC_subclass")

    # DSL by brackets
    main_pipeline = preprocessor >> (analyzer1 | analyzer2) >> transformer >> formatter 
    side_pipeline = init >> (cache_manager | logger)
    dsl:DSLComponent = (main_pipeline | side_pipeline) >> aggregator

    # Convert to adjacency list
    graph, jobs = dsl_to_precedence_graph(dsl)
    visualize_graph(graph)
    

    assert graph == expected_graph or print_diff(graph, expected_graph, "test_complex_JobABC_subclass")
    
    validate_graph(graph, name="test_complex_JobABC_subclass")

def test_complex_mixed():
    """
    Test a complex DSL with a mix of JobABC and functions and lambdas.
    """
    times = lambda x: x*2
    add = lambda x: x+3
    square = lambda x: x**2
    
    def collate(j_ctx):
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
            "collate": collate
        })

    dsl:DSLComponent = (
        p(jobs["analyzer2"], jobs["cache_manager"], jobs["times"]) 
        >> jobs["transformer"] 
        >> jobs["formatter"] 
        >> (jobs["add"] | jobs["square"]) 
        >> jobs["aggregator"] 
        >> jobs["collate"]
    )
        
    # Convert to adjacency list
    graph, jobs = dsl_to_precedence_graph(dsl)
    visualize_graph(graph)
        
    # Define expected graph structure
    expected_graph = {
            "analyzer2": {"next": ["transformer"]},
            "cache_manager": {"next": ["transformer"]},
            "times": {"next": ["transformer"]},
            "transformer": {"next": ["formatter"]},
            "formatter": {"next": ["add", "square"]},
            "add": {"next": ["aggregator"]},
            "square": {"next": ["aggregator"]},
            "aggregator": {"next": ["collate"]},
            "collate": {"next": []}
        }
        
    assert graph == expected_graph or print_diff(graph, expected_graph, "test_complex_mixed")
        
    validate_graph(graph, name="test_complex_mixed")


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
        
    fm = FlowManager()
    fq_name =fm.add_dsl(dsl, "test_execute_job_graph_from_dsl")
    print(fq_name)
    task = {"times": {"fn.x": 1}, "add": {"fn.x": 2}, "square": {"fn.x": 3}}
    fm.submit(task,fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    # Print results
    print("Task counts:", fm.get_counts())
    results = fm.pop_results()
    
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


def test_execute_with_task_params():
    """
    Tests job graph execution defined via DSL using shorthand parameter notation
    for wrapped callables (e.g., {"job.x": value} or {"job": {"x": value}}).
    """
    # Define simple callables
    times = lambda x: x * 2
    add = lambda x, y=1: x + y # Add a default arg to test args/kwargs override
    square = lambda x: x**2
    join = lambda **kwargs: "_".join(map(str, sorted(kwargs.values()))) # Test kwargs

    jobs: JobsDict = wrap({
        "times": times,
        "add": add,
        "square": square,
        "join": join
    })

    jobs["times"].save_result = True
    jobs["add"].save_result = True
    jobs["square"].save_result = True


    # Define DSL Graph (simple linear)
    dsl: DSLComponent = (
        jobs["times"]
        >> jobs["add"]
        >> jobs["square"]
        >> jobs["join"]
    )

    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "test_shorthand_params")

    task = {
        "times": {"x": 5},                   # times(x=5) -> 10
        "add": {"args": [100], "y": 5},      # add(100, y=5) -> 105 (overrides default y=1), Note: 'args' implicitly takes precedence over named params for positionals
        "square": {"x": 3},                  # square(x=3) -> 9 # This would be overridden by output of add
        "join": {"kwargs": {"a": 1, "b": 2, "c": 3}} # join(result=square_output, extra="data") # Result from square (e.g., 105^2) will be passed implicitly if not specified
    }

    # Submit task and wait
    fm.submit(task, fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for tasks to complete"
    
    results = fm.pop_results()
    result_dict = list(results["completed"].values())[0][0] # [0]= first job
    assert result_dict["result"] == "1_2_3"
    assert result_dict["task_pass_through"] == task
    assert result_dict["SAVED_RESULTS"] == {"times": 10, "add": 105, "square": 9}

def test_execute_with_shorthand_task_params():
    """
    Tests job graph execution defined via DSL using shorthand parameter notation
    for wrapped callables (e.g., {"job.x": value} or {"job": {"x": value}}).
    """
    # Define simple callables
    times = lambda x: x * 2
    add = lambda x, y=1: x + y # Add a default arg to test args/kwargs override
    square = lambda x: x**2
    join = lambda **kwargs: "_".join(map(str, sorted(kwargs.values()))) # Test kwargs

    jobs: JobsDict = wrap({
        "times": times,
        "add": add,
        "square": square,
        "join": join
    })

    jobs["times"].save_result = True
    jobs["add"].save_result = True
    jobs["square"].save_result = True


    # Define DSL Graph (simple linear)
    dsl: DSLComponent = (
        jobs["times"]
        >> jobs["add"]
        >> jobs["square"]
        >> jobs["join"]
    )

    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "test_shorthand_params")
    task = {"times.x": 5,"add.args": [100], "add.y": 5, "square.x": 3, "join.kwargs": {"a": 1, "b": 2, "c": 3}} 
    fm.submit(task, fq_name)
    success = fm.wait_for_completion()
    assert success, "Timed out waiting for  tasks to complete"
    
    results = fm.pop_results()
    result_dict = list(results["completed"].values())[0][0] # [0]= first job
    assert result_dict["result"] == "1_2_3"
    assert result_dict["task_pass_through"] == task
    assert result_dict["SAVED_RESULTS"] == {"times": 10, "add": 105, "square": 9}
