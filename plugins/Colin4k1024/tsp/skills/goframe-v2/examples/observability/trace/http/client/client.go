// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client implementation with distributed tracing.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Make traced HTTP requests
// 3. Handle trace propagation
// 4. Set trace baggage
//
// This example shows how to implement an HTTP client that traces
// all requests to the server.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlphttp/v2"
)

// Service configuration constants
const (
	serviceName = "otlp-http-client"                    // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-hz.aliyuncs.com" // Tracing endpoint
	path        = "adapt_******_******/api/otlp/traces" // Tracing path
)

// main initializes and starts an HTTP client with tracing
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
// 3. Makes HTTP requests
// 4. Handles responses and errors
func StartRequests() {
	// Create a new trace span
	ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
	defer span.End()

	// Set baggage value for tracing
	// This value will be propagated to all child spans
	ctx = gtrace.SetBaggageValue(ctx, "name", "GoFrame")

	// Make HTTP request with tracing
	response, err := g.Client().Get(ctx, "http://127.0.0.1:8000/hello")
	if err != nil {
		g.Log().Error(ctx, err)
		return
	}
	defer response.Close()

	g.Log().Info(ctx, response.ReadAllString())
}
