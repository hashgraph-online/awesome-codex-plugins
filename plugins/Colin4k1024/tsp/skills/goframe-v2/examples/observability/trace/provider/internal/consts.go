// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package internal provides shared constants and configurations for OpenTelemetry tracing.
// It defines service names, endpoints, and other configuration values used by both
// gRPC and HTTP trace providers.
package internal

// Constants for OpenTelemetry trace configuration
const (
	// GRPCServiceName is the service name for gRPC trace provider
	GRPCServiceName = "otlp-grpc-client"

	// Endpoint is the gRPC endpoint for trace collection
	Endpoint = "tracing-analysis-dc-bj.aliyuncs.com:8090"

	// TraceToken is the authentication token for trace collection
	TraceToken = "******_******"

	// HTTPServiceName is the service name for HTTP trace provider
	HTTPServiceName = "otlp-http-client"

	// HTTPEndpoint is the HTTP endpoint for trace collection
	HTTPEndpoint = "tracing-analysis-dc-hz.aliyuncs.com"

	// HTTPPath is the URL path for HTTP trace data submission
	HTTPPath = "adapt_******_******/api/otlp/traces"

	// TracerHostnameTagKey is the key for hostname attribute in traces
	TracerHostnameTagKey = "hostname"
)
