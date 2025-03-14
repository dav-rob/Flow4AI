from functools import reduce

"""
Improved operator overloading example for JobChain graph construction.
This implementation allows for direct operator usage between wrapped objects.
"""

class JobABC:
    def __init__(self, obj):
        self.obj = obj
    
    def __or__(self, other):
        """Implements the | operator for parallel composition"""
        if isinstance(other, Parallel):
            # If right side is already a parallel component, add to its components
            return Parallel(*([self] + other.components))
        elif isinstance(other, JobABC):
            return Parallel(self, other)
        else:
            # If other is a raw object, wrap it first
            return Parallel(self, JobABC(other))
    
    def __rshift__(self, other):
        """Implements the >> operator for serial composition"""
        if isinstance(other, Serial):
            # If right side is already a serial component, add to its components
            return Serial(*([self] + other.components))
        elif isinstance(other, JobABC):
            return Serial(self, other)
        else:
            # If other is a raw object, wrap it first
            return Serial(self, JobABC(other))
    
    def __repr__(self):
        if isinstance(self.obj, (str, int, float, bool)):
            return f"JobABC({repr(self.obj)})"
        return f"JobABC({self.obj.__class__.__name__})"

class Parallel(JobABC):
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite

    def __or__(self, other):
        """Support chaining with | operator"""
        if isinstance(other, ObjectWrapper):
            other = JobABC(other.obj)
        elif not isinstance(other, (JobABC, Parallel, Serial)):
            other = JobABC(other)
        
        return Parallel(*list(self.components) + [other])
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if isinstance(other, ObjectWrapper):
            other = JobABC(other.obj)
        elif not isinstance(other, (JobABC, Parallel, Serial)):
            other = JobABC(other)
            
        return Serial(self, other)

    def __repr__(self):
        return f"parallel({', '.join(repr(c) for c in self.components)})"

class Serial(JobABC):
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite
        
    def __or__(self, other):
        """Support chaining with | operator"""
        if isinstance(other, ObjectWrapper):
            other = JobABC(other.obj)
        elif not isinstance(other, (JobABC, Parallel, Serial)):
            other = JobABC(other)
            
        return Parallel(self, other)
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if isinstance(other, ObjectWrapper):
            other = JobABC(other.obj)
        elif not isinstance(other, (JobABC, Parallel, Serial)):
            other = JobABC(other)
            
        return Serial(*list(self.components) + [other])
        
    def __repr__(self):
        return f"serial({', '.join(repr(c) for c in self.components)})"

class ObjectWrapper:
    """
    Wrapper that adds operator overloading capabilities to any object.
    This allows objects to be used with | and >> operators.
    """
    def __init__(self, obj):
        self.obj = obj
    
    def __or__(self, other):
        """Implements | for parallel composition"""
        # Create JobABC versions of both objects
        left = JobABC(self.obj)
        
        if isinstance(other, ObjectWrapper):
            # If the other is also wrapped, unwrap it
            right = JobABC(other.obj)
        else:
            # If it's already a JobABC/Parallel/Serial, use it directly
            right = other if isinstance(other, (JobABC, Parallel, Serial)) else JobABC(other)
        
        # Return the parallel composition
        return left | right
    
    def __rshift__(self, other):
        """Implements >> for serial composition"""
        # Create JobABC versions of both objects
        left = JobABC(self.obj)
        
        if isinstance(other, ObjectWrapper):
            # If the other is also wrapped, unwrap it
            right = JobABC(other.obj)
        else:
            # If it's already a JobABC/Parallel/Serial, use it directly
            right = other if isinstance(other, (JobABC, Parallel, Serial)) else JobABC(other)
        
        # Return the serial composition
        return left >> right
    
    def __repr__(self):
        if isinstance(self.obj, (str, int, float, bool)):
            return f"g({repr(self.obj)})"
        return f"g({self.obj.__class__.__name__})"

def wrap(obj):
    """
    Wrap any object to enable direct graph operations with | and >> operators.
    
    This function is the key to enabling the clean syntax:
    wrap(obj1) | wrap(obj2)  # For parallel composition
    wrap(obj1) >> wrap(obj2)  # For serial composition
    """
    if isinstance(obj, JobABC):
        return obj  # Already has the operations we need
    return ObjectWrapper(obj)

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
    def evaluate(graph_obj):
        """
        Process/evaluate the graph object and return the result.
        This is where you would implement the actual graph processing logic.
        """
        if isinstance(graph_obj, Parallel):
            results = [GraphCreator.evaluate(c) for c in graph_obj.components]
            return f"Executed in parallel: [{', '.join(results)}]"
        
        elif isinstance(graph_obj, Serial):
            results = [GraphCreator.evaluate(c) for c in graph_obj.components]
            return f"Executed in series: [{', '.join(results)}]"
        
        elif isinstance(graph_obj, JobABC):
            # Simple case - just a single component
            return f"Executed {graph_obj.obj}"
        
        else:
            # Raw object (shouldn't normally happen)
            return f"Executed {graph_obj}"

# Create a convenient access to the evaluation method
evaluate = GraphCreator.evaluate