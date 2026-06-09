// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC server implementation with load balancing in GoFrame.
// It showcases how to:
// 1. Create gRPC server
// 2. Register service handlers
// 3. Configure load balancing
// 4. Handle service health checks
package main

import (
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/controller"
)

// main initializes and starts a gRPC server with load balancing support
func main() {
	// Create a new gRPC server instance
	// This configures:
	// 1. Server options
	// 2. Interceptors
	// 3. Health service
	// 4. Reflection service
	s := grpcx.Server.New()

	// Register service handlers
	// This registers:
	// 1. Service implementations
	// 2. Health checks
	// 3. Service metadata
	controller.Register(s)

	// Start the gRPC server
	// The server will:
	// 1. Listen on configured port
	// 2. Handle incoming connections
	// 3. Process health checks
	// 4. Handle graceful shutdown
	s.Run()
}
