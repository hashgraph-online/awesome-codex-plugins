// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC client implementation with distributed tracing.
// It showcases how to:
// 1. Configure distributed tracing
// 2. Make traced RPC calls
// 3. Handle trace propagation
// 4. Set trace baggage
//
// This example shows how to implement a gRPC client that traces
// all RPC calls to the server.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gtrace"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"
	"github.com/gogf/gf/contrib/trace/otlpgrpc/v2"

	"main/protobuf/user"
)

// Service configuration constants
const (
	serviceName = "otlp-grpc-client"                         // Name of the service for tracing
	endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090" // Tracing endpoint
	traceToken  = "******_******"                            // Token for authentication
)

// main initializes and starts a gRPC client with tracing
func main() {
	// Configure service discovery
	grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

	var (
		ctx           = gctx.New()
		shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
	)

	if err != nil {
		g.Log().Fatal(ctx, err)
	}
	defer shutdown(ctx)

	// Start making requests with tracing
	StartRequests()
}

// StartRequests demonstrates traced RPC calls.
// This function:
// 1. Creates a new trace span
// 2. Sets trace baggage
// 3. Makes RPC calls
// 4. Handles responses and errors
func StartRequests() {
	// Create a new trace span
	ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
	defer span.End()

	// Create a gRPC client
	client := user.NewUserClient(grpcx.Client.MustNewGrpcClientConn("demo"))

	// Set baggage value for tracing
	// This value will be propagated to all child spans
	ctx = gtrace.SetBaggageValue(ctx, "uid", 100)

	// Insert a new user
	// This operation will be traced
	insertRes, err := client.Insert(ctx, &user.InsertReq{
		Name: "john",
	})
	if err != nil {
		g.Log().Fatalf(ctx, `%+v`, err)
	}
	g.Log().Info(ctx, "insert id:", insertRes.Id)

	// Query the inserted user
	// This operation will be traced
	queryRes, err := client.Query(ctx, &user.QueryReq{
		Id: insertRes.Id,
	})
	if err != nil {
		g.Log().Errorf(ctx, `%+v`, err)
		return
	}
	g.Log().Info(ctx, "query result:", queryRes)

	// Delete the user
	// This operation will be traced
	if _, err = client.Delete(ctx, &user.DeleteReq{
		Id: insertRes.Id,
	}); err != nil {
		g.Log().Errorf(ctx, `%+v`, err)
		return
	}
	g.Log().Info(ctx, "delete id:", insertRes.Id)

	// Try to delete a non-existent user
	// This will generate an error that will be traced
	if _, err = client.Delete(ctx, &user.DeleteReq{
		Id: -1,
	}); err != nil {
		g.Log().Errorf(ctx, `%+v`, err)
		return
	}
	g.Log().Info(ctx, "delete id:", -1)
}
