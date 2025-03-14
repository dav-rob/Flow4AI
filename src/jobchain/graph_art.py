"""
Graph Visualization Module for JobChain

This module provides functionality to visualize job graphs using ASCII art.
It takes graph definitions in the form of adjacency lists and renders them
as ASCII art, similar to tree structures.
"""

from typing import Dict, List, Any, Tuple, Set
import math


def visualize_graph(graph_definition: Dict[str, Any], prefix: str = "T") -> str:
    """
    Visualize a graph defined by an adjacency list as ASCII art.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
                          Format: {node_id: {"next": [list_of_next_node_ids]}}
        prefix: Optional prefix to add before each node ID (default: "T")
        
    Returns:
        String containing the ASCII art representation of the graph
    """
    if not graph_definition:
        return "Empty graph"
    
    # Find root nodes (nodes with no incoming edges)
    all_nodes = set(graph_definition.keys())
    child_nodes = set()
    for node, edges in graph_definition.items():
        child_nodes.update(edges.get("next", []))
    
    root_nodes = all_nodes - child_nodes
    
    if not root_nodes:
        # If no root found, just pick the first node
        root_nodes = [list(graph_definition.keys())[0]]
    
    # Compute node depths and positions
    positions = _calculate_node_positions(graph_definition, list(root_nodes)[0])
    
    # Generate the ASCII art
    return _generate_ascii_art(graph_definition, positions, prefix)


def _calculate_node_positions(graph_definition: Dict[str, Any], 
                              root: str) -> Dict[str, Tuple[int, int]]:
    """
    Calculate the relative positions of nodes for display.
    
    Args:
        graph_definition: The graph definition
        root: The root node to start from
        
    Returns:
        Dictionary mapping node IDs to their (x, y) positions
    """
    positions = {}
    visited = set()
    
    # First pass: Calculate depths (y-coordinates)
    depths = {}
    _calculate_depths(graph_definition, root, 0, depths, set())
    
    # Group nodes by depth
    nodes_by_depth = {}
    for node, depth in depths.items():
        if depth not in nodes_by_depth:
            nodes_by_depth[depth] = []
        nodes_by_depth[depth].append(node)
    
    # Second pass: Assign x-coordinates by depth
    max_depth = max(depths.values()) if depths else 0
    width = 4  # Minimum horizontal spacing between nodes
    
    for depth in range(max_depth + 1):
        if depth not in nodes_by_depth:
            continue
            
        nodes = nodes_by_depth[depth]
        total_width = (len(nodes) - 1) * width
        
        # Assign x-coordinates
        for i, node in enumerate(nodes):
            x_pos = i * width
            positions[node] = (x_pos, depths[node])
    
    return positions


def _calculate_depths(graph_definition: Dict[str, Any], 
                     node: str, 
                     depth: int, 
                     depths: Dict[str, int],
                     visited: Set[str]):
    """
    Recursively calculate the depths (y-coordinates) of nodes.
    
    Args:
        graph_definition: The graph definition
        node: Current node
        depth: Current depth
        depths: Dictionary to store node depths
        visited: Set of visited nodes to avoid cycles
    """
    if node in visited:
        return
    
    visited.add(node)
    
    # Update depth if this path gives a greater depth
    if node not in depths or depth > depths[node]:
        depths[node] = depth
    
    # Process children
    for child in graph_definition.get(node, {}).get("next", []):
        _calculate_depths(graph_definition, child, depth + 1, depths, visited.copy())


def _generate_ascii_art(graph_definition: Dict[str, Any], 
                        positions: Dict[str, Tuple[int, int]], 
                        prefix: str) -> str:
    """
    Generate the ASCII art representation based on node positions.
    
    Args:
        graph_definition: The graph definition
        positions: Dictionary mapping node IDs to their positions
        prefix: Prefix to add before each node ID
        
    Returns:
        ASCII art representation as a string
    """
    if not positions:
        return "Empty graph"
    
    # Find dimensions of the canvas
    max_x = max(x for x, _ in positions.values())
    max_y = max(y for _, y in positions.values())
    
    # Create a character grid
    width = (max_x + 1) * 8  # Allow space for connections
    height = (max_y + 1) * 2  # Allow space for connections
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Place nodes on the grid
    node_positions = {}  # Store the center position of each node
    for node, (x, y) in positions.items():
        # Convert logical position to grid position
        grid_x = x * 8
        grid_y = y * 2
        
        # Store the actual grid position for edge drawing
        node_positions[node] = (grid_x, grid_y)
        
        # Place the node label
        node_label = f"{prefix}{node}"
        for i, char in enumerate(node_label):
            if grid_x + i < width:
                grid[grid_y][grid_x + i] = char
    
    # Draw edges
    for source, edges in graph_definition.items():
        if source not in node_positions:
            continue
            
        source_x, source_y = node_positions[source]
        
        for target in edges.get("next", []):
            if target not in node_positions:
                continue
                
            target_x, target_y = node_positions[target]
            
            # Draw vertical connection if needed
            if source_y < target_y - 1:
                for y in range(source_y + 1, target_y):
                    grid[y][source_x] = '|'
            
            # Draw horizontal connection if needed
            if source_x != target_x:
                y = target_y - 1 if source_y < target_y else source_y
                start_x, end_x = min(source_x, target_x), max(source_x, target_x)
                
                for x in range(start_x, end_x + 1):
                    grid[y][x] = '-'
                
                # Draw the corner if needed
                if source_y != target_y:
                    if source_x < target_x:
                        grid[y][source_x] = '|'
                    else:
                        grid[y][target_x] = '|'
    
    # Convert grid to string
    result = []
    for row in grid:
        result.append(''.join(row).rstrip())
    
    # Remove trailing empty lines
    while result and not result[-1].strip():
        result.pop()
    
    return '\n'.join(result)


def visualize_job_graph(graph_definition: Dict[str, Any]) -> str:
    """
    A specialized version of visualize_graph for job chains,
    uses 'J' prefix by default.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
        
    Returns:
        String containing the ASCII art representation of the graph
    """
    return visualize_graph(graph_definition, prefix="J")


def improved_visualize_graph(graph_definition: Dict[str, Any], prefix: str = "T") -> str:
    """
    An improved version of the graph visualization with better layout
    for complex graphs.
    
    Args:
        graph_definition: Dictionary representing the graph as an adjacency list.
                         Format: {node_id: {"next": [list_of_next_node_ids]}}
        prefix: Optional prefix to add before each node ID (default: "T")
        
    Returns:
        String containing the ASCII art representation of the graph
    """
    # Find root nodes
    all_nodes = set(graph_definition.keys())
    child_nodes = set()
    for node, edges in graph_definition.items():
        child_nodes.update(edges.get("next", []))
    
    root_nodes = all_nodes - child_nodes
    
    if not root_nodes:
        # If no root found, just pick the first node
        root_nodes = [list(graph_definition.keys())[0]]
    
    # Define drawing constants
    root = list(root_nodes)[0]
    layers = _assign_layers(graph_definition, root)
    max_layer = max(layers.values()) if layers else 0
    
    # Build the node positions
    positions = _assign_horizontal_positions(graph_definition, layers, root)
    
    # Create grid
    width = max(pos[0] for pos in positions.values()) + 20
    height = max_layer * 4 + 5
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Place nodes on the grid
    for node, (x, y) in positions.items():
        node_text = f"{prefix}{node}"
        for i, char in enumerate(node_text):
            if 0 <= x + i < width and 0 <= y < height:
                grid[y][x + i] = char
    
    # Draw edges
    for source, data in graph_definition.items():
        if source not in positions:
            continue
            
        source_x, source_y = positions[source]
        
        for target in data.get("next", []):
            if target not in positions:
                continue
                
            target_x, target_y = positions[target]
            
            # Draw from source to target
            _draw_edge(grid, source_x, source_y, target_x, target_y)
    
    # Convert grid to string
    result = []
    for row in grid:
        result.append(''.join(row).rstrip())
    
    # Remove trailing empty lines
    while result and not result[-1].strip():
        result.pop()
    
    return '\n'.join(result)


def _assign_layers(graph_definition: Dict[str, Any], 
                   root: str) -> Dict[str, int]:
    """
    Assign layers (vertical positions) to nodes using a topological approach.
    
    Args:
        graph_definition: The graph definition
        root: Root node
        
    Returns:
        Dictionary mapping nodes to their layer numbers
    """
    layers = {}
    visited = set()
    
    def dfs(node, layer):
        if node in visited:
            return
        visited.add(node)
        
        # Update layer if this path gives a higher layer number
        if node not in layers or layer > layers[node]:
            layers[node] = layer
        
        # Process children
        for child in graph_definition.get(node, {}).get("next", []):
            dfs(child, layer + 1)
    
    dfs(root, 0)
    return layers


def _assign_horizontal_positions(graph_definition: Dict[str, Any], 
                                layers: Dict[str, int],
                                root: str) -> Dict[str, Tuple[int, int]]:
    """
    Assign horizontal positions to nodes based on their layer and siblings.
    
    Args:
        graph_definition: The graph definition
        layers: Dictionary mapping nodes to their layers
        root: Root node
        
    Returns:
        Dictionary mapping nodes to their (x, y) positions
    """
    # Group nodes by layer
    nodes_by_layer = {}
    for node, layer in layers.items():
        if layer not in nodes_by_layer:
            nodes_by_layer[layer] = []
        nodes_by_layer[layer].append(node)
    
    # Sort nodes in each layer by their connectivity
    for layer in nodes_by_layer:
        nodes_by_layer[layer].sort(key=lambda n: len(graph_definition.get(n, {}).get("next", [])))
    
    # Assign x positions
    positions = {}
    spacing = 10  # Horizontal spacing between nodes
    
    for layer in sorted(nodes_by_layer.keys()):
        nodes = nodes_by_layer[layer]
        y_pos = layer * 4  # Vertical spacing
        
        # For the first layer, center the root
        if layer == 0:
            positions[root] = (40, y_pos)  # Start the root at position 40
            continue
        
        # Get parent positions for better child placement
        parent_positions = {}
        for node in nodes:
            # Find parents of this node
            for potential_parent, data in graph_definition.items():
                if node in data.get("next", []) and potential_parent in positions:
                    parent_positions[node] = parent_positions.get(node, []) + [positions[potential_parent][0]]
        
        # Assign positions based on parent positions
        x_offset = 0
        for i, node in enumerate(nodes):
            if node in parent_positions:
                # Place close to parent's average position
                avg_parent_x = sum(parent_positions[node]) / len(parent_positions[node])
                x_pos = max(x_offset, int(avg_parent_x) - 3 + i * 2)
            else:
                # Place sequentially if no parent info
                x_pos = x_offset
                
            positions[node] = (x_pos, y_pos)
            x_offset = x_pos + spacing
    
    return positions


def _draw_edge(grid: List[List[str]], 
              source_x: int, source_y: int, 
              target_x: int, target_y: int):
    """
    Draw an edge from source to target in the grid.
    
    Args:
        grid: The character grid
        source_x, source_y: Source coordinates
        target_x, target_y: Target coordinates
    """
    height = len(grid)
    width = len(grid[0]) if grid else 0
    
    # Draw vertical path from source down
    mid_y = (source_y + target_y) // 2
    
    # Draw down from source to mid_y
    for y in range(source_y + 1, mid_y + 1):
        if 0 <= y < height and 0 <= source_x < width:
            if grid[y][source_x] == ' ':
                grid[y][source_x] = '|'
    
    # Draw horizontal path from source_x to target_x at mid_y
    start_x, end_x = (source_x, target_x) if source_x <= target_x else (target_x, source_x)
    for x in range(start_x, end_x + 1):
        if 0 <= mid_y < height and 0 <= x < width:
            if grid[mid_y][x] == ' ' or grid[mid_y][x] == '|':
                grid[mid_y][x] = '-'
    
    # Draw vertical path from mid_y to target
    for y in range(mid_y, target_y):
        if 0 <= y < height and 0 <= target_x < width:
            if grid[y][target_x] == ' ' or grid[y][target_x] == '-':
                grid[y][target_x] = '|'
    
    # Mark crossings
    if 0 <= mid_y < height and 0 <= source_x < width:
        if grid[mid_y][source_x] == '-':
            grid[mid_y][source_x] = '+'
    if 0 <= mid_y < height and 0 <= target_x < width:
        if grid[mid_y][target_x] == '-':
            grid[mid_y][target_x] = '+'
