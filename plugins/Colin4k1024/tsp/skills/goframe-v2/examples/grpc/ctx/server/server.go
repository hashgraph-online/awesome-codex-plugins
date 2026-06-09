// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates gRPC server implementation with context handling in GoFrame.
// It showcases how to:
// 1. Create gRPC server
// 2. Register service handlers
// 3. Process context metadata
// 4. Handle incoming context values
//
// This example shows how the server processes context metadata
// and values passed from clients through gRPC context.
package main

import (
	"github.com/gogf/gf/contrib/rpc/grpcx/v2"

	"main/controller"
)

// main initializes and starts a gRPC server with context handling
func main() {
	// Create a new gRPC server instance
	// This configures:
	// 1. Server options
	// 2. Context interceptors
	// 3. Metadata processors
	s := grpcx.Server.New()

	// Register service handlers
	// This registers:
	// 1. Service implementations
	// 2. Context handlers
	// 3. Metadata processors
	controller.Register(s)

	// Start the gRPC server
	// The server will:
	// 1. Listen on configured port
	// 2. Process incoming metadata
	// 3. Handle context values
	// 4. Manage request lifecycle
	s.Run()
}
