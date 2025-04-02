from functools import reduce
from typing import Any, Dict, List, Union

from . import jc_logging as logging
from .job import JobABC
from .jobs.wrapping_job import WrappingJob

logger = logging.getLogger(__name__)

# Type definitions for DSL components
DSLComponent = Union[JobABC, 'Parallel', 'Serial']
JobsDict = Dict[str, JobABC]

class Parallel:
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite

    def __or__(self, other):
        """Support chaining with | operator"""
        if not isinstance(other, (JobABC, Parallel, Serial)):
            other = WrappingJob(other)
        
        return Parallel(*list(self.components) + [other])
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if not isinstance(other, (JobABC, Parallel, Serial)):
            other = WrappingJob(other)
            
        return Serial(self, other)

    def __repr__(self):
        return f"parallel({', '.join(repr(c) for c in self.components)})"

class Serial:
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite
        
    def __or__(self, other):
        """Support chaining with | operator"""
        if not isinstance(other, (JobABC, Parallel, Serial)):
            other = WrappingJob(other)
            
        return Parallel(self, other)
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if not isinstance(other, (JobABC, Parallel, Serial)):
            other = WrappingJob(other)
            
        return Serial(*list(self.components) + [other])
        
    def __repr__(self):
        return f"serial({', '.join(repr(c) for c in self.components)})"


def wrap(obj=None, **kwargs):
    """
    Wrap any object to enable direct graph operations with | and >> operators.
    
    This function is the key to enabling the clean syntax:
    wrap(obj1) | wrap(obj2)  # For parallel composition
    wrap(obj1) >> wrap(obj2)  # For serial composition
    
    Enhanced functionality:
    1. Single object wrapping:
       - For JobABC instances: sets the name property and returns the instance
       - For Serial/Parallel: returns the object unchanged
       - For other objects: creates a WrappingJob with the given name
    
    2. dict (kwargs) object wrapping:
       wrap(obj_a_name=obj_a, obj_b_name=obj_b) or wrap({"obj_a_name": obj_a, "obj_b_name": obj_b})
       - Returns a collection of wrapped objects following the rules in case 1
       - If only one item, returns a dict with the name as key and the wrapped object as value
    """
    # Case 1: Only keyword arguments provided (no positional argument)
    if obj is None and kwargs:
        # Process keyword arguments
        result = {}
        for name, value in kwargs.items():
            if isinstance(value, JobABC):
                value.name = name
                result[name] = value
            elif isinstance(value, (Parallel, Serial)):
                result[name] = value
            else:
                result[name] = WrappingJob(value, name)
        
        # If only one item, return just that item
        if len(result) == 1:
            return next(iter(result.values()))
        return result
    
    # Case 2: Dictionary passed as the first argument
    if isinstance(obj, dict):
        result = {}
        for name, value in obj.items():
            if isinstance(value, JobABC):
                value.name = name
                result[name] = value
            elif isinstance(value, (Parallel, Serial)):
                result[name] = value
            else:
                result[name] = WrappingJob(value, name)
        
        # If only one item, return just that item
        # if len(result) == 1:
        #     return next(iter(result.values()))
        return result
    
    # Case 3: Original behavior - single object
    # Handle the case where obj is None (could happen if called with wrap())
    if obj is None:
        raise ValueError("wrap() requires at least one argument")
        
    if isinstance(obj, (JobABC, Parallel, Serial)):
        return obj  # Already has the operations we need
    return WrappingJob(obj)

# Synonym for wrap
w = wrap

def parallel(*objects, **kwargs):
    """
    Create a parallel composition from multiple objects.
    
    This utility function takes objects (which can be a mix of JobABC
    instances and regular objects) and creates a parallel composition of all of them.
    
    Example:
        graph = parallel(obj1, obj2, obj3)  # Equivalent to wrap(obj1) | wrap(obj2) | wrap(obj3)
        
        # Also supports list argument for backward compatibility
        objects = [obj1, obj2, obj3]
        graph = parallel(objects)  # Still works if a single list is passed
        
        # Named objects using kwargs
        graph = parallel(object_a_name=object_a, object_b_name=object_b)
        
        # Named objects using a dictionary
        graph = parallel({"object_a_name": object_a, "object_b_name": object_b})
    """
    # Case 1: Only keyword arguments provided (no positional arguments)
    if not objects and kwargs:
        # Wrap each item with its name and then combine them with the | operator
        wrapped_items = wrap(**kwargs)
        if not isinstance(wrapped_items, dict):
            # If wrap returned a single item (not a dict), return it
            return wrapped_items
            
        if not wrapped_items:
            raise ValueError("Cannot create a parallel composition from empty arguments")
        
        # Convert dictionary to a list of items
        items = list(wrapped_items.values())
        if len(items) == 1:
            return items[0]
        
        # Combine all items with the | operator
        return reduce(lambda acc, obj: acc | obj, items[1:], items[0])
    
    # Case 2: Dictionary passed as the first argument
    if len(objects) == 1 and isinstance(objects[0], dict) and not kwargs:
        # Wrap each item with its name and then combine them with the | operator
        wrapped_items = wrap(objects[0])
        if not isinstance(wrapped_items, dict):
            # If wrap returned a single item (not a dict), return it
            return wrapped_items
            
        if not wrapped_items:
            raise ValueError("Cannot create a parallel composition from empty arguments")
        
        # Convert dictionary to a list of items
        items = list(wrapped_items.values())
        if len(items) == 1:
            return items[0]
        
        # Combine all items with the | operator
        return reduce(lambda acc, obj: acc | obj, items[1:], items[0])
    
    # Case 3: Original behavior - using positional arguments
    # Handle case where a single list is passed (for backward compatibility)
    if len(objects) == 1 and isinstance(objects[0], list):
        objects = objects[0]
        
    if not objects:
        raise ValueError("Cannot create a parallel composition from empty arguments")
    if len(objects) == 1:
        return wrap(objects[0])
    return reduce(lambda acc, obj: acc | wrap(obj), objects[1:], wrap(objects[0]))

# Synonym for parallel
p = parallel

def serial(*objects, **kwargs):
    """
    Create a serial composition from multiple objects.
    
    This utility function takes objects (which can be a mix of JobABC
    instances and regular objects) and creates a serial composition of all of them.
    
    Example:
        graph = serial(obj1, obj2, obj3)  # Equivalent to wrap(obj1) >> wrap(obj2) >> wrap(obj3)
        
        # Also supports list argument for backward compatibility
        objects = [obj1, obj2, obj3]
        graph = serial(objects)  # Still works if a single list is passed
        
        # Named objects using kwargs
        graph = serial(object_a_name=object_a, object_b_name=object_b)
        
        # Named objects using a dictionary
        graph = serial({"object_a_name": object_a, "object_b_name": object_b})
    """
    # Case 1: Dictionary argument
    if len(objects) == 1 and isinstance(objects[0], dict) and not kwargs:
        wrapped_items = {name: wrap({name: obj}) for name, obj in objects[0].items()}
        if not wrapped_items:
            raise ValueError("Cannot create a serial composition from empty arguments")
        if len(wrapped_items) == 1:
            return list(wrapped_items.values())[0]
        items = list(wrapped_items.values())
        return reduce(lambda acc, obj: acc >> obj, items[1:], items[0])
        
    # Case 2: Kwargs provided (object_name=object syntax)
    if kwargs:
        wrapped_items = {name: wrap({name: obj}) for name, obj in kwargs.items()}
        if not wrapped_items:
            raise ValueError("Cannot create a serial composition from empty arguments")
        if len(wrapped_items) == 1:
            return list(wrapped_items.values())[0]
        items = list(wrapped_items.values())
        return reduce(lambda acc, obj: acc >> obj, items[1:], items[0])
    
    # Case 3: Original behavior - using positional arguments
    # Handle case where a single list is passed (for backward compatibility)
    if len(objects) == 1 and isinstance(objects[0], list):
        objects = objects[0]
        
    if not objects:
        raise ValueError("Cannot create a serial composition from empty arguments")
    if len(objects) == 1:
        return wrap(objects[0])
    return reduce(lambda acc, obj: acc >> wrap(obj), objects[1:], wrap(objects[0]))

# Synonym for serial
s = serial

# Graph evaluation utilities have been moved to tests/test_utils/graph_evaluation.py