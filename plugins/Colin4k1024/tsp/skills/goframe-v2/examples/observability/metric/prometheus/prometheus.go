// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates direct Prometheus integration in GoFrame.
// It showcases how to:
// 1. Create and manage Prometheus metrics directly
// 2. Register metrics with Prometheus registry
// 3. Expose metrics via HTTP endpoint
// 4. Update metric values dynamically
//
// This example uses the native Prometheus client library without OpenTelemetry,
// which is simpler but provides fewer features than the OpenTelemetry integration.
package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/util/grand"
)

// Metric variables for demonstration
var (
	// metricCounter demonstrates a Counter metric type
	// Counter is a cumulative metric that can only increase or be reset to zero
	metricCounter = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "demo_counter", // Metric name in Prometheus format
			Help: "A demo counter.", // Description of the metric
		},
	)

	// metricGauge demonstrates a Gauge metric type
	// Gauge is a metric that can arbitrarily go up and down
	metricGauge = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "demo_gauge", // Metric name in Prometheus format
			Help: "A demo gauge.", // Description of the metric
		},
	)
)

// main initializes and starts an HTTP server that demonstrates
// direct Prometheus metric integration
func main() {
	// Create a new Prometheus registry
	// The registry holds all the metrics that will be exposed
	registry := prometheus.NewRegistry()

	// Register our metrics with the registry
	// This makes them available for collection
	registry.MustRegister(
		metricCounter, // Register the counter metric
		metricGauge,   // Register the gauge metric
	)

	// Create and configure the HTTP server
	s := g.Server()

	// Handler for generating fake metric values
	// Accessing this endpoint will:
	// 1. Increment the counter by 1
	// 2. Set the gauge to a random value between 1 and 100
	s.BindHandler("/", func(r *ghttp.Request) {
		metricCounter.Add(1)                         // Increment counter
		metricGauge.Set(float64(grand.N(1, 100)))   // Set random gauge value
		r.Response.Write("fake ok")
	})

	// Handler for exposing metrics
	// This endpoint exposes all registered metrics in Prometheus format
	// Access http://127.0.0.1:8000/metrics to view the metrics
	s.BindHandler("/metrics", ghttp.WrapH(promhttp.Handler()))

	// Configure and start the server
	s.SetPort(8000)
	s.Run()
}
