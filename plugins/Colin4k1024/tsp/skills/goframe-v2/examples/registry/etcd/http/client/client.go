// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates HTTP client service discovery with etcd in GoFrame.
// It showcases how to:
// 1. Configure etcd client
// 2. Discover HTTP services
// 3. Make HTTP requests using service discovery
// 4. Handle service failover
//
// The client will discover and connect to the "hello.svc" service
// registered in etcd automatically. It uses etcd's watch mechanism
// to stay updated with service changes.
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
)

// main initializes an HTTP client with etcd service discovery
func main() {
	// Initialize etcd client and set it as the global registry
	// This enables automatic service discovery using etcd
	// The client will:
	// 1. Watch for service changes
	// 2. Update service endpoints
	// 3. Handle failover automatically
	gsvc.SetRegistry(etcd.New(`127.0.0.1:2379`))

	var (
		ctx    = gctx.New()
		client = g.Client()
	)
	client.SetDiscovery(gsvc.GetRegistry())

	// Make an HTTP request to the service using service discovery
	// The client will:
	// 1. Discover the service using etcd
	// 2. Load balance between available instances
	// 3. Handle failover automatically
	// 4. Retry on connection failures
	res := client.GetContent(ctx, `http://hello.svc/`)

	// Log the response from the service
	g.Log().Info(ctx, res)
}
