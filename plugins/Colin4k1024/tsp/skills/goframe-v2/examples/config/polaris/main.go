// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package main demonstrates Polaris configuration center integration with GoFrame.
// It showcases how to:
// 1. Initialize Polaris configuration client
// 2. Access configuration values
// 3. Handle configuration updates
// 4. Manage configuration errors
//
// This example uses Polaris for centralized configuration management.
package main

import (
	_ "main/boot"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"
)

// main demonstrates various ways to access Polaris configuration values.
// It shows:
// 1. Configuration availability check
// 2. Bulk configuration retrieval
// 3. Single value access
func main() {
	// Initialize context for configuration operations
	var ctx = gctx.GetInitCtx()

	// Check if configuration is available and accessible
	// This verifies the connection to Polaris and configuration access
	g.Dump(g.Cfg().Available(ctx))

	// Retrieve and display all configuration key-value pairs
	// This shows all configurations stored in the specified file group
	g.Dump(g.Cfg().Data(ctx))

	// Get a specific configuration value by key
	// Here we retrieve the server address configuration
	// The configuration will be automatically updated if changed in Polaris
	g.Dump(g.Cfg().MustGet(ctx, "server.address"))
}
