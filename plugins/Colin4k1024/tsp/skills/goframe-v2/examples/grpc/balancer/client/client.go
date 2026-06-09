// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC client implementation with load balancing in GoFrame.
// It showcases how to:
// 1. Create gRPC client connection
// 2. Configure load balancing strategy
// 3. Make RPC calls
// 4. Handle connection failures
//
// The client demonstrates random load balancing between multiple server instances.
// It makes multiple requests to show the distribution of requests across servers.
package main

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// main initializes a gRPC client and makes requests with load balancing
func main() {
	var (
		ctx context.Context
		// Create a new gRPC client connection with random load balancing
		// This configures:
		// 1. Load balancing strategy
		// 2. Connection options
		// 3. Retry policy
		// 4. Health checking
		conn = grpcx.Client.MustNewGrpcClientConn(
			"demo",                      // Service name
			grpcx.Balancer.WithRandom(), // Use random load balancing
		)
		// Create a gRPC client using the connection
		// This client will automatically use the configured load balancer
		client = protobuf.NewGreeterClient(conn)
	)

	// Make multiple requests to demonstrate load balancing
	// Each request may be handled by a different server instance
	for i := 0; i < 10; i++ {
		// Create a new context for each request
		ctx = gctx.New()

		// Make the RPC call
		// The request will be:
		// 1. Load balanced across servers
		// 2. Automatically retried on failure
		// 3. Monitored for health
		res, err := client.SayHello(ctx, &protobuf.HelloRequest{
			Name: "World",
		})
		if err != nil {
			g.Log().Error(ctx, err)
			return
		}

		// Log the response
		// The server instance handling each request may be different
		g.Log().Debug(ctx, "Response:", res.Message)
	}
}
