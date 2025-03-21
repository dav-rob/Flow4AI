from functools import reduce
from typing import Any, Dict, Union

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

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union


class WrappingJob(JobABC):
    def __init__(
        self, 
        callable_obj: Callable, 
        name: str = None
    ):
        """
        Initialize a wrapper for a callable object.
        
        Args:
            callable_obj: The function or method to wrap
            name: Identifier for this callable in parameter dictionaries
        Raises:
            TypeError: If callable_obj is not actually callable
        """

        is_callable = callable(callable_obj)
        self.is_callable = is_callable
        if not is_callable: #and not isinstance(callable_obj, (JobABC, Parallel, Serial))
            raise TypeError(f"Expected a callable object or JobABC, Parallel, Serial, got {type(callable_obj).__name__}")
        self.wrapped_obj = callable_obj
        super().__init__(name)
        self.default_args = []
        self.default_kwargs = {}
        
    async def run(self, task: Union[Dict[str, Any], Task]) -> Dict[str, Any]:
        """
        Execute the wrapped callable with parameters from the params dictionary.
        
        Args:
            task: legacy parameter dictionary
            
        Returns:
            The result of the callable execution
        """
        if not self.is_callable:
            raise ValueError(f"Callable '{self.wrapped_obj}' is not callable")
            
        params = self.get_context()

        if self.name not in params:
            raise ValueError(f"No parameters found for callable '{self.name}'")
            
        callable_params = self._create_callable_params(params[self.name])
        
        # Add context to the kwargs if the callable accepts it
        if self.global_ctx and "context" in inspect.signature(self.wrapped_obj).parameters:
            callable_params["kwargs"]["context"] = self.global_ctx
            
        # Validate parameters against the callable's signature
        self._validate_params(callable_params["args"], callable_params["kwargs"])
        
        # Apply type conversions based on callable's signature
        args, kwargs = self._convert_param_types(
            callable_params["args"], 
            callable_params["kwargs"]
        )
        
        return await self._execute_callable(args, kwargs)
    
    def _create_callable_params(self, params: Dict[str, Any]) -> Dict[str, List[Any]]:
        """
        Extract and normalize parameters for the callable, supporting multiple styles.
        
        Args:
            params: Dictionary of parameters specific to this callable
            
        Returns:
            Dictionary containing 'args' and 'kwargs' keys
        """
        # Start with default values
        args = self.default_args.copy()
        kwargs = self.default_kwargs.copy()
        
        # Case 1: Explicit args list
        if "fn.args" in params:
            args = params["fn.args"]
            
        # Case 2: Explicit kwargs dictionary
        if "fn.kwargs" in params:
            kwargs.update(params["fn.kwargs"])
            
        # Case 3: Named parameters with fn. prefix
        for key, value in params.items():
            if key.startswith("fn.") and key not in ["fn.args", "fn.kwargs"]:
                param_name = key[3:]  # Remove "fn." prefix
                kwargs[param_name] = value
                
        return {"args": args, "kwargs": kwargs}
    
    def _validate_params(self, args: List[Any], kwargs: Dict[str, Any]) -> None:
        """
        Validate that the provided parameters match the callable's signature.
        
        Args:
            args: Positional arguments to validate
            kwargs: Keyword arguments to validate
            
        Raises:
            ValueError: If parameters don't match the callable's signature
        """
        sig = inspect.signature(self.wrapped_obj)
        try:
            sig.bind(*args, **kwargs)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for {self.name}: {e}")
            
    def _convert_param_types(self, args: List[Any], kwargs: Dict[str, Any]) -> tuple:
        """
        Convert parameter types based on the callable's type annotations.
        
        Args:
            args: Positional arguments to convert
            kwargs: Keyword arguments to convert
            
        Returns:
            Tuple containing converted args and kwargs
        """
        sig = inspect.signature(self.wrapped_obj)
        
        # Convert positional args
        converted_args = []
        for i, arg in enumerate(args):
            # Skip conversion if we have more args than parameters
            if i >= len(sig.parameters):
                converted_args.append(arg)
                continue
                
            param_name = list(sig.parameters.keys())[i]
            param = sig.parameters[param_name]
            
            # Skip if no annotation or if annotation is not a type
            if param.annotation == inspect.Parameter.empty or not isinstance(param.annotation, type):
                converted_args.append(arg)
                continue
                
            try:
                # Only convert if needed and possible
                if not isinstance(arg, param.annotation) and arg is not None:
                    converted_args.append(param.annotation(arg))
                else:
                    converted_args.append(arg)
            except (ValueError, TypeError):
                # If conversion fails, use original value
                converted_args.append(arg)
        
        # Convert kwargs
        converted_kwargs = {}
        for name, value in kwargs.items():
            if (name in sig.parameters and 
                sig.parameters[name].annotation != inspect.Parameter.empty and
                isinstance(sig.parameters[name].annotation, type)):
                
                try:
                    # Only convert if needed and possible
                    if not isinstance(value, sig.parameters[name].annotation) and value is not None:
                        converted_kwargs[name] = sig.parameters[name].annotation(value)
                    else:
                        converted_kwargs[name] = value
                except (ValueError, TypeError):
                    # If conversion fails, use original value
                    converted_kwargs[name] = value
            else:
                converted_kwargs[name] = value
                
        return converted_args, converted_kwargs
    
    async def _execute_callable(self, args: List[Any], kwargs: Dict[str, Any]) -> Any:
        """
        Execute the callable with the given parameters.
        
        Args:
            args: Positional arguments to pass
            kwargs: Keyword arguments to pass
            
        Returns:
            Result of the callable execution
        """
        result = self.wrapped_obj(*args, **kwargs)
        
        # Check if the result is a coroutine (from an async function)
        if inspect.iscoroutine(result):
            # Await the coroutine to get the actual result
            return await result
            
        return result
    



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

def parallel(*objects):
    """
    Create a parallel composition from multiple objects.
    
    This utility function takes objects (which can be a mix of JobABC
    instances and regular objects) and creates a parallel composition of all of them.
    
    Example:
        graph = parallel(obj1, obj2, obj3)  # Equivalent to wrap(obj1) | wrap(obj2) | wrap(obj3)
        
        # Also supports list argument for backward compatibility
        objects = [obj1, obj2, obj3]
        graph = parallel(objects)  # Still works if a single list is passed
    """
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

def serial(*objects):
    """
    Create a serial composition from multiple objects.
    
    This utility function takes objects (which can be a mix of JobABC
    instances and regular objects) and creates a serial composition of all of them.
    
    Example:
        graph = serial(obj1, obj2, obj3)  # Equivalent to wrap(obj1) >> wrap(obj2) >> wrap(obj3)
        
        # Also supports list argument for backward compatibility
        objects = [obj1, obj2, obj3]
        graph = serial(objects)  # Still works if a single list is passed
    """
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