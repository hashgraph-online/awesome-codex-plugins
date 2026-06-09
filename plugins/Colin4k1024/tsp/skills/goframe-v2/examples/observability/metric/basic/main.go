// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates basic metric collection using GoFrame.
// It showcases various metric types including:
// - Counter: Cumulative measurements that only increase
// - UpDownCounter: Bidirectional counter that can increase and decrease
// - Histogram: Distribution of measurements
// - Observable metrics: Callback-based measurements
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
		Instrument:        "github.com/gogf/gf/example/metric/basic",
		InstrumentVersion: "v1.0",
	})

	// counter demonstrates a Counter metric type
	// Counter only increases and is typically used for counting events
	counter = meter.MustCounter(
		"goframe.metric.demo.counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for Counter usage",
			Unit: "bytes",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_1", 1),
			},
		},
	)

	// upDownCounter demonstrates an UpDownCounter metric type
	// UpDownCounter can both increase and decrease, useful for measuring varying quantities
	upDownCounter = meter.MustUpDownCounter(
		"goframe.metric.demo.updown_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for UpDownCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_2", 2),
			},
		},
	)

	// histogram demonstrates a Histogram metric type
	// Histogram tracks the distribution of measurements
	histogram = meter.MustHistogram(
		"goframe.metric.demo.histogram",
		gmetric.MetricOption{
			Help: "This is a simple demo for histogram usage",
			Unit: "ms",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_3", 3),
			},
			Buckets: []float64{0, 10, 20, 50, 100, 500, 1000, 2000, 5000, 10000},
		},
	)

	// observableCounter demonstrates an ObservableCounter metric type
	// ObservableCounter is updated through callbacks
	observableCounter = meter.MustObservableCounter(
		"goframe.metric.demo.observable_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_4", 4),
			},
		},
	)

	// observableUpDownCounter demonstrates an ObservableUpDownCounter metric type
	// Similar to UpDownCounter but updated through callbacks
	observableUpDownCounter = meter.MustObservableUpDownCounter(
		"goframe.metric.demo.observable_updown_counter",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableUpDownCounter usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_5", 5),
			},
		},
	)

	// observableGauge demonstrates an ObservableGauge metric type
	// ObservableGauge represents a current value that can go up and down
	observableGauge = meter.MustObservableGauge(
		"goframe.metric.demo.observable_gauge",
		gmetric.MetricOption{
			Help: "This is a simple demo for ObservableGauge usage",
			Unit: "%",
			Attributes: gmetric.Attributes{
				gmetric.NewAttribute("const_attr_6", 6),
			},
		},
	)
)

func main() {
	var ctx = gctx.New()

	// Register callback for observable metrics
	// This callback will be called periodically to update the observable metrics
	meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
		obs.Observe(observableCounter, 10)
		obs.Observe(observableUpDownCounter, 20)
		obs.Observe(observableGauge, 30)
		return nil
	}, observableCounter, observableUpDownCounter, observableGauge)

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
	counter.Inc(ctx)         // Increment by 1
	counter.Add(ctx, 10)     // Add specific value

	// Demonstrate UpDownCounter usage
	upDownCounter.Inc(ctx)   // Increment by 1
	upDownCounter.Add(ctx, 10) // Add specific value
	upDownCounter.Dec(ctx)   // Decrement by 1

	// Demonstrate Histogram usage
	// Record various measurements to show distribution
	histogram.Record(1)      // Very small value
	histogram.Record(20)     // Small value
	histogram.Record(30)     // Medium value
	histogram.Record(101)    // Above medium value
	histogram.Record(2000)   // Large value
	histogram.Record(9000)   // Very large value
	histogram.Record(20000)  // Extreme value

	// Start HTTP server to expose metrics
	// Metrics will be available at http://localhost:8000/metrics
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
