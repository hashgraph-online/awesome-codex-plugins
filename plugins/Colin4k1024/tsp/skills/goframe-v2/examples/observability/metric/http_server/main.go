// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server metrics collection using GoFrame.
// It showcases how to:
// 1. Monitor HTTP server requests automatically
// 2. Track request latencies and error rates
// 3. Collect server performance metrics
// 4. Export metrics in Prometheus format
//
// The following metrics are collected automatically:
// - Request counts and durations
// - Response sizes and status codes
// - Error and panic counts
// - Server resource utilization
package main

import (
	"time"

	"go.opentelemetry.io/otel/exporters/prometheus"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/metric/otelmetric/v2"
)

// main initializes the metrics system and starts an HTTP server
// with various endpoints to demonstrate different metric collection scenarios
func main() {
	var ctx = gctx.New()

	// Configure Prometheus exporter for metrics
	// This enables the collection and export of metrics in Prometheus format
	exporter, err := prometheus.New(
		prometheus.WithoutCounterSuffixes(), // Remove counter suffixes for cleaner metric names
		prometheus.WithoutUnits(),           // Remove unit suffixes for cleaner metric names
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}

	// Initialize OpenTelemetry provider with Prometheus exporter
	// This sets up automatic collection of HTTP server metrics
	provider := otelmetric.MustProvider(
		otelmetric.WithReader(exporter),           // Configure the metrics reader
		otelmetric.WithBuiltInMetrics(),           // Enable built-in metrics collection
	)
	provider.SetAsGlobal()                         // Set as the global metrics provider
	defer provider.Shutdown(ctx)                   // Ensure clean shutdown of the provider

	// Create and configure the HTTP server
	s := g.Server()

	// Basic endpoint returning "ok"
	// Demonstrates normal request handling metrics
	s.BindHandler("/", func(r *ghttp.Request) {
		r.Response.Write("ok")
	})

	// Error endpoint that triggers a panic
	// Demonstrates error tracking and panic metrics
	s.BindHandler("/error", func(r *ghttp.Request) {
		panic("error")
	})

	// Slow endpoint with 5-second delay
	// Demonstrates latency tracking and histogram metrics
	s.BindHandler("/sleep", func(r *ghttp.Request) {
		time.Sleep(time.Second * 5)
		r.Response.Write("ok")
	})

	// Metrics endpoint for Prometheus
	// Exposes all collected metrics in Prometheus format
	s.BindHandler("/metrics", otelmetric.PrometheusHandler)

	// Configure server port
	s.SetPort(8000)

	// Start the HTTP server
	// Metrics will be automatically collected for all requests
	s.Run()
}
