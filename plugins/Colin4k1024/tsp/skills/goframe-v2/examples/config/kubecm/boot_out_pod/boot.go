// Copyright GoFrame Author(https://goframe.org). All Rights Reserved.
//
// This Source Code Form is subject to the terms of the MIT License.
// If a copy of the MIT was not distributed with this file,
// You can obtain one at https://github.com/gogf/gf.

// Package boot provides initialization for Kubernetes ConfigMap client outside pod.
// It handles:
// 1. Kubernetes client configuration
// 2. ConfigMap client initialization
// 3. Adapter setup
// 4. Error handling
//
// This package is used when the application runs outside a Kubernetes pod,
// such as during local development or testing.
package boot

import (
	"k8s.io/client-go/kubernetes"

	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gctx"

	"github.com/gogf/gf/contrib/config/kubecm/v2"
)

const (
	// namespace is the Kubernetes namespace where the ConfigMap is located
	namespace = "default"

	// configmapName is the name of the ConfigMap in Kubernetes
	// This ConfigMap should be created before running the application
	configmapName = "test-configmap"

	// dataItemInConfigmap is the key in the ConfigMap data field
	// that contains the configuration content
	dataItemInConfigmap = "config.yaml"

	// kubeConfigFilePathJohn is the path to the Kubernetes configuration file
	// This is used for authentication when running outside a pod
	kubeConfigFilePathJohn = `/Users/john/.kube/config`
)

// init initializes the Kubernetes ConfigMap client for out-of-pod usage.
// When running outside a pod:
// 1. Explicit Kubernetes client configuration is required
// 2. Namespace must be specified
// 3. KubeConfig file is used for authentication
func init() {
	var (
		err        error
		ctx        = gctx.GetInitCtx()
		kubeClient *kubernetes.Clientset
	)

	// Create Kubernetes client from KubeConfig file
	// This is required when running outside a pod
	// The client is used to interact with the Kubernetes API
	kubeClient, err = kubecm.NewKubeClientFromPath(ctx, kubeConfigFilePathJohn)
	if err != nil {
		// Log fatal error if client initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Create ConfigMap adapter with full configuration
	// The adapter implements gcfg.Adapter interface for configuration management
	// When running outside pod, we need to specify:
	// 1. Kubernetes client for API access
	// 2. Target namespace
	// 3. ConfigMap name and data item
	adapter, err := kubecm.New(gctx.GetInitCtx(), kubecm.Config{
		ConfigMap:  configmapName,     // Name of the ConfigMap to use
		DataItem:   dataItemInConfigmap, // Key in the ConfigMap data field
		Namespace:  namespace,         // Kubernetes namespace
		KubeClient: kubeClient,        // Kubernetes API client
	})
	if err != nil {
		// Log fatal error if adapter initialization fails
		g.Log().Fatalf(ctx, `%+v`, err)
	}

	// Set ConfigMap adapter as the configuration adapter
	// This enables GoFrame to use Kubernetes ConfigMap for configuration management
	g.Cfg().SetAdapter(adapter)
}
