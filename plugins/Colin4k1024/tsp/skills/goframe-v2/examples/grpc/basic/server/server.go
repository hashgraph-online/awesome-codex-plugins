// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates basic gRPC server implementation in GoFrame.
// It showcases how to:
// 1. Create gRPC server
// 2. Register service handlers
// 3. Handle RPC requests
// 4. Manage server lifecycle
//
// This example implements a simple Greeter service that responds
// to hello requests from clients.
package main

import (
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/controller"
)

// main initializes and starts a basic gRPC server
func main() {
	// Create a new gRPC server instance
	// This configures:
	// 1. Server options
	// 2. Interceptors
	// 3. Reflection service
	s := grpcx.Server.New()

	// Register service handlers
	// This registers:
	// 1. Service implementations
	// 2. Service methods
	// 3. Message types
	controller.Register(s)

	// Start the gRPC server
	// The server will:
	// 1. Listen on configured port
	// 2. Handle incoming requests
	// 3. Process RPC calls
	// 4. Handle graceful shutdown
	s.Run()
}
