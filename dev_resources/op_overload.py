"""
Improved operator overloading example for JobChain graph construction.
This implementation allows for direct operator usage between wrapped objects.
"""

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

    def __or__(self, other):
        """Support chaining with | operator"""
        if isinstance(other, GraphOperableWrapper):
            other = Component(other.obj)
        elif not isinstance(other, (Component, Parallel, Serial)):
            other = Component(other)
        
        return Parallel(*list(self.components) + [other])
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if isinstance(other, GraphOperableWrapper):
            other = Component(other.obj)
        elif not isinstance(other, (Component, Parallel, Serial)):
            other = Component(other)
            
        return Serial(self, other)

    def __repr__(self):
        return f"parallel({', '.join(repr(c) for c in self.components)})"

class Serial(Component):
    def __init__(self, *components):
        self.components = components
        self.obj = None  # No direct object for this composite
        
    def __or__(self, other):
        """Support chaining with | operator"""
        if isinstance(other, GraphOperableWrapper):
            other = Component(other.obj)
        elif not isinstance(other, (Component, Parallel, Serial)):
            other = Component(other)
            
        return Parallel(self, other)
        
    def __rshift__(self, other):
        """Support chaining with >> operator"""
        if isinstance(other, GraphOperableWrapper):
            other = Component(other.obj)
        elif not isinstance(other, (Component, Parallel, Serial)):
            other = Component(other)
            
        return Serial(*list(self.components) + [other])
        
    def __repr__(self):
        return f"serial({', '.join(repr(c) for c in self.components)})"

class GraphOperableWrapper:
    """
    Wrapper that adds operator overloading capabilities to any object.
    This allows objects to be used with | and >> operators.
    """
    def __init__(self, obj):
        self.obj = obj
    
    def __or__(self, other):
        """Implements | for parallel composition"""
        # Create Component versions of both objects
        left = Component(self.obj)
        
        if isinstance(other, GraphOperableWrapper):
            # If the other is also wrapped, unwrap it
            right = Component(other.obj)
        else:
            # If it's already a Component/Parallel/Serial, use it directly
            right = other if isinstance(other, (Component, Parallel, Serial)) else Component(other)
        
        # Return the parallel composition
        return left | right
    
    def __rshift__(self, other):
        """Implements >> for serial composition"""
        # Create Component versions of both objects
        left = Component(self.obj)
        
        if isinstance(other, GraphOperableWrapper):
            # If the other is also wrapped, unwrap it
            right = Component(other.obj)
        else:
            # If it's already a Component/Parallel/Serial, use it directly
            right = other if isinstance(other, (Component, Parallel, Serial)) else Component(other)
        
        # Return the serial composition
        return left >> right
    
    def __repr__(self):
        if isinstance(self.obj, (str, int, float, bool)):
            return f"g({repr(self.obj)})"
        return f"g({self.obj.__class__.__name__})"

def g(obj):
    """
    Wrap any object to enable direct graph operations with | and >> operators.
    
    This function is the key to enabling the clean syntax:
    g(obj1) | g(obj2)  # For parallel composition
    g(obj1) >> g(obj2)  # For serial composition
    """
    if isinstance(obj, Component):
        return obj  # Already has the operations we need
    return GraphOperableWrapper(obj)


from functools import reduce

def all_p(objects):
    """
    Create a parallel composition from a list of objects.
    
    This utility function takes a list of objects (which can be a mix of Component
    instances and regular objects) and creates a parallel composition of all of them.
    
    Example:
        objects = [obj1, obj2, obj3]
        graph = all_p(objects)  # Equivalent to g(obj1) | g(obj2) | g(obj3)
    """
    if not objects:
        raise ValueError("Cannot create a parallel composition from an empty list")
    if len(objects) == 1:
        return g(objects[0])
    return reduce(lambda acc, obj: acc | g(obj), objects[1:], g(objects[0]))


def all_s(objects):
    """
    Create a serial composition from a list of objects.
    
    This utility function takes a list of objects (which can be a mix of Component
    instances and regular objects) and creates a serial composition of all of them.
    
    Example:
        objects = [obj1, obj2, obj3]
        graph = all_s(objects)  # Equivalent to g(obj1) >> g(obj2) >> g(obj3)
    """
    if not objects:
        raise ValueError("Cannot create a serial composition from an empty list")
    if len(objects) == 1:
        return g(objects[0])
    return reduce(lambda acc, obj: acc >> g(obj), objects[1:], g(objects[0]))

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
        
        elif isinstance(graph_obj, Component):
            # Simple case - just a single component
            return f"Executed {graph_obj.obj}"
        
        else:
            # Raw object (shouldn't normally happen)
            return f"Executed {graph_obj}"

# Create a convenient access to the evaluation method
evaluate = GraphCreator.evaluate

class AnyObject:
    """
    Example class that represents any user-defined object.
    No operator overloading is needed in this class.
    """
    def __init__(self, obj):
        self.obj = obj
    
    def __repr__(self):
        return f"AnyObject({self.obj})"

# ------------------- DEMO CODE -------------------
if __name__ == "__main__":
    # Create some sample objects
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    obj4 = AnyObject("Object 4")
    
    # Test different graph compositions
    print("\n----- Example 1: Simple parallel -----")
    g1 = g(obj1) | g(obj2)
    print(f"Graph structure: {g1}")
    print(f"Evaluation: {evaluate(g1)}")
    
    print("\n----- Example 2: Simple serial -----")
    g2 = g(obj1) >> g(obj2)
    print(f"Graph structure: {g2}")
    print(f"Evaluation: {evaluate(g2)}")
    
    print("\n----- Example 3: Multiple parallel -----")
    g3 = g(obj1) | g(obj2) | g(obj3)
    print(f"Graph structure: {g3}")
    print(f"Evaluation: {evaluate(g3)}")
    
    print("\n----- Example 4: Multiple serial -----")
    g4 = g(obj1) >> g(obj2) >> g(obj3)
    print(f"Graph structure: {g4}")
    print(f"Evaluation: {evaluate(g4)}")
    
    print("\n----- Example 5: Parallel then serial -----")
    g5 = (g(obj1) | g(obj2)) >> g(obj3)
    print(f"Graph structure: {g5}")
    print(f"Evaluation: {evaluate(g5)}")
    
    print("\n----- Example 6: Serial then parallel -----")
    g6 = (g(obj1) >> g(obj2)) | g(obj3)
    print(f"Graph structure: {g6}")
    print(f"Evaluation: {evaluate(g6)}")
    
    print("\n----- Example 7: Multiple parallel then serial -----")
    g7 = (g(obj1) | g(obj2) | g(obj3)) >> g(obj4)
    print(f"Graph structure: {g7}")
    print(f"Evaluation: {evaluate(g7)}")
    
    print("\n----- Example 8: Complex composition -----")
    g8 = (g(obj1) >> g(obj2)) | g(obj3) >> g(obj4)
    print(f"Graph structure: {g8}")
    print(f"Evaluation: {evaluate(g8)}")
    
    print("\n----- Example 9: Using parentheses to control order -----")
    g9 = g(obj1) >> (g(obj2) | g(obj3))
    print(f"Graph structure: {g9}")
    print(f"Evaluation: {evaluate(g9)}")
    
    # Non-string objects also work
    class CustomProcessor:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"Processor({self.name})"
    
    print("\n----- Example 10: Using custom objects -----")
    p1 = CustomProcessor("Processor1")
    p2 = CustomProcessor("Processor2")
    g10 = g(p1) >> g(p2)
    print(f"Graph structure: {g10}")
    print(f"Evaluation: {evaluate(g10)}")
    
    # Compare with regular object notation
    print("\n----- Example 11: Testing operator precedence without parentheses -----")
    g11 = g(obj1) | g(obj2) >> g(obj3)  # Should be equivalent to (g(obj1) | g(obj2)) >> g(obj3)
    print(f"Graph structure: {g11}")
    print(f"Evaluation: {evaluate(g11)}")
    
    print("\n----- Example 12: Testing operator precedence without parentheses (2) -----")
    g12 = g(obj1) >> g(obj2) | g(obj3)  # Should be equivalent to (g(obj1) >> g(obj2)) | g(obj3)
    print(f"Graph structure: {g12}")
    print(f"Evaluation: {evaluate(g12)}")
    
    print("\n----- Example 13: Component subclasses don't need g() wrapping -----")
    # Create a custom Component subclass
    class ProcessorComponent(Component):
        def __init__(self, name, process_type):
            self.process_type = process_type
            super().__init__(name)
        
        def __repr__(self):
            return f"ProcessorComponent({self.obj}, {self.process_type})"
    
    # Create instances of the Component subclass
    pc1 = ProcessorComponent("Processor1", "transform")
    pc2 = ProcessorComponent("Processor2", "validate")
    
    # These don't need g() wrapping since they're already Component instances
    g13 = pc1 | pc2
    print(f"Direct Component subclass composition: {g13}")
    print(f"Evaluation: {evaluate(g13)}")
    
    print("\n----- Example 14: Serial composition with Component subclasses -----")
    g14 = pc1 >> pc2
    print(f"Serial Component subclass composition: {g14}")
    print(f"Evaluation: {evaluate(g14)}")
    
    print("\n----- Example 15: Mixing Component subclasses with g()-wrapped objects -----")
    # Mix Component subclasses with g()-wrapped objects
    g15 = pc1 | g(obj1) >> pc2
    print(f"Mixed composition: {g15}")
    print(f"Evaluation: {evaluate(g15)}")
    
    print("\n----- Example 16: Complex composition with Component subclasses and g()-wrapped objects -----")
    g16 = (pc1 | g(obj1)) >> (pc2 | g(obj2))
    print(f"Complex mixed composition: {g16}")
    print(f"Evaluation: {evaluate(g16)}")

    print("\n----- Example 17: Working with mixed object lists -----")
    # Create a mixed list of Component instances and regular objects
    mixed_objects = [pc1, obj1, pc2, obj2]
    
    # g() already handles both Component and non-Component objects correctly
    # Create the same complex expression using g() directly
    g17 = (g(mixed_objects[0]) | g(mixed_objects[1])) >> (g(mixed_objects[2]) | g(mixed_objects[3]))
    print(f"Mixed list composition: {g17}")
    print(f"Evaluation: {evaluate(g17)}")

    # Create more objects for demonstration
    pc3 = ProcessorComponent("Processor3", "analyze")
    obj4 = AnyObject("Object 4")
    
    # A list with mixed object types
    objects = [pc1, obj1, pc2, obj2, pc3, obj4]

    print("\n----- Example 18: Using all_p() utility function -----")
    # Create a parallel composition from all objects in the list using all_p()
    g18 = all_p(objects)
    print(f"Parallel composition using all_p(): {g18}")
    print(f"Evaluation: {evaluate(g18)}")

    print("\n----- Example 19: Using all_s() utility function -----")
    # Create a serial composition from all objects in the list using all_s()
    g19 = all_s(objects)
    print(f"Serial composition using all_s(): {g19}")
    print(f"Evaluation: {evaluate(g19)}")
    
    print("\n----- Example 20: Combining all_p() and all_s() for complex patterns -----")
    # Split list into two groups
    group1 = objects[:3]  # First three objects
    group2 = objects[3:]  # Last three objects
    
    # Create parallel compositions for each group, then connect them in series
    g20 = all_p(group1) >> all_p(group2)
    print(f"Complex pattern with utility functions: {g20}")
    print(f"Evaluation: {evaluate(g20)}")
    