# Flow4AI Glossary

This document defines key terminology used throughout the Flow4AI platform documentation and codebase.

## Core Concepts

### Flow4AI
A sophisticated Python framework designed for parallel and asynchronous job execution, with a focus on AI and data processing workflows. Flow4AI provides a flexible, graph-based job scheduling system that enables complex task dependencies and parallel processing.

### Job Graph
The complete workflow of interconnected jobs that defines the execution flow. Job graphs represent the directed acyclic graph (DAG) of execution units where each node is a `JobABC` instance, often wrapping functions from LangChain, LlamaIndex, or other AI and data processing frameworks. While "workflow" describes the higher-level business process being automated, "job graph" specifically refers to the technical implementation of execution flow.

### DSL (Domain Specific Language)
A Python-based interface for defining workflow configurations programmatically. The DSL allows developers to construct job graphs using intuitive syntax and object-oriented patterns.

### Workflow Configuration
A declarative representation of job graphs using YAML or JSON files. These configurations provide an alternative to the DSL approach, allowing workflows to be defined, stored, and version-controlled in a human-readable format.

### Job
A single execution unit in the workflow that inherits from `JobABC`. Each job takes inputs from preceding jobs and passes its output to subsequent jobs in the job graph. Jobs encapsulate discrete processing logic and maintain isolation between task executions.

### Head Job
The entry point or starting job in a job graph. If multiple starting jobs are defined, a `DefaultHeadJob` is automatically added to serve as a single entry point. The name of the entire job graph equals the name of the head job.

### Tail Job
The final job in a job graph that produces the ultimate result. This job's output is returned by default as the final result of workflow execution. If multiple endpoints exist in the graph, a default tail job is created to consolidate results from all terminal jobs.

### Short Job Name
The simplified identifier used for referencing jobs within a workflow. This is the name assigned to a job in the `wrap()` function when using the DSL, or in the job definition when using YAML configuration files.

### FQ_Name (Fully Qualified Name)
An expanded job name created by the workflow engine to prevent naming collisions across job graphs. The format follows `graph_name$$param_name$$job_name$$`, providing a unique identifier for each job in the system.  Indices are added to the param_name to prevent collisions.

## Operational Components

### Task
A dictionary subclass with a unique identifier that represents a unit of work to be processed by a job graph. Tasks contain input parameters and maintain metadata throughout execution. Tasks are units of work (data + metadata) that flow through the job graph, while jobs are the processing units that operate on tasks. This distinction is fundamental to understanding the Flow4AI execution model.

### FlowManager
A singleton class that manages job graphs and tasks. The FlowManager maintains internal state about job graphs, tasks, and results, and provides methods for submission, waiting, and result collection.

### FlowManagerMP
A multiprocessing implementation of FlowManager that enables parallel task execution across multiple processes.

### JobABC
The abstract base class that defines the core contract for job execution. All custom jobs must inherit from this class and implement the required `run` method.

### WrappingJob
A specialized job implementation that wraps regular Python functions, enabling them to be integrated into Flow4AI job graphs without creating custom `JobABC` subclasses.

## Technical Patterns

### Job Context (j_ctx)
A special parameter used in wrapped functions to access task data, inputs from predecessor jobs, and other contextual information required for execution.

### get_inputs()
A method available in `JobABC` subclasses that provides access to inputs from predecessor jobs, returning a dictionary with short job names as keys.

## Recommended Practices and Clarifications

While the architecture documents provide a solid foundation for understanding Flow4AI, the following clarification may help address a potential area of confusion:

**Job Execution Paradigms**: The distinction between `JobABC` subclasses and wrapped functions represents two different programming paradigms (object-oriented vs. functional) that achieve the same goal. Understanding when to use each approach can help developers make appropriate design decisions.
