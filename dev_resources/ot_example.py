# Example Singleton usage
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.otel_wrapper import TracerFactory, trace_function


# Example usage of the decorator
@trace_function
def example_function(x, y):
    return x + y

@trace_function
class ExampleClass:
    def __init__(self, value):
        self.value = value

    def multiply(self, factor):
        return self.value * factor


class ExampleClass2:
    def __init__(self, value):
        self.value = value
    
    @trace_function
    def multiply(self, factor):
        return self.value * factor
    
class ExampleClass3:
    def __init__(self, value):
        self.value = value
    
    
    def multiply(self, factor):
        TracerFactory.trace("trace singleton in a method")
        return self.value * factor

# Use decorated function
result = example_function(3, 4)
print(f"Result from example_function: {result}")

# Use decorated class method
example_obj = ExampleClass(1)
print(f"Result from ExampleClass.multiply: {example_obj.multiply(2)}")

# Use TracerFactory's trace method directly
TracerFactory.trace("This is a traced message.")

example_obj2 = ExampleClass2(2)
print(f"Result from ExampleClass.multiply: {example_obj2.multiply(2)}")

example_obj3 = ExampleClass3(3)
print(f"Result from ExampleClass.multiply: {example_obj3.multiply(2)}")
