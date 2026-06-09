// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates dynamic attribute usage in metrics using GoFrame.
// It showcases how to:
// 1. Create metrics with constant attributes
// 2. Add dynamic attributes at runtime
// 3. Use attributes in different metric types
// 4. Combine constant and dynamic attributes
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
		Instrument:        "github.com/gogf/gf/example/metric/dynamic_attributes",
		InstrumentVersion: "v1.0",
	})

	// counter demonstrates a Counter metric type with a constant attribute
	// Additional dynamic attributes can be added when recording values
	counter = meter.MustCounter(
		"goframe.metric.demo.counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for Counter usage",
			Unit: "bytes",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_1", 1), // Constant attribute
			},
		},
	)

	// observableCounter demonstrates an ObservableCounter with a constant attribute
	// Dynamic attributes can be added in the callback function
	observableCounter = meter.MustObservableCounter(
		"goframe.metric.demo.observable_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_4", 4), // Constant attribute
			},
		},
	)
)

// main initializes and starts the metrics server demonstrating
// dynamic attribute usage in different metric types
func main() {
	var ctx = gctx.New()

	// Register callback for observable metrics
	// This demonstrates adding dynamic attributes in a callback
	meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
		obs.Observe(observableCounter, 10, gmetric.Option{
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("dynamic_attr_1", 1), // Dynamic attribute
			},
		})
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

	// Demonstrate Counter usage with dynamic attributes
	counter.Inc(ctx) // Uses only constant attributes
	counter.Add(ctx, 10, gmetric.Option{
		Attributes: gmetric.Attributes{
			gmetric.NewAttribute("dynamic_attr_2", 2), // Dynamic attribute
		},
	})

	// Start HTTP server to expose metrics
	// Metrics will show both constant and dynamic attributes
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
