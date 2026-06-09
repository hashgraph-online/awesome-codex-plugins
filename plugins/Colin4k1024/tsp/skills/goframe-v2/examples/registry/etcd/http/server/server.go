// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server registration with etcd in GoFrame.
// It showcases how to:
// 1. Configure etcd client
// 2. Register HTTP service
// 3. Handle HTTP requests
// 4. Implement TTL-based health checks
//
// The service will be registered as "hello.svc" in etcd and will be
// automatically discovered by clients using the same service name.
// The registration includes automatic lease management and health checks.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
)

// main initializes and starts an HTTP server with etcd registration
func main() {
	// Initialize etcd client and set it as the global registry
	// This enables automatic service registration with etcd
	// The registration includes:
	// 1. Service metadata
	// 2. TTL-based health check
	// 3. Automatic lease renewal
	gsvc.SetRegistry(etcd.New(`127.0.0.1:2379`))

	// Create a new HTTP server with the service name "hello.svc"
	// This name will be used by clients to discover the service
	// The service information will be stored in etcd with this name
	s := g.Server(`hello.svc`)

	// Register a simple handler for the root path
	// This handler will respond to all GET requests to "/"
	s.BindHandler("/", func(r *ghttp.Request) {
		g.Log().Info(r.Context(), `request received`) // Log incoming requests
		r.Response.Write(`Hello world`)               // Send response
	})

	// Start the HTTP server
	// The server will automatically:
	// 1. Register itself with etcd
	// 2. Create and maintain lease
	// 3. Update TTL for health check
	// 4. Handle graceful shutdown
	s.Run()
}
