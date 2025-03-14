"""
Graph ASCII Art Generator

This module provides functionality to convert graph definitions into ASCII art
representations for visualization purposes.
"""

from typing import Dict, List, Any, Tuple, Set
import math
import jobchain.jc_logging as logging

logger = logging.getLogger(__name__)

class GraphArtGenerator:
    """
    A class to generate ASCII art representations of directed graphs.
    """
    
    def __init__(self, graph_definition: Dict[str, Any], node_prefix: str = "T"):
        """
        Initialize the GraphArtGenerator with a graph definition.
        
        Args:
            graph_definition: Dictionary representation of the graph where keys are node IDs
                             and values are dictionaries with a 'next' key containing a list
                             of successor node IDs.
            node_prefix: Optional prefix to add before node IDs in the visualization (default: "T")
        """
        self.graph = graph_definition
        self.node_prefix = node_prefix
        self.node_positions = {}
        self.max_width = 0
        self.max_height = 0
        self.canvas = []
        
    def _calculate_node_levels(self) -> Dict[str, int]:
        """
        Calculate the level (depth) of each node in the graph.
        
        Returns:
            Dictionary mapping node IDs to their levels.
        """
        levels = {}
        visited = set()
        
        def dfs(node: str, current_level: int):
            if node in visited:
                return
            
            visited.add(node)
            levels[node] = max(levels.get(node, 0), current_level)
            
            for next_node in self.graph.get(node, {}).get("next", []):
                dfs(next_node, current_level + 1)
        
        # Find root nodes (nodes with no incoming edges)
        all_nodes = set(self.graph.keys())
        child_nodes = set()
        for node in self.graph:
            for child in self.graph[node].get("next", []):
                child_nodes.add(child)
        
        root_nodes = all_nodes - child_nodes
        if not root_nodes:
            # If no root nodes found, use the first node as root
            root_nodes = {next(iter(self.graph.keys()))}
        
        # Run DFS from each root node
        for root in root_nodes:
            dfs(root, 0)
            
        return levels
    
    def _calculate_node_positions(self) -> Dict[str, Tuple[int, int]]:
        """
        Calculate the (x, y) position of each node in the ASCII grid.
        
        Returns:
            Dictionary mapping node IDs to their (x, y) positions.
        """
        levels = self._calculate_node_levels()
        
        # Group nodes by level
        nodes_by_level = {}
        for node, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)
        
        # Sort levels
        sorted_levels = sorted(nodes_by_level.keys())
        
        # Calculate positions
        positions = {}
        max_nodes_per_level = max(len(nodes) for nodes in nodes_by_level.values())
        spacing = max(4, max_nodes_per_level * 2)
        
        for level in sorted_levels:
            nodes = nodes_by_level[level]
            
            # Sort nodes within level based on their connections
            if level > 0:
                # Try to position nodes near their parents
                def get_parent_position(node):
                    parent_positions = []
                    for potential_parent in self.graph:
                        if node in self.graph[potential_parent].get("next", []):
                            if potential_parent in positions:
                                parent_positions.append(positions[potential_parent][0])
                    return sum(parent_positions) / len(parent_positions) if parent_positions else 0
                
                nodes.sort(key=get_parent_position)
            
            # Position nodes within level
            level_width = len(nodes) * spacing
            start_x = max(0, (max_nodes_per_level * spacing - level_width) // 2)
            
            for i, node in enumerate(nodes):
                x = start_x + i * spacing
                y = level * 3  # Vertical spacing between levels
                positions[node] = (x, y)
        
        return positions
    
    def _create_canvas(self) -> List[List[str]]:
        """
        Create an empty canvas (2D grid) for drawing the graph.
        
        Returns:
            2D list representing the canvas.
        """
        self.node_positions = self._calculate_node_positions()
        
        # Calculate canvas dimensions
        max_x = max(x for x, _ in self.node_positions.values()) + 10  # Add padding
        max_y = max(y for _, y in self.node_positions.values()) + 5   # Add padding
        
        self.max_width = max_x
        self.max_height = max_y
        
        # Create empty canvas
        return [[' ' for _ in range(max_x)] for _ in range(max_y)]
    
    def _draw_node(self, canvas: List[List[str]], node: str, x: int, y: int) -> None:
        """
        Draw a node on the canvas at the specified position.
        
        Args:
            canvas: The canvas to draw on
            node: The node ID
            x: X-coordinate
            y: Y-coordinate
        """
        node_label = f"{self.node_prefix}{node}"
        for i, char in enumerate(node_label):
            if 0 <= x + i < self.max_width:
                canvas[y][x + i] = char
    
    def _draw_edge(self, canvas: List[List[str]], from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> None:
        """
        Draw an edge between two nodes on the canvas.
        
        Args:
            canvas: The canvas to draw on
            from_pos: (x, y) position of the source node
            to_pos: (x, y) position of the target node
        """
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        # Adjust starting position to be below the node
        from_y += 1
        
        # Calculate intermediate points for drawing the edge
        if from_x == to_x:
            # Vertical edge
            for y in range(from_y, to_y):
                if 0 <= y < self.max_height and 0 <= from_x < self.max_width:
                    canvas[y][from_x] = '|'
        else:
            # Diagonal or complex edge
            # First go down
            mid_y = from_y + (to_y - from_y) // 2
            
            # Draw vertical line from source
            for y in range(from_y, mid_y):
                if 0 <= y < self.max_height and 0 <= from_x < self.max_width:
                    canvas[y][from_x] = '|'
            
            # Draw horizontal line
            if from_x < to_x:
                for x in range(from_x, to_x + 1):
                    if 0 <= mid_y < self.max_height and 0 <= x < self.max_width:
                        canvas[mid_y][x] = '-'
            else:
                for x in range(to_x, from_x + 1):
                    if 0 <= mid_y < self.max_height and 0 <= x < self.max_width:
                        canvas[mid_y][x] = '-'
            
            # Draw vertical line to target
            for y in range(mid_y + 1, to_y):
                if 0 <= y < self.max_height and 0 <= to_x < self.max_width:
                    canvas[y][to_x] = '|'
            
            # Add diagonal connectors
            if 0 <= mid_y < self.max_height:
                if from_x < to_x and 0 <= from_x < self.max_width:
                    canvas[mid_y][from_x] = '\\'
                elif from_x > to_x and 0 <= to_x < self.max_width:
                    canvas[mid_y][to_x] = '/'
            
            # Add arrow
            if 0 <= to_y - 1 < self.max_height and 0 <= to_x < self.max_width:
                canvas[to_y - 1][to_x] = 'v'
    
    def generate_ascii_art(self) -> str:
        """
        Generate an ASCII art representation of the graph.
        
        Returns:
            String containing the ASCII art representation.
        """
        # Create empty canvas
        canvas = self._create_canvas()
        
        # Draw edges
        for node, data in self.graph.items():
            if node in self.node_positions:
                from_pos = self.node_positions[node]
                for next_node in data.get("next", []):
                    if next_node in self.node_positions:
                        to_pos = self.node_positions[next_node]
                        self._draw_edge(canvas, from_pos, to_pos)
        
        # Draw nodes (after edges so they're not overwritten)
        for node, pos in self.node_positions.items():
            self._draw_node(canvas, node, pos[0], pos[1])
        
        # Convert canvas to string
        result = []
        for row in canvas:
            # Remove trailing spaces
            while row and row[-1] == ' ':
                row.pop()
            result.append(''.join(row))
        
        # Remove trailing empty lines
        while result and not result[-1].strip():
            result.pop()
        
        return '\n'.join(result)


def generate_graph_art(graph_definition: Dict[str, Any], node_prefix: str = "T") -> str:
    """
    Generate ASCII art representation of a graph.
    
    Args:
        graph_definition: Dictionary representation of the graph where keys are node IDs
                         and values are dictionaries with a 'next' key containing a list
                         of successor node IDs.
        node_prefix: Optional prefix to add before node IDs in the visualization (default: "T")
    
    Returns:
        String containing the ASCII art representation of the graph.
    
    Example:
        >>> graph_def = {
        ...     "1": {"next": ["2", "3"]},
        ...     "2": {"next": ["4"]},
        ...     "3": {"next": ["4"]},
        ...     "4": {"next": []}
        ... }
        >>> print(generate_graph_art(graph_def))
        T1
        |  \
        v   v
        T2  T3
        |   |
        v   v
         T4
    """
    generator = GraphArtGenerator(graph_definition, node_prefix)
    return generator.generate_ascii_art()


if __name__ == "__main__":
    # Example usage
    example_graph = {
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
    
    ascii_art = generate_graph_art(example_graph)
    print(ascii_art)
