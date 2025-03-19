#!/usr/bin/env python
"""
Test script for DSL to precedence graph conversion.
This file contains the test code extracted from dsl_to_graph.py.
"""
from typing import Any, Dict, List, Union

from dsl_play import MockJobABC, Parallel, Serial, WrappingJob, p, s, w, wrap
from dsl_to_graph import (debug_dsl_structure, dsl_to_precedence_graph,
                          visualize_graph)

from jobchain.jc_graph import validate_graph


class CustomAnyObject:
    """Example custom processor class."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"{self.name}"


class ProcessorJob(MockJobABC):
    """Example component that implements JobABC interface."""
    def __init__(self, name, process_type):
        super().__init__(name)
        self.process_type = process_type
    def __repr__(self):
        return f"{self.name}"
    
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return f"{self.name}"


def example12():
    """
    Show the example 12 DSL and its corresponding graph structure in a simple format.
    """
    # Example 12 DSL representation
    g12 = w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)
    
    print("\n===== Example 12 =====")
    print("DSL: w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)")
    
    # Display the graph structure
    graph = dsl_to_precedence_graph(g12)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        '1': {'next': ['5', '4', '3', '2']},
        '2': {'next': ['6']},
        '3': {'next': ['7']},
        '4': {'next': ['7']},
        '5': {'next': ['7']},
        '6': {'next': ['8']},
        '7': {'next': ['9']},
        '8': {'next': ['10']},
        '9': {'next': ['11']},
        '10': {'next': ['11']},
        '11': {'next': []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 12")
    
    validate_graph(graph, name="Example 12")
    
    return g12


def example12_verbose():
    """Test the DSL to graph conversion with example 12 with detailed output."""
    # Example from the test file
    g12 = w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)
    
    # Convert and visualize
    graph = dsl_to_precedence_graph(g12)
    print("\nPrecedence Graph for Example 12:")
    visualize_graph(graph)
    
    # Display the expected structure
    expected_structure = """
    {
        '1': {'next': ['5', '4', '3', '2']},
        '2': {'next': ['6']},
        '3': {'next': ['7']},
        '4': {'next': ['7']},
        '5': {'next': ['7']},
        '6': {'next': ['8']},
        '7': {'next': ['9']},
        '8': {'next': ['10']},
        '9': {'next': ['11']},
        '10': {'next': ['11']},
        '11': {'next': []}
    }
    """
    print(f"\nExpected structure:{expected_structure}")
    
    # Check if the graph matches the expected structure
    expected_graph = {
        '1': {'next': ['5', '4', '3', '2']},
        '2': {'next': ['6']},
        '3': {'next': ['7']},
        '4': {'next': ['7']},
        '5': {'next': ['7']},
        '6': {'next': ['8']},
        '7': {'next': ['9']},
        '8': {'next': ['10']},
        '9': {'next': ['11']},
        '10': {'next': ['11']},
        '11': {'next': []}
    }
    
    # Compare expected with actual
    if graph == expected_graph:
        print("\n✅ The generated graph matches the expected structure!")
    else:
        print_diff(graph, expected_graph, "Example 12 Verbose")


def print_diff(graph, expected_graph, test_name="Unknown"):
    """
    Print the differences between the two graphs.
    Also returns False if there are differences, True if graphs match.
    """
    print(f"\n❌ The generated graph for {test_name} does NOT match the expected structure!")
    print("Differences:")
    has_differences = False
    
    for k in set(list(graph.keys()) + list(expected_graph.keys())):
        if k not in graph:
            print(f"  Missing key {k} in generated graph")
            has_differences = True
        elif k not in expected_graph:
            print(f"  Extra key {k} in generated graph")
            has_differences = True
        else:
            # Check the 'next' attribute in each node
            if 'next' in graph[k] and 'next' in expected_graph[k]:
                if set(graph[k]['next']) != set(expected_graph[k]['next']):
                    print(f"  For key {k}, 'next' values differ:")
                    print(f"    Expected: {sorted(expected_graph[k]['next'])}")
                    print(f"    Actual:   {sorted(graph[k]['next'])}")
                    
                    # Show which elements were added or removed
                    added = set(graph[k]['next']) - set(expected_graph[k]['next'])
                    removed = set(expected_graph[k]['next']) - set(graph[k]['next'])
                    if added:
                        print(f"    Added elements: {sorted(added)}")
                    if removed:
                        print(f"    Removed elements: {sorted(removed)}")
                    has_differences = True
            else:
                # Check for other differences in the node dictionaries
                if graph[k] != expected_graph[k]:
                    print(f"  For key {k}, values differ:")
                    print(f"    Expected: {expected_graph[k]}")
                    print(f"    Actual:   {graph[k]}")
                    has_differences = True
    
    if has_differences:
        # Print the graph as a dictionary for reference
        print("\nActual graph as dictionary:")
        print("{")
        for node, edges in graph.items():
            print(f"    '{node}': {edges},")
        print("}")
    else:
        print("✅ No differences found! This is unexpected since the assertion failed.")
    
    validate_graph(graph, name=test_name)
    
    return not has_differences


def example1_simple_parallel():
    """Example 1: Simple parallel composition"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    
    g1 = w(obj1) | obj2
    
    print("\n===== Example 1: Simple Parallel =====")
    print(f"DSL: w(obj1) | obj2")    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g1)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": []},
        "Object 2": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 1")
    
    validate_graph(graph, name="Example 1")
    
    return g1


def example2_serial_composition():
    """Example 2: Serial composition"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    
    g2 = w(obj1) >> w(obj2)
    
    print("\n===== Example 2: Serial Composition =====")
    print(f"DSL: w(obj1) >> w(obj2)")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g2)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": ["Object 2"]},
        "Object 2": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 2")
    
    validate_graph(graph, name="Example 2")
    
    return g2


def example3_combining_serial_and_parallel():
    """Example 3: Combining serial and parallel compositions"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    obj3 = "Object 3"
    
    g3 = (w(obj1) >> obj2) | obj3
    
    print("\n===== Example 3: Combining Serial and Parallel =====")
    print(f"DSL: (w(obj1) >> obj2) | obj3")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g3)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": ["Object 2"]},
        "Object 3": {"next": []},
        "Object 2": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 3")
    
    validate_graph(graph, name="Example 3")
    
    return g3


def example4_complex_compositions():
    """Example 4: More complex compositions"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    obj3 = "Object 3"
    
    g4 = w(obj1) >> (w(obj2) | obj3)
    
    print("\n===== Example 4: Complex Compositions =====")
    print(f"DSL: w(obj1) >> (w(obj2) | obj3)")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g4)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": ["Object 2", "Object 3"]},
        "Object 2": {"next": []},
        "Object 3": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 4")
    
    validate_graph(graph, name="Example 4")
    
    return g4


def example5_using_parallel_function():
    """Example 5: Using parallel function"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    obj3 = "Object 3"
    
    objs = [obj1, obj2, obj3]
    g5 = p(objs)
    
    print("\n===== Example 5: Using Parallel Function =====")
    print(f"DSL: p([obj1, obj2, obj3])")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g5)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": []},
        "Object 2": {"next": []},
        "Object 3": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 5")
    
    validate_graph(graph, name="Example 5")
    
    return g5


def example6_using_serial_function():
    """Example 6: Using serial function"""
    obj1 = "Object 1"
    obj2 = "Object 2"
    obj3 = "Object 3"
    
    objs = [obj1, obj2, obj3]
    g6 = s(objs)
    
    print("\n===== Example 6: Using Serial Function =====")
    print(f"DSL: s([obj1, obj2, obj3])")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g6)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Object 1": {"next": ["Object 2"]},
        "Object 2": {"next": ["Object 3"]},
        "Object 3": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 6")
    
    validate_graph(graph, name="Example 6")
    
    return g6


def example7_composition_with_primitives():
    """Example 7: Composition with strings and numbers"""
    g7 = w("Task A") >> 123 | "Task B"
    
    print("\n===== Example 7: Composition with Primitives =====")
    print(f"DSL: w(\"Task A\") >> 123 | \"Task B\"")

    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g7)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Task A": {"next": ["123"]},
        "123": {"next": []},
        "Task B": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 7")
    
    validate_graph(graph, name="Example 7")
    
    return g7


def example8_direct_wrapping_job():
    """Example 8: Using direct WrappingJob instances"""
    c1 = WrappingJob("Direct WrappingJob")
    g8 = w("Task C") >> c1
    
    print("\n===== Example 8: Direct WrappingJob Instances =====")
    print(f"DSL: w(\"Task C\") >> WrappingJob(\"Direct WrappingJob\")")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g8)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Task C": {"next": ["Direct WrappingJob"]},
        "Direct WrappingJob": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 8")
    
    validate_graph(graph, name="Example 8")
    
    return g8


def example9_combining_everything():
    """Example 9: Combining everything together"""
    g9 = p([w("T1") >> w(1), "T2", 3]) >> w(4) | w(s([5, "T3", w(6)]))
    
    print("\n===== Example 9: Combining Everything =====")
    print(f"DSL: p([w(\"T1\") >> w(1), \"T2\", 3]) >> w(4) | w(s([5, \"T3\", w(6)]))")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g9)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "T1": {"next": ["1"]},
        "T2": {"next": ["4"]},
        "3": {"next": ["4"]},
        "5": {"next": ["T3"]},
        "1": {"next": ["4"]},
        "T3": {"next": ["6"]},
        "4": {"next": []},
        "6": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 9")
    
    validate_graph(graph, name="Example 9")
    
    return g9


def example10_custom_objects():
    """Example 10: Using custom objects"""
    # Using strings as placeholders for custom objects
    c1 = CustomAnyObject("Custom1")
    c2 = CustomAnyObject("Custom2")
    
    g10 = w(c1) >> c2
    
    print("\n===== Example 10: Custom Objects =====")
    print(f"DSL: w(c1) >> c2")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g10)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Custom1": {"next": ["Custom2"]},
        "Custom2": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 10")
    
    validate_graph(graph, name="Example 10")
    
    return g10


def example11_ordinary_JobABC_subclasses():
    """Example 11: Using ordinary JobABC subclasses"""
    # Using simpler representations for this example
    processorA = ProcessorJob("Processor A", "type1")
    processorB = ProcessorJob("Processor B", "type2")
    
    g11 = w(processorA) >> processorB
    
    print("\n===== Example 11: Component Subclasses =====")
    print(f"DSL: w(processorA) >> processorB")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g11)
    visualize_graph(graph)
    
    # Define expected graph structure
    expected_graph = {
        "Processor A": {"next": ["Processor B"]},
        "Processor B": {"next": []}
    }
    
    # Verify graph structure
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 11")
    
    validate_graph(graph, name="Example 11")
    
    return g11


def example13_complex_JobABC_subclass():
    """Example 13: Complex DSL with both wrapped objects and direct MockJobABC subclasses"""
    # Create various ProcessorJob instances (MockJobABC subclasses)
    preprocessor = ProcessorJob("Preprocessor", "preprocess")
    analyzer1 = ProcessorJob("Analyzer1", "analyze")
    analyzer2 = ProcessorJob("Analyzer2", "analyze")
    transformer = ProcessorJob("Transformer", "transform")
    aggregator = ProcessorJob("Aggregator", "aggregate")
    formatter = ProcessorJob("Formatter", "format")
    cache_manager = ProcessorJob("CacheManager", "cache")
    logger = ProcessorJob("Logger", "log")
    
    # Create a complex DSL with various combinations of wrapping and direct usage
    # Main pipeline has a preprocessor followed by parallel analyzers, then transforms and formats
    # Side pipeline handles caching and logging which can run in parallel with the main pipeline
    main_pipeline = preprocessor >> p([analyzer1, analyzer2]) >> transformer >> formatter
    side_pipeline = w("Init") >> p([cache_manager, logger])
    
    # Combine pipelines and add an aggregator at the end
    g13 = p([main_pipeline, side_pipeline]) >> aggregator
    
    print("\n===== Example 13: Complex JobABC Subclass Usage =====")
    print(f"DSL: Complex expression with ProcessorJob instances combined with p(), s(), >> and |")
    
    # Convert to adjacency list
    graph = dsl_to_precedence_graph(g13)
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
    assert graph == expected_graph or print_diff(graph, expected_graph, "Example 13")
    
    validate_graph(graph, name="Example 13")

    return g13


if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(description='DSL to Graph Conversion Tests')
    parser.add_argument('--example', type=str, 
                       choices=['all', 'list', 'example1', 'example2', 'example3', 'example4', 'example5', 
                                'example6', 'example7', 'example8', 'example9', 'example10', 
                                'example11', 'example12', 'example12_verbose', 'example13'],
                       default='all', help='Which example to run. Use "list" to just show available examples without running any.')
    
    args = parser.parse_args()
    
    # Dictionary mapping example names to their functions
    examples = {
        'example1': example1_simple_parallel,
        'example2': example2_serial_composition,
        'example3': example3_combining_serial_and_parallel,
        'example4': example4_complex_compositions,
        'example5': example5_using_parallel_function,
        'example6': example6_using_serial_function,
        'example7': example7_composition_with_primitives,
        'example8': example8_direct_wrapping_job,
        'example9': example9_combining_everything,
        'example10': example10_custom_objects,
        'example11': example11_ordinary_JobABC_subclasses,
        'example12': example12,
        'example12_verbose': example12_verbose,
        'example13': example13_complex_JobABC_subclass
    }
    
    # Just list available examples without running any
    if args.example == 'list':
        print("\n===== Available Examples =====")
        for example_name in examples.keys():
            print(f"  python dsl_to_graph_test.py --example {example_name}")
    # Run all examples except verbose by default
    elif args.example == 'all':
        for example_name, example_func in examples.items():
            # Skip the verbose example in the default run
            if example_name != 'example12_verbose':
                example_func()
        
        # Print usage instructions after running all examples
        print("\n===== Usage =====")
        print("To see a list of all examples without running them:")
        print("  python dsl_to_graph_test.py --example list")
        print("\nTo run a specific example:")
        print("  python dsl_to_graph_test.py --example <example_name>")
    else:
        # Run a specific example
        examples[args.example]()
