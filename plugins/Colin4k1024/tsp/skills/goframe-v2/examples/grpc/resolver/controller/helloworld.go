// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package controller implements the gRPC service handlers.
// It showcases how to:
// 1. Implement service interfaces
// 2. Handle RPC requests
// 3. Process requests
// 4. Return responses
//
// This example shows how to implement a simple Greeter service
// that can be discovered through etcd.
package controller

import (
	"context"

	"github.com/gogf/gf/v2/frame/g"

	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/protobuf"
)

// Controller implements the Greeter service
type Controller struct {
	protobuf.UnimplementedGreeterServer
}

// Register registers the service controller with the gRPC server.
// This function:
// 1. Creates a new controller instance
// 2. Registers it with the server
// 3. Sets up service handlers
func Register(s *grpcx.GrpcServer) {
	protobuf.RegisterGreeterServer(s.Server, &Controller{})
}

// SayHello implements the SayHello RPC method.
// This method:
// 1. Receives the request
// 2. Processes it
// 3. Returns a response
// 4. Handles any errors
//
// The method demonstrates basic request handling and
// response generation in a gRPC service.
func (s *Controller) SayHello(ctx context.Context, in *protobuf.HelloRequest) (*protobuf.HelloReply, error) {
	// Log the incoming request
	// This helps with debugging and monitoring
	g.Log().Debugf(ctx, `received user name: %s`, in.Name)

	// Create and return the response
	// The response includes a greeting with the requested name
	return &protobuf.HelloReply{
		Message: "Hello " + in.GetName(),
	}, nil
}
