"""
Utility functions for evaluating graph objects in tests.
"""
from jobchain.job import JobABC
from jobchain.dsl import Parallel, Serial


class GraphCreator:
    @staticmethod
    async def evaluate(graph_obj):
        """
        Process/evaluate the graph object and return the result.
        This is where you would implement the actual graph processing logic.
        """
        if isinstance(graph_obj, Parallel):
            results = [str(await GraphCreator.evaluate(c)) for c in graph_obj.components]
            return f"Executed in parallel: [{', '.join(results)}]"
        
        elif isinstance(graph_obj, Serial):
            results = [str(await GraphCreator.evaluate(c)) for c in graph_obj.components]
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
