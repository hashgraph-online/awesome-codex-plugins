// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a simple HTTP server with service registration.
// It demonstrates how to:
// 1. Set up a HTTP server using GoFrame
// 2. Register the service with etcd for service discovery
// 3. Handle basic HTTP requests
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
)

func main() {
	// Initialize etcd registry with the etcd server address
	// This enables service registration and discovery
	gsvc.SetRegistry(etcd.New(`127.0.0.1:2379`))

	// Create a new server instance with service name "hello.svc"
	// The service name is used for service discovery
	s := g.Server(`hello.svc`)

	// Register a simple HTTP handler for the root path
	// This handler writes "Hello world" as response
	s.BindHandler("/", func(r *ghttp.Request) {
		// Log each received request for monitoring
		g.Log().Info(r.Context(), `request received`)
		r.Response.Write(`Hello world`)
	})

	// Start the HTTP server
	// The server will automatically register itself with etcd
	// Port can be configured via GF_SERVER_PORT environment variable
	s.Run()
}
