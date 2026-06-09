// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates callback-based metric collection using GoFrame.
// It showcases two approaches to metric updates:
// 1. Callback-based metrics that update automatically
// 2. Regular metrics that require manual updates
// This example helps understand when to use each approach.
package main

import (
	"context"

	"go.opentelemetry.io/otel/exporters/prometheus"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gmetric"

	"github.com/gogf/gf/contrib/metric/otelmetric/v2"
)

// Global metric variables
var (
	// meter is the global metric meter instance
	meter = gmetric.GetGlobalProvider().Meter(gmetric.MeterOption{
		Instrument:        "github.com/gogf/gf/example/metric/callback",
		InstrumentVersion: "v1.0",
	})

	// counter demonstrates a regular Counter metric type
	// This metric requires manual updates through Inc() or Add() calls
	counter = meter.MustCounter(
		"goframe.metric.demo.counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for Counter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_1", 1),
			},
		},
	)

	// This demonstrates an ObservableCounter with a callback
	// The metric value is automatically updated by the callback function
	_ = meter.MustObservableCounter(
		"goframe.metric.demo.observable_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_3", 3),
			},
			// Callback function that automatically updates the metric value
			// This is called periodically by the metrics system
			Callback: func(ctx context.Context, obs gmetric.MetricObserver) error {
				obs.Observe(10) // Always sets the value to 10
				return nil
			},
		},
	)
)

// main initializes and starts the metrics server with both
// callback-based and regular metrics demonstration
func main() {
	var ctx = gctx.New()

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

	// Demonstrate manual metric updates
	// This is required for non-callback metrics
	counter.Inc(ctx)         // Increment by 1
	counter.Add(ctx, 10)     // Add specific value

	// Start HTTP server to expose metrics
	// The callback metric will be automatically updated
	// while the regular counter retains its last set value
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
