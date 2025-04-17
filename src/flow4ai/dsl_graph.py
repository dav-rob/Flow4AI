from typing import Dict, List, Tuple

from . import f4a_logging as logging
from .dsl import JobsDict, Parallel, Serial
from .job import JobABC
from .jobs.wrapping_job import WrappingJob

logger = logging.getLogger(__name__)


PrecedenceGraph = Dict[str, Dict[str, List[str]]]

def dsl_to_precedence_graph(dsl_obj) -> Tuple[PrecedenceGraph, JobsDict]:
    """
    Convert a DSL object into a precedence graph with nested dictionary.
    
    Args:
        dsl_obj: A DSL object created with operators >> and |, or functions p() and s()
    
    Returns:
        Dict[str, Dict[str, List[str]]]: A graph definition in the format:
        {
            'Task A': {'next': ['Task B', 'Task C']},
            'Task B': {'next': []},
            ...
        }
        Where keys are node string representations and values are dictionaries with 'next' key
        pointing to lists of successor node representations.
    """
    # Print the DSL object structure details to help with debugging and understanding
    if logger.getEffectiveLevel() == logging.DEBUG:
        debug_dsl_structure(dsl_obj)
    
    # Extract all unique job objects from the DSL structure
    jobs = extract_jobs(dsl_obj)
    logger.info(f"Extracted {len(jobs)} jobs from DSL")
    
    # Initialize the graph with empty adjacency nested dictionaries using string representation of jobs
    graph = {job.name: {'next': []} for job in jobs}
    jobs: JobsDict = {job.name: job for job in jobs}
    
    # Build connections based on DSL structure using the new format
    build_connections(dsl_obj, graph, nested=True)
    
    return graph, jobs



def extract_jobs(dsl_obj):
    """
    Extract all individual job objects from a DSL structure.
    
    Args:
        dsl_obj: The DSL object to extract jobs from
        
    Returns:
        list: List of unique job objects
    """
    jobs = []
    
    def _extract(obj):
        if isinstance(obj, (Serial, Parallel)):
            # For compositional structures, extract jobs from each component
            for comp in obj.components:
                _extract(comp)
        elif isinstance(obj, JobABC):
            # Recursively extract jobs from wrapped compositional structures
            if isinstance(obj, WrappingJob) and isinstance(obj.callable, (Serial, Parallel)):
                _extract(obj.callable)
            # Terminal job object
            elif obj not in jobs:
                jobs.append(obj)
        else:
            # This is a primitive value that will be auto-wrapped
            wrapped = WrappingJob(obj)
            if wrapped not in jobs:
                jobs.append(wrapped)
    
    _extract(dsl_obj)
    return jobs



def build_connections(dsl_obj, graph, nested=False):
    """
    Build the connections in the graph based on the DSL structure.
    
    Args:
        dsl_obj: The DSL object to analyze
        graph: The graph to build connections in where keys and values are string representations of jobs
        nested: If True, the graph uses the nested format {'next': [...]} for edges instead of direct lists
    """
    def _process_serial(serial_obj, prev_terminals=None):
        if not serial_obj.components:
            return []
        
        # Start with the first component
        curr_terminals = []
        for i, comp in enumerate(serial_obj.components):
            # Process the current component
            if i == 0:
                # First component
                curr_terminals = _process_component(comp, prev_terminals)
            else:
                # Connect previous terminals to the current component
                curr_terminals = _process_component(comp, curr_terminals)
        
        return curr_terminals
    
    def _process_parallel(parallel_obj, prev_terminals=None):
        if not parallel_obj.components:
            return []
        
        all_terminals = []
        for comp in parallel_obj.components:
            # Process each component in parallel
            comp_terminals = _process_component(comp, prev_terminals)
            all_terminals.extend(comp_terminals)
        
        return all_terminals
    
    def _process_component(comp, prev_terminals=None):
        # Handle different types of components
        if isinstance(comp, Serial):
            return _process_serial(comp, prev_terminals)
        elif isinstance(comp, Parallel):
            return _process_parallel(comp, prev_terminals)
        elif isinstance(comp, JobABC):
            if isinstance(comp, WrappingJob):
                # Check if the wrapped object is a compositional structure
                wrapped = comp.callable
                if isinstance(wrapped, (Serial, Parallel)):
                    return _process_component(wrapped, prev_terminals)
            
            # This is a terminal job object (either WrappingJob with non-compositional object
            # or any other JobABC subclass)
            comp_str = comp.name
            
            # Connect previous terminals to this component
            if prev_terminals:
                for term in prev_terminals:
                    term_str = term.name
                    if nested:
                        if comp_str not in graph[term_str]['next']:
                            graph[term_str]['next'].append(comp_str)
                    else:
                        if comp_str not in graph[term_str]:
                            graph[term_str].append(comp_str)
            
            return [comp]
        else:
            # This is a primitive value that will be auto-wrapped
            wrapped = WrappingJob(comp)
            comp_str = wrapped.name
            
            # Connect previous terminals to this component
            if prev_terminals:
                for term in prev_terminals:
                    term_str = term.name
                    if nested:
                        if comp_str not in graph[term_str]['next']:
                            graph[term_str]['next'].append(comp_str)
                    else:
                        if comp_str not in graph[term_str]:
                            graph[term_str].append(comp_str)
            
            return [wrapped]
    
    # Start processing from the top-level DSL object
    _process_component(dsl_obj)

def debug_dsl_structure(dsl_obj, indent=0):
    """
    Print the structure of a DSL object for debugging purposes.
    
    Args:
        dsl_obj: The DSL object to analyze
        indent: Current indentation level for nested printing
    """
    indent_str = "  " * indent
    
    if isinstance(dsl_obj, Serial):
        print(f"{indent_str}Serial with {len(dsl_obj.components)} components")
        for i, comp in enumerate(dsl_obj.components):
            print(f"{indent_str}Component {i}:")
            debug_dsl_structure(comp, indent + 1)
    
    elif isinstance(dsl_obj, Parallel):
        print(f"{indent_str}Parallel with {len(dsl_obj.components)} components")
        for i, comp in enumerate(dsl_obj.components):
            print(f"{indent_str}Component {i}:")
            debug_dsl_structure(comp, indent + 1)
    
    elif isinstance(dsl_obj, WrappingJob):
        print(f"{indent_str}WrappingJob wrapping: {dsl_obj.callable}")
    
    else:
        print(f"{indent_str}Other Type: {type(dsl_obj).__name__} - Value: {dsl_obj}")



def visualize_graph(graph):
    """
    Visualize the graph structure for debugging purposes.
    Displays parent nodes before their children for better readability.
    Ensures a node is only displayed after all of its parents have been processed.
    
    Args:
        graph: A graph definition, either in:
            - Adjacency list format Dict[str, List[str]]
            - Or nested dictionary format Dict[str, Dict[str, List[str]]] with 'next' key
    """
    print("Graph Structure:")
    
    # Check if we're using the nested format
    is_nested = all(isinstance(node_data, dict) and 'next' in node_data for node_data in graph.values())
    
    # Build a reverse graph (child -> parents) to track parent relationships
    reverse_graph = {}
    for node in graph:
        reverse_graph[node] = []
    
    # Find all parent-child relationships
    for parent, node_data in graph.items():
        # Get children based on the graph format
        if is_nested:
            children = node_data['next']
        else:
            children = node_data
            
        for child in children:
            if child not in reverse_graph:
                reverse_graph[child] = []
            reverse_graph[child].append(parent)
    
    # Use Kahn's algorithm for topological sorting
    # Identify nodes with no parents (root nodes)
    root_nodes = []
    for node, parents in reverse_graph.items():
        if not parents and node in graph:  # Only include nodes that are in the original graph
            root_nodes.append(node)
    
    # Process nodes in order, ensuring a node is only processed after all its parents
    node_order = []
    while root_nodes:
        node = root_nodes.pop(0)  # Get a node with no unprocessed parents
        node_order.append(node)
        
        # Process this node's children
        if is_nested:
            children = graph.get(node, {}).get('next', [])
        else:
            children = graph.get(node, [])
            
        for child in children:
            # Remove this parent from the child's parent list
            reverse_graph[child].remove(node)
            # If the child has no more unprocessed parents, add it to the root nodes
            if not reverse_graph[child]:
                root_nodes.append(child)
    
    # Check for cycles or disconnected components
    remaining_nodes = [node for node in graph if node not in node_order]
    if remaining_nodes:
        # For disconnected components, process them separately
        for node in sorted(remaining_nodes):
            if node not in node_order:  # Skip if already added through processing
                node_order.append(node)
    
    # Print the graph in the calculated order
    for node in node_order:
        if is_nested:
            next_nodes = graph.get(node, {}).get('next', [])
            print(f"{node}: {{'next': {next_nodes}}}")
        else:
            next_nodes = graph.get(node, [])
            if next_nodes:
                print(f"{node}: {next_nodes}")
            else:
                print(f"{node}: []")



if __name__ == "__main__":
   pass