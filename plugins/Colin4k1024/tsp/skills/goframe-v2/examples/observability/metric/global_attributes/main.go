// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates global attribute usage in metrics using GoFrame.
// It showcases how to:
// 1. Set and manage global attributes
// 2. Apply global attributes across multiple metrics
// 3. Configure attribute scope and patterns
// 4. Combine global attributes with local ones
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
	instrument = "github.com/gogf/gf/example/metric/global_attributes"
	// instrumentVersion defines the version of the metrics
	instrumentVersion = "v1.0"
)

// Global metric variables
var (
	// meter is the global metric meter instance
	meter = gmetric.GetGlobalProvider().Meter(gmetric.MeterOption{
		Instrument:        instrument,
		InstrumentVersion: instrumentVersion,
	})

	// counter demonstrates a Counter metric type with a local constant attribute
	// Global attributes will be automatically added to this metric
	counter = meter.MustCounter(
		"goframe.metric.demo.counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for Counter usage",
			Unit: "bytes",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_1", 1), // Local constant attribute
			},
		},
	)

	// observableCounter demonstrates an ObservableCounter with a local constant attribute
	// Global attributes will be automatically added to this metric
	observableCounter = meter.MustObservableCounter(
		"goframe.metric.demo.observable_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_2", 2), // Local constant attribute
			},
		},
	)
)

// main initializes and starts the metrics server demonstrating
// global attribute usage across different metric types
func main() {
	var ctx = gctx.New()

	// Configure global attributes that will be added to all matching metrics
	// These attributes will be combined with local attributes of each metric
	gmetric.SetGlobalAttributes(gmetric.Attributes{
		gmetric.NewAttribute("global_attr_1", 1), // Global attribute
	}, gmetric.SetGlobalAttributesOption{
		Instrument:        instrument,        // Only apply to metrics from this instrument
		InstrumentVersion: instrumentVersion, // Only apply to this version
		InstrumentPattern: "",               // Empty pattern means apply to all metrics
	})

	// Register callback for observable metrics
	// The global attributes will be automatically added to observations
	meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
		obs.Observe(observableCounter, 10) // Global attributes are automatically added
		return nil
	}, observableCounter)

	// Configure Prometheus exporter
	// This allows metrics to be exported in Prometheus format
	exporter, err := prometheus.New(
		prometheus.WithoutCounterSuffixes(),
		prometheus.WithoutUnits(),
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}

	// Initialize OpenTelemetry provider with Prometheus exporter
	provider := otelmetric.MustProvider(
		otelmetric.WithReader(exporter),
		otelmetric.WithBuiltInMetrics(),
	)
	provider.SetAsGlobal()
	defer provider.Shutdown(ctx)

	// Demonstrate Counter usage
	// Global attributes will be automatically added to these operations
	counter.Inc(ctx)         // Increment by 1
	counter.Add(ctx, 10)     // Add specific value

	// Start HTTP server to expose metrics
	// Metrics will show both global and local attributes
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
