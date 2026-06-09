---
title: Meter Attributes
slug: /examples/observability/metric/meter_attributes
keywords: [metrics, meter attributes, prometheus, opentelemetry, goframe]
description: Demonstrates meter-level attribute management in GoFrame using OpenTelemetry and Prometheus for scoped metric labeling. This example showcases meter-specific attribute configuration, attribute scoping within meters, isolated metric labeling, meter-level metadata management, attribute inheritance from meters to metrics, and fine-grained attribute control. Features include creating meters with custom attributes, scoping attributes to specific metric groups, isolated attribute namespaces, automatic attribute application to meter metrics, meter-based multi-tenancy, and production-ready patterns. Ideal for organizing metrics by module or component, implementing scoped metric labeling, managing multiple metric namespaces, isolating attributes between metric groups, building modular monitoring systems, and establishing hierarchical metric organization for complex applications.
hide_title: true
---

# Metric - Meter Attributes Example

## Description

This example demonstrates how to work with meter-level attributes in `GoFrame` using `OpenTelemetry` and `Prometheus` integration. It shows how to:
- Configure meter-level attributes
- Apply attributes across all metrics
- Combine meter and metric attributes
- Manage attribute inheritance

## Structure

```text
- `go.mod`: The Go module file for dependency management
- `go.sum`: The Go module checksums file
- `main.go`: The main application demonstrating meter attributes
```

## Features

The example showcases the following features:
1. Meter Attributes
   - Global meter configuration
   - Meter-level attributes
   - Attribute inheritance

2. Metric Types with Inherited Attributes
   - Counter with combined attributes
   - Observable Counter with combined attributes
   - Attribute precedence rules

3. Attribute Management
   - Meter attribute configuration
   - Version-based attributes
   - Attribute combination

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
   goframe_metric_demo_counter{const_attr_1="1",meter_label_1="1",meter_label_2="2"} 11
   
   # HELP goframe_metric_demo_observable_counter This is a simple demo for ObservableCounter usage
   goframe_metric_demo_observable_counter{const_attr_2="2",meter_label_1="1",meter_label_2="2"} 10
   ```

## Implementation Details

The example demonstrates:
1. Setting up meter attributes
2. Attribute inheritance rules
3. Version-based configuration
4. Attribute combination logic
5. Proper attribute scoping

## Notes

- Meter attributes apply to all metrics
- Metric attributes take precedence
- Consider attribute cardinality
- Version filtering available
- Attributes are immutable
- Default port is 8000
- Metrics endpoint is at /metrics
- Consider performance impact of many attributes
