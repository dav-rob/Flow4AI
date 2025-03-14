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


def identify_paths(G: nx.DiGraph) -> Dict[str, List[List[str]]]:
    """
    Identify all paths from source nodes to sink nodes in the graph.
    This helps in maintaining straight-line paths in the visualization.
    
    Args:
        G: A NetworkX DiGraph object
        
    Returns:
        Dictionary mapping node IDs to the paths they belong to
    """
    # Find source nodes (nodes with no incoming edges)
    sources = [n for n, d in G.in_degree() if d == 0]
    # Find sink nodes (nodes with no outgoing edges)
    sinks = [n for n, d in G.out_degree() if d == 0]
    
    # Get all paths from each source to each sink
    all_paths = []
    for source in sources:
        for sink in sinks:
            try:
                # Find all simple paths between source and sink
                paths = list(nx.all_simple_paths(G, source, sink))
                all_paths.extend(paths)
            except nx.NetworkXNoPath:
                continue
    
    # If we couldn't find any paths, return an empty dictionary
    if not all_paths:
        return {}
    
    # Map each node to the paths it belongs to
    node_paths = {}
    for i, path in enumerate(all_paths):
        for node in path:
            if node not in node_paths:
                node_paths[node] = []
            node_paths[node].append((i, path))
    
    return node_paths

def custom_hierarchical_layout(G: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
    """
    A custom hierarchical layout that arranges nodes in levels based on topology,
    with special attention to maintaining straight paths and vertical alignment.
    
    Key features:
    - Head nodes are positioned equidistant between their child nodes
    - Tail nodes are positioned at the rightmost side
    - Nodes that belong to the same path are vertically aligned when possible
    
    Args:
        G: A NetworkX DiGraph object
        
    Returns:
        Dictionary mapping node names to (x, y) coordinates
    """
    # Get nodes arranged in topological generations
    generations = get_topological_generations(G)
    
    # Identify source nodes (no incoming edges) and sink nodes (no outgoing edges)
    source_nodes = [n for n, d in G.in_degree() if d == 0]
    sink_nodes = [n for n, d in G.out_degree() if d == 0]
    
    # Calculate positions
    pos = {}
    
    # First pass: assign x positions based on generation
    for i, gen in enumerate(generations):
        for node in gen:
            # Standard x position is determined by generation index (level)
            x = i
            
            # Special case: ensure sink nodes are positioned at the rightmost side
            # by adding a small offset to their x position
            if node in sink_nodes:
                x = len(generations) # Put at the far right
                
            pos[node] = (x, 0)  # Y will be assigned later
    
    # Group nodes by their x position
    x_groups = {}
    for node, (x, _) in pos.items():
        if x not in x_groups:
            x_groups[x] = []
        x_groups[x].append(node)
    
    # Sort nodes within each level by various criteria for better layout
    for level, nodes in x_groups.items():
        def node_sort_key(node):
            # Consider the number of connections for better placement
            pred_count = len(list(G.predecessors(node)))
            succ_count = len(list(G.successors(node)))
            # Sort by connection counts, then by node name for consistency
            return (pred_count, succ_count, str(node))
        
        # Sort the nodes in this level
        x_groups[level] = sorted(nodes, key=node_sort_key)
    
    # Second pass: assign y positions
    # Track vertical slots for each column to prevent overlap
    x_slots = {x: set() for x in x_groups}
    
    # Process source nodes specially to center them between their children
    for node in source_nodes:
        # Find direct children
        children = list(G.successors(node))
        if children:
            # If this source node has children, we position it equidistant from them
            # First, make sure the children have y-positions assigned
            child_level = pos[children[0]][0]  # All children should be at the same level
            
            # Get existing y-positions of the children, if any
            child_ys = [pos[child][1] for child in children if pos[child][1] != 0]
            
            if child_ys:
                # Center the source node between its children
                center_y = sum(child_ys) / len(child_ys)
            else:
                # If children don't have positions yet, use a centered position
                # This will be adjusted later when child positions are calculated
                center_y = 0
                
            # Assign the position
            x, _ = pos[node]
            pos[node] = (x, center_y)
    
    # Process remaining nodes level by level
    for level in sorted(x_groups.keys()):
        # Assign y positions for nodes in this level
        slot_counter = 0
        for node in x_groups[level]:
            # Skip nodes that already have a y position (source nodes)
            if pos[node][1] != 0 and node in source_nodes:
                continue
                
            # Try to align with predecessors or successors if possible
            aligned_y = None
            
            # Check predecessors for alignment first
            preds = list(G.predecessors(node))
            if preds:
                # Try to use the average y position of predecessors
                pred_ys = [pos[p][1] for p in preds if p in pos]
                if pred_ys:
                    aligned_y = sum(pred_ys) / len(pred_ys)
            
            # If no alignment from predecessors, check successors
            if aligned_y is None:
                succs = list(G.successors(node))
                succ_ys = [pos[s][1] for s in succs if s in pos and pos[s][1] != 0]
                if succ_ys:
                    aligned_y = sum(succ_ys) / len(succ_ys)
            
            # If we couldn't align, find a free slot
            if aligned_y is None:
                while slot_counter in x_slots[level]:
                    slot_counter += 1
                aligned_y = slot_counter
                slot_counter += 1
            
            # Make sure this slot isn't too close to an existing one
            while any(abs(aligned_y - existing) < 0.8 for existing in x_slots[level]):
                aligned_y += 0.8
            
            # Mark this slot as used
            x_slots[level].add(aligned_y)
            
            # Assign the position
            x, _ = pos[node]
            pos[node] = (x, aligned_y)
    
    # Third pass: adjust source node positions based on final positions of children
    for node in source_nodes:
        children = list(G.successors(node))
        if children:
            child_ys = [pos[child][1] for child in children]
            if child_ys:
                # Center the source node between its children's final positions
                center_y = sum(child_ys) / len(child_ys)
                x, _ = pos[node]
                pos[node] = (x, center_y)
    
    # Normalize the positions
    x_values = [p[0] for p in pos.values()]
    y_values = [p[1] for p in pos.values()]
    
    # Get min/max for normalization
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    
    # Avoid division by zero
    x_range = x_max - x_min if x_max > x_min else 1
    y_range = y_max - y_min if y_max > y_min else 1
    
    # Normalize to [0,1] range and apply spacing
    normalized_pos = {}
    for node, (x, y) in pos.items():
        norm_x = (x - x_min) / x_range if x_range else 0.5
        norm_y = (y - y_min) / y_range if y_range else 0.5
        normalized_pos[node] = (norm_x * 1.5, norm_y * 1.5)  # Add scaling for clarity
    
    return normalized_pos


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
