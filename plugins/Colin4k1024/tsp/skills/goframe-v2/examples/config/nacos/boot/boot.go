// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Nacos configuration client.
// It handles:
// 1. Nacos client configuration
// 2. Client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is imported by main to ensure Nacos client is properly initialized.
package boot

import (
	"github.com/nacos-group/nacos-sdk-go/v2/common/constant"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/config/nacos/v2"
)

// init initializes the Nacos configuration client and sets up the adapter.
// It configures:
// 1. Server connection settings
// 2. Client cache and logging
// 3. Configuration parameters
// 4. Error handling
func init() {
	var (
		ctx = gctx.GetInitCtx()

		// Configure Nacos server connection
		// This defines how to connect to the Nacos server
		serverConfig = constant.ServerConfig{
			IpAddr: "localhost", // Nacos server address
			Port:   8848,       // Nacos server port
		}

		// Configure Nacos client settings
		// This defines local cache and logging behavior
		clientConfig = constant.ClientConfig{
			CacheDir: "/tmp/nacos", // Directory for local cache
			LogDir:   "/tmp/nacos", // Directory for log files
		}

		// Configure configuration parameters
		// This defines which configuration to retrieve
		configParam = vo.ConfigParam{
			DataId: "config.toml", // Configuration file identifier
			Group:  "test",        // Configuration group name
		}
	)

	// Create Nacos adapter with configuration
	// The adapter implements gcfg.Adapter interface for configuration management
	adapter, err := nacos.New(ctx, nacos.Config{
		ServerConfigs: []constant.ServerConfig{serverConfig}, // Server connection settings
		ClientConfig:  clientConfig,                         // Client behavior settings
		ConfigParam:   configParam,                          // Configuration retrieval settings
	})
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Set Nacos adapter as the configuration adapter
	// This enables GoFrame to use Nacos for configuration management
	g.Cfg().SetAdapter(adapter)
}
