"""
Graph Art Play - Examples of converting graph definitions to ASCII art
"""

from typing import Dict, Any
import sys
import os

# Add the project root to the Python path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jobchain.graph_art import generate_graph_art

def print_graph_and_art(name: str, graph_definition: Dict[str, Any]) -> None:
    """
    Print a graph definition and its ASCII art representation.
    
    Args:
        name: Name of the graph example
        graph_definition: The graph definition dictionary
    """
    print(f"\n{'=' * 50}")
    print(f"Example: {name}")
    print(f"{'=' * 50}")
    
    # Print the graph definition
    print("Graph Definition:")
    print("graph_definition: dict[str, Any] = {")
    for node, data in graph_definition.items():
        next_nodes = data.get("next", [])
        print(f"    \"{node}\": {{\"next\": {next_nodes}}},")
    print("}")
    
    # Print the ASCII art representation
    print("\nASCII Art Representation:")
    print(generate_graph_art(graph_definition))
    print(f"{'=' * 50}\n")


# Example 1: Simple Linear Chain
linear_chain = {
    "1": {"next": ["2"]},
    "2": {"next": ["3"]},
    "3": {"next": ["4"]},
    "4": {"next": []}
}

# Example 2: Simple Fork and Join
fork_join = {
    "1": {"next": ["2", "3"]},
    "2": {"next": ["4"]},
    "3": {"next": ["4"]},
    "4": {"next": []}
}

# Example 3: Diamond Pattern
diamond = {
    "1": {"next": ["2", "3"]},
    "2": {"next": ["4"]},
    "3": {"next": ["4"]},
    "4": {"next": ["5"]},
    "5": {"next": []}
}

# Example 4: Binary Tree
binary_tree = {
    "1": {"next": ["2", "3"]},
    "2": {"next": ["4", "5"]},
    "3": {"next": ["6", "7"]},
    "4": {"next": []},
    "5": {"next": []},
    "6": {"next": []},
    "7": {"next": []}
}

# Example 5: Complex Graph with Multiple Paths
complex_graph = {
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

# Example 6: Cyclic Graph (with a cycle)
# Note: The ASCII art generator will still work but may not represent cycles perfectly
cyclic_graph = {
    "1": {"next": ["2", "3"]},
    "2": {"next": ["4"]},
    "3": {"next": ["5"]},
    "4": {"next": ["6"]},
    "5": {"next": ["6"]},
    "6": {"next": ["7", "2"]},  # Cycle back to node 2
    "7": {"next": []}
}

# Example 7: Complex Web with Multiple Paths and Dependencies
web_graph = {
    "1": {"next": ["2", "3", "4"]},
    "2": {"next": ["5", "6"]},
    "3": {"next": ["5", "7"]},
    "4": {"next": ["7", "8"]},
    "5": {"next": ["9"]},
    "6": {"next": ["9", "10"]},
    "7": {"next": ["10", "11"]},
    "8": {"next": ["11"]},
    "9": {"next": ["12"]},
    "10": {"next": ["12"]},
    "11": {"next": ["12"]},
    "12": {"next": []}
}

if __name__ == "__main__":
    # Print all examples
    print_graph_and_art("Simple Linear Chain", linear_chain)
    print_graph_and_art("Simple Fork and Join", fork_join)
    print_graph_and_art("Diamond Pattern", diamond)
    print_graph_and_art("Binary Tree", binary_tree)
    print_graph_and_art("Complex Graph with Multiple Paths", complex_graph)
    print_graph_and_art("Cyclic Graph", cyclic_graph)
    print_graph_and_art("Complex Web", web_graph)
