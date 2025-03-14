"""
Test script for the graph_pic module in JobChain.

This script demonstrates how to use the graph_pic module to visualize
job graphs using NetworkX and Matplotlib.

Usage:
    python graph_pic_test.py [example_number]
    - If no argument is provided, runs example 1 (basic precedence graph)
    - If a number is provided, runs the specified example
"""

import os
import sys
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.jobchain.graph_pic import visualize_graph, compare_layouts


def print_graph_definition(graph_definition):
    """Print a graph definition in a nicely formatted way."""
    print("\nGraph Definition:")
    print("================")
    for node, edges in graph_definition.items():
        print(f"    \"{node}\": {json.dumps(edges)},")
    print()


def example_1_basic_precedence():
    """Basic precedence graph with a single source and sink."""
    graph_definition = {
        "1": {"next": ["2", "3", "4", "5"]},
        "2": {"next": ["6"]},
        "3": {"next": ["7"]},
        "4": {"next": ["7"]},
        "5": {"next": ["7"]},
        "6": {"next": ["8"]},
        "7": {"next": ["9"]},
        "8": {"next": ["10"]},
        "9": {"next": ["11"]},
        "10": {"next": ["11"]},
        "11": {"next": []}
    }
    
    print_graph_definition(graph_definition)
    
    print("Creating visualization with hierarchical layout...")
    visualize_graph(
        graph_definition, 
        layout='hierarchical',
        title='Basic Precedence Graph',
        node_size=1200,
        edge_width=2.0,
        font_size=12,
        show=True
    )


def example_2_diamond_dependency():
    """Diamond-shaped dependency structure."""
    graph_definition = {
        "A": {"next": ["B", "C"]},
        "B": {"next": ["D"]},
        "C": {"next": ["D"]},
        "D": {"next": ["E"]},
        "E": {"next": []}
    }
    
    print_graph_definition(graph_definition)
    
    print("Creating visualization with hierarchical layout...")
    visualize_graph(
        graph_definition, 
        layout='hierarchical',
        title='Diamond Dependency Graph',
        node_size=1200,
        edge_width=2.0,
        font_size=12,
        show=True
    )


def example_3_multi_path():
    """Multi-path graph with branches and merges."""
    graph_definition = {
        "start": {"next": ["branch1", "branch2", "branch3"]},
        "branch1": {"next": ["merge1"]},
        "branch2": {"next": ["merge1", "merge2"]},
        "branch3": {"next": ["merge2"]},
        "merge1": {"next": ["final"]},
        "merge2": {"next": ["final"]},
        "final": {"next": []}
    }
    
    print_graph_definition(graph_definition)
    
    print("Creating visualization with hierarchical layout...")
    visualize_graph(
        graph_definition, 
        layout='hierarchical',
        title='Multi-Path Graph',
        node_size=1200,
        edge_width=2.0,
        font_size=12,
        show=True
    )


def main():
    """
    Run examples based on command-line arguments.
    If no argument is provided, runs example 1.
    If a number is provided, runs the example with that number.
    """
    # Available examples
    examples = {
        1: example_1_basic_precedence,
        2: example_2_diamond_dependency,
        3: example_3_multi_path
    }
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            if example_num in examples:
                print(f"Running example {example_num}...")
                examples[example_num]()
            else:
                print(f"Error: Example {example_num} does not exist.")
                print(f"Available examples: {list(examples.keys())}")
        except ValueError:
            print(f"Error: Please provide a valid example number.")
            print(f"Available examples: {list(examples.keys())}")
    else:
        # Default to running example 1
        print("Running default example (1)...")
        example_1_basic_precedence()
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
