---
title: OpenTelemetry Example
slug: /examples/observability/trace/otlp
keywords: [trace, otlp, grpc, http, goframe]
description: Demonstrates comprehensive OpenTelemetry trace data export methods in GoFrame using OTLP protocol with both gRPC and HTTP exporters. This example showcases OTLP (OpenTelemetry Protocol) configuration for trace export, gRPC and HTTP exporter setup and comparison, trace data serialization and transmission, connection management and retry logic, batch processing and performance optimization, and integration with OpenTelemetry collectors. Features include flexible exporter configuration, efficient trace data transmission, automatic batching and compression, error handling and retry mechanisms, production-ready export patterns, and protocol selection guidance. Ideal for implementing production trace export, choosing appropriate export protocols, optimizing trace data transmission, ensuring reliable trace delivery, and building enterprise observability infrastructure with OpenTelemetry standard compliance.
hide_title: true
---

# OpenTelemetry Tracing Examples

## Description

This directory contains examples demonstrating different methods of exporting OpenTelemetry trace data in GoFrame applications. It includes:

1. gRPC-based Export (`grpc/`)
   - Uses gRPC protocol for trace data transmission
   - Suitable for high-performance, streaming trace data export
   - Supports bidirectional streaming and connection multiplexing

2. HTTP-based Export (`http/`)
   - Uses HTTP protocol for trace data transmission
   - Suitable for environments with HTTP proxy or firewall restrictions
   - Simpler to configure and debug

## Directory Structure

```
.
├── grpc/           # gRPC-based tracing example
│   └── main.go     # gRPC trace exporter implementation
├── http/           # HTTP-based tracing example
│   └── main.go     # HTTP trace exporter implementation
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame OpenTelemetry gRPC Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlpgrpc)
- [GoFrame OpenTelemetry HTTP Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlphttp)

## Prerequisites

1. Running Jaeger instance:
   ```bash
   docker run --rm --name jaeger \
   -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
   -p 6831:6831/udp \
   -p 6832:6832/udp \
   -p 5778:5778 \
   -p 16686:16686 \
   -p 4317:4317 \
   -p 4318:4318 \
   -p 14250:14250 \
   -p 14268:14268 \
   -p 14269:14269 \
   -p 9411:9411 \
   jaegertracing/all-in-one:1.55
   ```

## Comparison of Export Methods

### gRPC Export (grpc/)
1. Advantages:
   - Higher performance
   - Bidirectional streaming
   - Connection multiplexing
   - Better for high-volume tracing

2. Configuration:
   - Requires gRPC endpoint
   - Supports authentication token
   - Configurable connection settings

3. Use Cases:
   - High-volume trace data
   - Microservices architecture
   - Performance-critical systems

### HTTP Export (http/)
1. Advantages:
   - Simpler setup
   - Works through HTTP proxies
   - Easier to debug
   - Better firewall compatibility

2. Configuration:
   - Requires HTTP endpoint
   - Supports path configuration
   - Standard HTTP settings

3. Use Cases:
   - Environments with HTTP proxy
   - Simpler deployment requirements
   - Development and testing

## Usage

### gRPC Export Example
1. Navigate to gRPC example:
   ```bash
   cd grpc
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

### HTTP Export Example
1. Navigate to HTTP example:
   ```bash
   cd http
   ```

2. Run the example:
   ```bash
   go run main.go
   ```

3. View traces:
   Open http://localhost:16686 in your browser to view traces in Jaeger UI.

## Implementation Details

Both examples demonstrate:
1. Trace Context Management
   - Span creation and management
   - Context propagation
   - Baggage handling

2. Error Handling
   - Connection error handling
   - Export error handling
   - Graceful shutdown

3. Configuration
   - Service name configuration
   - Endpoint configuration
   - Authentication setup

## Troubleshooting

1. gRPC Export Issues:
   - Check gRPC endpoint accessibility
   - Verify authentication token
   - Review gRPC connection logs

2. HTTP Export Issues:
   - Check HTTP endpoint accessibility
   - Verify path configuration
   - Review HTTP response codes

3. General Issues:
   - Verify Jaeger is running
   - Check network connectivity
   - Review application logs
