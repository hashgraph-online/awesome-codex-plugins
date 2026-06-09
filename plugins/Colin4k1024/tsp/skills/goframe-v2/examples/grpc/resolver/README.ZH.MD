---
title: 服务发现
slug: /examples/grpc/resolver
keywords: [grpc, 服务发现, etcd, goframe]
description: 演示在GoFrame中实现gRPC服务解析器并集成etcd以实现动态服务发现和解析。本示例展示了如何使用etcd作为服务注册中心配置服务解析器、通过自动心跳向etcd注册gRPC服务、使用解析器API动态发现和解析服务、自动处理服务实例的更新和移除、实现客户端服务发现、以及管理服务健康监控。主要功能包括:基于etcd的服务注册中心、自动服务注册和注销、动态服务解析、健康检查集成、服务变更时的自动故障转移、生产级连接管理。非常适合构建具有动态服务发现的云原生微服务、实现服务网格模式、无需客户端重新配置即可扩展服务、通过自动服务解析确保高可用性。通过本示例可以学习如何在gRPC中实现服务发现和解析、etcd在微服务架构中的应用、以及构建动态可扩展的分布式系统的最佳实践。
hide_title: true
sidebar_position: 1
---

# `gRPC` - 服务发现

## 介绍

本示例展示了如何在 `GoFrame` 的 `gRPC` 服务中使用 `etcd` 进行服务发现。


## 目录结构

```text
.
├── client/              # 客户端示例
│   └── client.go        # 带服务发现的客户端
├── controller/          # 服务控制器
│   └── helloworld.go    # Hello 服务实现
├── protobuf/            # protobuf协议定义
│   └── helloworld.proto # 服务和消息定义
├── server/              # 服务器示例
│   └── server.go        # 带服务注册的服务器
├── go.mod               # Go 模块文件
└── go.sum               # Go 模块校验和
```



## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [etcd](https://etcd.io/)

## 使用说明

1. 启动 `etcd`：
   ```bash
   docker run -d --name etcd -p 2379:2379 -e ALLOW_NONE_AUTHENTICATION=yes bitnami/etcd:3.4.24
   ```

2. 启动服务器：
   ```bash
   cd server
   go run server.go
   ```

3. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```

