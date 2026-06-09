// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client service discovery with Polaris in GoFrame.
// It showcases how to:
// 1. Configure Polaris client
// 2. Discover HTTP services
// 3. Make HTTP requests using service discovery
// 4. Handle service failover
//
// The client will discover and connect to the "hello-world.svc" service
// registered in Polaris automatically. It uses Polaris's service discovery
// and load balancing features to maintain reliable connections.
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/polarismesh/polaris-go/api"
	"github.com/polarismesh/polaris-go/pkg/config"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/polaris/v2"
)

// main initializes an HTTP client with Polaris service discovery
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
	// The client will:
	// 1. Discover services
	// 2. Handle load balancing
	// 3. Manage circuit breaking
	gsvc.SetRegistry(polaris.NewWithConfig(conf, polaris.WithTTL(10)))

	client := g.Client()
	client.SetDiscovery(gsvc.GetRegistry())

	// Make 100 requests to demonstrate service discovery
	// This shows:
	// 1. Automatic service discovery
	// 2. Load balancing
	// 3. Circuit breaking
	// 4. Failover handling
	for i := 0; i < 100; i++ {
		// Create a new context for each request
		ctx := gctx.New()

		// Make an HTTP request to the service using service discovery
		// The client will:
		// 1. Discover the service using Polaris
		// 2. Load balance between instances
		// 3. Handle circuit breaking
		// 4. Retry on failures
		res, err := client.Get(ctx, `http://hello-world.svc/`)
		if err != nil {
			panic(err)
		}

		// Print the response and clean up
		fmt.Println(res.ReadAllString())
		_ = res.Close()

		// Wait before next request
		time.Sleep(time.Second)
	}
}
