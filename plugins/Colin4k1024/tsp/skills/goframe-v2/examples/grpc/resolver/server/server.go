// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC server implementation with etcd service registration.
// It showcases how to:
// 1. Configure etcd registry
// 2. Register gRPC services
// 3. Start the server
// 4. Handle service registration
//
// This example shows how to implement a gRPC server that registers
// itself with etcd for service discovery.
package main

import (
	"github.com/gogf/gf/contrib/registry/etcd/v2"
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/controller"
)

// main initializes and starts a gRPC server with etcd registration
func main() {
	// Create a new etcd registry
	// This will be used for service registration
	// The etcd endpoints are configured for local development
	grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

	// Create a new gRPC server instance
	// This configures:
	// 1. Server options
	// 2. Service registration
	// 3. Health checking
	s := grpcx.Server.New()

	// Register the Greeter service
	// This makes the service available to clients
	// The service will be registered in etcd
	controller.Register(s)

	// Start the gRPC server
	// This will:
	// 1. Register with etcd
	// 2. Start listening for requests
	// 3. Handle service health checks
	s.Run()
}
