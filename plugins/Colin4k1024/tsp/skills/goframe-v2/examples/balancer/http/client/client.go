// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main implements a HTTP client with load balancing capabilities.
// It demonstrates how to:
// 1. Set up service discovery using etcd
// 2. Configure round-robin load balancing
// 3. Make HTTP requests to distributed services
package main

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/gsel"
	"github.com/gogf/gf/v2/net/gsvc"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/registry/etcd/v2"
)

func main() {
	// Initialize etcd registry with the etcd server address
	// This enables service discovery for the client
	gsvc.SetRegistry(etcd.New(`127.0.0.1:2379`))

	// Set up round-robin load balancing strategy
	// This ensures requests are distributed evenly across available servers
	gsel.SetBuilder(gsel.NewBuilderRoundRobin())

	client := g.Client()
	client.SetDiscovery(gsvc.GetRegistry())

	// Make 10 HTTP requests to demonstrate load balancing
	// Each request will be routed to a different server instance in round-robin fashion
	for i := 0; i < 10; i++ {
		// Create a new context for each request
		ctx := gctx.New()

		// Make HTTP request to the service using its service name
		// The client automatically handles service discovery and load balancing
		res := client.GetContent(ctx, `http://hello.svc/`)

		// Log the response from the server
		g.Log().Info(ctx, res)
	}
}
