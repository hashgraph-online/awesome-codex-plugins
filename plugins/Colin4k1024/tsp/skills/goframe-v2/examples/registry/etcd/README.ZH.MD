---
title: Etcd
slug: /examples/registry/etcd
keywords: [注册中心, etcd, 服务发现, goframe]
description: 演示在GoFrame中全面集成Etcd服务注册中心实现分布式服务发现和注册。本示例展示了使用自动心跳机制向Etcd注册服务、服务发现和监听实时更新、基于TTL的服务健康管理、服务元数据和端点配置、关闭时自动服务注销、以及与GoFrame服务器和客户端组件集成。主要功能包括:分布式服务注册中心、通过watch机制实现实时服务更新、健康检查集成、负载均衡器集成、自动故障转移支持、生产级模式。适合构建需要动态服务发现的云原生微服务、实现服务网格架构、通过自动服务注册确保高可用性、以及实现零停机部署。
hide_title: true
sidebar_position: 1
---

# 注册中心 - `Etcd` 集成

## 简介

本示例演示了如何在 `GoFrame` 应用程序中集成 `Etcd` 服务注册中心。主要展示：
- 使用 `Etcd` 注册服务
- 使用 `Etcd` 发现服务
- 实现服务健康检查
- 构建分布式系统

## 目录结构

```text
.
├── grpc/                # gRPC服务示例
│   ├── client/          # gRPC客户端实现
│   ├── controller/      # gRPC服务控制器
│   ├── protobuf/        # Protocol buffer定义
│   └── server/          # gRPC服务器实现
│       ├── main.go      # 服务器启动代码
│       └── config.yaml  # 服务器配置
├── http/                # HTTP服务示例
│   ├── client/          # HTTP客户端实现
│   └── server/          # HTTP服务器实现
├── go.mod               # Go模块文件
└── go.sum               # Go模块校验和
```

## 功能特性

本示例展示了以下功能：

1. 服务注册
   - 自动服务注册
   - 基于TTL的健康检查
   - 元数据管理
   - 租约管理

2. 服务发现
   - 动态服务发现
   - 负载均衡
   - 故障转移支持
   - Watch机制监控

3. 协议支持
   - `HTTP` 服务注册与发现
   - `gRPC` 服务注册与发现

## 环境要求

- `Go` `1.22` 或更高版本
- `Docker` (用于运行 `Etcd`)
- `Etcd` 3.4+

## 使用说明

1. 启动 `Etcd` 服务：
   ```bash
   docker run -d --name etcd -p 2379:2379 -e ALLOW_NONE_AUTHENTICATION=yes bitnami/etcd:3.4.24
   ```

2. `HTTP` 服务示例：
   ```bash
   # 启动HTTP服务器
   cd http/server
   go run server.go

   # 运行HTTP客户端
   cd http/client
   go run client.go
   ```

3. `gRPC` 服务示例：
   ```bash
   # 启动gRPC服务器
   cd grpc/server
   go run server.go

   # 运行gRPC客户端
   cd grpc/client
   go run client.go
   ```

## 实现说明

1. `HTTP` 服务实现
   - 服务器使用 `g.Server` 创建 `HTTP` 服务
   - 通过 `gsvc.SetRegistry` 设置 `Etcd` 注册中心
   - 客户端使用 `g.Client()` 自动发现并访问服务
   - 支持自动的健康检查和租约续期

2. `gRPC` 服务实现
   - 服务器使用 `grpc.Server` 创建 `gRPC` 服务
   - 通过 `gsvc.SetRegistry` 设置 `Etcd` 注册中心
   - 客户端使用 `grpc.Client` 自动发现并访问服务
   - 支持自动的健康检查和租约续期
