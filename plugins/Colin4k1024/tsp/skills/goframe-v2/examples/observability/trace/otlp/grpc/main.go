// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates OpenTelemetry trace data export using gRPC protocol.
// It showcases how to:
// 1. Configure gRPC-based trace export
// 2. Create and manage trace spans
// 3. Set trace baggage
// 4. Make traced HTTP requests
//
// This example uses gRPC protocol for high-performance trace data transmission.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlpgrpc/v2"
)

// Service configuration constants for gRPC-based trace export
const (
	serviceName = "otlp-grpc-client"                         // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090" // gRPC endpoint for trace collection
	traceToken  = "******_******"                            // Authentication token for gRPC connection
)

// main initializes the gRPC trace exporter and starts the application.
// It demonstrates:
// 1. gRPC trace exporter initialization
// 2. Error handling for gRPC connection
// 3. Graceful shutdown of trace export
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
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
// 4. Exports trace data using gRPC
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
