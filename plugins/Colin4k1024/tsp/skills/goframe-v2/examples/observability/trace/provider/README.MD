---
title: OpenTelemetry Provider Examples
slug: /examples/observability/trace/provider
keywords: [trace, provider, grpc, http, goframe]
description: Demonstrates comprehensive OpenTelemetry trace provider configurations in GoFrame including gRPC and HTTP exporters with different setup patterns. This example showcases trace provider initialization and configuration, resource attribute management for service identification, sampling strategy configuration and selection, gRPC-based and HTTP-based exporter setup and comparison, span processor configuration for batch and simple processing, and provider lifecycle management. Features include flexible provider configuration patterns, resource semantic conventions, multiple sampling strategies (always, never, parent-based, ratio-based), exporter protocol selection guidance, production-ready provider setup, and enterprise deployment patterns. Ideal for understanding OpenTelemetry provider architecture, configuring production trace pipelines, selecting appropriate exporters and samplers, optimizing trace collection performance, and building scalable observability infrastructure with proper provider configuration.
hide_title: true
---

# OpenTelemetry Provider Examples

## Description

This directory contains examples demonstrating different OpenTelemetry trace provider configurations in GoFrame applications. It includes:

1. gRPC Provider (`grpc/`)
   - Uses gRPC protocol for trace data transmission
   - Configures trace provider with gRPC exporter
   - Demonstrates resource and sampler configuration

2. HTTP Provider (`http/`)
   - Uses HTTP protocol for trace data transmission
   - Configures trace provider with HTTP exporter
   - Shows resource and sampler configuration

3. Internal Components (`internal/`)
   - Common provider initialization code
   - Shared constants and configurations
   - Utility functions for tracing setup

## Directory Structure

```
.
├── grpc/           # gRPC provider example
│   └── main.go     # gRPC provider implementation
├── http/           # HTTP provider example
│   └── main.go     # HTTP provider implementation
├── internal/       # Shared components
│   ├── consts.go   # Constants definition
│   ├── provider.go # Provider initialization
│   └── request.go  # Request utilities
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [OpenTelemetry](https://opentelemetry.io)

## Features

The examples showcase the following features:

1. Provider Configuration
   - Resource configuration
   - Sampler configuration
   - Exporter setup
   - Context propagation

2. Resource Attributes
   - Service name
   - Host information
   - Process details
   - Custom attributes

3. Sampling Strategies
   - Always sample
   - Never sample
   - Parent-based sampling
   - Trace ID ratio based sampling

4. Span Processing
   - Simple span processor
   - Batch span processor
   - Span limits configuration

## Comparison of Providers

### gRPC Provider (grpc/)
1. Features:
   - High-performance streaming
   - Bidirectional communication
   - Connection multiplexing
   - Compression support

2. Configuration:
   - gRPC endpoint
   - Authentication headers
   - Compression options
   - Connection security

3. Use Cases:
   - High-volume tracing
   - Performance-critical systems
   - Streaming trace data

### HTTP Provider (http/)
1. Features:
   - Standard HTTP protocol
   - Simple configuration
   - Firewall friendly
   - Compression support

2. Configuration:
   - HTTP endpoint
   - URL path
   - Headers configuration
   - Compression level

3. Use Cases:
   - Basic tracing needs
   - HTTP proxy environments
   - Simple deployment

## Usage

### gRPC Provider Example
1. Navigate to gRPC example:
   ```bash
   cd grpc
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

### HTTP Provider Example
1. Navigate to HTTP example:
   ```bash
   cd http
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

## Implementation Details

Both examples demonstrate:

1. Provider Setup
   - Resource configuration
   - Sampler configuration
   - Exporter initialization
   - Context management

2. Resource Configuration
   - Service identification
   - Host information
   - Process attributes
   - Custom tags

3. Sampling Configuration
   - Sampling strategy selection
   - Sampling rate configuration
   - Parent context handling

4. Error Handling
   - Connection errors
   - Export errors
   - Shutdown handling

## Troubleshooting

1. Provider Issues:
   - Check endpoint configuration
   - Verify authentication settings
   - Review connection errors
   - Check compression settings

2. Resource Issues:
   - Verify service name
   - Check host information
   - Review attribute values

3. Sampling Issues:
   - Check sampling strategy
   - Verify sampling rate
   - Review parent context

4. General Issues:
   - Check network connectivity
   - Verify dependencies
   - Review error logs
