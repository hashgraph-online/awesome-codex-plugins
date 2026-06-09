---
title: Dynamic Attributes
slug: /examples/observability/metric/dynamic_attributes
keywords: [metrics, dynamic attributes, prometheus, opentelemetry, goframe]
description: Demonstrates dynamic metric attribute management in GoFrame using OpenTelemetry and Prometheus for runtime attribute updates. This example showcases runtime attribute modification, context-based attribute injection, request-scoped metric labeling, dynamic attribute value resolution, per-request metric customization, and flexible labeling patterns. Features include updating attributes during metric recording, extracting attributes from request context, injecting user/tenant/session IDs, dynamic label value computation, attribute value caching, and production-ready patterns. Ideal for implementing per-request metric labeling, tracking user-specific metrics, supporting multi-tenancy, enriching metrics with runtime context, analyzing behavior by dynamic dimensions, and building flexible monitoring systems that adapt to application state.
hide_title: true
---

# Metric - Dynamic Attributes Example

## Description

This example demonstrates how to work with dynamic metric attributes in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Add dynamic attributes to metrics at runtime
- Combine constant and dynamic attributes
- Use attributes in both regular and observable metrics
- Export metrics with dynamic attributes

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating dynamic metric attributes
```

## Features

The example showcases the following features:
1. Dynamic Attributes
   - Runtime attribute assignment
   - Attribute combination
   - Value-based attributes

2. Metric Types with Attributes
   - Counter with dynamic attributes
   - Observable Counter with dynamic attributes
   - Constant attribute baseline

3. Attribute Management
   - Attribute creation
   - Value typing
   - Attribute scoping

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
   goframe_metric_demo_counter{const_attr_1="1",dynamic_attr_2="2"} 11
   
   # HELP goframe_metric_demo_observable_counter This is a simple demo for ObservableCounter usage
   goframe_metric_demo_observable_counter{const_attr_4="4",dynamic_attr_1="1"} 10
   ```

## Implementation Details

The example demonstrates:
1. Creating metrics with constant attributes
2. Adding dynamic attributes at runtime
3. Combining different attribute types
4. Attribute scoping and inheritance
5. Proper attribute value typing

## Notes

- Dynamic attributes are added per observation
- Constant attributes are always present
- Attributes can be of various types
- Consider cardinality when using dynamic attributes
- High cardinality can impact performance
- Default port is 8000
- Metrics endpoint is at /metrics
