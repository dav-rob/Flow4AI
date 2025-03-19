from typing import Any, Dict, Union
from functools import reduce

from . import jc_logging as logging
from .job import JobABC, Task

logger = logging.getLogger(__name__)

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

class WrappingJob(JobABC):
    def __init__(self, wrapped_object: Any):
        self.wrapped_object = wrapped_object
        super().__init__(str(wrapped_object))

    def __repr__(self):
        return self.name

    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        logger.debug(f"Executing {self.name} with task: {task}")
        return f"{self.wrapped_object}"

def wrap(obj):
    """
    Wrap any object to enable direct graph operations with | and >> operators.
    
    This function is the key to enabling the clean syntax:
    wrap(obj1) | wrap(obj2)  # For parallel composition
    wrap(obj1) >> wrap(obj2)  # For serial composition
    """
    if isinstance(obj, JobABC):
        return obj  # Already has the operations we need
    return WrappingJob(obj)

# Synonym for wrap
w = wrap

def parallel(objects):
    """
    Create a parallel composition from a list of objects.
    
    This utility function takes a list of objects (which can be a mix of JobABC
    instances and regular objects) and creates a parallel composition of all of them.
    
    Example:
        objects = [obj1, obj2, obj3]
        graph = all_parallel(objects)  # Equivalent to wrap(obj1) | wrap(obj2) | wrap(obj3)
    """
    if not objects:
        raise ValueError("Cannot create a parallel composition from an empty list")
    if len(objects) == 1:
        return wrap(objects[0])
    return reduce(lambda acc, obj: acc | wrap(obj), objects[1:], wrap(objects[0]))

# Synonym for parallel
p = parallel

def serial(objects):
    """
    Create a serial composition from a list of objects.
    
    This utility function takes a list of objects (which can be a mix of JobABC
    instances and regular objects) and creates a serial composition of all of them.
    
    Example:
        objects = [obj1, obj2, obj3]
        graph = all_serial(objects)  # Equivalent to wrap(obj1) >> wrap(obj2) >> wrap(obj3)
    """
    if not objects:
        raise ValueError("Cannot create a serial composition from an empty list")
    if len(objects) == 1:
        return wrap(objects[0])
    return reduce(lambda acc, obj: acc >> wrap(obj), objects[1:], wrap(objects[0]))

# Synonym for serial
s = serial

class GraphCreator:
    @staticmethod
    async def evaluate(graph_obj):
        """
        Process/evaluate the graph object and return the result.
        This is where you would implement the actual graph processing logic.
        """
        if isinstance(graph_obj, Parallel):
            results = [await GraphCreator.evaluate(c) for c in graph_obj.components]
            return f"Executed in parallel: [{', '.join(results)}]"
        
        elif isinstance(graph_obj, Serial):
            results = [await GraphCreator.evaluate(c) for c in graph_obj.components]
            return f"Executed in series: [{', '.join(results)}]"
        
        elif isinstance(graph_obj, JobABC):
            # Simple case - just a single component
            result = await graph_obj.run({})
            return result
        
        else:
            # Raw object (shouldn't normally happen)
            return f"Executed {graph_obj}"

# Create a convenient access to the evaluation method
evaluate = GraphCreator.evaluate