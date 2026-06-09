// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Consul configuration client.
// It handles:
// 1. Consul client configuration
// 2. Client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is imported by main to ensure Consul client is properly initialized.
package boot

import (
	"github.com/hashicorp/consul/api"
	"github.com/hashicorp/go-cleanhttp"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	consul "github.com/gogf/gf/contrib/config/consul/v2"
)

// init initializes the Consul configuration client and sets up the adapter.
// It configures:
// 1. Consul server connection
// 2. Authentication and access control
// 3. Configuration path and watching
// 4. Error handling
func init() {
	var (
		ctx = gctx.GetInitCtx()
		// Configure Consul client settings
		consulConfig = api.Config{
			Address:    "127.0.0.1:8500",    // Consul server address
			Scheme:     "http",              // Connection scheme (http/https)
			Datacenter: "dc1",               // Datacenter name
			Transport:  cleanhttp.DefaultPooledTransport(), // HTTP transport with connection pooling
			Token:      "CONSUL_ACL_TOKEN_PLACEHOLDER", // Replace with an env-provided token in real deployments
		}
		// Path in Consul's Key-Value store where configurations are stored
		configPath = "server/message"
	)

	// Create Consul adapter with configuration
	// The adapter implements gcfg.Adapter interface for configuration management
	adapter, err := consul.New(ctx, consul.Config{
		ConsulConfig: consulConfig, // Consul client configuration
		Path:         configPath,   // Configuration path in KV store
		Watch:        true,         // Enable configuration watching for updates
	})
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `New consul adapter error: %+v`, err)
	}

	// Set Consul adapter as the configuration adapter
	// This enables GoFrame to use Consul for configuration management
	g.Cfg().SetAdapter(adapter)
}
