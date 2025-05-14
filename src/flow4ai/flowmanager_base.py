"""
Base class for Flow Manager implementations.

This module provides the abstract base class that defines the common interface
for all Flow Manager implementations in the Flow4AI framework.
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import (Any, Callable, Collection, Dict, List, Optional, Set,
                    Tuple, Union)

import flow4ai.f4a_logging as logging
from flow4ai.job_abc import JobABC
from flow4ai.task import Task


class FlowManagerABC(ABC):
    """
    Abstract base class for Flow Manager implementations.
    
    FlowManagerABC defines the minimal common interface for all Flow Manager implementations.
    Since FlowManager and FlowManagerMP were developed independently with different interfaces,
    this base class focuses on the core conceptual similarities rather than enforcing identical
    method signatures.
    """
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Initialize the FlowManager instance.
        
        Each implementation should handle its own initialization with appropriate parameters.
        """
        pass
