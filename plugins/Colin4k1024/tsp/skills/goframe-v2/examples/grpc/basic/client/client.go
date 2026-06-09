// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates basic gRPC client implementation in GoFrame.
// It showcases how to:
// 1. Create gRPC client connection
// 2. Make RPC calls
// 3. Handle responses
// 4. Manage errors
//
// This example implements a simple client that makes hello requests
// to a Greeter service and handles the responses.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// main initializes a gRPC client and makes a request
func main() {
	var (
		// Create a new context for the request
		ctx = gctx.New()

		// Create a new gRPC client connection
		// This configures:
		// 1. Connection options
		// 2. Interceptors
		// 3. Retry policy
		conn = grpcx.Client.MustNewGrpcClientConn("demo")

		// Create a gRPC client using the connection
		// This client provides the RPC methods defined in the proto file
		client = protobuf.NewGreeterClient(conn)
	)

	// Make the RPC call
	// Send a hello request with "World" as the name
	// The server will respond with a greeting message
	res, err := client.SayHello(ctx, &protobuf.HelloRequest{
		Name: "World",
	})
	if err != nil {
		// Handle any errors that occurred during the RPC call
		g.Log().Error(ctx, err)
		return
	}

	// Log the successful response
	// The response contains the greeting message from the server
	g.Log().Debug(ctx, "Response:", res.Message)
}
