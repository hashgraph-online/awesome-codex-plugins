---
title: Basic
slug: /examples/observability/metric/basic
keywords: [metrics, basic, prometheus, opentelemetry, goframe]
description: Demonstrates comprehensive basic metric types and their usage in GoFrame with OpenTelemetry and Prometheus integration. This example showcases counter metrics for tracking event occurrences, histogram metrics for measuring distributions, gauge metrics for current values, and UpDownCounter for bidirectional counting. Features include metric creation and registration, attribute configuration and labeling, metric value recording and observation, integration with Prometheus exporter, OpenTelemetry metric pipeline setup, and production-ready instrumentation patterns. Ideal for learning fundamental metric types, implementing application observability, monitoring service performance, building custom metrics dashboards, and establishing baseline monitoring for GoFrame applications.
hide_title: true
---

# Metric - Basic Example

## Description

This example demonstrates the basic usage of various metric types in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Create and use different types of metrics
- Configure metric attributes
- Export metrics in `Prometheus` format
- Set up a metrics endpoint

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating metric usage
```

## Features

The example showcases the following metric types:
1. Counter
   - Cumulative measurements
   - Only increases
   - Used for counting events

2. UpDownCounter
   - Bidirectional counter
   - Can increase and decrease
   - Used for measuring varying quantities

3. Histogram
   - Distribution of measurements
   - Configurable buckets
   - Used for latency/size measurements

4. Observable Metrics
   - Counter
   - UpDownCounter
   - Gauge
   - Updated via callbacks

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
   
   # HELP goframe_metric_demo_histogram This is a simple demo for histogram usage
   goframe_metric_demo_histogram_bucket{const_attr_3="3",le="0"} 0
   goframe_metric_demo_histogram_bucket{const_attr_3="3",le="10"} 1
   ...
   ```

## Implementation Details

The example demonstrates:
1. Proper metric initialization and configuration
2. Different ways to update metrics
3. Attribute handling
4. `Prometheus` integration
5. Observable metric callbacks

## Notes

- Metrics are exported in `Prometheus` format
- Default port is 8000
- Metrics endpoint is at /metrics
- All metrics include constant attributes
- Observable metrics are updated via callbacks
- Proper cleanup is handled via defer
