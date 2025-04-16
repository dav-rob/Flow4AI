"""
Utility functions for evaluating graph objects in tests.
"""
from flow4ai.job import JobABC
from flow4ai.dsl import DSLComponent, Parallel, Serial


class GraphCreator:
    @staticmethod
    async def evaluate(graph_obj: DSLComponent, prefix="0"):
        """
        Process/evaluate the graph object and return the result.
        This is where you would implement the actual graph processing logic.
        
        Args:
            graph_obj: The graph object to evaluate
            prefix: The prefix to use for hierarchical numbering (e.g., "1.2.3")
        """
        indent = "    " * (prefix.count("."))
        
        if isinstance(graph_obj, Parallel):
            result_lines = [f"{prefix})Executed in parallel: ["]
            for i, component in enumerate(graph_obj.components):
                component_prefix = f"{prefix}.{i+1}"
                component_result = await GraphCreator.evaluate(component, component_prefix)
                result_lines.append(f"{indent}    {component_result},")
            result_lines.append(f"{indent}]")
            return "\n".join(result_lines)
        
        elif isinstance(graph_obj, Serial):
            result_lines = [f"{prefix})Executed in series: ["]
            for i, component in enumerate(graph_obj.components):
                component_prefix = f"{prefix}.{i+1}"
                component_result = await GraphCreator.evaluate(component, component_prefix)
                result_lines.append(f"{indent}    {component_result},")
            result_lines.append(f"{indent}]")
            return "\n".join(result_lines)
        
        elif isinstance(graph_obj, JobABC):
            # Simple case - just a single component
            result = await graph_obj.run({})
            return f"{prefix}) {result}"
        
        else:
            # Raw object (shouldn't normally happen)
            return f"{prefix}) Executed {graph_obj}"


# Create a convenient access to the evaluation method
evaluate = GraphCreator.evaluate

def print_diff(graph, expected_graph, test_name="Unknown"):
    """
    Print the differences between the two graphs.
    Also returns False if there are differences, True if graphs match.
    """
    print(f"\n❌ The generated graph for {test_name} does NOT match the expected structure!")
    print("Differences:")
    has_differences = False
    
    for k in set(list(graph.keys()) + list(expected_graph.keys())):
        if k not in graph:
            print(f"  Missing key {k} in generated graph")
            has_differences = True
        elif k not in expected_graph:
            print(f"  Extra key {k} in generated graph")
            has_differences = True
        else:
            # Check the 'next' attribute in each node
            if 'next' in graph[k] and 'next' in expected_graph[k]:
                if set(graph[k]['next']) != set(expected_graph[k]['next']):
                    print(f"  For key {k}, 'next' values differ:")
                    print(f"    Expected: {sorted(expected_graph[k]['next'])}")
                    print(f"    Actual:   {sorted(graph[k]['next'])}")
                    
                    # Show which elements were added or removed
                    added = set(graph[k]['next']) - set(expected_graph[k]['next'])
                    removed = set(expected_graph[k]['next']) - set(graph[k]['next'])
                    if added:
                        print(f"    Added elements: {sorted(added)}")
                    if removed:
                        print(f"    Removed elements: {sorted(removed)}")
                    has_differences = True
            else:
                # Check for other differences in the node dictionaries
                if graph[k] != expected_graph[k]:
                    print(f"  For key {k}, values differ:")
                    print(f"    Expected: {expected_graph[k]}")
                    print(f"    Actual:   {graph[k]}")
                    has_differences = True
    
    if has_differences:
        # Print the graph as a dictionary for reference
        print("\nActual graph as dictionary:")
        print("{")
        for node, edges in graph.items():
            print(f"    '{node}': {edges},")
        print("}")
    else:
        print("✅ No differences found! This is unexpected since the assertion failed.")
    
    validate_graph(graph, name=test_name)
    
    return not has_differences
