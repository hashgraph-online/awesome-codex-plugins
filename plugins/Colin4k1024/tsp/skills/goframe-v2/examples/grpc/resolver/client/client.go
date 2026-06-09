// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC client implementation with service discovery.
// It showcases how to:
// 1. Configure service resolver
// 2. Discover services using etcd
// 3. Make RPC calls
// 4. Handle service updates
//
// This example shows how to implement a gRPC client that discovers
// services through etcd service registry.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// main initializes a gRPC client with service discovery
func main() {
	// Create a new etcd registry
	// This will be used for service discovery
	// The etcd endpoints are configured for local development
	grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

	var (
		// Create a new context
		// This will be used for the RPC call
		ctx = gctx.New()

		// Create a connection to the service
		// This will:
		// 1. Discover the service using etcd
		// 2. Create a connection
		// 3. Handle service updates
		conn = grpcx.Client.MustNewGrpcClientConn("demo")
	)

	// Create a new gRPC client
	// This will be used to make RPC calls
	client := protobuf.NewGreeterClient(conn)

	// Make RPC calls
	// This demonstrates:
	// 1. Service discovery
	// 2. Load balancing
	// 3. Error handling
	res, err := client.SayHello(ctx, &protobuf.HelloRequest{Name: "World"})
	if err != nil {
		g.Log().Error(ctx, err)
		return
	}
	g.Log().Debug(ctx, "Response:", res.Message)
}
