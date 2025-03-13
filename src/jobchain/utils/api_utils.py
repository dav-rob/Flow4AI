"""
Utility functions for handling API keys and authentication.
"""
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

import jobchain.jc_logging as logging

logger = logging.getLogger(__name__)


def get_api_key(params: Optional[Dict[str, Any]] = None, 
               env_file: str = "api.env",
               key_name: str = None,
               required: bool = True) -> Optional[str]:
    """
    Resolves and returns an API key from parameters or environment variables.
    
    Args:
        params: Dictionary of parameters that may contain an 'api_key' entry
        env_file: Path to the .env file to load (defaults to "api.env")
        key_name: Default environment variable name to use if not specified in params
        required: Whether to raise an error if the API key is not found
        
    Returns:
        The API key string or None if not required and not found
        
    Raises:
        ValueError: If required is True and the API key is not found
    """
    # Initialize params if None
    params = params or {}
    
    # Load environment variables from env file
    load_dotenv(env_file)
    
    # Extract key name from params or use default
    env_var = params.pop("api_key", None) if params else key_name
    
    # Resolve API key: either from the env var specified in params or from default env var
    api_key = os.getenv(env_var)
    logger.info(f"Resolved API Key exists: {bool(api_key)}")
    
    # Check if the API key is not set and raise an error if required
    if not api_key and required:
        raise ValueError("API key is not set. Please provide an API key.")
        
    return api_key


