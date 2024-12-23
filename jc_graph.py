"""
JobChain Graph module for handling directed acyclic graphs with subgraphs.
Provides functionality for graph traversal, cycle detection, and validation.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

import jc_logging as logging


def has_cycle(graph: Dict[str, Dict[str, Any]], node: str, 
             visited: Optional[Set[str]] = None, path: Optional[Set[str]] = None) -> Tuple[bool, List[str]]:
    """
    Check if the graph has a cycle starting from the given node.
    
    Args:
        graph: The graph structure to check
        node: Starting node for cycle detection
        visited: Set of all visited nodes (for recursive calls)
        path: Set of nodes in current path (for cycle detection)
    
    Returns:
        Tuple[bool, List[str]]: (has_cycle, cycle_path)
    """
    if visited is None:
        visited = set()
    if path is None:
        path = set()
    
    visited.add(node)
    path.add(node)
    
    node_obj = graph[node]
    # Check next nodes
    for next_node in node_obj.get('next', []):
        if next_node in path:  # Cycle detected
            return True, [*path, next_node]
        if next_node not in visited:
            has_cycle_result, cycle_path = has_cycle(graph, next_node, visited, path)
            if has_cycle_result:
                return True, cycle_path
    
    # Check subgraph if it exists
    if 'subgraph' in node_obj:
        subgraph = node_obj['subgraph']
        for subnode in subgraph:
            if subnode not in visited:
                has_cycle_result, cycle_path = has_cycle(subgraph, subnode, visited, path)
                if has_cycle_result:
                    return True, cycle_path
    
    path.remove(node)
    return False, []

def check_graph_for_cycles(graph: Dict[str, Dict[str, Any]], name: str = "") -> bool:
    """
    Check entire graph for cycles.
    
    Args:
        graph: The graph structure to check
        name: Optional name for the graph (for logging)
    
    Returns:
        bool: True if cycles were found, False otherwise
    """
    print(f"\nChecking {name} for cycles...")
    for node in graph:
        has_cycle_result, cycle_path = has_cycle(graph, node)
        if has_cycle_result:
            print(f"Cycle detected! Path: {' -> '.join(cycle_path)}")
            return True
    print("No cycles detected")
    return False

def find_node_and_graph(main_graph: Dict[str, Dict[str, Any]], target_node: str, 
                       current_graph: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[Optional[Dict[str, Dict[str, Any]]], List[str]]:
    """
    Recursively finds a node and its containing graph in the graph structure.
    
    Args:
        main_graph: The root graph structure
        target_node: The node to find
        current_graph: Current graph being searched (for recursive calls)
    
    Returns:
        Tuple[Optional[Dict], List[str]]: (containing_graph, path_to_node)
    """
    if current_graph is None:
        current_graph = main_graph
        
    # Check if node is in current level
    if target_node in current_graph:
        return current_graph, []
        
    # Search in subgraphs
    for node in current_graph:
        if 'subgraph' in current_graph[node]:
            subgraph = current_graph[node]['subgraph']
            result_graph, path = find_node_and_graph(main_graph, target_node, subgraph)
            if result_graph is not None:
                return result_graph, [node] + path
                
    return None, []

def add_edge(graph: Dict[str, Dict[str, Any]], from_node: str, to_node: str) -> bool:
    """
    Attempts to add an edge between two nodes in the same graph level.
    
    Args:
        graph: The graph containing both nodes
        from_node: Source node
        to_node: Target node
    
    Returns:
        bool: True if edge was added successfully
    """
    if from_node not in graph:
        print(f"Error: Source node {from_node} not found in graph")
        return False
    
    # Initialize 'next' list if it doesn't exist
    if 'next' not in graph[from_node]:
        graph[from_node]['next'] = []
    
    # Check if edge already exists
    if to_node in graph[from_node]['next']:
        print(f"Edge {from_node} -> {to_node} already exists")
        return True
    
    # Temporarily add the edge
    graph[from_node]['next'].append(to_node)
    
    # Check for cycles
    has_cycle_result, cycle_path = has_cycle(graph, from_node)
    
    if has_cycle_result:
        # Remove the edge if it would create a cycle
        graph[from_node]['next'].remove(to_node)
        print(f"Cannot add edge {from_node} -> {to_node} as it would create a cycle")
        print(f"Cycle detected: {' -> '.join(cycle_path)}")
        return False
    
    print(f"Successfully added edge {from_node} -> {to_node}")
    return True

def add_edge_anywhere(main_graph: Dict[str, Dict[str, Any]], from_node: str, to_node: str) -> bool:
    """
    Attempts to add an edge between two nodes in the graph structure.
    
    Rules for edge addition:
    1. Both nodes must exist in the graph structure
    2. Nodes can only reference other nodes within the same graph level:
       - Main graph nodes can only reference other main graph nodes
       - Subgraph nodes can only reference nodes within the same subgraph
    3. No cycles are allowed within any graph level
    
    Args:
        main_graph: The root graph structure
        from_node: Source node
        to_node: Target node
    
    Returns:
        bool: True if edge was added successfully
    """
    # Find the containing graphs for both nodes
    from_graph, from_path = find_node_and_graph(main_graph, from_node)
    to_graph, to_path = find_node_and_graph(main_graph, to_node)
    
    if from_graph is None:
        print(f"Error: Source node {from_node} not found in graph")
        return False
        
    if to_graph is None:
        print(f"Error: Target node {to_node} not found in graph")
        return False
    
    # Check if nodes are in the same graph level
    if from_graph is not to_graph:
        print(f"Error: Cannot create edge between different graph levels")
        print(f"Source node {from_node} is in {' -> '.join(['main'] + from_path) if from_path else 'main graph'}")
        print(f"Target node {to_node} is in {' -> '.join(['main'] + to_path) if to_path else 'main graph'}")
        return False
    
    return add_edge(from_graph, from_node, to_node)

def print_graph(graph: Dict[str, Dict[str, Any]], spaces: int = 0) -> None:
    """
    Traverse and print the graph structure.
    
    Args:
        graph: The graph structure to traverse
        spaces: Number of spaces for indentation
    """
    for key in graph.keys():
        print("." * spaces + key)
        print_visit_node(graph, key, spaces)

def print_visit_node(graph: Dict[str, Dict[str, Any]], key: str, spaces: int = 0) -> None:
    """
    Visit and print a node's details.
    
    Args:
        graph: The graph containing the node
        key: The node key to visit
        spaces: Number of spaces for indentation
    """
    node_key_obj = graph[key]
    sub_graph_obj = node_key_obj.get('subgraph')
    if sub_graph_obj:
        print("-" * (spaces + 2) + "subgraph:")
        print_graph(sub_graph_obj, spaces+2)
        print("-" * (spaces + 2) + "end subgraph.")
    next_obj = node_key_obj.get('next')
    if next_obj:
        print_traverse_list(next_obj, graph, spaces+2)

def print_traverse_list(nodes: List[str], graph: Dict[str, Dict[str, Any]], spaces: int = 0) -> None:
    """
    Traverse and print a list of nodes.
    
    Args:
        nodes: List of node names
        graph: The graph containing the nodes
        spaces: Number of spaces for indentation
    """
    for node in nodes:
        print("." * spaces + " has dependent " + node)

def validate_graph_references(graph: Dict[str, Dict[str, Any]], path: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Validates that all node references in a graph structure are within their own graph level.
    This includes the main graph and all subgraphs.
    
    Args:
        graph: The graph structure to validate
        path: Current path in the graph (for error reporting)
        
    Returns:
        tuple: (is_valid, list_of_violations)
        where violations are strings describing each cross-graph reference found
    """
    if path is None:
        path = []
        
    violations = []
    graph_nodes = set(graph.keys())
    
    # Check each node's references
    for node, node_data in graph.items():
        current_path = path + [node] if path else [node]
        
        # Check 'next' references
        next_nodes = node_data.get('next', [])
        for next_node in next_nodes:
            if next_node not in graph_nodes:
                violations.append(
                    f"Node '{' -> '.join(current_path)}' references '{next_node}' "
                    f"which is not in the same graph level"
                )
        
        # Recursively check subgraphs
        if 'subgraph' in node_data:
            subgraph_valid, subgraph_violations = validate_graph_references(
                node_data['subgraph'], 
                current_path
            )
            violations.extend(subgraph_violations)
    
    return len(violations) == 0, violations

def find_head_nodes(graph: Dict[str, Dict[str, Any]]) -> Set[str]:
    """
    Find all nodes that have no incoming edges (head nodes) in a graph.
    
    Args:
        graph: The graph structure to check
        
    Returns:
        Set[str]: Set of nodes that have no incoming edges
    """
    # First collect all nodes that are destinations
    has_incoming_edges = set()
    for node in graph:
        # Check next nodes
        for next_node in graph[node].get('next', []):
            has_incoming_edges.add(next_node)
        # Check subgraph if it exists
        if 'subgraph' in graph[node]:
            subgraph = graph[node]['subgraph']
            # Recursively find head nodes in subgraph
            subgraph_heads = find_head_nodes(subgraph)
            # All nodes in subgraph are considered to have an incoming edge
            # from the parent node that contains the subgraph
            has_incoming_edges.update(subgraph.keys())
    
    # Head nodes are those that exist in the graph but have no incoming edges
    return set(graph.keys()) - has_incoming_edges

def find_tail_nodes(graph: Dict[str, Dict[str, Any]]) -> Set[str]:
    """
    Find all nodes that have no outgoing edges (tail nodes) in a graph.
    
    Args:
        graph: The graph structure to check
        
    Returns:
        Set[str]: Set of nodes that have no outgoing edges
    """
    tail_nodes = set()
    for node, node_data in graph.items():
        has_next = bool(node_data.get('next', []))
        has_subgraph = 'subgraph' in node_data
        
        if not has_next:
            if has_subgraph:
                # If node has no next but has subgraph, the tail nodes are in the subgraph
                subgraph_tails = find_tail_nodes(node_data['subgraph'])
                tail_nodes.update(subgraph_tails)
            else:
                # Node with no next and no subgraph is a tail
                tail_nodes.add(node)
    
    return tail_nodes

def validate_graph(graph: Dict[str, Dict[str, Any]], name: str = "") -> None:
    """
    Performs comprehensive validation of a graph structure.
    Checks for:
    1. Graph cycles
    2. Cross-graph reference violations
    3. Head node requirements (exactly one head node)
    4. Tail node requirements (exactly one tail node)
    
    Args:
        graph: The graph structure to validate
        name: Optional name for the graph (for logging)
        
    Raises:
        ValueError: If any validation fails, with detailed error message
    """
    errors = []
    
    # Check for cycles
    has_cycles = check_graph_for_cycles(graph, name)
    if has_cycles:
        msg = f"Graph {name} contains cycles"
        logging.error(msg)
        errors.append(msg)
    
    # Check for cross-graph reference violations
    is_valid_refs, violations = validate_graph_references(graph)
    if not is_valid_refs:
        msg = f"Graph {name} contains invalid cross-graph references:\n" + "\n".join(violations)
        logging.error(msg)
        errors.append(msg)
    
    # Check for head node requirements
    head_nodes = find_head_nodes(graph)
    if len(head_nodes) == 0:
        msg = f"Graph {name} has no head nodes (nodes with no incoming edges)"
        logging.error(msg)
        errors.append(msg)
    elif len(head_nodes) > 1:
        msg = f"Graph {name} has multiple head nodes: {head_nodes}. Exactly one head node is required."
        logging.error(msg)
        errors.append(msg)
    
    # Check for tail node requirements
    tail_nodes = find_tail_nodes(graph)
    if len(tail_nodes) == 0:
        msg = f"Graph {name} has no tail nodes (nodes with no outgoing edges)"
        logging.error(msg)
        errors.append(msg)
    elif len(tail_nodes) > 1:
        msg = f"Graph {name} has multiple tail nodes: {tail_nodes}. Exactly one tail node is required."
        logging.error(msg)
        errors.append(msg)
    
    # If any errors were found, raise exception with all error messages
    if errors:
        raise ValueError(f"Graph validation failed:\n" + "\n".join(errors))
    
    # Log success if no errors
    logging.info(f"Graph {name} passed all validations")
