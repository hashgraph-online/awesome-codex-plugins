// Copyright GoFrame gf Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client metrics collection using GoFrame.
// It showcases how to:
// 1. Monitor HTTP client requests automatically
// 2. Track request and response metrics
// 3. Collect connection-level statistics
// 4. Export metrics in Prometheus format
//
// The following metrics are collected automatically:
// - Request counts and durations
// - Response sizes and status codes
// - Connection pool statistics
// - TLS and DNS timing information
package main

import (
	"go.opentelemetry.io/otel/exporters/prometheus"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/metric/otelmetric/v2"
)

// main initializes the metrics system and demonstrates HTTP client
// metrics collection through a simple HTTP request
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
	// This sets up automatic collection of HTTP client metrics
	provider := otelmetric.MustProvider(
		otelmetric.WithReader(exporter),           // Configure the metrics reader
		otelmetric.WithBuiltInMetrics(),           // Enable built-in metrics collection
	)
	provider.SetAsGlobal()                         // Set as the global metrics provider
	defer provider.Shutdown(ctx)                   // Ensure clean shutdown of the provider

	// Perform a sample HTTP request to demonstrate metric collection
	// The following metrics will be automatically collected:
	// - Request duration
	// - Response size
	// - Status code
	// - Connection reuse
	url := `https://goframe.org`
	content := g.Client().GetContent(ctx, url)     // Make HTTP GET request
	g.Log().Infof(ctx, `content length from "%s": %d`, url, len(content))

	// Start HTTP server to expose collected metrics
	// Access metrics at http://localhost:8000/metrics
	otelmetric.StartPrometheusMetricsServer(8000, "/metrics")
}
