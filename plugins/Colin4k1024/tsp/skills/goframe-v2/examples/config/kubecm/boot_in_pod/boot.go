// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Kubernetes ConfigMap client in pod.
// It handles:
// 1. ConfigMap client configuration
// 2. Client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is used when the application runs inside a Kubernetes pod.
package boot

import (
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/config/kubecm/v2"
)

const (
	// configmapName is the name of the ConfigMap in Kubernetes
	// This ConfigMap should be created before running the application
	configmapName = "test-configmap"

	// dataItemInConfigmap is the key in the ConfigMap data field
	// that contains the configuration content
	dataItemInConfigmap = "config.yaml"
)

// init initializes the Kubernetes ConfigMap client for in-pod usage.
// When running in a pod:
// 1. Service account is automatically used for authentication
// 2. Namespace is automatically detected
// 3. No explicit Kubernetes client is needed
func init() {
	var (
		err error
		ctx = gctx.GetInitCtx()
	)

	// Create ConfigMap adapter with minimal configuration
	// The adapter implements gcfg.Adapter interface for configuration management
	// When running in pod, it automatically:
	// 1. Uses the pod's service account for authentication
	// 2. Detects the current namespace
	// 3. Sets up the Kubernetes client
	adapter, err := kubecm.New(gctx.GetInitCtx(), kubecm.Config{
		ConfigMap: configmapName,     // Name of the ConfigMap to use
		DataItem:  dataItemInConfigmap, // Key in the ConfigMap data field
	})
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Set ConfigMap adapter as the configuration adapter
	// This enables GoFrame to use Kubernetes ConfigMap for configuration management
	g.Cfg().SetAdapter(adapter)
}
