// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a HTTP server with Polaris service registration.
// It demonstrates how to:
// 1. Set up a HTTP server using GoFrame
// 2. Configure and register the service with Polaris
// 3. Handle basic HTTP requests
// 4. Set up local cache and logging for Polaris
package main

import (
	"context"
	"os"

	"github.com/polarismesh/polaris-go/api"
	"github.com/polarismesh/polaris-go/pkg/config"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"

	"github.com/gogf/gf/contrib/registry/polaris/v2"
)

func main() {
	// Create default Polaris configuration with server address
	// This configuration includes service discovery and registry settings
	conf := config.NewDefaultConfiguration([]string{"127.0.0.1:8091"})

	// Configure local cache directory for Polaris
	// This improves performance by caching service information locally
	conf.Consumer.LocalCache.SetPersistDir(os.TempDir() + "/polaris/backup")

	// Set up logging directory for Polaris
	// This helps with debugging and monitoring
	if err := api.SetLoggersDir(os.TempDir() + "/polaris/log"); err != nil {
		g.Log().Fatal(context.Background(), err)
	}

	// Initialize Polaris registry with the configuration
	// TTL (Time To Live) is set to 10 seconds for service registration
	// The service needs to send heartbeat within this interval to maintain registration
	gsvc.SetRegistry(polaris.NewWithConfig(conf, polaris.WithTTL(10)))

	// Create a new server instance with service name "hello-world.svc"
	// The service name is used for service discovery
	s := g.Server(`hello-world.svc`)

	// Register a simple HTTP handler for the root path
	// This handler writes "Hello world" as response
	s.BindHandler("/", func(r *ghttp.Request) {
		// Log each received request for monitoring
		g.Log().Info(r.Context(), `request received`)
		r.Response.Write(`Hello world`)
	})

	// Start the HTTP server
	// The server will automatically register itself with Polaris
	// The server port will be randomly assigned if not specified
	s.Run()
}
