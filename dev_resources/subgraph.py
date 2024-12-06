graph1: dict = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {'next': ['D']},
    'D': {'next': []}
}

graph2: dict = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {
        'next': ['D'],
        'subgraph': {  # Attributed subgraph
            'V': {'next': ['W']},
            'W': {'next': ['X', 'Y']},
            'X': {'next': ['Z']},
            'Y': {'next': ['Z']},
            'Z': {'next': []}
        }
    },
    'D': {'next': []}
}

graph3: dict = {
    'A': {'next': ['B', 'C']},
    'B': {'next': ['C', 'D']},
    'C': {
        'next': ['D'],
        'subgraph': {  # Attributed subgraph
            'V': {'next': ['W']},
            'W': {
                'next': ['X', 'Y'],
                'subgraph': {  # Attributed subgraph
                    'alpha': {'next': ['beta']},
                    'beta': {'next': ['sigma', 'pi']},
                    'sigma': {'next': ['zeta']},
                    'pi': {'next': ['zeta']},
                    'zeta': {'next': []}
                }
            },
            'X': {'next': ['Z']},
            'Y': {'next': ['Z']},
            'Z': {'next': []}
        }
    },
    'D': {'next': []}
}

def has_cycle(graph, node, visited=None, path=None):
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

def check_graph_for_cycles(graph, name=""):
    print(f"\nChecking {name} for cycles...")
    for node in graph:
        has_cycle_result, cycle_path = has_cycle(graph, node)
        if has_cycle_result:
            print(f"Cycle detected! Path: {' -> '.join(cycle_path)}")
            return True
    print("No cycles detected")
    return False

def traverse(graph,spaces=0):
    for key in graph.keys():
        print("." * spaces + key)
        visit_node(graph, key, spaces)

def visit_node(graph, key, spaces=0):
    
    node_key_obj = graph[key]
    sub_graph_obj = node_key_obj.get('subgraph')
    if sub_graph_obj:
        print("-" * (spaces + 2) + "subgraph:")
        traverse(sub_graph_obj, spaces+2,)
        print("-" * (spaces + 2) + "end subgraph.")
    next_obj = node_key_obj.get('next')
    if next_obj:
        traverse_list(next_obj, graph, spaces+2)

def traverse_list(list: list,graph: dict,spaces=0):
    for node in list:
        print("." * spaces + " has dependent " + node)

def add_edge(graph, from_node, to_node):
    """
    Attempts to add an edge between two nodes in the graph.
    Returns True if successful, False if it would create a cycle.
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

def find_node_and_graph(main_graph, target_node, current_graph=None):
    """
    Recursively finds a node and its containing graph in the graph structure.
    Returns a tuple of (containing_graph, path_to_node) where:
    - containing_graph is the dictionary containing the target_node
    - path_to_node is the list of nodes traversed to reach the subgraph containing the target_node
    Returns (None, None) if the node is not found.
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
                
    return None, None

def add_edge_anywhere(main_graph, from_node, to_node):
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
        from_node: The source node name
        to_node: The target node name
        
    Returns:
        bool: True if edge was added successfully, False otherwise
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

print("--------")       
print("Graph 1:")
print("--------")
traverse(graph1)

print("--------")
print("\nGraph 2:")
print("--------")
traverse(graph2)

print("--------")
print("\nGraph 3:")
print("--------")
traverse(graph3)

# Check each graph for cycles
check_graph_for_cycles(graph1, "Graph 1")
check_graph_for_cycles(graph2, "Graph 2")
check_graph_for_cycles(graph3, "Graph 3")

# Test the cycle prevention
print("\nTesting cycle prevention:")
print("------------------------")

# Create a test graph
test_graph = {
    'A': {'next': ['B']},
    'B': {'next': ['C']},
    'C': {'next': ['D']},
    'D': {'next': []}
}

print("\nInitial test graph:")
traverse(test_graph)

# Try to add some edges
print("\nTrying to add edges:")
add_edge(test_graph, 'D', 'A')  # This should create a cycle and be prevented
add_edge(test_graph, 'A', 'C')  # This should be fine (shortcut path)
add_edge(test_graph, 'B', 'D')  # This should be fine (shortcut path)

print("\nFinal test graph after attempted modifications:")
traverse(test_graph)

# Test subgraph edge addition
print("\nTesting subgraph edge addition:")
print("-----------------------------")

# Create a test graph with subgraphs
test_graph_with_sub = {
    'A': {'next': ['B']},
    'B': {
        'next': ['C'],
        'subgraph': {
            'X': {'next': ['Y']},
            'Y': {'next': ['Z']},
            'Z': {'next': []}
        }
    },
    'C': {'next': []}
}

print("\nInitial test graph with subgraph:")
traverse(test_graph_with_sub)

print("\nTrying to add edges in subgraph:")
# Test cases for edge addition rules
print("\n1. Adding edge within same subgraph (should succeed):")
add_edge_anywhere(test_graph_with_sub, 'X', 'Z')  # Should succeed (valid shortcut within subgraph)

print("\n2. Adding edge that would create cycle in subgraph (should fail):")
add_edge_anywhere(test_graph_with_sub, 'Z', 'X')  # Should fail (would create cycle)

print("\n3. Adding cross-graph edge from main to subgraph (should fail):")
add_edge_anywhere(test_graph_with_sub, 'A', 'X')  # Should fail (cross-graph reference)

print("\n4. Adding cross-graph edge from subgraph to main (should fail):")
add_edge_anywhere(test_graph_with_sub, 'Z', 'C')  # Should fail (cross-graph reference)

print("\n5. Adding edge in main graph (should succeed):")
add_edge_anywhere(test_graph_with_sub, 'A', 'C')  # Should succeed (valid edge in main graph)

print("\nFinal test graph after attempted modifications:")
traverse(test_graph_with_sub)
