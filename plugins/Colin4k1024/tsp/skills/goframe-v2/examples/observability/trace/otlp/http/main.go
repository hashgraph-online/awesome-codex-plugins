// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates OpenTelemetry trace data export using HTTP protocol.
// It showcases how to:
// 1. Configure HTTP-based trace export
// 2. Create and manage trace spans
// 3. Set trace baggage
// 4. Make traced HTTP requests
//
// This example uses HTTP protocol for simple and firewall-friendly trace data transmission.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlphttp/v2"
)

// Service configuration constants for HTTP-based trace export
const (
	serviceName = "otlp-http-client"                    // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-hz.aliyuncs.com" // HTTP endpoint for trace collection
	path        = "adapt_******_******/api/otlp/traces" // HTTP path for trace data submission
)

// main initializes the HTTP trace exporter and starts the application.
// It demonstrates:
// 1. HTTP trace exporter initialization
// 2. Error handling for HTTP connection
// 3. Graceful shutdown of trace export
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlphttp.Init(serviceName, endpoint, path)
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	StartRequests()
}

// StartRequests demonstrates traced HTTP requests.
// This function:
// 1. Creates a new trace span
// 2. Sets trace baggage
// 3. Makes an HTTP request with trace context
// 4. Exports trace data using HTTP
func StartRequests() {
	// Create new trace span
	ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
	defer span.End()

	// Set baggage value for tracing
	ctx = gtrace.SetBaggageValue(ctx, "name", "john")

	// Make HTTP request with tracing
	content := g.Client().GetContent(ctx, "http://127.0.0.1:8000/hello")
	g.Log().Print(ctx, content)
}
