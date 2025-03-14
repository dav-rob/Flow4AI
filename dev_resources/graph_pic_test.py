"""
Test script for the graph_pic module in JobChain.

This script demonstrates how to use the graph_pic module to visualize
job graphs using NetworkX and Matplotlib.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.jobchain.graph_pic import visualize_graph, compare_layouts


def main():
    # Example graph definition from the image
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
    
    # Print the graph definition in a nicely formatted way
    print("\nGraph Definition:")
    print("================")
    import json
    for node, edges in graph_definition.items():
        print(f"    \"{node}\": {json.dumps(edges)},")
    print()
    
    # Visualize with our new custom hierarchical layout
    print("Creating visualization with hierarchical layout...")
    visualize_graph(graph_definition, 
                   layout='hierarchical',  # Using our custom hierarchical layout
                   title="Precedence Graph",
                   node_size=1200,
                   edge_width=2.0,
                   font_size=12,
                   show=True)
    
    # This is optional - only uncomment if you want to see multiple layouts compared
    # print("\nComparing different layouts...")
    # compare_layouts(graph_definition, 
    #               layouts=['hierarchical', 'dot', 'spring', 'circular'],
    #               save_path='graph_layouts_comparison.png')
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
