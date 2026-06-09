// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates file-based service discovery in GoFrame.
// It showcases how to:
// 1. Configure file-based registry client
// 2. Discover HTTP services
// 3. Make HTTP requests using service discovery
// 4. Handle basic failover
//
// The client will discover services from the local file system
// using the same registry path as the server. This approach is
// suitable for development and testing environments.
package main

import (
	"time"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"
	"github.com/gogf/gf/v2/os/gfile"

	"github.com/gogf/gf/contrib/registry/file/v2"
)

// main initializes an HTTP client with file-based service discovery
func main() {
	// Initialize file registry in system temp directory
	// This must be the same directory used by the server
	// The client will:
	// 1. Read service information from files
	// 2. Monitor file changes
	// 3. Update service endpoints
	gsvc.SetRegistry(file.New(gfile.Temp("gsvc")))

	// Create an HTTP client for making requests
	client := g.Client()
	client.SetDiscovery(gsvc.GetRegistry())

	// Make 10 requests to demonstrate service discovery
	for i := 0; i < 10; i++ {
		// Create a new context for each request
		ctx := gctx.New()

		// Make an HTTP request to the service using service discovery
		// The client will:
		// 1. Discover the service from files
		// 2. Handle basic load balancing
		// 3. Retry on failures
		res, err := client.Get(ctx, `http://hello.svc/`)
		if err != nil {
			panic(err)
		}

		// Log the response and clean up
		g.Log().Debug(ctx, res.ReadAllString())
		_ = res.Close()

		// Wait before next request
		time.Sleep(time.Second)
	}
}
