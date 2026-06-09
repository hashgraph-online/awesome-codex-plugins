---
title: HTTP Server
slug: /examples/observability/metric/http_server
keywords: [metrics, http server, prometheus, opentelemetry, goframe]
description: Demonstrates comprehensive HTTP server metrics collection in GoFrame using OpenTelemetry and Prometheus for monitoring inbound HTTP requests. This example showcases automatic HTTP server instrumentation, request latency histograms, throughput metrics by endpoint and method, HTTP status code distribution, concurrent request tracking, and error rate monitoring. Features include automatic metric collection through middleware, detailed request attributes (path, method, status), integration with GoFrame's HTTP server, customizable metric buckets, Prometheus endpoint exposure, and production-ready monitoring patterns. Ideal for monitoring API performance, tracking service health, analyzing traffic patterns, identifying performance bottlenecks, implementing SLA monitoring, and ensuring high availability of HTTP services in production environments.
hide_title: true
---

# Metric - HTTP Server Example

## Description

This example demonstrates how to collect and monitor HTTP server metrics in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Monitor HTTP server requests
- Track request latencies
- Collect error rates
- Export server-side metrics

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating HTTP server metrics
```

## Features

The example showcases the following endpoints and metrics:
1. Endpoints
   - `/`: Basic endpoint returning "ok"
   - `/error`: Endpoint that triggers an error
   - `/sleep`: Endpoint with 5-second delay
   - `/metrics`: Prometheus metrics endpoint

2. Request Metrics
   - Total requests count
   - Active requests
   - Request duration
   - Request size

3. Response Metrics
   - Response status codes
   - Response size
   - Error count
   - Response latency

4. Server Metrics
   - Goroutine count
   - Memory usage
   - GC statistics
   - Connection stats

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame OpenTelemetry Metric](https://github.com/gogf/gf/tree/master/contrib/metric/otelmetric)

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. Test different endpoints:
   ```bash
   # Basic request
   curl http://localhost:8000/
   
   # Error request
   curl http://localhost:8000/error
   
   # Slow request
   curl http://localhost:8000/sleep
   ```

3. View metrics:
   ```bash
   # Using curl
   curl http://localhost:8000/metrics
   
   # Or open in browser
   http://localhost:8000/metrics
   ```

4. Example metrics output:
   ```text
   # HELP goframe_http_server_requests_total Total number of HTTP requests made
   goframe_http_server_requests_total{method="GET",path="/",status="200"} 1
   
   # HELP goframe_http_server_request_duration_seconds Duration of HTTP requests
   goframe_http_server_request_duration_seconds_bucket{method="GET",path="/sleep",status="200",le="5.0"} 1
   
   # HELP goframe_http_server_panics_total Total number of HTTP requests that caused a panic
   goframe_http_server_panics_total{method="GET",path="/error"} 1
   ```

## Implementation Details

The example demonstrates:
1. HTTP server setup with metrics
2. Automatic metric collection
3. Built-in metrics integration
4. Error handling and tracking
5. Latency monitoring

## Notes

- Metrics are collected automatically
- No manual instrumentation needed
- Built-in metrics are enabled by default
- Supports all HTTP methods
- Tracks all response codes
- Default port is 8000
- Metrics endpoint is at /metrics
- Consider security when exposing metrics
- High cardinality paths are normalized
