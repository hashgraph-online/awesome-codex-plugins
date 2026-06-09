// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Polaris configuration client.
// It handles:
// 1. Polaris client configuration
// 2. Client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is imported by main to ensure Polaris client is properly initialized.
package boot

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/config/polaris/v2"
)

// init initializes the Polaris configuration client and sets up the adapter.
// It configures:
// 1. Namespace and group settings
// 2. File configuration
// 3. Logging settings
// 4. Watch mode
func init() {
	var (
		ctx = gctx.GetInitCtx()

		// Configure Polaris namespace
		// This isolates configurations in different environments
		namespace = "default"

		// Configure file group and name
		// These identify the specific configuration to use
		fileGroup = "TestGroup" // Group name for the configuration
		fileName  = "config.yaml" // Configuration file name

		// Configure paths and directories
		// These specify where to find and store files
		path   = "manifest/config/polaris.yaml" // Path to Polaris configuration
		logDir = "/tmp/polaris/log" // Directory for log files
	)

	// Create Polaris adapter with configuration
	// The adapter implements gcfg.Adapter interface for configuration management
	adapter, err := polaris.New(ctx, polaris.Config{
		Namespace: namespace, // Configuration namespace
		FileGroup: fileGroup, // Configuration group
		FileName:  fileName,  // Configuration file name
		Path:      path,      // Polaris configuration path
		LogDir:    logDir,    // Log directory
		Watch:     true,      // Enable configuration watching
	})
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Set Polaris adapter as the configuration adapter
	// This enables GoFrame to use Polaris for configuration management
	g.Cfg().SetAdapter(adapter)
}
