from typing import Any, Dict

from jobchain.dsl import p
from jobchain.dsl_graph import dsl_to_precedence_graph, visualize_graph
from jobchain.jc_graph import validate_graph
from jobchain.job import JobABC
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
    dsl = p(main_pipeline, side_pipeline) >> aggregator
    
    print(f"DSL: Complex expression with ProcessorJob instances combined with p(), s(), >> and |")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(dsl)
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