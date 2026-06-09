// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Apollo configuration client.
// It handles:
// 1. Apollo client configuration
// 2. Client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is imported by main to ensure Apollo client is properly initialized.
package boot

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/config/apollo/v2"
)

// init initializes the Apollo configuration client and sets up the adapter.
// It configures:
// 1. Application ID and cluster
// 2. Apollo server connection
// 3. Configuration adapter
// 4. Error handling
func init() {
	var (
		ctx     = gctx.GetInitCtx()
		appId   = "SampleApp"     // Application identifier
		cluster = "default"       // Configuration cluster name
		ip      = "http://localhost:8080" // Apollo server address
	)

	// Create Apollo client with configuration
	// The client implements gcfg.Adapter interface for configuration management
	adapter, err := apollo.New(ctx, apollo.Config{
		AppID:   appId,   // Unique identifier for the application
		IP:      ip,      // Apollo server endpoint
		Cluster: cluster, // Logical partition for configurations
	})
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Set Apollo client as the configuration adapter
	// This enables GoFrame to use Apollo for configuration management
	g.Cfg().SetAdapter(adapter)
}
