// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates in-process distributed tracing implementation using gRPC.
// It showcases how to:
// 1. Configure distributed tracing with gRPC
// 2. Create and manage trace spans
// 3. Propagate trace context
// 4. Handle error cases
//
// This example shows how to implement tracing in a single process
// with multiple function calls using gRPC for trace data transmission.
package main

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/util/gutil"

	"github.com/gogf/gf/contrib/trace/otlpgrpc/v2"
)

// Service configuration constants
const (
	serviceName = "inprocess-grpc"                           // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090" // gRPC endpoint for trace collection
	traceToken  = "******_******"                            // Authentication token for trace collection
)

// main initializes gRPC tracing and demonstrates function call tracing
func main() {
	var (
		ctx           = gctx.New()
		shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
	)
	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	// Create root span for the entire process
	ctx, span := gtrace.NewSpan(ctx, "main")
	defer span.End()

	// Demonstrate tracing with existing user
	user1 := GetUser(ctx, 1)
	g.Dump(user1)

	// Demonstrate tracing with non-existent user
	user100 := GetUser(ctx, 100)
	g.Dump(user100)
}

// GetUser retrieves and returns user data by merging information from multiple sources.
// This function:
// 1. Creates a new trace span
// 2. Retrieves user information from different sources
// 3. Merges all information into a single map
// 4. Handles the case of non-existent users
// 5. Propagates trace context through gRPC
func GetUser(ctx context.Context, id int) g.Map {
	ctx, span := gtrace.NewSpan(ctx, "GetUser")
	defer span.End()

	// Merge user data from different sources
	m := g.Map{}
	gutil.MapMerge(
		m,
		GetInfo(ctx, id),    // Basic user information
		GetDetail(ctx, id),  // Detailed user information
		GetScores(ctx, id),  // User scores
	)
	return m
}

// GetInfo retrieves basic user information.
// This function:
// 1. Creates a new trace span
// 2. Returns user ID, name, and gender for ID 100
// 3. Returns nil for non-existent users
// 4. Propagates trace context through gRPC
func GetInfo(ctx context.Context, id int) g.Map {
	ctx, span := gtrace.NewSpan(ctx, "GetInfo")
	defer span.End()

	if id == 100 {
		return g.Map{
			"id":     100,
			"name":   "john",
			"gender": 1,
		}
	}
	return nil
}

// GetDetail retrieves detailed user information.
// This function:
// 1. Creates a new trace span
// 2. Returns user website and email for ID 100
// 3. Returns nil for non-existent users
// 4. Propagates trace context through gRPC
func GetDetail(ctx context.Context, id int) g.Map {
	ctx, span := gtrace.NewSpan(ctx, "GetDetail")
	defer span.End()

	if id == 100 {
		return g.Map{
			"site":  "https://goframe.org",
			"email": "john@goframe.org",
		}
	}
	return nil
}

// GetScores retrieves user academic scores.
// This function:
// 1. Creates a new trace span
// 2. Returns user scores in different subjects for ID 100
// 3. Returns nil for non-existent users
// 4. Propagates trace context through gRPC
func GetScores(ctx context.Context, id int) g.Map {
	ctx, span := gtrace.NewSpan(ctx, "GetScores")
	defer span.End()

	if id == 100 {
		return g.Map{
			"math":    100,
			"english": 60,
			"chinese": 50,
		}
	}
	return nil
}
