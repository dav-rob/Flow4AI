"""
Graph visualization module for JobChain.

This module provides functionality to visualize job graphs from adjacency list
representations using NetworkX and Matplotlib. It can generate visual representations
of job dependencies and workflows.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# Define some color schemes for the graphs
COLOR_SCHEMES = {
    "default": {
        "node_color": "#1f78b4",  # Blue
        "edge_color": "#333333",  # Dark Gray
        "font_color": "black",
        "border_color": "#000000",  # Black
    },
    "light": {
        "node_color": "#a6cee3",  # Light Blue
        "edge_color": "#666666",  # Gray
        "font_color": "black",
        "border_color": "#000000",  # Black
    },
    "dark": {
        "node_color": "#1f78b4",  # Blue
        "edge_color": "#cccccc",  # Light Gray
        "font_color": "white",
        "border_color": "#ffffff",  # White
        "background": "#333333",  # Dark Gray
    },
    "colorful": {
        "node_color": "#b2df8a",  # Light Green
        "edge_color": "#33a02c",  # Green
        "font_color": "black",
        "border_color": "#000000",  # Black
    }
}


def adjacency_to_nx_graph(graph_definition: Dict[str, Any]) -> nx.DiGraph:
    """
    Convert a JobChain adjacency list to a NetworkX directed graph.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
                         Format: {node_id: {"next": [list_of_next_node_ids]}}
    
    Returns:
        A NetworkX DiGraph object representing the graph.
    """
    G = nx.DiGraph()
    
    # Add all nodes first
    for node_id in graph_definition:
        G.add_node(node_id)
    
    # Add all edges
    for node_id, edges in graph_definition.items():
        next_nodes = edges.get("next", [])
        for next_node in next_nodes:
            G.add_edge(node_id, next_node)
    
    return G


def get_topological_generations(G: nx.DiGraph) -> List[List[str]]:
    """
    Get nodes arranged in topological generations (levels).
    Each generation contains nodes that have the same "distance" from the source nodes.
    
    Args:
        G: A NetworkX DiGraph object
        
    Returns:
        List of lists where each inner list contains nodes in the same generation
    """
    # Find root nodes (nodes with no incoming edges)
    root_nodes = [n for n, d in G.in_degree() if d == 0]
    
    if not root_nodes:
        # If no root found, just pick a random node
        root_nodes = [list(G.nodes())[0]]
    
    # Initialize generations
    generations = [root_nodes]
    visited = set(root_nodes)
    
    # Continue until all nodes are assigned to a generation
    while len(visited) < len(G.nodes()):
        # Get the last generation
        last_gen = generations[-1]
        
        # Find all successors of nodes in the last generation
        # that haven't been visited yet
        next_gen = []
        for node in last_gen:
            for succ in G.successors(node):
                if succ not in visited:
                    next_gen.append(succ)
                    visited.add(succ)
        
        # If we found new nodes, add them to the generations
        if next_gen:
            generations.append(next_gen)
        else:
            # Find any remaining unvisited nodes and add them to a new generation
            # This handles disconnected components
            remaining = [n for n in G.nodes() if n not in visited]
            if remaining:
                generations.append(remaining)
                visited.update(remaining)
            else:
                break
    
    return generations


def custom_hierarchical_layout(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    """
    A custom hierarchical layout that arranges nodes in levels based on topology.
    This is designed to create a cleaner left-to-right flow similar to Graphviz's dot layout.
    
    Args:
        G: A NetworkX DiGraph object
        
    Returns:
        Dictionary mapping node names to (x, y) coordinates
    """
    # Get nodes arranged in topological generations
    generations = get_topological_generations(G)
    
    # Calculate positions
    pos = {}
    max_nodes_per_level = max(len(gen) for gen in generations)
    
    # Place each node
    for i, gen in enumerate(generations):
        # Sort nodes within a generation to maintain consistency
        gen.sort(key=str)
        
        # Calculate y-coordinates for this generation
        y_positions = np.linspace(0, 1, len(gen) + 2)[1:-1]
        if len(gen) == 1:
            y_positions = [0.5]  # Center a single node
        
        # Assign positions
        for j, node in enumerate(gen):
            x = i / max(1, len(generations) - 1)  # Normalize x to [0, 1]
            y = y_positions[j]  # Evenly spaced along y-axis
            pos[node] = (x, y)
    
    # Apply additional spacing for clarity
    for node in pos:
        x, y = pos[node]
        pos[node] = (x * 1.5, y * 1.5)  # Scale for better spacing
    
    return pos


def visualize_graph(graph_definition: Dict[str, Any], 
                   layout: str = "hierarchical", 
                   color_scheme: str = "default",
                   node_size: int = 1500,
                   title: Optional[str] = None,
                   figsize: Tuple[int, int] = (12, 8),
                   dpi: int = 100,
                   node_shape: str = 'o',
                   show_labels: bool = True,
                   font_size: int = 12,
                   edge_width: float = 1.5,
                   save_path: Optional[str] = None,
                   show: bool = True) -> Union[plt.Figure, str]:
    """
    Visualize a graph defined by an adjacency list using NetworkX and Matplotlib.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
                         Format: {node_id: {"next": [list_of_next_node_ids]}}
        layout: Layout algorithm to use:
                - 'hierarchical' (default): Custom hierarchical layout with left-to-right flow
                - 'dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo': Graphviz layouts
                - 'spring', 'circular', 'random', 'shell', 'spectral': NetworkX layouts
        color_scheme: Color scheme to use ('default', 'light', 'dark', 'colorful')
        node_size: Size of the nodes in the visualization
        title: Optional title for the plot
        figsize: Figure size as a tuple (width, height)
        dpi: DPI for the figure
        node_shape: Shape of the nodes ('o', 's', 'D', 'v', '^', '<', '>', 'p', 'h', '8')
        show_labels: Whether to show labels on nodes
        font_size: Font size for node labels
        edge_width: Width of the edges
        save_path: Optional path to save the figure
        show: Whether to display the figure
        
    Returns:
        If show is True, returns the figure. If save_path is provided, returns the save path.
    """
    # Create a NetworkX graph from the adjacency list
    G = adjacency_to_nx_graph(graph_definition)
    
    # If there are no nodes, return early
    if not G.nodes():
        print("Graph has no nodes to visualize.")
        return plt.figure(figsize=figsize, dpi=dpi)
    
    # Get the color scheme
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Set background color if specified
    if "background" in colors:
        ax.set_facecolor(colors["background"])
        fig.set_facecolor(colors["background"])
    
    # Get the layout positions
    if layout == 'hierarchical':
        # Use our custom hierarchical layout
        pos = custom_hierarchical_layout(G)
    elif layout in ['dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo']:
        # Use graphviz layout if available
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog=layout)
        except (ImportError, Exception) as e:
            print(f"Could not use {layout} layout, using custom hierarchical layout instead: {e}")
            pos = custom_hierarchical_layout(G)
    else:
        # Use NetworkX layout
        if layout == 'spring':
            pos = nx.spring_layout(G, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'random':
            pos = nx.random_layout(G, seed=42)
        elif layout == 'shell':
            pos = nx.shell_layout(G)
        elif layout == 'spectral':
            pos = nx.spectral_layout(G)
        else:
            # Default to our custom hierarchical layout
            pos = custom_hierarchical_layout(G)
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_color=colors["node_color"],
        node_size=node_size,
        node_shape=node_shape,
        edgecolors=colors["border_color"],
        linewidths=2,
        ax=ax,
    )
    
    # Draw edges with more prominent arrows
    nx.draw_networkx_edges(
        G, pos,
        edge_color=colors["edge_color"],
        width=edge_width,
        arrowsize=30,  # Larger arrows for better visibility
        arrowstyle='-|>', 
        connectionstyle='arc3,rad=0.0',  # Straight connection lines
        min_source_margin=10,  # Margin from source node
        min_target_margin=15,  # Margin from target node to better show arrows
        ax=ax,
    )
    
    # Draw labels if requested
    if show_labels:
        nx.draw_networkx_labels(
            G, pos,
            font_size=font_size,
            font_color=colors["font_color"],
            ax=ax,
        )
    
    # Set the title if provided
    if title:
        plt.title(title, color=colors.get("font_color", "black"), fontsize=font_size + 4)
    
    # Remove axes
    plt.axis('off')
    
    # Tight layout for better spacing
    plt.tight_layout()
    
    # Save the figure if requested
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor=fig.get_facecolor())
        print(f"Graph saved to {save_path}")
        
    # Show the figure if requested
    if show:
        plt.show()
    
    # Return the figure or save path
    if save_path:
        return save_path
    return fig


def save_graph_as_temp_image(graph_definition: Dict[str, Any], 
                            format: str = 'png', 
                            **kwargs) -> str:
    """
    Save a graph as a temporary image file and return the path.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
        format: Image format ('png', 'svg', 'pdf', 'jpg')
        **kwargs: Additional arguments to pass to visualize_graph
        
    Returns:
        Path to the temporary image file
    """
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=f'.{format}')
    os.close(fd)  # Close the file descriptor
    
    # Set show to False to prevent displaying the graph
    kwargs['show'] = False
    kwargs['save_path'] = path
    
    # Visualize the graph and save it
    visualize_graph(graph_definition, **kwargs)
    
    return path


def visualize_to_display(graph_definition: Dict[str, Any],
                        width: int = 800,
                        height: int = 600,
                        **kwargs) -> None:
    """
    Visualize a graph and display it using IPython display (for Jupyter notebooks).
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
        width: Width of the displayed image
        height: Height of the displayed image
        **kwargs: Additional arguments to pass to visualize_graph
    """
    try:
        from IPython.display import display, Image
        
        # Save the graph as a temporary image
        path = save_graph_as_temp_image(graph_definition, **kwargs)
        
        # Display the image
        display(Image(filename=path, width=width, height=height))
        
        # Clean up the temporary file
        try:
            os.unlink(path)
        except:
            pass
            
    except ImportError:
        print("IPython not available. Use visualize_graph() instead.")
        visualize_graph(graph_definition, **kwargs)


def compare_layouts(graph_definition: Dict[str, Any],
                   layouts: List[str] = None,
                   color_scheme: str = "default",
                   node_size: int = 1000,
                   figsize: Tuple[int, int] = (15, 10),
                   save_path: Optional[str] = None) -> plt.Figure:
    """
    Compare different layouts for the same graph.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
        layouts: List of layout algorithms to compare
        color_scheme: Color scheme to use
        node_size: Size of the nodes
        figsize: Figure size
        save_path: Optional path to save the figure
        
    Returns:
        Matplotlib figure with subplots for each layout
    """
    if layouts is None:
        layouts = ['hierarchical', 'dot', 'spring', 'circular', 'spectral']
    
    # Create figure
    num_layouts = len(layouts)
    rows = (num_layouts + 2) // 3  # 3 per row, rounded up
    cols = min(3, num_layouts)
    
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    if rows * cols == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(-1, 1) if cols == 1 else axes.reshape(1, -1)
        
    # Flatten axes for easier indexing
    axes_flat = axes.flatten()
    
    # Get the color scheme
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    
    # Create the graph
    G = adjacency_to_nx_graph(graph_definition)
    
    # Draw each layout
    for i, layout in enumerate(layouts):
        if i < len(axes_flat):
            ax = axes_flat[i]
            
            # Get layout positions
            try:
                if layout == 'hierarchical':
                    pos = custom_hierarchical_layout(G)
                elif layout in ['dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo']:
                    pos = nx.nx_agraph.graphviz_layout(G, prog=layout)
                else:
                    if layout == 'spring':
                        pos = nx.spring_layout(G, seed=42)
                    elif layout == 'circular':
                        pos = nx.circular_layout(G)
                    elif layout == 'random':
                        pos = nx.random_layout(G, seed=42)
                    elif layout == 'shell':
                        pos = nx.shell_layout(G)
                    elif layout == 'spectral':
                        pos = nx.spectral_layout(G)
                    else:
                        pos = custom_hierarchical_layout(G)
            except Exception as e:
                print(f"Layout '{layout}' failed: {e}. Using custom hierarchical layout.")
                pos = custom_hierarchical_layout(G)
                
            # Draw graph with more prominent arrows
            nx.draw_networkx(
                G, pos,
                node_color=colors["node_color"],
                node_size=node_size,
                edge_color=colors["edge_color"],
                font_color=colors["font_color"],
                ax=ax,
                arrows=True,
                arrowstyle='-|>',
                arrowsize=20,  # Larger arrowsize for better visibility
                font_size=10,
                font_weight='bold',
                connectionstyle='arc3,rad=0.0',  # Straight connection lines
                min_source_margin=15,  # Margin from source node
                min_target_margin=15,  # Margin from target node
            )
            
            # Set title
            ax.set_title(layout.capitalize(), fontsize=12, fontweight='bold')
            
            # Turn off axis
            ax.axis('off')
    
    # Hide any unused subplots
    for i in range(len(layouts), len(axes_flat)):
        axes_flat[i].axis('off')
        
    # Adjust layout
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        print(f"Comparison saved to {save_path}")
    
    # Show the plot
    plt.show()
    
    return fig


# Example usage function
def example_usage():
    """Example of how to use the graph_pic module."""
    # Example graph definition
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
    
    # Basic visualization using our custom hierarchical layout
    visualize_graph(graph_definition, 
                   layout="hierarchical",
                   title="Precedence Graph", 
                   node_size=1200,
                   edge_width=2.0)
    
    # Compare different layouts
    compare_layouts(graph_definition, 
                   layouts=['hierarchical', 'spring', 'circular', 'spectral'])
    
    # For Jupyter Notebooks
    # visualize_to_display(graph_definition, layout='hierarchical', color_scheme='default')
    
    return "Example completed"


if __name__ == "__main__":
    example_usage()
