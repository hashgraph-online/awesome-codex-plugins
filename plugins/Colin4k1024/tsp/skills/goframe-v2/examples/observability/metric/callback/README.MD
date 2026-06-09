---
title: Callback
slug: /examples/observability/metric/callback
keywords: [metrics, callback, prometheus, opentelemetry, goframe]
description: Demonstrates callback-based metric collection in GoFrame using OpenTelemetry and Prometheus for asynchronous metric updates. This example showcases callback function registration for metrics, automatic metric value updates through callbacks, asynchronous metric observation, observable counter and gauge patterns, system resource metrics collection, and scheduled metric updates. Features include non-blocking metric collection, periodic callback execution, system metrics integration (CPU, memory, goroutines), lazy metric evaluation, automatic value refresh, and production-ready patterns. Ideal for collecting system metrics, monitoring resource usage, implementing asynchronous metric updates, reducing metric collection overhead, observing expensive-to-compute values, and building efficient monitoring systems with minimal performance impact.
hide_title: true
---

# Metric - Callback Example

## Description

This example demonstrates how to implement callback-based metric collection in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Create metrics with callback functions
- Automatically update metric values through callbacks
- Configure metric attributes
- Export metrics in `Prometheus` format

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating callback-based metrics
```

## Features

The example showcases the following features:
1. Callback-based Metrics
   - Automatic value updates
   - Custom callback functions
   - No manual update needed

2. Regular Metrics
   - Manual value updates
   - Direct control over values
   - Comparison with callback approach

3. Metric Configuration
   - Custom attributes
   - Help text
   - Units

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
   # HELP goframe_metric_demo_counter This is a simple demo for Counter usage
   goframe_metric_demo_counter{const_attr_1="1"} 11
   
   # HELP goframe_metric_demo_observable_counter This is a simple demo for ObservableCounter usage
   goframe_metric_demo_observable_counter{const_attr_3="3"} 10
   ```

## Implementation Details

The example demonstrates:
1. Creating metrics with callback functions
2. Automatic value updates through callbacks
3. Comparison between callback and manual updates
4. Proper metric configuration
5. `Prometheus` integration

## Notes

- Callbacks are executed automatically by the metrics system
- No need for manual updates of callback-based metrics
- Callbacks should be lightweight and fast
- Consider thread safety in callbacks
- Proper cleanup is handled via defer
- Default port is 8000
- Metrics endpoint is at /metrics
