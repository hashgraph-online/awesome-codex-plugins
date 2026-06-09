---
title: Kubernetes ConfigMap
slug: /examples/config/kubecm
keywords: [配置中心, kubernetes, configmap, goframe]
description: 演示如何在GoFrame应用程序中全面集成Kubernetes ConfigMap实现云原生配置管理。本示例展示了Pod内部和外部两种配置场景、Kubernetes客户端的初始化与认证、ConfigMap的访问与动态加载、实时配置监听与更新、命名空间和资源管理、完善的错误处理和日志记录、以及安全的配置值获取。主要功能包括:原生Kubernetes ConfigMap集成、支持多种部署场景(集群内和集群外)、ConfigMap变更时自动刷新配置、与GoFrame配置组件无缝集成、符合RBAC规范的访问模式、生产级错误处理机制。非常适合构建部署在Kubernetes上的云原生应用,特别是需要原生配置管理、GitOps工作流、配置即代码实践的场景。通过本示例可以学习如何在Kubernetes环境中实现声明式配置管理和云原生最佳实践。
hide_title: true
sidebar_position: 9
---

# `Kubernetes ConfigMap` 配置示例

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中通过配置管理组件集成 `Kubernetes ConfigMap`。


## 目录结构

```text
.
├── boot_in_pod/     # Pod内部署的启动配置
│   └── boot.go      # Pod内客户端初始化
├── boot_out_pod/    # Pod外部署的启动配置
│   └── boot.go      # Pod外客户端初始化
├── main.go          # 主程序入口
├── go.mod           # Go 模块文件
└── go.sum           # Go 模块校验和
```


## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Kubernetes ConfigMap Config](https://github.com/gogf/gf/tree/master/contrib/config/kubecm)




