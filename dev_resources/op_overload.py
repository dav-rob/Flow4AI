class Component:
    def __init__(self, obj):
        self.obj = obj
    
    def __or__(self, other):
        """Implements the | operator for parallel composition"""
        if isinstance(other, Parallel):
            # If right side is already a parallel component, add to its components
            return Parallel(*([self] + other.components))
        elif isinstance(other, Component):
            return Parallel(self, other)
        else:
            # If other is a raw object, wrap it first
            return Parallel(self, Component(other))
    
    def __rshift__(self, other):
        """Implements the >> operator for serial composition"""
        if isinstance(other, Serial):
            # If right side is already a serial component, add to its components
            return Serial(*([self] + other.components))
        elif isinstance(other, Component):
            return Serial(self, other)
        else:
            # If other is a raw object, wrap it first
            return Serial(self, Component(other))
    
    def __repr__(self):
        if isinstance(self.obj, (str, int, float, bool)):
            return f"Component({repr(self.obj)})"
        return f"Component({self.obj.__class__.__name__})"

class Parallel(Component):
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite

    def __repr__(self):
        return f"parallel({', '.join(repr(c) for c in self.components)})"

class Serial(Component):
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite
        
    def __repr__(self):
        return f"serial({', '.join(repr(c) for c in self.components)})"

def wrap_component(obj):
    """Wrap an object in a Component if it's not already a component type"""
    if isinstance(obj, (Component, Parallel, Serial)):
        return obj
    return Component(obj)

def auto_component(func):
    """
    Decorator that ensures the first argument to a function 
    is wrapped as a Component, enabling operator overloading.
    """
    def wrapper(*args, **kwargs):
        if not args:
            return func()
        
        # Wrap the first positional argument
        first_arg = wrap_component(args[0])
        rest_args = args[1:]
        
        return func(first_arg, *rest_args, **kwargs)
    return wrapper

class GraphCreator:
    @staticmethod
    @auto_component
    def graph(composition=None):
        """
        Create a graph from the given composition structure.
        The @auto_component decorator ensures the first object is properly wrapped.
        """
        # Return the composition structure as is, since it's already been 
        # processed by the auto_component decorator
        return composition
    
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
        
        elif isinstance(graph_obj, Component):
            # Simple case - just a single component
            return f"Executed {graph_obj.obj}"
        
        else:
            # Raw object (shouldn't normally happen)
            return f"Executed {graph_obj}"

# Create a more convenient access to the graph method
graph = GraphCreator.graph
evaluate = GraphCreator.evaluate

class AnyObject:
    def __init__(self, obj):
        self.obj = obj

# ------------------- DEMO CODE -------------------
if __name__ == "__main__":



    # Create some sample objects (these could be any Python objects)
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    obj4 = AnyObject("Object 4")
    
    # Test different graph compositions
    print("\n----- Example 1: Simple parallel -----")
    g1 = graph(obj1 | obj2)
    print(f"Graph structure: {g1}")
    print(f"Evaluation: {evaluate(g1)}")
    
    print("\n----- Example 2: Simple serial -----")
    g2 = graph(obj1 >> obj2)
    print(f"Graph structure: {g2}")
    print(f"Evaluation: {evaluate(g2)}")
    
    print("\n----- Example 3: Complex composition -----")
    # This should produce serial(parallel(serial(obj1,obj2), obj3), obj4)
    g3 = graph(obj1 >> obj2 | obj3 >> obj4)
    print(f"Graph structure: {g3}")
    print(f"Evaluation: {evaluate(g3)}")

    print("\n----- Example 4: Another complex composition -----")
    # This creates parrallel(obj1, serial(obj2, obj3))
    g4 = graph(obj1 | obj2 >> obj3)
    print(f"Graph structure: {g4}")
    print(f"Evaluation: {evaluate(g4)}")
    
    print("\n----- Example 5: Using parentheses to control order -----")
    # This creates serial(obj1, parallel(obj2, obj3))
    g5 = graph(obj1 >> (obj2 | obj3))
    print(f"Graph structure: {g5}")
    print(f"Evaluation: {evaluate(g5)}")
    
    # Non-string objects also work
    class CustomProcessor:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"Processor({self.name})"
    
    print("\n----- Example 6: Using custom objects -----")
    p1 = CustomProcessor("Processor1")
    p2 = CustomProcessor("Processor2")
    g6 = graph(p1 >> p2)
    print(f"Graph structure: {g6}")
    print(f"Evaluation: {evaluate(g6)}")
