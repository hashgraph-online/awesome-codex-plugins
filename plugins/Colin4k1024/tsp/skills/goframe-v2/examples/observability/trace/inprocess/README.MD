---
title: In-Process Service (HTTP Exporter)
slug: /examples/observability/trace/inprocess
keywords: [trace, inprocess, goframe, otlp-http]
description: Demonstrates distributed tracing implementation in single-process applications using GoFrame with HTTP-based OpenTelemetry exporter for simplified observability. This example showcases in-process function call tracing with HTTP OTLP exporter configuration, span creation and management for internal operations, trace context propagation within a single process, HTTP-based trace data export to OpenTelemetry collectors, parent-child span relationships for nested function calls, and simplified deployment without gRPC dependencies. Features include lightweight HTTP exporter setup, automatic span instrumentation, in-memory trace context, firewall-friendly HTTP export, development-friendly configuration, and production-ready patterns. Ideal for monolithic application observability, development and testing environments, simplified trace data export, applications with HTTP-only infrastructure, and learning distributed tracing concepts.
hide_title: true
---

# Tracing - In-Process Service (HTTP Exporter)

## Description

This example demonstrates how to implement distributed tracing in in-process services using GoFrame with HTTP-based OpenTelemetry exporter. It shows how to:
- Configure tracing in a single process using HTTP exporter
- Trace function calls and operations
- Propagate trace context
- Visualize distributed traces

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame OpenTelemetry HTTP Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlphttp)

## Structure

```
.
├── main.go         # Main application with HTTP-based tracing
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Features

The example showcases the following features:
1. Distributed Tracing with HTTP Exporter
   - HTTP-based trace data transmission
   - Span management
   - Trace visualization

2. Function Call Tracing
   - Function entry/exit tracing
   - Context propagation
   - Error handling

3. Data Operations
   - User data retrieval
   - Data aggregation
   - Error handling

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

## Usage

1. Run the application:
   ```bash
   go run main.go
   ```

2. View traces:
   Open http://localhost:16686 in your browser to view traces in Jaeger UI.

## Implementation Details

The example demonstrates:

1. User Data Operations
   ```go
   GetUser(ctx, id)       // Retrieves complete user data
   ├── GetInfo(ctx, id)   // Gets basic user information
   ├── GetDetail(ctx, id) // Gets detailed user information
   └── GetScores(ctx, id) // Gets user scores
   ```

2. Trace Context Flow
   - Main function creates root span
   - Each function creates child span
   - Context propagates through function calls
   - All spans are properly ended

3. Error Handling
   - Non-existent user IDs return nil
   - Each function handles errors independently
   - Errors are traced and logged

4. HTTP-based Trace Export
   - Uses HTTP protocol for trace data transmission
   - Configures HTTP trace collector endpoint
   - Handles HTTP connection management

## Troubleshooting

1. Application Issues:
   - Check if application is running correctly
   - Verify function call outputs
   - Review error logs

2. Tracing Issues:
   - Verify Jaeger is running: `docker ps | grep jaeger`
   - Check Jaeger UI accessibility: http://localhost:16686
   - Ensure HTTP endpoint is correct in configuration

3. HTTP Export Issues:
   - Check HTTP connection status
   - Verify HTTP endpoint accessibility
   - Review HTTP error messages

## Example Output

For user ID 100:
```go
{
    "id":      100,
    "name":    "john",
    "gender":  1,
    "site":    "https://goframe.org",
    "email":   "john@goframe.org",
    "math":    100,
    "english": 60,
    "chinese": 50
}
```

For non-existent user IDs:
```go
{}
