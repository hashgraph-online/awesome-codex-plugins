---
title: HTTP Client
slug: /examples/observability/metric/http_client
keywords: [metrics, http client, prometheus, opentelemetry, goframe]
description: Demonstrates comprehensive HTTP client metrics collection in GoFrame using OpenTelemetry and Prometheus for monitoring outbound HTTP requests. This example showcases automatic HTTP client instrumentation, request duration histograms, request count metrics by status code and method, error rate tracking, connection pool metrics, and retry attempt monitoring. Features include automatic metric collection without code changes, detailed request/response attributes, integration with GoFrame's HTTP client, customizable metric labels, Prometheus exporter configuration, and production-ready observability patterns. Ideal for monitoring external API calls, tracking HTTP client performance, debugging connectivity issues, analyzing request patterns, and ensuring reliability of outbound HTTP communications in microservices architectures.
hide_title: true
---

# Metric - HTTP Client Example

## Description

This example demonstrates how to collect and monitor HTTP client metrics in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Monitor HTTP client requests
- Track request durations
- Collect response status codes
- Export client-side metrics

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating HTTP client metrics
```

## Features

The example showcases the following metrics:
1. Request Metrics
   - Total requests count
   - Active requests
   - Request duration
   - Request size

2. Response Metrics
   - Response status codes
   - Response size
   - Error count
   - Response duration

3. Connection Metrics
   - Connection pool stats
   - DNS lookup duration
   - TLS handshake duration

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

2. Access the metrics:
   ```bash
   # Using curl
   curl http://localhost:8000/metrics
   
   # Or open in browser
   http://localhost:8000/metrics
   ```

3. Example metrics output:
   ```text
   # HELP goframe_http_client_request_duration_seconds Duration of HTTP requests
   goframe_http_client_request_duration_seconds_bucket{method="GET",status="200",url="https://goframe.org",le="0.1"} 1
   
   # HELP goframe_http_client_requests_total Total number of HTTP requests made
   goframe_http_client_requests_total{method="GET",status="200",url="https://goframe.org"} 1
   
   # HELP goframe_http_client_response_size_bytes Size of HTTP response payloads
   goframe_http_client_response_size_bytes{method="GET",status="200",url="https://goframe.org"} 12345
   ```

## Implementation Details

The example demonstrates:
1. HTTP client configuration
2. Automatic metric collection
3. Built-in metrics integration
4. Prometheus export setup
5. Metric attribute handling

## Notes

- Metrics are collected automatically
- No manual instrumentation needed
- Built-in metrics are enabled by default
- Supports all HTTP methods
- Tracks all response codes
- Default port is 8000
- Metrics endpoint is at /metrics
- Consider security implications when exposing metrics
