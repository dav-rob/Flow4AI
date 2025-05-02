"""Utility functions for FlowManager to support unique FQ name generation."""

from typing import Dict, List

from flow4ai.dsl import DSLComponent


def find_unique_variant_suffix(job_map: Dict, base_name_prefix: str) -> str:
    """
    Find a unique numeric suffix to append to a variant name to avoid FQ name collisions.
    
    This function checks for existing keys in job_map that start with the given base_name_prefix
    and returns a suffix that will make the name unique when appended to the variant name.
    
    Args:
        job_map: The job map dictionary containing existing job FQ names as keys
        base_name_prefix: The prefix of the FQ name to check for collisions (graph_name$$variant)
        
    Returns:
        str: A numeric suffix (empty string if no collision found, or "_1", "_2", etc.)
    """
    # If no collision in job_map, no suffix needed
    collision_found = False
    for existing_key in job_map.keys():
        if existing_key.startswith(base_name_prefix):
            collision_found = True
            break
            
    if not collision_found:
        return ""
        
    # Find existing suffixes by looking at keys with the same base name prefix
    # Extract suffix numbers from variants like "graph_name$$_1$$job_name$$"
    existing_suffixes = set()
    import re
    # Match variants with numeric suffixes in the format "prefix_N$$"
    suffix_pattern = re.compile(re.escape(base_name_prefix) + r'_([0-9]+)\$\$')
    
    for existing_key in job_map.keys():
        match = suffix_pattern.match(existing_key)
        if match and match.group(1).isdigit():
            existing_suffixes.add(int(match.group(1)))
    
    # Find the next available suffix number
    suffix_num = 1
    while suffix_num in existing_suffixes:
        suffix_num += 1
    
    return f"_{suffix_num}"
