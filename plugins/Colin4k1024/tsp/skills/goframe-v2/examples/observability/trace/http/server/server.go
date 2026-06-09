// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server implementation with distributed tracing.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Handle HTTP requests
// 3. Propagate trace context
// 4. Manage error handling and logging
//
// This example shows how to implement an HTTP server that traces
// all incoming requests.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/trace/otlphttp/v2"
)

// Service configuration constants
const (
	serviceName = "otlp-http-server"                    // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-hz.aliyuncs.com" // Tracing endpoint
	path        = "adapt_******_******/api/otlp/traces" // Tracing path
)

// main initializes and starts an HTTP server with tracing
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlphttp.Init(serviceName, endpoint, path)
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	// Start HTTP server
	s := g.Server()
	s.Group("/", func(group *ghttp.RouterGroup) {
		group.GET("/hello", HelloHandler)
	})
	s.SetPort(8000)
	s.Run()
}

// HelloHandler is a demo handler for tracing.
// This handler:
// 1. Creates a new trace span
// 2. Sets trace baggage
// 3. Returns a simple response
// 4. Traces the operation
func HelloHandler(r *ghttp.Request) {
	// Create a new trace span
	ctx, span := gtrace.NewSpan(r.Context(), "HelloHandler")
	defer span.End()

	// Get baggage value for tracing
	value := gtrace.GetBaggageVar(ctx, "name").String()

	// Return response
	r.Response.Write("hello:", value)
}
