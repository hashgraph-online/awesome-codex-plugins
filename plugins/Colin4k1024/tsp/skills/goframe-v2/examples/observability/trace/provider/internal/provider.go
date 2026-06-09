// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package internal provides shared functionality for OpenTelemetry trace providers.
// It includes initialization functions and utility methods used by both
// gRPC and HTTP trace providers.
package internal

import (
	"context"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/trace"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gipv4"
)

// InitTracer initializes and registers `otlpgrpc` or `otlphttp` to global TracerProvider.
// It configures:
// 1. Trace provider with provided options
// 2. Global text map propagator for context propagation
// 3. Global tracer provider
//
// Returns a shutdown function that should be called when the application exits.
func InitTracer(opts ...trace.TracerProviderOption) (func(ctx context.Context), error) {
	// Create trace provider with provided options
	tracerProvider := trace.NewTracerProvider(opts...)

	// Configure global propagator for distributed tracing
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{}, // W3C Trace Context format
		propagation.Baggage{},      // W3C Baggage format
	))

	// Set global trace provider
	otel.SetTracerProvider(tracerProvider)

	// Return shutdown function
	return func(ctx context.Context) {
		// Create context with timeout for shutdown
		ctx, cancel := context.WithTimeout(ctx, time.Second)
		defer cancel()

		// Shutdown trace provider and wait for spans to be exported
		if err := tracerProvider.Shutdown(ctx); err != nil {
			g.Log().Errorf(ctx, "Shutdown tracerProvider failed err:%+v", err)
		} else {
			g.Log().Debug(ctx, "Shutdown tracerProvider success")
		}
	}, nil
}

// GetLocalIP returns the IP address of the server.
// It attempts to:
// 1. Get intranet IP addresses first
// 2. Fall back to all available IP addresses if no intranet IP is found
// 3. Return "NoHostIpFound" if no IP address is available
func GetLocalIP() (string, error) {
	// Try to get intranet IP addresses
	var intranetIPArray, err = gipv4.GetIntranetIpArray()
	if err != nil {
		return "", err
	}

	// If no intranet IP found, try to get all IP addresses
	if len(intranetIPArray) == 0 {
		if intranetIPArray, err = gipv4.GetIpArray(); err != nil {
			return "", err
		}
	}

	// Set default value if no IP found
	var hostIP = "NoHostIpFound"
	if len(intranetIPArray) > 0 {
		hostIP = intranetIPArray[0]
	}
	return hostIP, nil
}
