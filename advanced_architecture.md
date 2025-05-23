# Flow4AI: Scalable AI Job Scheduling and Execution Platform

## Overview

Flow4AI is a sophisticated Python framework designed for parallel and asynchronous job execution, with a focus on AI and data processing workflows. It provides a flexible, graph-based job scheduling system that allows complex task dependencies and parallel processing.

> **Terminology Clarification**: Throughout this document, "job graph" refers specifically to the technical implementation of execution flow, while "workflow" describes the higher-level business process being automated. A job graph is the concrete realization of a workflow in the Flow4AI system.

> **Asynchronous Architecture**: Flow4AI is built on an entirely asynchronous architecture. This is a fundamental design choice that enables efficient handling of concurrent operations and optimal resource utilization. When implementing custom jobs or integrating external libraries, use asynchronous patterns and avoid synchronous code that could block the event loop. Synchronous frameworks should be wrapped carefully or avoided when possible.

## Core Architectural Components

### Starting and terminating a FlowManagerMP
- Anywhere in you code, within a function, create a FlowManagerMP instance:
  ```python
  flowmanagerMP = FlowManagerMP()
  ```
  The FlowManagerMP will configure itself with multiple job types from the configuration file.  The FlowManagerMPFactory creates a singleton instance of FlowManagerMP for convenience.

- Submit tasks to the FlowManagerMP from many places to many different jobs:
  ```python
  flowmanagerMP.submit_task(task, job_name='job_name')
  ```
- Mark the FlowManagerMP as input completed, when you have finished submitting tasks:
  ```python
  flowmanagerMP.mark_input_completed()
  ```
This ensures all previous tasks are completed, and all processes are cleaned up.

### 1. Job Abstraction (`job.py`)

#### JobABC (Abstract Base Class)
- Defines the core contract for job execution
- Key methods:
  - `run(task)`: **Async** method to process a task - **must leverage async/await patterns**
  - `_execute(task)`: Internal **async** method handling job lifecycle
- Supports complex job graphs with dependencies
- Implements tracing for performance monitoring
- **Fundamentally asynchronous**: All methods use async/await for non-blocking execution

> **Note on Task vs. Job Distinction**: Tasks are units of work (data + metadata) that flow through the job graph, while jobs are the processing units that operate on tasks. This distinction is fundamental to understanding the Flow4AI execution model.

#### Key Features
- Automatic unique naming for job instances
- Support for job dependencies
- Async execution model
- Tracing and performance instrumentation
- Automatic task metadata preservation throughout job graphs

#### Custom Job Implementation

### Choosing Between JobABC Subclasses and Wrapped Functions

Flow4AI supports two primary approaches for implementing jobs:

#### When to Use Wrapped Functions

Wrapped functions were designed to enable seamless integration with existing frameworks and simplify the developer experience:

- **Framework Integration**: Easily wrap code from LangChain, LlamaIndex, or any other AI or data processing framework that users are already familiar with.

- **Simplicity First**: For users who prefer writing standard Python functions, wrapped functions provide a straightforward approach with no reduction in functionality compared to JobABC subclasses.

- **Minimal Context Dependencies**: Most transformation functions don't need access to job context data. When a job doesn't need to access inputs from predecessor jobs or task metadata, wrapped functions without the `j_ctx` parameter offer the cleanest implementation.

```python
# Example: Simple wrapped function without need for context
def process_document(document):
    # Process the document
    return {"processed_document": process_result}

# If context access is needed, use j_ctx parameter
def advanced_process(j_ctx):
    # Access task and inputs when needed
    task = j_ctx["task"]
    inputs = j_ctx["inputs"]
    return {"result": processed_data}
```

#### When to Use JobABC Subclasses

For more complex scenarios, subclassing JobABC remains fully supported and is recommended when:

- You need direct access to built-in context methods like `get_inputs()` and `get_task()`
- Your job benefits from object-oriented design principles
- You're extending existing JobABC-based code

When creating custom job classes by extending `JobABC`, follow these guidelines:

1. **Implement the `run` method**: This is the only abstract method that must be implemented. It defines the job-specific behavior.

   ```python
async def run(self, task) -> Dict[str, Any]:
    # Implement job-specific logic here using async patterns
    # Avoid blocking operations or wrap them appropriately
    result = await async_operation(task)
    return {"result": result}
```

2. **NEVER override the `_execute` method**: This method is part of the core Flow4AI execution flow and handles critical operations including job graph traversal, state management, and result propagation.

3. **Access configuration via properties**: Use `self.properties.get('property_name')` to access job configuration parameters.

4. **Return results as dictionaries**: The `run` method should always return a dictionary with the job's results.

#### Custom Job Implementation Requirements
1. Job Class Structure:
   - Must inherit from JobABC
   - Must implement the abstract `run` method (not `_execute`)
   - Constructor must accept name and properties parameters:
     ```python
     def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
         super().__init__(name, properties)
     ```

2. Method Implementation:
   - The `run` method is where job-specific logic goes:
     ```python
     async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
         # Job-specific processing logic here
         return result_dict
     ```
   - Do not override `_execute` - it's handled by JobABC for job graph processing
   - The `run` method receives task data and must return a dictionary
   - Task metadata is automatically preserved and propagated through the job graph

3. Important Notes:
   - JobABC handles job graph execution through `_execute`
   - Custom jobs only need to implement business logic in `run`
   - The `run` method is called by `_execute` with processed inputs
   - Always call super().__init__ with name and properties parameters
   - Task metadata like task_id and custom metadata fields are automatically preserved

### 2. Job Graph Management (`f4a_graph.py`)

#### Graph Validation and Manipulation
- Cycle detection in job graphs
- Cross-graph reference validation
- Head and tail node identification
- Edge addition with cycle prevention

#### Task Routing and Graph Instances
- Tasks can flow through shared graph instances
- Multiple tasks can be processed concurrently by the same graph
- Design rationale:
  - Efficient resource utilization
  - Simplified configuration
  - Natural parallel processing
- Implementation approach:
  - Tasks are queued and processed asynchronously
  - Each job in the graph can handle multiple tasks
  - State isolation is maintained at the task level
  - Results are tracked per task through the graph
- Example configuration:
  ```yaml
  processing_graph:
    read_file:
      next: [process_data]
    process_data:
      next: [save_results]
    save_results:
      next: []
  ```

Note: there can only be one head job, the starting job, and one tail job, the last job in the graph. There can be many jobs in between. The name of the entire job graph equals the name of the head job in a logical sense for workflow management purposes, not necessarily reflecting all physical implementation details.
- Multiple tasks can be submitted to the same graph:
  ```python
  # All tasks use the same graph instance
  for task in tasks:
      flowmanagerMP.submit_task(task, job_name='processing_graph__read_file')
  ```

### 3. Job Execution Engine (`flowmanagerMP.py`)

#### FlowManagerMP
- Manages parallel task execution
- Supports multiple processing modes:
  - Parallel processing
  - Serial processing
- Task queue management
- Result processing
- Multiprocessing support

#### Job Graph Loading in Multiprocessing

##### Process Synchronization Challenges
- Not all jobs are picklable, so we cannot depend on passing them between processes.
- Uses a unique approach to share job information across processes

##### Loading Mechanism in Separate Process
1. When no job map is provided, the separate process:
   - Loads job registry using specified directories
   - Reloads configuration
   - Retrieves head jobs from configuration
   - Creates a job map using job names

2. Process Synchronization Strategy
   - Uses a shared `job_name_map` to communicate job names between processes
   - Job instances are recreated in the separate process
   - Only job names are shared, not the actual job objects

##### Key Synchronization Code
```python
# In separate process (_async_worker method)
if not job_map:
    JobFactory.load_jobs_into_registry(directories)
    ConfigLoader._set_directories(directories)
    ConfigLoader.reload_configs()
    head_jobs = JobFactory.get_head_jobs_from_config()
    
    # Create job map with job names
    job_map = {job.name: job for job in head_jobs}
    
    # Update shared job name map
    job_name_map.clear()
    job_name_map.update({name: name for name in job_map.keys()})
```

### 4. Job Loading and Configuration (`job_loader.py`)

#### Job Graph Construction Workflow

##### Configuration to Job Graph Transformation
- Combines text-based configuration with dynamic job loading
- Bridges static configuration and runtime job graph creation
- Enables complex, configurable job workflows

##### Key Transformation Steps
1. Configuration Parsing
   - Read configuration files (YAML/JSON)
   - Extract job definitions and graph structures
   - Resolve parameterized job configurations

2. Dynamic Job Registry
   - Scan specified directories for job implementations
   - Dynamically load custom job classes
   - Register job types for instantiation

3. Job Graph Generation Process
   ```python
   def create_job_graph_from_config(graph_name, graph_definition):
       # Load all registered job types
       JobFactory.load_jobs_into_registry()
       
       # Create job instances for each node in the graph
       job_instances = {}
       for job_name, job_config in graph_definition.items():
           # Dynamically create job instance
           job_type = job_config.get('type')
           job_properties = job_config.get('properties', {})
           
           # Use JobFactory to instantiate job
           job = JobFactory.create_job(
               name=job_name, 
               job_type=job_type, 
               job_def={'properties': job_properties}
           )
           job_instances[job_name] = job
       
       # Create job graph with dependencies
       head_job = create_job_graph(graph_definition, job_instances)
       return head_job
   ```

##### Configuration-to-Graph Transformation Mechanisms
- Supports multiple configuration strategies:
  - Separate configuration files
  - Combined configuration files
  - Runtime job graph generation
- Enables complex, parameterized job workflows
- Provides runtime flexibility in job graph construction

##### Job Configuration Requirements
- Job configuration in jobs.yaml defines job types and their properties:
  ```yaml
  job_name:
    type: JobType  # Any name that matches a registered job class
    properties:    # Optional properties passed to job constructor
      key: value
  ```
- The type field MUST be the exact case-sensitive name of the job class.
- Properties are passed to the job's constructor during instantiation
- Jobs are dynamically loaded and registered from Python files in specified directories

##### Multiprocessing Job Graph Loading
- In `_async_worker` of FlowManagerMP:
  1. Load job registry from specified directories
  2. Reload configurations
  3. Retrieve head jobs from configuration
  4. Create job map with dynamically loaded job instances
  5. Share job names between processes

##### Key Design Principles
- Decouples job definition from job implementation
- Supports runtime job graph generation
- Enables flexible, configurable job workflows
- Maintains process isolation in multiprocessing

##### Parameter Substitution
- Replace configuration placeholders dynamically
- A new graph and graph name is generated for each param1, param2, param3, to enable tests of different LLM models in separate configurations
- The name of the parameter headings params1 etc. is arbitrary, it can be anything, it is added to the graph name.
- Example:
  ```yaml
  jobs:
    read_file:
      type: FileReader
      properties:
        filepath: $filepath  # Placeholder to be replaced
  
  parameters:
    params1:
      read_file:
        - filepath: './data1.txt'
    params2:
      read_file:
        - filepath: './data2.txt'
  ```

##### Validation and Safety
- Comprehensive configuration validation
- Cycle detection in job graphs
- Cross-reference checking
- Parameter completeness verification

### 5. Logging System (`f4a_logging.py`)

#### Advanced Logging Configuration
- Environment variable-based configuration
- Flexible logging handlers
- Debug, info, warning etc. level logging
- File and console logging support

## Execution Flow

1. Job Configuration
   - Define job types in configuration
   - Specify job graphs and dependencies
   - Configure parameter substitution

2. Job Initialization
   - Load jobs from configuration
   - Create job instances
   - Build job graph with dependencies

3. Task Submission
   - Submit tasks to FlowManagerMP
   - Tasks routed to appropriate jobs
   - Parallel or serial execution based on configuration

4. Result Processing
   - Optional result processing function
   - Supports picklable and non-picklable processors
   - Parallel or serial result handling

## Advanced Features

- OpenTelemetry Tracing
- Rate Limiting
- Flexible Job Factories
- Error Handling
- Scalable Task Processing

## Performance Characteristics

- Designed for high-concurrency environments
- Minimal overhead in task scheduling
- Supports thousands of parallel tasks
- Configurable processing modes

## Use Cases

- AI Model Inference Pipelines
- Web Scraping
- Data Processing
- Machine Learning Workflows
- Distributed Task Execution

## Example Workflow

```python
# Define a job graph for web scraping and analysis
flowmanagerMP = FlowManagerMP(
    result_processing_function=save_to_database,
    serial_processing=False
)

# Submit tasks for parallel processing
for url in urls:
    flowmanagerMP.submit_task({"url": url})

flowmanagerMP.mark_input_completed()
```

## Performance Recommendations

- Use serial processing for unpicklable result handlers
- Configure rate limits for external API calls
- Monitor system resources during execution
- Use tracing to identify bottlenecks

## Extensibility

Flow4AI is designed to be easily extended:
- Create custom job types
- Implement custom result processors
- Add new configuration loaders
- Integrate with various tracing systems

## Limitations and Considerations

- Parallel processing of results requires module level function, not inner functions.
- Performance depends on system resources
- Complex graphs may increase complexity

## Future Roadmap

- Enhanced graph visualization
- More sophisticated scheduling algorithms
- Improved error recovery mechanisms
- Cloud and distributed computing support
