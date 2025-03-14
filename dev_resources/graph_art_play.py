"""
Test script for the graph_art module in JobChain.

This script demonstrates how to use the graph_art module to visualize different types
of job graphs using ASCII art.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.jobchain.graph_art import improved_visualize_graph


def display_graph(title, graph_definition):
    """Helper function to display a graph with a title"""
    print(f"\n{'='*50}")
    print(f"{title}:")
    print(f"{'='*50}")
    print(improved_visualize_graph(graph_definition))
    print("\n")


def main():
    # Example 1: Original precedence graph
    original_graph = {
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
    display_graph("Original Precedence Graph", original_graph)
    
    # Example 2: Simple linear chain
    linear_chain = {
        "A": {"next": ["B"]},
        "B": {"next": ["C"]},
        "C": {"next": ["D"]},
        "D": {"next": ["E"]},
        "E": {"next": []}
    }
    display_graph("Linear Chain", linear_chain)
    
    # Example 3: Simple tree structure
    tree_structure = {
        "Root": {"next": ["A", "B", "C"]},
        "A": {"next": ["A1", "A2"]},
        "B": {"next": ["B1"]},
        "C": {"next": ["C1", "C2", "C3"]},
        "A1": {"next": []},
        "A2": {"next": []},
        "B1": {"next": []},
        "C1": {"next": []},
        "C2": {"next": []},
        "C3": {"next": []}
    }
    display_graph("Tree Structure", tree_structure)
    
    # Example 4: Diamond pattern (converging and diverging paths)
    diamond_pattern = {
        "Start": {"next": ["Left", "Right"]},
        "Left": {"next": ["End"]},
        "Right": {"next": ["End"]},
        "End": {"next": []}
    }
    display_graph("Diamond Pattern", diamond_pattern)
    
    # Example 5: Wide fan-out (one-to-many)
    fan_out = {
        "Source": {"next": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]},
        "T1": {"next": []},
        "T2": {"next": []},
        "T3": {"next": []},
        "T4": {"next": []},
        "T5": {"next": []},
        "T6": {"next": []},
        "T7": {"next": []},
        "T8": {"next": []}
    }
    display_graph("Fan-Out Pattern (One-to-Many)", fan_out)
    
    # Example 6: Wide fan-in (many-to-one)
    fan_in = {
        "A": {"next": ["Target"]},
        "B": {"next": ["Target"]},
        "C": {"next": ["Target"]},
        "D": {"next": ["Target"]},
        "E": {"next": ["Target"]},
        "F": {"next": ["Target"]},
        "Target": {"next": []}
    }
    display_graph("Fan-In Pattern (Many-to-One)", fan_in)
    
    # Example 7: Complex workflow with multiple stages
    complex_workflow = {
        "Start": {"next": ["Validate", "Initialize", "Setup"]},
        "Validate": {"next": ["Process"]},
        "Initialize": {"next": ["Process"]},
        "Setup": {"next": ["Process"]},
        "Process": {"next": ["Transform1", "Transform2"]},
        "Transform1": {"next": ["Combine"]},
        "Transform2": {"next": ["Combine"]},
        "Combine": {"next": ["Export", "Save"]},
        "Export": {"next": ["End"]},
        "Save": {"next": ["End"]},
        "End": {"next": []}
    }
    display_graph("Complex Workflow", complex_workflow)
    
    # Example 8: Data pipeline
    data_pipeline = {
        "Extract": {"next": ["Validate", "Clean"]},
        "Validate": {"next": ["Transform"]},
        "Clean": {"next": ["Transform"]},
        "Transform": {"next": ["Model1", "Model2", "Model3"]},
        "Model1": {"next": ["Evaluate"]},
        "Model2": {"next": ["Evaluate"]},
        "Model3": {"next": ["Evaluate"]},
        "Evaluate": {"next": ["Deploy", "ReportResults"]},
        "Deploy": {"next": []},
        "ReportResults": {"next": []}
    }
    display_graph("Data Pipeline", data_pipeline)


if __name__ == "__main__":
    main()