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

def validate_graph_references(graph, path=None):
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

def test_cycle_detection():
    """
    Comprehensive tests for cycle detection in graphs.
    Tests include:
    1. Simple cycles in main graph
    2. Complex cycles in main graph
    3. Cycles in subgraphs
    4. Cycles across nested subgraphs
    5. Valid acyclic graphs with complex paths
    """
    print("\nComprehensive Cycle Detection Tests")
    print("==================================")

    # Test Case 1: Simple cycle in main graph
    print("\n1. Simple cycle in main graph (should fail):")
    simple_cycle = {
        'A': {'next': ['B']},
        'B': {'next': ['C']},
        'C': {'next': ['A']}  # Creates cycle A -> B -> C -> A
    }
    check_graph_for_cycles(simple_cycle, "Simple cycle")

    # Test Case 2: Complex cycle in main graph
    print("\n2. Complex cycle in main graph (should fail):")
    complex_cycle = {
        'A': {'next': ['B', 'C']},
        'B': {'next': ['D']},
        'C': {'next': ['E']},
        'D': {'next': ['F']},
        'E': {'next': ['F']},
        'F': {'next': ['B']}  # Creates cycle B -> D -> F -> B
    }
    check_graph_for_cycles(complex_cycle, "Complex cycle")

    # Test Case 3: Cycle in subgraph
    print("\n3. Cycle in subgraph (should fail):")
    subgraph_cycle = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {'next': ['Z']},
                'Z': {'next': ['X']}  # Creates cycle X -> Y -> Z -> X
            }
        },
        'C': {'next': []}
    }
    check_graph_for_cycles(subgraph_cycle, "Subgraph cycle")

    # Test Case 4: Cycle in nested subgraph
    print("\n4. Cycle in nested subgraph (should fail):")
    nested_cycle = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {
                    'next': ['Z'],
                    'subgraph': {
                        'P': {'next': ['Q']},
                        'Q': {'next': ['R']},
                        'R': {'next': ['P']}  # Creates cycle P -> Q -> R -> P
                    }
                },
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    check_graph_for_cycles(nested_cycle, "Nested cycle")

    # Test Case 5: Valid complex graph (should succeed)
    print("\n5. Valid complex graph (should succeed):")
    valid_complex = {
        'A': {'next': ['B', 'C']},
        'B': {
            'next': ['D'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {
                    'next': ['Z'],
                    'subgraph': {
                        'P': {'next': ['Q']},
                        'Q': {'next': ['R']},
                        'R': {'next': []}
                    }
                },
                'Z': {'next': []}
            }
        },
        'C': {'next': ['D']},
        'D': {'next': []}
    }
    check_graph_for_cycles(valid_complex, "Valid complex")

    # Test Case 6: Diamond pattern (should succeed)
    print("\n6. Diamond pattern - multiple paths to same node (should succeed):")
    diamond_pattern = {
        'A': {'next': ['B', 'C']},
        'B': {'next': ['D']},
        'C': {'next': ['D']},
        'D': {'next': []}
    }
    check_graph_for_cycles(diamond_pattern, "Diamond pattern")

    # Test Case 7: Complex subgraph paths (should succeed)
    print("\n7. Complex subgraph paths (should succeed):")
    complex_subgraph = {
        'A': {
            'next': ['B'],
            'subgraph': {
                'X1': {'next': ['X2', 'X3']},
                'X2': {'next': ['X4']},
                'X3': {'next': ['X4']},
                'X4': {'next': []}
            }
        },
        'B': {
            'next': ['C'],
            'subgraph': {
                'Y1': {'next': ['Y2', 'Y3']},
                'Y2': {'next': ['Y4']},
                'Y3': {'next': ['Y4']},
                'Y4': {'next': []}
            }
        },
        'C': {'next': []}
    }
    check_graph_for_cycles(complex_subgraph, "Complex subgraph paths")

# Run the comprehensive tests
test_cycle_detection()

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

# Test invalid graph structures
print("\nTesting graph validation:")
print("------------------------")

# Test case 1: Valid graph
print("\n1. Testing valid graph:")
valid_graph = {
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
is_valid, violations = validate_graph_references(valid_graph)
print(f"Valid graph is {'valid' if is_valid else 'invalid'}")
if not is_valid:
    print("Violations found:")
    for v in violations:
        print(f"- {v}")

# Test case 2: Invalid graph with cross-graph reference from main to subgraph
print("\n2. Testing invalid graph (main -> subgraph reference):")
invalid_graph1 = {
    'A': {'next': ['B', 'X']},  # Invalid: references subgraph node X
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
is_valid, violations = validate_graph_references(invalid_graph1)
print(f"Invalid graph 1 is {'valid' if is_valid else 'invalid'}")
if not is_valid:
    print("Violations found:")
    for v in violations:
        print(f"- {v}")

# Test case 3: Invalid graph with cross-graph reference from subgraph to main
print("\n3. Testing invalid graph (subgraph -> main reference):")
invalid_graph2 = {
    'A': {'next': ['B']},
    'B': {
        'next': ['C'],
        'subgraph': {
            'X': {'next': ['Y']},
            'Y': {'next': ['Z']},
            'Z': {'next': ['C']}  # Invalid: references main graph node C
        }
    },
    'C': {'next': []}
}
is_valid, violations = validate_graph_references(invalid_graph2)
print(f"Invalid graph 2 is {'valid' if is_valid else 'invalid'}")
if not is_valid:
    print("Violations found:")
    for v in violations:
        print(f"- {v}")
