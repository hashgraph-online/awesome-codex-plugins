// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package internal provides request handling utilities for OpenTelemetry tracing examples.
// It includes functions for making traced HTTP requests and demonstrating context propagation.
package internal

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"
)

// StartRequests demonstrates traced HTTP request handling.
// It shows:
// 1. Creating a new trace span
// 2. Setting trace baggage
// 3. Making HTTP requests with trace context
// 4. Logging with trace context
func StartRequests() {
	// Create new trace span for request handling
	ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
	defer span.End()

	// Set baggage value for request tracing
	ctx = gtrace.SetBaggageValue(ctx, "name", "john")

	// Make HTTP request with trace context propagation
	content := g.Client().GetContent(ctx, "http://127.0.0.1:8000/hello")

	// Log response with trace context
	g.Log().Print(ctx, content)
}
