// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client service discovery with Nacos in GoFrame.
// It showcases how to:
// 1. Configure Nacos client
// 2. Discover HTTP services
// 3. Make HTTP requests using service discovery
// 4. Handle service failover
//
// The client will discover and connect to the "hello.svc" service
// registered in Nacos automatically. It uses Nacos's service discovery
// mechanism to maintain an up-to-date list of service instances.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/nacos/v2"
)

// main initializes an HTTP client with Nacos service discovery
func main() {
	// Initialize Nacos client and set it as the global registry
	// This enables automatic service discovery using Nacos
	// The client will:
	// 1. Subscribe to service updates
	// 2. Maintain service list
	// 3. Handle service changes
	gsvc.SetRegistry(nacos.New(`127.0.0.1:8848`))

	var (
		ctx    = gctx.New()
		client = g.Client()
	)
	client.SetDiscovery(gsvc.GetRegistry())

	// Make an HTTP request to the service using service discovery
	// The client will:
	// 1. Discover the service using Nacos
	// 2. Load balance between instances
	// 3. Handle failover automatically
	// 4. Retry on connection failures
	res := client.GetContent(ctx, `http://hello.svc/`)

	// Log the response from the service
	g.Log().Info(ctx, res)
}
