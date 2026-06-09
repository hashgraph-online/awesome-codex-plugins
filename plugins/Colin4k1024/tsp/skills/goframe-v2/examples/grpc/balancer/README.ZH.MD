---
title: 负载均衡
slug: /examples/grpc/balancer
keywords: [grpc, 负载均衡, 服务发现, goframe]
description: 演示在GoFrame中实现全面的gRPC负载均衡以构建弹性分布式系统。本示例展示了如何使用多种策略配置gRPC负载均衡器、实现客户端负载均衡以获得最佳性能、与etcd等服务发现机制集成、处理自动故障转移和服务健康检查、在多个服务器实例间分发请求、以及管理连接池。主要功能包括:多种负载均衡算法(轮询、加权、最少连接)、自动服务实例发现、基于健康状态的路由、连接状态管理、重试策略、生产级错误处理。非常适合构建高可用微服务、实现容错分布式系统、水平扩展gRPC服务、确保跨服务实例的最佳资源利用。通过本示例可以学习如何在分布式环境中实现gRPC负载均衡、服务发现与负载均衡的协同工作、以及构建高可用高性能微服务架构的最佳实践。
hide_title: true
sidebar_position: 2
---

# `gRPC` - 负载均衡

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中实现 `gRPC` 负载均衡。


## 目录结构

```text
.
├── client/         # 客户端示例
│   └── client.go   # 带负载均衡的客户端实现
├── controller/     # 服务控制器
│   └── hello.go    # Hello 服务实现
├── protobuf/       # protobuf协议定义
├── server/         # 服务器示例
│   ├── config.yaml # 服务器配置
│   └── server.go   # 服务器实现
├── go.mod          # Go 模块文件
└── go.sum          # Go 模块校验和
```



## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)

## 使用说明

1. 启动多个服务器实例（使用随机端口）：
   ```bash
   cd server
   go run server.go

   # 启动第二个服务器实例
   go run server.go

   # 启动第三个服务器实例
   go run server.go
   ```

2. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```
