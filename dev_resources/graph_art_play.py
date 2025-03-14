"""
Test script for the graph_art module in JobChain.

This script demonstrates how to use the graph_art module to visualize a job graph
using ASCII art.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.jobchain.graph_art import visualize_graph, improved_visualize_graph

def main():
    # Example graph definition from the precedence graph
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

    # Visualize the graph using the basic algorithm
    print("Basic visualization:")
    print(visualize_graph(graph_definition))
    
    print("\n" + "="*50 + "\n")
    
    # Visualize the graph using the improved algorithm
    print("Improved visualization:")
    print(improved_visualize_graph(graph_definition))

if __name__ == "__main__":
    main()
