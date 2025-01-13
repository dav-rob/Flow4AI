# JobChain: Scalable AI Job Scheduling and Execution Platform

## Overview

JobChain is a sophisticated Python framework designed for parallel and asynchronous job execution, with a focus on AI and data processing workflows. It provides a flexible, graph-based job scheduling system that allows complex task dependencies and parallel processing.

## Core Architectural Components

### 1. Job Abstraction (`job.py`)

#### JobABC (Abstract Base Class)
- Defines the core contract for job execution
- Key methods:
  - `run(task)`: Async method to process a task
  - `_execute(task)`: Internal method handling job lifecycle
- Supports complex job graphs with dependencies
- Implements tracing for performance monitoring

#### Key Features
- Automatic unique naming for job instances
- Support for job dependencies
- Async execution model
- Tracing and performance instrumentation

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

3. Important Notes:
   - JobABC handles job graph execution through `_execute`
   - Custom jobs only need to implement business logic in `run`
   - The `run` method is called by `_execute` with processed inputs
   - Always call super().__init__ with name and properties parameters

### 2. Job Graph Management (`jc_graph.py`)

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
  - Results are tracked per task through the chain
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
- Multiple tasks can be submitted to the same graph:
  ```python
  # All tasks use the same graph instance
  for task in tasks:
      job_chain.submit_task(task, job_name='processing_graph__read_file')
  ```

### 3. Job Execution Engine (`job_chain.py`)

#### JobChain
- Manages parallel task execution
- Supports multiple processing modes:
  - Parallel processing
  - Serial processing
- Task queue management
- Result processing
- Multiprocessing support

#### Job Graph Loading in Multiprocessing

##### Process Synchronization Challenges
- Jobs are not picklable (cannot be directly transferred between processes)
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

##### Limitations and Design Considerations
- Job recreation ensures process isolation
- Prevents direct object transfer between processes
- Maintains flexibility in job configuration
- Allows dynamic job loading at runtime

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
- The type field can be any name as long as a job class is registered with that name
- Properties are passed to the job's constructor during instantiation
- Jobs are dynamically loaded and registered from Python files in specified directories

##### Multiprocessing Job Graph Loading
- In `_async_worker` of JobChain:
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
        - filepath: './data2.txt'
  ```

##### Validation and Safety
- Comprehensive configuration validation
- Cycle detection in job graphs
- Cross-reference checking
- Parameter completeness verification

### 5. Logging System (`jc_logging.py`)

#### Advanced Logging Configuration
- Environment variable-based configuration
- Flexible logging handlers
- Debug and info level logging
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
   - Submit tasks to JobChain
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
job_chain = JobChain(
    result_processing_function=save_to_database,
    serial_processing=False
)

# Submit tasks for parallel processing
for url in urls:
    job_chain.submit_task({"url": url})

job_chain.mark_input_completed()
```

## Performance Recommendations

- Use serial processing for unpicklable result handlers
- Configure rate limits for external API calls
- Monitor system resources during execution
- Use tracing to identify bottlenecks

## Extensibility

JobChain is designed to be easily extended:
- Create custom job types
- Implement custom result processors
- Add new configuration loaders
- Integrate with various tracing systems

## Limitations and Considerations

- Requires picklable job and result processing functions
- Performance depends on system resources
- Complex graphs may increase complexity

## TODO

### Task Pass-Through Implementation
- Implement automatic task metadata preservation in JobChain core
- Currently users must manually implement task_pass_through in their jobs
- This creates error-prone boilerplate code
- Should be handled automatically by the system
- Need to modify JobABC._execute to handle metadata preservation
- Implementation plan:
  - Store original task data in JobABC._execute
  - Pass it through each job in the chain
  - Merge it with job-specific results
  - Return complete task context in final result

## Future Roadmap

- Enhanced graph visualization
- More sophisticated scheduling algorithms
- Improved error recovery mechanisms
- Cloud and distributed computing support
