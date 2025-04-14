# Temporary Migration Structures

This document tracks temporary structures and workarounds implemented during the jobchain → flow4ai migration.
These items should be removed once the full migration is complete to maintain code cleanliness.

## Temporary Methods and Functions

### `_is_job_abc_like()` in flow4ai.job_chain.JobChain
- **Purpose**: Enables cross-package compatibility by allowing JobABC instances from either package to work
- **Location**: `src/flow4ai/job_chain.py`
- **Replacement**: Once migration is complete, direct `isinstance(obj, JobABC)` checks can be used
- **Removal Criteria**: When all imports are updated to use flow4ai package only

```python
def _is_job_abc_like(self, obj):
    """More flexible check for JobABC compatibility that works across package boundaries.
    
    This helps with cross-package compatibility between jobchain and flow4ai.
    Checks for duck-typing by looking for essential JobABC attributes/methods.
    """
    # Check if it's an actual JobABC instance (preferred, fastest check)
    if isinstance(obj, JobABC):
        return True
        
    # Otherwise use duck typing to check if it's JobABC-compatible
    # Must have these attributes/methods to be considered JobABC-like
    required_attributes = ['name', 'run']
    for attr in required_attributes:
        if not hasattr(obj, attr):
            return False
            
    # If we pass all checks, it's probably a JobABC-like object
    return True
```

## Temporary Forwarding Modules

### jobchain.jc_logging → flow4ai.f4a_logging
- **Purpose**: Provides backward compatibility for code using the old module
- **Location**: `src/jobchain/jc_logging.py`
- **Replacement**: Direct imports from flow4ai.f4a_logging
- **Removal Criteria**: When all imports are updated to use flow4ai.f4a_logging

### jobchain.jc_graph → flow4ai.f4a_graph
- **Purpose**: Provides backward compatibility for code using the old module
- **Location**: `src/jobchain/jc_graph.py`
- **Replacement**: Direct imports from flow4ai.f4a_graph
- **Removal Criteria**: When all imports are updated to use flow4ai.f4a_graph

## Dual Package Support

### Dual Import Paths in flow4ai/__init__.py
- **Purpose**: Allows importing from both old and new package paths during transition
- **Location**: `src/flow4ai/__init__.py`
- **Replacement**: Clean imports from flow4ai package only
- **Removal Criteria**: When all code is updated to import directly from flow4ai

### Dual Log File Support in f4a_logging.py
- **Purpose**: Logs to both jobchain.log and flow4ai.log during transition
- **Location**: `src/flow4ai/f4a_logging.py`
- **Replacement**: Log to flow4ai.log only
- **Removal Criteria**: When all code is updated to use flow4ai environment variables

### Dual Environment Variable Support with Special Priority Logic
- **Purpose**: Checks both JOBCHAIN_* and FLOW4AI_* environment variables with special priority for backward compatibility
- **Location**: `src/flow4ai/f4a_logging.py`
- **Details**: We prioritize JOBCHAIN_* environment variables when they're explicitly set
  ```python
  # For backward compatibility in tests, if JOBCHAIN_LOG_LEVEL is explicitly set, use it
  jobchain_log_level = os.getenv('JOBCHAIN_LOG_LEVEL')
  flow4ai_log_level = os.getenv('FLOW4AI_LOG_LEVEL')
  
  log_level = (jobchain_log_level if jobchain_log_level else flow4ai_log_level) or 'INFO'
  ```
- **Replacement**: Check only FLOW4AI_* environment variables
- **Removal Criteria**: When all code and documentation is updated to use new environment variables
