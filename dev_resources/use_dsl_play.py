from dsl_play import *


class AnyObject:
    """Example class that represents any user-defined object.
    No operator overloading is needed in this class."""
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        return f"AnyObject({self.obj})"
    

    

if __name__ == "__main__":
    # Create some sample objects
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")

    # Example 1: Simple parallel composition
    g1 = w(obj1) | w(obj2)
    print("\n----- Example 1: Simple parallel composition -----")
    print(g1)
    print("Evaluated:", evaluate(g1))

    # Example 2: Serial composition
    g2 = w(obj1) >> w(obj2)
    print("\n----- Example 2: Serial composition -----")
    print(g2)
    print("Evaluated:", evaluate(g2))

    # Example 3: Combining serial and parallel compositions
    g3 = (w(obj1) >> w(obj2)) | w(obj3)
    print("\n----- Example 3: Combining serial and parallel compositions -----")
    print(g3)
    print("Evaluated:", evaluate(g3))

    # Example 4: More complex compositions
    g4 = w(obj1) >> (w(obj2) | w(obj3))
    print("\n----- Example 4: More complex compositions -----")
    print(g4)
    print("Evaluated:", evaluate(g4))

    # Example 5: Using all_p and all_s
    objs = [obj1, obj2, obj3]
    g5 = p(objs)
    print("\n----- Example 5: Using all_p and all_s -----")
    print(g5)
    print("Evaluated:", evaluate(g5))

    g6 = s(objs)
    print("\n----- Example 6: Using all_s -----")
    print(g6)
    print("Evaluated:", evaluate(g6))

    # Example 7: Composition with strings and numbers
    g7 = w("Task A") >> w(123) | w("Task B")
    print("\n----- Example 7: Composition with strings and numbers -----")
    print(g7)
    print("Evaluated:", evaluate(g7))

    # Example 8: Using direct Component instances
    c1 = WrappingJob("Direct Component")
    g8 = w("Task C") >> c1
    print("\n----- Example 8: Using direct Component instances -----")
    print(g8)
    print("Evaluated:", evaluate(g8))

    # Example 9: Combining everything together
    g9 = p([w("T1") >> w(1), "T2", 3]) >> w(4) | w(s([5, "T3", w(6)]))
    print("\n----- Example 9: Combining everything together -----")
    print(g9)
    print("Evaluated:", evaluate(g9))

    class CustomProcessor:
        def __init__(self, name):
                self.name = name
        def __repr__(self):
            return f"CustomProcessor({self.name})"
    
    print("\n----- Example 10: Using custom objects -----")
    p1 = CustomProcessor("Processor1")
    p2 = CustomProcessor("Processor2")
    g10 = w(p1) >> w(p2)
    print(g10)
    print("Evaluated:", evaluate(g10))

    class ProcessorComponent:
        def __init__(self, name, process_type):
            self.process_type = process_type
            self.name = name
        def __repr__(self):
            return f"ProcessorComponent(name={self.name}, type={self.process_type})"
    
    # Create instances of the Component subclass
    pc1 = ProcessorComponent("Processor1", "transform")
    pc2 = ProcessorComponent("Processor2", "validate")
    
    g11 = w(pc1) | w(pc2)
    print("\n----- Example 11: Using Component subclasses -----")
    print(g11)
    print("Evaluated:", evaluate(g11))
