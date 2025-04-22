# Flow4AI Configuration

Flow4AI can be configured using environment variables to customize its behavior. This document outlines the available environment variables and their usage.

## Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `FLOW4AI_OT_CONFIG` | Path to the OpenTelemetry configuration YAML file. This file configures tracing behavior, including the exporter type (console or file) and related settings. | None |
| `FLOW4AI_LOG_LEVEL` | Sets the root logger's logging level. Valid values are: DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO |

## Usage Guide

### OpenTelemetry Configuration (FLOW4AI_OT_CONFIG)

This variable specifies the path to a YAML configuration file for OpenTelemetry tracing. The configuration file can set up either console or file-based tracing.

#### Console Tracing Example
```yaml
exporter: console
service_name: Flow4AIDemo
batch_processor:
  max_queue_size: 1000
  schedule_delay_millis: 1000
```

#### File Tracing Example
```yaml
exporter: file
service_name: Flow4AIDemo
batch_processor:
  max_queue_size: 1000
  schedule_delay_millis: 1000
file_exporter:
  path: path/to/trace_output.json
```

To use a specific configuration:
```bash
export FLOW4AI_OT_CONFIG=/path/to/your/config.yaml
python your_script.py
```

### Logging Level (FLOW4AI_LOG_LEVEL)

This variable controls the verbosity of Flow4AI's root logger. The logging level affects what messages are output to the console.

Available logging levels (in order of increasing severity):
- DEBUG: Detailed information for debugging
- INFO: General information about program execution
- WARNING: Indicate a potential problem
- ERROR: A more serious problem
- CRITICAL: A critical problem that may prevent program execution

To set the logging level:
```bash
export FLOW4AI_LOG_LEVEL=DEBUG  # For detailed debug output
# or
export FLOW4AI_LOG_LEVEL=WARNING  # For only warning and above messages
```

## Best Practices

1. **OpenTelemetry Configuration**:
   - Use console exporter during development for immediate feedback
   - Use file exporter in production for persistent trace storage
   - Consider storage implications when using file exporter

2. **Logging Level**:
   - Use DEBUG level during development and troubleshooting
   - Use INFO level for general production use
   - Use WARNING or above in production if you need to minimize log volume
