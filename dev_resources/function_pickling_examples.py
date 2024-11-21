import asyncio
import os
import pickle
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job import Job
from job_chain import JobChain


# Example of a valid standalone function that can be pickled
def valid_result_processor(result):
    """This function can be pickled because it's defined at module level
    and only uses built-in Python functionality."""
    print(f"Processing result: {result}")
    # Process the result using standard Python operations
    if isinstance(result, dict):
        return {k.upper(): v.upper() for k, v in result.items()}
    return str(result).upper()

# Example of a class with a method that can be pickled
class ValidProcessor:
    """This class can be pickled because it's defined at module level."""
    def __init__(self, prefix):
        self.prefix = prefix
    
    def process_result(self, result):
        """This method can be pickled when the class instance is created at module level."""
        print(f"{self.prefix}: {result}")

# Create instance at module level - this works
valid_processor = ValidProcessor("VALID")

# Example of an INVALID approach - using a closure
def create_invalid_processor(prefix):
    """This creates a function that CANNOT be pickled because it's a closure."""
    def process_result(result):  # This function captures prefix from outer scope
        print(f"{prefix}: {result}")
    return process_result

# Example of an INVALID approach - using a lambda
invalid_lambda_processor = lambda result: print(f"Lambda: {result}")

# Example of a class that can't be pickled
class UnpicklableProcessor:
    def __init__(self):
        # Create an unpicklable attribute (file handle)
        self.log_file = open('temp.log', 'w')
    
    def process_result(self, result):
        self.log_file.write(str(result) + '\n')

# Example of an INVALID approach - using instance method from local instance
def run_with_invalid_instance():
    # Create a processor with unpicklable state
    processor = UnpicklableProcessor()
    try:
        print("\nTrying to pickle the processor instance:")
        pickle.dumps(processor)  # This will fail
    except Exception as e:
        print(f"Failed to pickle processor: {e}")

    try:
        print("\nTrying to use processor with JobChain:")
        job = ExampleJob()
        # This will fail because processor has unpicklable state
        job_chain = JobChain(job, processor.process_result)
        job_chain.submit_task("test")
        job_chain.mark_input_completed()
    except Exception as e:
        print(f"Failed to use processor with JobChain: {e}")
    finally:
        processor.log_file.close()
        if os.path.exists('temp.log'):
            os.remove('temp.log')

class ExampleJob(Job):
    def __init__(self):
        super().__init__("Example Job")

    async def run(self, task):
        return {"task": task, "result": f"Processed {task}"}

def demonstrate_valid_usage():
    """Demonstrate valid ways to use result processing functions."""
    print("\n=== Valid Usage Examples ===")
    
    print("\n1. Using standalone function:")
    try:
        print("Testing if function can be pickled:")
        pickle.dumps(valid_result_processor)
        print("Function successfully pickled!")
        
        job = ExampleJob()
        job_chain = JobChain(job, valid_result_processor)
        job_chain.submit_task("test1")
        job_chain.mark_input_completed()
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\n2. Using method from module-level instance:")
    try:
        print("Testing if instance method can be pickled:")
        pickle.dumps(valid_processor.process_result)
        print("Instance method successfully pickled!")
        
        job = ExampleJob()
        job_chain = JobChain(job, valid_processor.process_result)
        job_chain.submit_task("test2")
        job_chain.mark_input_completed()
    except Exception as e:
        print(f"Unexpected error: {e}")

def demonstrate_invalid_usage():
    """Demonstrate invalid ways that will fail due to pickling errors."""
    print("\n=== Invalid Usage Examples ===")
    
    print("\n1. Using a closure:")
    try:
        invalid_processor = create_invalid_processor("INVALID")
        print("Trying to pickle closure:")
        pickle.dumps(invalid_processor)
        print("This line shouldn't be reached!")
    except Exception as e:
        print(f"Failed as expected: {e}")
    
    print("\n2. Using a lambda:")
    try:
        print("Trying to pickle lambda:")
        pickle.dumps(invalid_lambda_processor)
        print("This line shouldn't be reached!")
    except Exception as e:
        print(f"Failed as expected: {e}")
    
    print("\n3. Using method from unpicklable instance:")
    run_with_invalid_instance()

def main():
    demonstrate_valid_usage()
    demonstrate_invalid_usage()

if __name__ == "__main__":
    main()
