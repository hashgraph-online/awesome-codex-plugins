---
title: HTTP Service
slug: /examples/observability/trace/http
keywords: [trace, http, goframe]
description: Demonstrates comprehensive distributed tracing implementation in HTTP services using GoFrame with OpenTelemetry integration. This example showcases HTTP request and response tracing with automatic instrumentation, trace context propagation across service boundaries, span creation and attribute management, trace data export to OpenTelemetry collectors, integration with GoFrame's HTTP server middleware, and visualization of distributed traces. Features include automatic HTTP trace instrumentation, context propagation headers, custom span attributes, parent-child span relationships, trace sampling configuration, and production-ready observability patterns. Ideal for implementing distributed tracing in microservices, monitoring HTTP service performance, debugging request flows, ensuring observability in cloud-native applications, and building production monitoring systems.
hide_title: true
---

# Tracing - HTTP Service

## Description

This example demonstrates how to implement distributed tracing in HTTP services using `GoFrame`. It shows how to:
- Configure tracing in HTTP services
- Trace HTTP requests and responses
- Propagate trace context
- Visualize distributed traces

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame OpenTelemetry Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlphttp)

## Structure

```text
.
├── client/          # Client example
│   └── client.go    # Client with tracing
├── server/          # Server example
│   └── server.go    # Server with tracing
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Features

The example showcases the following features:
1. Distributed Tracing
   - Trace propagation
   - Span management
   - Trace visualization

2. HTTP Integration
   - Request tracing
   - Context propagation
   - Error handling

## Prerequisites

1. Running `Jaeger` instance:
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

1. Start the server:
   ```bash
   cd server
   go run server.go
   ```

2. Run the client:
   ```bash
   cd client
   go run client.go
   ```

3. View traces:
   Open http://localhost:16686 in your browser to view traces in `Jaeger` UI.

## API Endpoints

The server provides the following HTTP endpoint:

1. Hello World
   ```text
   GET /hello
   Response: "Hello World"
   ```

## Implementation Details

The example demonstrates:
1. HTTP request tracing
2. Trace context propagation
3. Error handling and logging

## Troubleshooting

1. Server Issues:
   - Ensure server is running: `curl http://localhost:8000/hello`
   - Check server logs for detailed error messages

2. Tracing Issues:
   - Verify `Jaeger` is running: `docker ps | grep jaeger`
   - Check `Jaeger` UI accessibility: http://localhost:16686
   - Ensure trace endpoint is correct in configuration
