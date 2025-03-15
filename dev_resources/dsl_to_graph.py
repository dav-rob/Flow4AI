from typing import Dict, List

from dsl_play import Parallel, Serial, WrappingJob


def dsl_to_precedence_graph(dsl_obj) -> Dict[int, List[int]]:
    """
    Convert a DSL object into a precedence graph (adjacency list).
    
    Args:
        dsl_obj: A DSL object created with operators >> and |, or functions p() and s()
    
    Returns:
        Dict[int, List[int]]: A graph definition in the format:
        {
            1: [2, 3, 4, 5],
            2: [6],
            ...
        }
        Where keys are node values and values are lists of successor nodes.
    """
    # Print the DSL object structure details to help with debugging and understanding
    debug_dsl_structure(dsl_obj)
    
    # Extract all unique job objects from the DSL structure
    jobs = extract_jobs(dsl_obj)
    print(f"DEBUG: Extracted {len(jobs)} jobs from DSL")
    
    # Assign node IDs to jobs (1-based indexing)
    node_mapping = {job: i+1 for i, job in enumerate(jobs)}
    
    # Initialize the graph with empty adjacency lists
    graph = {node_id: [] for node_id in node_mapping.values()}
    
    # Build connections based on DSL structure
    build_connections(dsl_obj, graph, node_mapping)
    
    return graph



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
        elif isinstance(obj, WrappingJob):
            # Check if the wrapped object is a compositional structure
            wrapped = obj.wrapped_object
            if isinstance(wrapped, (Serial, Parallel)):
                _extract(wrapped)
            else:
                # This is a terminal job object
                if obj not in jobs:
                    jobs.append(obj)
        else:
            # This is a primitive value that will be auto-wrapped
            wrapped = WrappingJob(obj)
            if wrapped not in jobs:
                jobs.append(wrapped)
    
    _extract(dsl_obj)
    return jobs


def extract_terminal_jobs(dsl_obj):
    """
    Extract terminal job objects (those without successors) from a DSL structure.
    
    Args:
        dsl_obj: The DSL object to extract terminal jobs from
        
    Returns:
        list: List of terminal job objects
    """
    terminal_jobs = []
    
    def _extract_terminals(obj):
        if isinstance(obj, Serial):
            # For Serial, only the last component has terminal jobs
            if obj.components:
                _extract_terminals(obj.components[-1])
        elif isinstance(obj, Parallel):
            # For Parallel, all components have terminal jobs
            for comp in obj.components:
                _extract_terminals(comp)
        elif isinstance(obj, WrappingJob):
            # Check if the wrapped object is a compositional structure
            wrapped = obj.wrapped_object
            if isinstance(wrapped, (Serial, Parallel)):
                _extract_terminals(wrapped)
            else:
                # This is a terminal job object
                if obj not in terminal_jobs:
                    terminal_jobs.append(obj)
        else:
            # This is a primitive value that will be auto-wrapped
            wrapped = WrappingJob(obj)
            if wrapped not in terminal_jobs:
                terminal_jobs.append(wrapped)
    
    _extract_terminals(dsl_obj)
    return terminal_jobs


def build_connections(dsl_obj, graph, node_mapping):
    """
    Build the connections in the graph based on the DSL structure.
    
    Args:
        dsl_obj: The DSL object to analyze
        graph: The graph to build connections in
        node_mapping: Mapping from job objects to node IDs
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
        elif isinstance(comp, WrappingJob):
            # Check if the wrapped object is a compositional structure
            wrapped = comp.wrapped_object
            if isinstance(wrapped, (Serial, Parallel)):
                return _process_component(wrapped, prev_terminals)
            else:
                # This is a terminal job object
                comp_id = node_mapping[comp]
                
                # Connect previous terminals to this component
                if prev_terminals:
                    for term in prev_terminals:
                        term_id = node_mapping[term]
                        if comp_id not in graph[term_id]:
                            graph[term_id].append(comp_id)
                
                return [comp]
        else:
            # This is a primitive value that will be auto-wrapped
            wrapped = WrappingJob(comp)
            comp_id = node_mapping[wrapped]
            
            # Connect previous terminals to this component
            if prev_terminals:
                for term in prev_terminals:
                    term_id = node_mapping[term]
                    if comp_id not in graph[term_id]:
                        graph[term_id].append(comp_id)
            
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
        print(f"{indent_str}WrappingJob wrapping: {dsl_obj.wrapped_object}")
    
    else:
        print(f"{indent_str}Other Type: {type(dsl_obj).__name__} - Value: {dsl_obj}")



def visualize_graph(graph: Dict[int, List[int]]):
    """
    Visualize the graph structure for debugging purposes.
    
    Args:
        graph: A graph definition in adjacency list format
    """
    print("Graph Structure:")
    for node, next_nodes in sorted(graph.items()):
        if next_nodes:
            print(f"{node}: {sorted(next_nodes)}")
        else:
            print(f"{node}: []")



if __name__ == "__main__":
   pass