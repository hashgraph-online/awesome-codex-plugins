---
title: HTTP负载均衡
slug: /examples/balancer/http
keywords: [负载均衡, http, 服务发现, goframe]
description: 演示如何使用GoFrame框架结合etcd实现HTTP服务的负载均衡功能。本示例展示了基于客户端的负载均衡实现，采用轮询策略进行请求分发，支持自动服务发现和动态路由。主要功能包括：使用etcd进行服务注册与发现、客户端轮询负载均衡策略、多服务实例请求分发、与GoFrame的HTTP服务器和客户端组件无缝集成，适用于构建高可用、可扩展的微服务架构系统。通过本示例可以学习如何在分布式环境中实现服务负载均衡和服务发现机制。
hide_title: true
---

# HTTP 服务负载均衡示例

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中实现 HTTP 服务的负载均衡。主要演示：
- 使用 `etcd` 配置负载均衡器
- 服务注册和服务发现
- 请求路由和负载分发

## 目录结构

```text
.
├── server/         # HTTP 服务器
├── client/         # HTTP 客户端
├── go.mod          # Go 模块文件
└── go.sum          # Go 模块校验
```

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 使用说明

1. 启动服务器：
   ```bash
   go run server/main.go
   ```

2. 在另一个终端启动客户端：
   ```bash
   go run client/main.go
   ```
