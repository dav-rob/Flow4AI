import asyncio
from typing import Any, Dict, List, Union

from dsl_play import *


class AnyObject:
    """Example class that represents any user-defined object.
    No operator overloading is needed in this class."""
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        return f"AnyObject({self.obj})"


class CustomAnyObject:
    """Example custom processor class."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"{self.name}"


class ProcessorJob(MockJobABC):
    """Example component that implements JobABC interface."""
    def __init__(self, name, process_type):
        super().__init__(name)
        self.process_type = process_type
    def __repr__(self):
        return f"ProcessorComponent(name={self.name}, type={self.process_type})"
    
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        return f"{self.name}"


async def example_1_simple_parallel():
    """Simple parallel composition.
    
    Demonstrates that only the first instance needs to be wrapped.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    
    g1 = w(obj1) | obj2
    print("\n----- Example 1: Simple parallel composition -----")
    result = await evaluate(g1)
    print("Evaluated:", result)
    return result


async def example_2_serial_composition():
    """Serial composition.
    
    Demonstrates that only the first instance needs to be wrapped,
    but wrapping it does no harm.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    
    g2 = w(obj1) >> w(obj2)
    print("\n----- Example 2: Serial composition -----")
    result = await evaluate(g2)
    print("Evaluated:", result)
    return result


async def example_3_combining_serial_and_parallel():
    """Combining serial and parallel compositions.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    
    g3 = (w(obj1) >> obj2) | obj3
    print("\n----- Example 3: Combining serial and parallel compositions -----")

    result = await evaluate(g3)
    print("Evaluated:", result)
    return result


async def example_4_complex_compositions():
    """More complex compositions.
    
    Objects inside brackets are evaluated separately, so the first
    instance needs to be wrapped.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    
    g4 = w(obj1) >> (w(obj2) | obj3)
    print("\n----- Example 4: More complex compositions -----")

    result = await evaluate(g4)
    print("Evaluated:", result)
    return result


async def example_5_using_parallel_function():
    """Using parallel function.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    
    objs = [obj1, obj2, obj3]
    g5 = p(objs)
    print("\n----- Example 5: Using parallel function -----")
    result = await evaluate(g5)
    print("Evaluated:", result)
    return result


async def example_6_using_serial_function():
    """Using serial function.
    
    Returns:
        The evaluation result
    """
    obj1 = AnyObject("Object 1")
    obj2 = AnyObject("Object 2")
    obj3 = AnyObject("Object 3")
    
    objs = [obj1, obj2, obj3]
    g6 = s(objs)
    print("\n----- Example 6: Using serial function -----")
    result = await evaluate(g6)
    print("Evaluated:", result)
    return result


async def example_7_composition_with_primitives():
    """Composition with strings and numbers.
    
    Returns:
        The evaluation result
    """
    g7 = w("Task A") >> 123 | "Task B"
    print("\n----- Example 7: Composition with strings and numbers -----")
    result = await evaluate(g7)
    print("Evaluated:", result)
    return result


async def example_8_direct_wrapping_job():
    """Using direct WrappingJob instances.
    
    Returns:
        The evaluation result
    """
    c1 = WrappingJob("Direct WrappingJob")
    g8 = w("Task C") >> c1
    print("\n----- Example 8: Using direct WrappingJob instances -----")
    result = await evaluate(g8)
    print("Evaluated:", result)
    return result


async def example_9_combining_everything():
    """Combining everything together in a somewhat nonsensical way.
    
    You don't have to wrap anything but the first object in the chain.
    Wrapping is done automatically by the operators after that.
    
    Returns:
        The evaluation result
    """
    g9 = p(w("T1") >> w(1), "T2", 3) >> w(4) | w(s(5, "T3", w(6)))
    print("\n----- Example 9: Combining everything together -----")
    result = await evaluate(g9)
    print("Evaluated:", result)
    return result


async def example_10_custom_objects():
    """Using custom objects.
    
    For instances that are not JobABC, only the first instance needs to be wrapped.
    
    Returns:
        The evaluation result
    """
    c1 = CustomAnyObject("CustomAnyObject1")
    c2 = CustomAnyObject("CustomAnyObject2")
    
    g10 = w(c1) >> c2
    print("\n----- Example 10: Using custom objects -----")
    result = await evaluate(g10)
    print("Evaluated:", result)
    return result


async def example_11_component_subclasses():
    """Using Component subclasses.
    
    Instances of JobABC don't need to be wrapped.
    
    Returns:
        The evaluation result
    """
    pc1 = ProcessorJob("ProcessorJob1", "transform")
    pc2 = ProcessorJob("ProcessorJob2", "validate")
    
    g11 = pc1 | pc2
    print("\n----- Example 11: Using Component subclasses -----")
    result = await evaluate(g11)
    print("Evaluated:", result)
    return result

async def example_12_precedence_graph():
    """Creating an adjacency list / precedence graph.
    
    Returns:
        The evaluation result
    """

    g12 = w(1) >> ((p(5,4,3) >> 7 >> 9) | (w(2) >> 6 >> 8>> 10)) >> w(11)

    print("\n----- Example 12: Creating an adjacency list / precedence graph -----")
    result = await evaluate(g12)
    print("Evaluated:", result)
    return result


async def main(example_num=None):
    """Run all examples or a specific example demonstrating DSL functionality.
    
    Args:
        example_num (int, optional): The specific example number to run.
            If None, runs all examples. Defaults to None.
    """
    # Dictionary mapping example numbers to their corresponding functions
    examples = {
        1: example_1_simple_parallel,
        2: example_2_serial_composition,
        3: example_3_combining_serial_and_parallel,
        4: example_4_complex_compositions,
        5: example_5_using_parallel_function,
        6: example_6_using_serial_function,
        7: example_7_composition_with_primitives,
        8: example_8_direct_wrapping_job,
        9: example_9_combining_everything,
        10: example_10_custom_objects,
        11: example_11_component_subclasses,
        12: example_12_precedence_graph
    }
    
    if example_num is not None:
        # Run only the specified example
        if example_num in examples:
            await examples[example_num]()
        else:
            print(f"Error: Example {example_num} not found. Available examples: 1-12")
    else:
        # Run all examples
        for example_func in examples.values():
            await example_func()


if __name__ == "__main__":
    import sys

    # Check if an example number was provided as a command-line argument
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            asyncio.run(main(example_num))
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid example number. Please provide a number between 1 and 11.")
    else:
        # Run all examples if no specific example was requested
        asyncio.run(main())

