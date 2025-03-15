#!/usr/bin/env python
"""
Test script for DSL to precedence graph conversion.
This file contains the test code extracted from dsl_to_graph.py.
"""
from typing import Dict, List
from dsl_play import JobABC, Parallel, Serial, WrappingJob, wrap, w, p, s
from dsl_to_graph import dsl_to_precedence_graph, debug_dsl_structure, visualize_graph


def example12():
    """
    Show the example 12 DSL and its corresponding graph structure in a simple format.
    """
    # Example 12 DSL representation
    g12 = w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)
    
    print("\n===== Example 12 =====")
    print("DSL: w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)")
    
    # Display the graph structure
    print("\nGraph Structure:")
    print("1: [2, 3, 4, 5]")
    print("2: [6]")
    print("3: [7]")
    print("4: [7]")
    print("5: [7]")
    print("6: [8]")
    print("7: [9]")
    print("8: [10]")
    print("9: [11]")
    print("10: [11]")
    print("11: []")
    
    return g12


def example12_verbose():
    """Test the DSL to graph conversion with example 12 with detailed output."""
    # Example from the test file
    g12 = w(1) >> ((p([5,4,3]) >> 7 >> 9) | (w(2) >> 6 >> 8 >> 10)) >> w(11)
    
    # Print the structure of g12 for debugging
    print("\nDSL Object Structure:")
    if isinstance(g12, Serial):
        print(f"Serial object with {len(g12.components)} components")
        for i, comp in enumerate(g12.components):
            print(f"Component {i}: {type(comp).__name__}")
            if isinstance(comp, Parallel) and hasattr(comp, 'components'):
                print(f"  Parallel with {len(comp.components)} sub-components")
                for j, subcomp in enumerate(comp.components):
                    print(f"  Sub-component {j}: {type(subcomp).__name__}")
    
    # Convert and visualize
    graph = dsl_to_precedence_graph(g12)
    print("\nPrecedence Graph for Example 12:")
    visualize_graph(graph)
    
    # Display the expected structure
    expected_structure = """
    {
      1: [2,3,4,5],
      2: [6],
      3: [7],
      4: [7],
      5: [7],
      6: [8],
      7: [9],
      8: [10],
      9: [11],
      10: [11],
      11: []
    }
    """
    print(f"\nExpected structure:{expected_structure}")
    
    # Check if the graph matches the expected structure
    expected_graph = {
        1: [2, 3, 4, 5],
        2: [6],
        3: [7],
        4: [7],
        5: [7],
        6: [8],
        7: [9],
        8: [10],
        9: [11],
        10: [11],
        11: []
    }
    
    # Compare expected with actual
    if graph == expected_graph:
        print("\n✅ The generated graph matches the expected structure!")
    else:
        print("\n❌ The generated graph does NOT match the expected structure!")
        print("Differences:")
        for k in set(list(graph.keys()) + list(expected_graph.keys())):
            if k not in graph:
                print(f"  Missing key {k} in generated graph")
            elif k not in expected_graph:
                print(f"  Extra key {k} in generated graph")
            elif set(graph[k]) != set(expected_graph[k]):
                print(f"  For key {k}: Expected {sorted(expected_graph[k])}, got {sorted(graph[k])}")
    
    # Print the graph as a dictionary for reference
    print("\nGraph as dictionary:")
    print("{")
    for node, edges in sorted(graph.items()):
        print(f"    {node}: {edges},")
    print("}")
    
    return graph


def test_additional_examples():
    """Test additional examples from dsl_play_test.py"""
    print("\n===== Examining Additional DSL Structures =====\n")
    
    # Example 2: Diamond dependency
    print("\n=== Testing Example 2: Diamond Dependency ===\n")
    g2 = w('A') >> (w('B') | w('C')) >> 'D'
    debug_dsl_structure(g2)
    graph = dsl_to_precedence_graph(g2)
    visualize_graph(graph)
    
    # Example 3: More complex composition
    print("\n=== Testing Example 3: Complex Composition ===\n")
    g3 = (w('X') >> 'Y') | 'Z'
    debug_dsl_structure(g3)
    graph = dsl_to_precedence_graph(g3)
    visualize_graph(graph)


if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='DSL to Graph Conversion Tests')
    parser.add_argument('--example', type=str, choices=['example12', 'example12_verbose', 'additional', 'all'],
                        default='all', help='Which example to run')
    
    args = parser.parse_args()
    
    # Run the requested example(s)
    if args.example == 'example12' or args.example == 'all':
        example12()
    
    if args.example == 'example12_verbose' or args.example == 'all':
        print("\n===== Testing DSL to Precedence Graph Conversion (Verbose) =====\n")
        result = example12_verbose()
    
    if args.example == 'additional' or args.example == 'all':
        test_additional_examples()
    
    # Print usage instructions if run with no options
    if args.example == 'all':
        print("\n===== Usage =====")
        print("Run a specific example with:")
        print("  python dsl_to_graph_test.py --example example12")
        print("  python dsl_to_graph_test.py --example example12_verbose")
        print("  python dsl_to_graph_test.py --example additional")
