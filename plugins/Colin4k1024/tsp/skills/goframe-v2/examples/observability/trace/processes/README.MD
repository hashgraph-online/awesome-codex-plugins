---
title: Multi-Process Example
slug: /examples/observability/trace/processes
keywords: [trace, processes, gcmd, gproc, goframe]
description: Demonstrates comprehensive distributed tracing across multiple processes using GoFrame's process management approaches including gcmd and gproc. This example showcases inter-process trace context propagation, process spawning and lifecycle management with tracing, distributed span relationships across process boundaries, trace correlation in multi-process architectures, different process communication patterns with tracing support, and integration with GoFrame's command and process components. Features include multi-process trace visibility, automatic context propagation between processes, parent-child process span relationships, process isolation with trace continuity, production-ready multi-process patterns, and enterprise architecture support. Ideal for building multi-process applications with observability, implementing distributed task processing, monitoring daemon and worker processes, ensuring trace continuity in complex process topologies, and creating scalable multi-process systems with comprehensive tracing.
hide_title: true
---

# Multi-Process Tracing Examples

## Description

This directory contains examples demonstrating distributed tracing across multiple processes using different GoFrame process management approaches. It includes:

1. Command-Line Process Management (`gcmd/`)
   - Uses `gcmd` package for process management
   - Demonstrates command-line based process creation
   - Shows trace context propagation between parent and child processes

2. Process Management (`gproc/`)
   - Uses `gproc` package for process management
   - Demonstrates programmatic process creation
   - Shows trace context propagation in process hierarchy

## Directory Structure

```
.
├── gcmd/           # Command-line process management example
│   ├── main.go     # Main process implementation
│   └── sub/        # Sub-process implementation
│       └── sub.go  # Sub-process code
├── gproc/          # Process management example
│   ├── main.go     # Main process implementation
│   └── sub/        # Sub-process implementation
│       └── sub.go  # Sub-process code
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Features

The examples showcase the following features:

1. Process Management
   - Process creation and execution
   - Command-line argument handling
   - Process communication
   - Error handling

2. Trace Context Propagation
   - Parent-child process trace linking
   - Context management across processes
   - Trace baggage handling

3. Logging and Debugging
   - Process identification
   - Debug logging
   - Error reporting

## Comparison of Approaches

### Command-Line Management (gcmd/)
1. Features:
   - Command-line interface
   - Structured command handling
   - Built-in help and documentation
   - Command hierarchy support

2. Use Cases:
   - CLI applications
   - Command-driven tools
   - Interactive applications

### Process Management (gproc/)
1. Features:
   - Programmatic process control
   - Direct process manipulation
   - Shell command execution
   - Process synchronization

2. Use Cases:
   - Background processes
   - Service management
   - Process automation

## Usage

### Command-Line Example
1. Navigate to gcmd example:
   ```bash
   cd gcmd
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

### Process Management Example
1. Navigate to gproc example:
   ```bash
   cd gproc
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

## Implementation Details

Both examples demonstrate:

1. Process Creation
   - Main process initialization
   - Sub-process spawning
   - Process environment setup

2. Context Management
   - Context creation and initialization
   - Context propagation between processes
   - Context cleanup

3. Error Handling
   - Process execution errors
   - Command execution errors
   - Graceful error reporting

## Troubleshooting

1. Process Issues:
   - Check process execution permissions
   - Verify process environment variables
   - Review process exit codes

2. Context Issues:
   - Verify context propagation
   - Check context cancellation
   - Review context deadlines

3. General Issues:
   - Check Go environment setup
   - Verify GoFrame installation
   - Review application logs
