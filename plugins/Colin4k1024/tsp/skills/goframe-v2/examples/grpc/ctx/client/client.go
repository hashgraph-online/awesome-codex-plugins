// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC client implementation with context handling in GoFrame.
// It showcases how to:
// 1. Create gRPC client connection
// 2. Set context metadata
// 3. Make RPC calls with context
// 4. Process context values
//
// This example shows how to pass metadata and values to the server
// through gRPC context, and how to handle the responses.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// main initializes a gRPC client and makes requests with context metadata
func main() {
	var (
		// Create a new gRPC client connection
		// This configures:
		// 1. Connection options
		// 2. Context interceptors
		// 3. Metadata processors
		conn = grpcx.Client.MustNewGrpcClientConn("demo")

		// Create a gRPC client using the connection
		// This client will handle context and metadata
		client = protobuf.NewGreeterClient(conn)

		// Create a new context with metadata
		// The metadata includes:
		// 1. User ID
		// 2. User name
		// These values will be passed to the server
		ctx = grpcx.Ctx.NewOutgoing(gctx.New(), g.Map{
			"UserId":   "1000",
			"UserName": "john",
		})
	)

	// Log the outgoing metadata for debugging
	// This shows what data we're sending to the server
	g.Log().Infof(ctx, `outgoing data: %v`, grpcx.Ctx.OutgoingMap(ctx).Map())

	// Make the RPC call with context
	// The server will:
	// 1. Receive the context metadata
	// 2. Process the request
	// 3. Return a response
	res, err := client.SayHello(ctx, &protobuf.HelloRequest{
		Name: "World",
	})
	if err != nil {
		// Handle any errors that occurred during the RPC call
		g.Log().Error(ctx, err)
		return
	}

	// Log the successful response
	// The response may include server-side context values
	g.Log().Debug(ctx, "Response:", res.Message)
}
