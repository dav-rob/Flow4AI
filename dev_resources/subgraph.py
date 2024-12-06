import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    print_graph(test_graph)

    # Try to add some edges
    print("\nTrying to add edges:")
    add_edge_anywhere(test_graph, 'D', 'A')  # This should create a cycle and be prevented
    add_edge_anywhere(test_graph, 'A', 'C')  # This should be fine (shortcut path)
    add_edge_anywhere(test_graph, 'B', 'D')  # This should be fine (shortcut path)

    print("\nFinal test graph after attempted modifications:")
    print_graph(test_graph)

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
    print_graph(test_graph_with_sub)

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
    print_graph(test_graph_with_sub)

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

def test_cross_graph_references():
    """
    Test validation of graph references to ensure nodes only reference other nodes
    within their own graph level (main graph or subgraph).
    
    Tests include:
    1. Valid graph with proper references
    2. Invalid graph with main graph referencing subgraph node
    3. Invalid graph with subgraph referencing main graph node
    """
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


# Run all tests
test_print_format()
test_simple_cross_graph_cycle_detection()
test_comprehensive_cycle_detection()
test_cross_graph_references()
