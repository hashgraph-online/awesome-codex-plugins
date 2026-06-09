// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates raw gRPC client implementation in GoFrame.
// It showcases how to:
// 1. Create raw gRPC client connection
// 2. Make RPC calls
// 3. Handle responses
// 4. Use file-based registry
//
// This example shows how to implement a gRPC client without using
// the higher-level abstractions provided by GoFrame.
package main

import (
	"fmt"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gfile"

	"github.com/gogf/gf/contrib/registry/file/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	pb "main/helloworld"
)

// main initializes a raw gRPC client and makes requests
func main() {
	// Create a file registry instance
	// This will be used for service discovery
	grpcx.Resolver.Register(file.New(gfile.Temp("gsvc")))

	// Create a connection to the gRPC server
	// This configures:
	// 1. Connection options
	// 2. Registry for service discovery
	// 3. Retry policy
	var (
		ctx     = gctx.GetInitCtx()
		service = gsvc.NewServiceWithName(`hello`)
	)
	conn, err := grpc.Dial(
		fmt.Sprintf(`%s://%s`, gsvc.Schema, service.GetKey()),
		grpcx.Balancer.WithRandom(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		g.Log().Fatalf(ctx, "did not connect: %v", err)
	}
	defer conn.Close()

	// Create a new gRPC client using the connection
	// This client provides the RPC methods defined in the proto file
	client := pb.NewGreeterClient(conn)

	// Make the RPC call
	// Send a hello request with "GoFrame" as the name
	// The server will respond with a greeting message
	for i := 0; i < 10; i++ {
		res, err := client.SayHello(ctx, &pb.HelloRequest{Name: `GoFrame`})
		if err != nil {
			g.Log().Fatalf(ctx, "could not greet: %+v", err)
		}
		g.Log().Printf(ctx, "Greeting: %s", res.Message)
		time.Sleep(time.Second)
	}
}
