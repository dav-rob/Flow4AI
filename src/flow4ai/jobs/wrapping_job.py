import inspect
from typing import Any, Callable, Dict, List, Union

from jobchain import JobABC
from jobchain.job import Task


class WrappingJob(JobABC):
    FN_CONTEXT='j_ctx'

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
            raise TypeError(f"WrappingJob will only wrap a callable, error due to {type(callable_obj).__name__}")
        self.callable = callable_obj
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
            raise ValueError(f"Callable '{self.callable}' is not callable")

        params = task if task else self.get_task()  # if calling run() directly in tests use get_task(), "if task" is falsey so fails on {}

        # Process shorthand dot notation params (e.g., "job.param": value)
        params = self._process_shorthand_params(params)

        # Check if the callable requires parameters
        sig = inspect.signature(self.callable)
        requires_params = bool(sig.parameters)
        
        # Check if the only parameter required is 'context' which is auto-provided
        requires_non_context_params = False
        if requires_params:
            non_context_params = [param for param in sig.parameters if param != self.FN_CONTEXT]
            requires_non_context_params = bool(non_context_params)

        parsed_name = JobABC.parse_job_name(self.name)
        short_name = self.name if parsed_name == "UNSUPPORTED NAME FORMAT" else parsed_name
        # Only check for parameters if the callable requires non-context parameters
        if requires_non_context_params and short_name not in params:
            raise ValueError(f"No parameters found for callable '{short_name}'")  

        # If no parameters are required, use empty args and kwargs
        if not requires_params or short_name not in params:
            callable_params = {"args": [], "kwargs": {}}
        else:
            callable_params = self._create_callable_params(params[short_name])

        # Add context to the kwargs if the callable accepts it
        if self.FN_CONTEXT in sig.parameters:
            callable_params["kwargs"][self.FN_CONTEXT] = {}
            callable_params["kwargs"][self.FN_CONTEXT]["global"] = self.global_ctx
            callable_params["kwargs"][self.FN_CONTEXT]["task"] = params
            callable_params["kwargs"][self.FN_CONTEXT]["inputs"] = self.get_inputs()

        # Validate parameters against the callable's signature
        self._validate_params(callable_params["args"], callable_params["kwargs"])

        # Apply type conversions based on callable's signature
        args, kwargs = self._convert_param_types(
            callable_params["args"],
            callable_params["kwargs"]
        )

        return await self._execute_callable(args, kwargs)

    def _process_shorthand_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process shorthand dot notation params (e.g., "job.param": value) and
        convert them to the standard nested format.
        
        Args:
            params: Dictionary of parameters that may contain shorthand notation
            
        Returns:
            Updated parameters dictionary with shorthand notation expanded
        """
        result = params.copy()
        dot_params = {}
        
        # Find and collect all shorthand dot notation parameters
        for key, value in params.items():
            if '.' in key and not key.startswith('fn.'):
                job_name, param_name = key.split('.', 1)
                if job_name not in dot_params:
                    dot_params[job_name] = {}
                dot_params[job_name][param_name] = value
                del result[key]  # Remove the dot notation key from the result
                
        # Merge the dot params with the existing job params
        for job_name, job_params in dot_params.items():
            if job_name in result:
                # If the job already exists in the params, merge the parameters
                result[job_name].update(job_params)
            else:
                # Otherwise, create a new entry
                result[job_name] = job_params
                
        return result
        
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

        # Case 1: Explicit args list via 'fn.args' (legacy) or 'args' (new)
        if "fn.args" in params:
            args = params["fn.args"]
        elif "args" in params:
            args = params["args"]

        # Case 2: Explicit kwargs dictionary via 'fn.kwargs' (legacy) or 'kwargs' (new)
        if "fn.kwargs" in params:
            kwargs.update(params["fn.kwargs"])
        elif "kwargs" in params:
            kwargs.update(params["kwargs"])

        # Case 3: Named parameters with fn. prefix (legacy)
        for key, value in params.items():
            if key.startswith("fn.") and key not in ["fn.args", "fn.kwargs"]:
                param_name = key[3:]  # Remove "fn." prefix
                kwargs[param_name] = value
            # Case 4: Direct parameter passing (new)
            elif key not in ["args", "kwargs"]:
                kwargs[key] = value

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
        sig = inspect.signature(self.callable)
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
        sig = inspect.signature(self.callable)

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
        result = self.callable(*args, **kwargs)

        # Check if the result is a coroutine (from an async function)
        if inspect.iscoroutine(result):
            # Await the coroutine to get the actual result
            return await result

        return result
