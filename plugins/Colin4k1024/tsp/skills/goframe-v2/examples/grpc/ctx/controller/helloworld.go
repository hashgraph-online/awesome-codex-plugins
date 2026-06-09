// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package controller implements the gRPC service handlers with context support.
// It demonstrates how to:
// 1. Access context metadata
// 2. Process context values
// 3. Handle incoming context
// 4. Return context-aware responses
//
// The handlers show how to extract and use metadata passed through
// gRPC context from clients.
package controller

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// Controller implements the Greeter service with context handling
type Controller struct {
	protobuf.UnimplementedGreeterServer
}

// Register registers the gRPC service controller to server.
// This function:
// 1. Creates a new controller instance
// 2. Registers it with the gRPC server
// 3. Sets up context handlers
func Register(s *grpcx.GrpcServer) {
	protobuf.RegisterGreeterServer(s.Server, &Controller{})
}

// SayHello implements the SayHello RPC method with context support.
// This method:
// 1. Extracts metadata from context
// 2. Processes the request
// 3. Returns a response
// 4. Handles any errors
//
// The context contains metadata passed from the client, such as:
// - User ID
// - User name
func (s *Controller) SayHello(ctx context.Context, in *protobuf.HelloRequest) (*protobuf.HelloReply, error) {
	// Extract metadata from the incoming context
	// This includes any values set by the client
	m := grpcx.Ctx.IncomingMap(ctx)

	// Log the incoming metadata for debugging
	// This shows what data we received from the client
	g.Log().Infof(ctx, `incoming data: %v`, m.Map())

	// Create and return the response
	// The response includes a greeting with the requested name
	return &protobuf.HelloReply{
		Message: "Hello " + in.GetName(),
	}, nil
}
