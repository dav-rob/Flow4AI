from jc_graph import (add_edge_anywhere, check_graph_for_cycles, print_graph,
                      validate_graph_references)

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

def test_print_format():
    """
    Test the print formatting of different graph structures.
    Tests include:
    1. Simple graph with multiple paths
    2. Graph with single subgraph
    3. Graph with nested subgraphs
    """
    print("--------")       
    print("Graph 1:")
    print("--------")
    print_graph(graph1)

    print("--------")
    print("\nGraph 2:")
    print("--------")
    print_graph(graph2)

    print("--------")
    print("\nGraph 3:")
    print("--------")
    print_graph(graph3)

def test_simple_cross_graph_cycle_detection():
    """
    Test cycle detection and edge addition rules for simple graphs and cross-graph scenarios.
    Tests include:
    1. Basic cycle detection on predefined graphs
    2. Edge addition with cycle prevention
    3. Cross-graph edge addition rules with subgraphs
    """
    # Check each graph for cycles
    assert check_graph_for_cycles(graph1, "Graph 1") == False, "Graph 1 should not have cycles"
    assert check_graph_for_cycles(graph2, "Graph 2") == False, "Graph 2 should not have cycles"
    assert check_graph_for_cycles(graph3, "Graph 3") == False, "Graph 3 should not have cycles"

    # Create a test graph
    test_graph = {
        'A': {'next': ['B']},
        'B': {'next': ['C']},
        'C': {'next': ['D']},
        'D': {'next': []}
    }
    original_graph = test_graph.copy()

    # Try to add edges that would create cycles - should be prevented
    result = add_edge_anywhere(test_graph, 'D', 'A')
    assert result == False, "Adding edge D->A should fail as it creates a cycle"
    assert test_graph == original_graph, "Graph should remain unchanged after failed edge addition"

    # Add valid shortcut paths
    result = add_edge_anywhere(test_graph, 'A', 'C')
    assert result == True, "Adding edge A->C should succeed as it's a valid shortcut"
    assert 'C' in test_graph['A']['next'], "Edge A->C should be added to graph"

    result = add_edge_anywhere(test_graph, 'B', 'D')
    assert result == True, "Adding edge B->D should succeed as it's a valid shortcut"
    assert 'D' in test_graph['B']['next'], "Edge B->D should be added to graph"

    # Test subgraph edge addition
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
    original_subgraph = test_graph_with_sub.copy()

    # Test cases for edge addition rules
    # 1. Adding edge within same subgraph
    result = add_edge_anywhere(test_graph_with_sub, 'X', 'Z')
    assert result == True, "Adding edge X->Z within subgraph should succeed"
    assert 'Z' in test_graph_with_sub['B']['subgraph']['X']['next'], "Edge X->Z should be added to subgraph"

    # 2. Adding edge that would create cycle in subgraph
    result = add_edge_anywhere(test_graph_with_sub, 'Z', 'X')
    assert result == False, "Adding edge Z->X should fail as it creates a cycle"

    # 3. Adding cross-graph edge from main to subgraph
    result = add_edge_anywhere(test_graph_with_sub, 'A', 'X')
    assert result == False, "Adding edge A->X should fail as cross-graph references are not allowed"

    # 4. Adding cross-graph edge from subgraph to main
    result = add_edge_anywhere(test_graph_with_sub, 'Z', 'C')
    assert result == False, "Adding edge Z->C should fail as cross-graph references are not allowed"

    # 5. Adding edge in main graph
    result = add_edge_anywhere(test_graph_with_sub, 'A', 'C')
    assert result == True, "Adding edge A->C in main graph should succeed"
    assert 'C' in test_graph_with_sub['A']['next'], "Edge A->C should be added to main graph"

def test_comprehensive_cycle_detection():
    """
    Comprehensive tests for cycle detection in graphs.
    Tests include:
    1. Simple cycles in main graph
    2. Complex cycles in main graph
    3. Cycles in subgraphs
    4. Cycles across nested subgraphs
    5. Valid acyclic graphs with complex paths
    """
    # Test Case 1: Simple cycle in main graph
    simple_cycle = {
        'A': {'next': ['B']},
        'B': {'next': ['C']},
        'C': {'next': ['A']}  # Creates cycle A -> B -> C -> A
    }
    assert check_graph_for_cycles(simple_cycle, "Simple cycle") == True, "Should detect cycle in simple graph A->B->C->A"

    # Test Case 2: Complex cycle in main graph
    complex_cycle = {
        'A': {'next': ['B', 'C']},
        'B': {'next': ['D']},
        'C': {'next': ['E']},
        'D': {'next': ['F']},
        'E': {'next': ['F']},
        'F': {'next': ['B']}  # Creates cycle B -> D -> F -> B
    }
    assert check_graph_for_cycles(complex_cycle, "Complex cycle") == True, "Should detect cycle in complex graph B->D->F->B"

    # Test Case 3: Cycle in subgraph
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
    assert check_graph_for_cycles(subgraph_cycle, "Subgraph cycle") == True, "Should detect cycle in subgraph X->Y->Z->X"

    # Test Case 4: Valid acyclic graph with multiple paths
    valid_complex = {
        'A': {'next': ['B', 'C', 'D']},
        'B': {'next': ['E']},
        'C': {'next': ['E']},
        'D': {'next': ['E']},
        'E': {'next': []}
    }
    assert check_graph_for_cycles(valid_complex, "Valid complex") == False, "Should not detect cycles in valid complex graph"

    # Test Case 5: Valid acyclic graph with nested subgraphs
    valid_nested = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {
                    'next': ['Z'],
                    'subgraph': {
                        'alpha': {'next': ['beta']},
                        'beta': {'next': ['gamma']},
                        'gamma': {'next': []}
                    }
                },
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    assert check_graph_for_cycles(valid_nested, "Valid nested") == False, "Should not detect cycles in valid nested graph"

    # Test Case 6: Multiple paths to same node (diamond pattern)
    diamond_pattern = {
        'A': {'next': ['B', 'C']},
        'B': {'next': ['D']},
        'C': {'next': ['D']},
        'D': {'next': []}
    }
    assert check_graph_for_cycles(diamond_pattern, "Diamond pattern") == False, "Should not detect cycles in diamond pattern"

    # Test Case 7: Complex nested subgraph with cycle
    nested_cycle = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {
                    'next': ['Z'],
                    'subgraph': {
                        'alpha': {'next': ['beta']},
                        'beta': {'next': ['gamma']},
                        'gamma': {'next': ['alpha']}  # Creates cycle in nested subgraph
                    }
                },
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    assert check_graph_for_cycles(nested_cycle, "Nested cycle") == True, "Should detect cycle in deeply nested subgraph alpha->beta->gamma->alpha"

def test_cross_graph_references():
    """
    Test validation of graph references to ensure nodes only reference other nodes
    within their own graph level (main graph or subgraph).
    
    Tests include:
    1. Valid graph with proper references
    2. Invalid graph with main graph referencing subgraph node
    3. Invalid graph with subgraph referencing main graph node
    """
    # Test Case 1: Valid graph with proper references
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
    assert is_valid, "Valid graph should be valid"
    assert len(violations) == 0, "Valid graph should have no reference violations"

    # Test Case 2: Invalid - main graph referencing subgraph node
    invalid_main_ref = {
        'A': {'next': ['B', 'X']},  # 'X' is in subgraph, can't be referenced from main
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
    is_valid, violations = validate_graph_references(invalid_main_ref)
    assert not is_valid, "Graph with main->subgraph reference should be invalid"
    assert len(violations) == 1, "Should detect one violation for main graph referencing subgraph node"
    assert "Node 'A' references 'X' which is not in the same graph level" in violations[0], \
        "Should detect invalid reference from main graph to subgraph node"

    # Test Case 3: Invalid - subgraph referencing main graph node
    invalid_sub_ref = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {'next': ['C']},  # 'C' is in main graph, can't be referenced from subgraph
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    is_valid, violations = validate_graph_references(invalid_sub_ref)
    assert not is_valid, "Graph with subgraph->main reference should be invalid"
    assert len(violations) == 1, "Should detect one violation for subgraph referencing main graph node"
    assert "Node 'B -> Y' references 'C' which is not in the same graph level" in violations[0], \
        "Should detect invalid reference from subgraph to main graph node"

    # Test Case 4: Invalid - multiple cross-graph references
    invalid_multiple_refs = {
        'A': {'next': ['B', 'X', 'Y']},  # Multiple invalid references
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y', 'C']},  # Invalid reference to main graph
                'Y': {'next': ['Z', 'A']},  # Invalid reference to main graph
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    is_valid, violations = validate_graph_references(invalid_multiple_refs)
    assert not is_valid, "Graph with multiple cross-graph references should be invalid"
    assert len(violations) == 4, "Should detect all cross-graph reference violations"
    violation_texts = ' '.join(violations)
    assert "Node 'A' references 'X' which is not in the same graph level" in violation_texts, "Should detect A->X violation"
    assert "Node 'A' references 'Y' which is not in the same graph level" in violation_texts, "Should detect A->Y violation"
    assert "Node 'B -> X' references 'C' which is not in the same graph level" in violation_texts, "Should detect X->C violation"
    assert "Node 'B -> Y' references 'A' which is not in the same graph level" in violation_texts, "Should detect Y->A violation"

    # Test Case 5: Valid - nested subgraphs with proper references
    valid_nested = {
        'A': {'next': ['B']},
        'B': {
            'next': ['C'],
            'subgraph': {
                'X': {'next': ['Y']},
                'Y': {
                    'next': ['Z'],
                    'subgraph': {
                        'alpha': {'next': ['beta']},
                        'beta': {'next': ['gamma']},
                        'gamma': {'next': []}
                    }
                },
                'Z': {'next': []}
            }
        },
        'C': {'next': []}
    }
    is_valid, violations = validate_graph_references(valid_nested)
    assert is_valid, "Valid nested subgraphs should be valid"
    assert len(violations) == 0, "Valid nested subgraphs should have no reference violations"
