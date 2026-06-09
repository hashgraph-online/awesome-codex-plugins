// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server registration with Nacos in GoFrame.
// It showcases how to:
// 1. Configure Nacos client
// 2. Register HTTP service
// 3. Handle HTTP requests
// 4. Implement health checks
//
// The service will be registered as "hello.svc" in Nacos and will be
// automatically discovered by clients using the same service name.
// The registration includes metadata and health check configuration.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"

	"github.com/gogf/gf/contrib/registry/nacos/v2"
)

// main initializes and starts an HTTP server with Nacos registration
func main() {
	// Initialize Nacos client and set it as the global registry
	// This enables automatic service registration with Nacos
	// The registration includes:
	// 1. Service metadata
	// 2. Health check configuration
	// 3. Namespace and group info
	gsvc.SetRegistry(nacos.New(`127.0.0.1:8848`))

	// Create a new HTTP server with the service name "hello.svc"
	// This name will be used by clients to discover the service
	// The service information will be stored in Nacos with this name
	s := g.Server(`hello.svc`)

	// Register a simple handler for the root path
	// This handler will respond to all GET requests to "/"
	s.BindHandler("/", func(r *ghttp.Request) {
		g.Log().Info(r.Context(), `request received`) // Log incoming requests
		r.Response.Write(`Hello world`)               // Send response
	})

	// Start the HTTP server
	// The server will automatically:
	// 1. Register itself with Nacos
	// 2. Configure health checks
	// 3. Update service status
	// 4. Handle graceful shutdown
	s.Run()
}
