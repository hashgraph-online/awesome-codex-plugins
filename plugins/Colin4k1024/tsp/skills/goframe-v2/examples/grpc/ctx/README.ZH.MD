---
title: 上下文示例
slug: /examples/grpc/ctx
keywords: [grpc, 上下文, 元数据, goframe]
description: 演示在GoFrame的gRPC服务中进行高级上下文和元数据管理，用于请求跟踪和数据传播。本示例展示了如何通过gRPC上下文传递元数据以处理横切关注点、处理上下文值和截止时间以实现请求取消、跨服务边界管理请求上下文、处理和提取上下文元数据、实现分布式追踪集成、以及传播认证令牌和关联ID。主要功能包括:元数据注入和提取、上下文超时和取消处理、自定义元数据键和值、基于拦截器的元数据处理、分布式追踪支持、请求关联模式。非常适合在微服务中实现可观测性、跨分布式系统追踪请求、实现认证和授权、管理请求超时和取消、构建具有适当上下文管理的生产级gRPC服务。通过本示例可以学习gRPC上下文的高级用法、如何在分布式系统中传播请求信息、以及实现微服务间通信的最佳实践和可观测性模式。
hide_title: true
sidebar_position: 3
---

# `gRPC` - 上下文示例

## 介绍

本示例展示了如何在 `GoFrame` 的 `gRPC` 中使用上下文和元数据。


## 目录结构

```text
.
├── client/           # 客户端示例
│   └── client.go     # 带上下文处理的客户端实现
├── controller/       # 服务控制器
│   └── helloworld.go # 带上下文处理的 Hello 服务
├── protobuf/         # protobuf协议定义
├── server/           # 服务器示例
│   ├── config.yaml   # 服务器配置
│   └── server.go     # 服务器实现
├── go.mod           # Go 模块文件
└── go.sum           # Go 模块校验和
```

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [GoFrame](https://goframe.org)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)

## 使用说明

1. 启动服务器：
   ```bash
   cd server
   go run server.go
   ```

2. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```
