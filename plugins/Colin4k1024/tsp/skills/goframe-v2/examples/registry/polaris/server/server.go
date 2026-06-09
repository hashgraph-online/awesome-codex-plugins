// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP server registration with Polaris in GoFrame.
// It showcases how to:
// 1. Configure Polaris client
// 2. Register HTTP service
// 3. Handle HTTP requests
// 4. Implement health checks
//
// The service will be registered as "hello-world.svc" in Polaris and will be
// automatically discovered by clients using the same service name.
// The registration includes metadata, health checks, and rate limiting configuration.
package main

import (
	"context"

	"github.com/polarismesh/polaris-go/api"
	"github.com/polarismesh/polaris-go/pkg/config"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
	"github.com/gogf/gf/v2/net/gsvc"

	"github.com/gogf/gf/contrib/registry/polaris/v2"
)

// main initializes and starts an HTTP server with Polaris registration
func main() {
	// Create Polaris configuration with default settings
	// This configures:
	// 1. Server address
	// 2. Local cache
	// 3. Load balancing
	// 4. Circuit breaking
	conf := config.NewDefaultConfiguration([]string{"183.47.111.80:8091"})

	// Configure local cache directory for service information
	// This improves performance and provides offline capability
	conf.Consumer.LocalCache.SetPersistDir("/tmp/polaris/backup")

	// Configure logging directory for Polaris client
	// This helps with debugging and monitoring
	if err := api.SetLoggersDir("/tmp/polaris/log"); err != nil {
		g.Log().Fatal(context.Background(), err)
	}

	// Initialize Polaris registry with configuration
	// TTL must be at least 2 seconds
	// The registration includes:
	// 1. Service metadata
	// 2. Health check configuration
	// 3. Rate limiting rules
	gsvc.SetRegistry(polaris.NewWithConfig(conf, polaris.WithTTL(10)))

	// Create a new HTTP server with the service name "hello-world.svc"
	// This name will be used by clients to discover the service
	// The service information will be stored in Polaris with this name
	s := g.Server(`hello-world.svc`)

	// Register a simple handler for the root path
	// This handler will respond to all GET requests to "/"
	s.BindHandler("/", func(r *ghttp.Request) {
		g.Log().Info(r.Context(), `request received`) // Log incoming requests
		r.Response.Write(`Hello world`)               // Send response
	})

	// Start the HTTP server
	// The server will automatically:
	// 1. Register itself with Polaris
	// 2. Configure health checks
	// 3. Set up rate limiting
	// 4. Handle graceful shutdown
	s.Run()
}
