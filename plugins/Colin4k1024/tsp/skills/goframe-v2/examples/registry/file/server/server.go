// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates file-based service registration in GoFrame.
// It showcases how to:
// 1. Configure file-based registry
// 2. Register HTTP service
// 3. Handle HTTP requests
// 4. Store service metadata in files
//
// The service will be registered in the local file system and will be
// automatically discovered by clients using the same registry path.
// This is suitable for development and testing environments.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gfile"

	"github.com/gogf/gf/contrib/registry/file/v2"
)

// main initializes and starts an HTTP server with file-based registration
func main() {
	// Initialize file registry in system temp directory
	// This creates a directory to store service registration information
	// The registration includes:
	// 1. Service metadata
	// 2. Service endpoints
	// 3. Basic health status
	gsvc.SetRegistry(file.New(gfile.Temp("gsvc")))

	// Create a new HTTP server with the service name "hello.svc"
	// This name will be used by clients to discover the service
	// The service information will be stored in files with this name
	s := g.Server(`hello.svc`)

	// Register a simple handler for the root path
	// This handler will respond to all GET requests to "/"
	s.BindHandler("/", func(r *ghttp.Request) {
		g.Log().Info(r.Context(), `request received`) // Log incoming requests
		r.Response.Write(`Hello world`)               // Send response
	})

	// Start the HTTP server
	// The server will automatically:
	// 1. Register itself in the file system
	// 2. Create service metadata files
	// 3. Handle graceful shutdown
	s.Run()
}
