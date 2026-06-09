---
title: Kubernetes ConfigMap
slug: /examples/config/kubecm
keywords: [config, kubernetes, configmap, goframe]
description: Demonstrates comprehensive integration of Kubernetes ConfigMap with GoFrame applications for cloud-native configuration management. This example showcases both in-pod and out-of-pod configuration setups, Kubernetes client initialization and authentication, ConfigMap access and dynamic loading, real-time configuration watching and updates, namespace and resource management, error handling and logging, and secure configuration value retrieval. Features include native Kubernetes ConfigMap integration, support for multiple deployment scenarios (in-cluster and external), automatic configuration refresh when ConfigMap changes, seamless integration with GoFrame's config component, RBAC-compliant access patterns, and production-ready error handling. Perfect for building cloud-native applications deployed on Kubernetes requiring native configuration management, GitOps workflows, and configuration-as-code practices.
hide_title: true
---

# `Kubernetes ConfigMap` Configuration Example

## Description

This directory contains an example demonstrating how to integrate `Kubernetes ConfigMap` with `GoFrame` applications for configuration management. It shows:

1. `Kubernetes` Client Configuration
   - In-Pod configuration setup
   - Out-of-Pod configuration setup
   - `ConfigMap` access and management
   - Error handling and logging

2. Configuration Management
   - Configuration loading and parsing
   - Dynamic configuration updates
   - Configuration value retrieval

## Directory Structure

```text
.
├── boot_in_pod/     # Bootstrap configuration for in-pod deployment
│   └── boot.go      # In-pod client initialization
├── boot_out_pod/    # Bootstrap configuration for out-of-pod deployment
│   └── boot.go      # Out-of-pod client initialization
├── main.go          # Main application entry
├── go.mod           # Go module file
└── go.sum           # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Kubernetes ConfigMap Config](https://github.com/gogf/gf/tree/master/contrib/config/kubecm)

## Features

The example showcases the following features:

1. `Kubernetes` Integration
   - In-Pod configuration
   - Out-of-Pod configuration
   - `ConfigMap` management
   - Error handling

2. Configuration Management
   - Configuration loading
   - Value retrieval
   - Type conversion
   - Default values

3. Dynamic Updates
   - Configuration watching
   - Change notification
   - Hot reload support

## Configuration

### `Kubernetes` Setup
1. Cluster Configuration:
   - `Kubernetes` cluster access
   - Namespace management
   - RBAC permissions

2. `ConfigMap` Setup:
   - `ConfigMap` creation
   - Data item management
   - Access control

### Client Configuration
1. In-Pod Settings:
   - Automatic service account
   - `ConfigMap` name
   - Data item name

2. Out-of-Pod Settings:
   - `KubeConfig` path
   - Namespace selection
   - Client configuration
   - Access permissions

## Usage

1. Create `ConfigMap`:
   ```bash
   # Create a ConfigMap with configuration data
   kubectl create configmap test-configmap --from-file=config.yaml=./config.yaml
   ```

2. Configure Access:
   ```bash
   # Ensure proper RBAC permissions
   kubectl create role config-reader --verb=get,list,watch --resource=configmaps
   kubectl create rolebinding config-reader-binding --role=config-reader --serviceaccount=default:default
   ```

3. Run Example:
   ```bash
   # For in-pod deployment
   go run main.go

   # For out-of-pod deployment (local development)
   KUBE_CONFIG=~/.kube/config go run main.go
   ```

## Implementation Details

1. In-Pod Setup (`boot_in_pod/boot.go`):
   - Simple configuration for in-pod deployment
   - Automatic service account usage
   - Minimal configuration required

2. Out-of-Pod Setup (`boot_out_pod/boot.go`):
   - External cluster access configuration
   - KubeConfig file usage
   - Namespace specification
   - Custom client configuration

3. Configuration Access (`main.go`):
   - Configuration availability check
   - Bulk configuration retrieval
   - Single value access
   - Error handling

## Notes

- The example supports both in-pod and out-of-pod deployments
- In-pod deployment uses the pod's service account
- Out-of-pod deployment requires KubeConfig file
- ConfigMap changes are automatically reflected
- Proper RBAC permissions are required
- Configuration paths can be customized based on needs
