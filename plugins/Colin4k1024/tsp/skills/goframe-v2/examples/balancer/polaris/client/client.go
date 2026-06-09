// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a HTTP client with Polaris service discovery and load balancing.
// It demonstrates how to:
// 1. Set up service discovery using Polaris
// 2. Configure round-robin load balancing
// 3. Make HTTP requests to distributed services
// 4. Set up local cache and logging for better performance and debugging
package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/polarismesh/polaris-go/api"
	"github.com/polarismesh/polaris-go/pkg/config"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsel"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/polaris/v2"
)

func main() {
	// Create default Polaris configuration with server address
	// This configuration includes service discovery settings
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
	// TTL is set to 10 seconds to match the server configuration
	gsvc.SetRegistry(polaris.NewWithConfig(conf, polaris.WithTTL(10)))

	// Set up round-robin load balancing strategy
	// This ensures requests are distributed evenly across available servers
	gsel.SetBuilder(gsel.NewBuilderRoundRobin())

	client := g.Client()
	client.SetDiscovery(gsvc.GetRegistry())

	// Make 100 HTTP requests to demonstrate load balancing
	// Each request will be routed to a different server instance in round-robin fashion
	for i := 0; i < 100; i++ {
		// Make HTTP request to the service using its service name
		// The client automatically handles service discovery and load balancing
		res, err := g.Client().Get(gctx.New(), `http://hello-world.svc/`)
		if err != nil {
			panic(err)
		}

		// Print response details including:
		// - Response content
		// - Request ID
		// - Current timestamp
		// - HTTP status code
		fmt.Println(res.ReadAllString(), " id: ", i,
			" time: ", time.Now().Format("2006-01-02 15:04:05"),
			" code: ", res.StatusCode)

		// Close the response body to prevent resource leaks
		_ = res.Close()

		// Wait for 1 second before next request
		// This helps to demonstrate the load balancing effect
		time.Sleep(time.Second)
	}
}
