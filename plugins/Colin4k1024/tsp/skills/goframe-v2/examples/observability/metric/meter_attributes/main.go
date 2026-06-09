// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates meter-level attribute usage in metrics using GoFrame.
// It showcases how to:
// 1. Configure meter-level attributes
// 2. Apply attributes across all metrics
// 3. Combine meter and metric attributes
// 4. Manage attribute inheritance
//
// The following concepts are demonstrated:
// - Meter attributes that apply to all metrics
// - Metric-specific attributes
// - Attribute inheritance and precedence
package main

import (
	"context"

	"go.opentelemetry.io/otel/exporters/prometheus"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gmetric"

	"github.com/gogf/gf/contrib/metric/otelmetric/v2"
)

// Constants for metric configuration
const (
	// instrument is the unique identifier for this metric collection
	instrument = "github.com/gogf/gf/example/metric/meter_attributes"
	// instrumentVersion defines the version of the metrics
	instrumentVersion = "v1.0"
)

// Global metric variables
var (
	// meter is the global metric meter instance with meter-level attributes
	// These attributes will be automatically added to all metrics created by this meter
	meter = gmetric.GetGlobalProvider().Meter(gmetric.MeterOption{
		Instrument:        instrument,
		InstrumentVersion: instrumentVersion,
		Attributes: gmetric.Attributes{
			gmetric.NewAttribute("meter_label_1", 1), // Meter-level attribute
			gmetric.NewAttribute("meter_label_2", 2), // Meter-level attribute
		},
	})

	// counter demonstrates a Counter metric type with both meter and metric attributes
	// The final metric will have both meter-level and metric-specific attributes
	counter = meter.MustCounter(
		"goframe.metric.demo.counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for Counter usage",
			Unit: "bytes",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_1", 1), // Metric-specific attribute
			},
		},
	)

	// observableCounter demonstrates an ObservableCounter with combined attributes
	// The final metric will include both meter-level and metric-specific attributes
	observableCounter = meter.MustObservableCounter(
		"goframe.metric.demo.observable_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_2", 2), // Metric-specific attribute
			},
		},
	)
)

// main initializes the metrics system and demonstrates
// meter-level attribute inheritance across different metric types
func main() {
	var ctx = gctx.New()

	// Register callback for observable metrics
	// The callback will automatically include meter-level attributes
	meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
		obs.Observe(observableCounter, 10) // Inherits meter attributes
		return nil
	}, observableCounter)

	// Configure Prometheus exporter
	// This allows metrics to be exported in Prometheus format
	exporter, err := prometheus.New(
		prometheus.WithoutCounterSuffixes(), // Remove counter suffixes for cleaner metric names
		prometheus.WithoutUnits(),           // Remove unit suffixes for cleaner metric names
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}

	// Initialize OpenTelemetry provider with Prometheus exporter
	provider := otelmetric.MustProvider(
		otelmetric.WithReader(exporter),           // Configure the metrics reader
		otelmetric.WithBuiltInMetrics(),           // Enable built-in metrics collection
	)
	provider.SetAsGlobal()                         // Set as the global metrics provider
	defer provider.Shutdown(ctx)                   // Ensure clean shutdown of the provider

	// Demonstrate Counter usage
	// All operations will include meter-level attributes
	counter.Inc(ctx)         // Increment by 1
	counter.Add(ctx, 10)     // Add specific value

	// Start HTTP server to expose metrics
	// Metrics will show both meter-level and metric-specific attributes
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
