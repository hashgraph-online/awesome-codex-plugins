// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates raw gRPC server implementation in GoFrame.
// It showcases how to:
// 1. Create raw gRPC server
// 2. Implement service handlers
// 3. Handle RPC requests
// 4. Use file-based registry
//
// This example shows how to implement a gRPC server without using
// the higher-level abstractions provided by GoFrame.
package main

import (
	"context"
	"fmt"
	"net"

	"google.golang.org/grpc"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gipv4"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/net/gtcp"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gfile"

	"github.com/gogf/gf/contrib/registry/file/v2"

	"main/helloworld"
)

// GreetingServer implements the Greeter service
type GreetingServer struct {
	helloworld.UnimplementedGreeterServer
}

// SayHello implements the SayHello RPC method.
// This method:
// 1. Receives the request
// 2. Processes it
// 3. Returns a response
// 4. Handles any errors
func (s *GreetingServer) SayHello(ctx context.Context, in *helloworld.HelloRequest) (*helloworld.HelloReply, error) {
	// Create and return the response
	// The response includes a greeting with the requested name
	return &helloworld.HelloReply{Message: "Hello " + in.GetName()}, nil
}

// main initializes and starts a raw gRPC server
func main() {
	gsvc.SetRegistry(file.New(gfile.Temp("gsvc")))

	var (
		err     error
		ctx     = gctx.GetInitCtx()
		address = fmt.Sprintf("%s:%d", gipv4.MustGetIntranetIp(), gtcp.MustGetFreePort())
		service = &gsvc.LocalService{
			Name:      "hello",
			Endpoints: gsvc.NewEndpoints(address),
		}
	)

	// Service registry.
	_, err = gsvc.Register(ctx, service)
	if err != nil {
		panic(err)
	}
	defer func() {
		_ = gsvc.Deregister(ctx, service)
	}()

	// Server listening.
	listen, err := net.Listen("tcp", address)
	if err != nil {
		g.Log().Fatalf(ctx, "failed to listen: %v", err)
	}

	s := grpc.NewServer()
	helloworld.RegisterGreeterServer(s, &GreetingServer{})
	g.Log().Printf(ctx, "server listening at %v", listen.Addr())
	if err = s.Serve(listen); err != nil {
		g.Log().Fatalf(ctx, "failed to serve: %v", err)
	}
}
