---
title: 基础示例
slug: /examples/grpc/basic
keywords: [grpc, 基础, goframe]
description: 演示GoFrame应用程序中gRPC的基础实现，涵盖协议缓冲区定义、服务创建和客户端-服务器通信。本示例展示了如何使用GoFrame创建gRPC服务器和客户端、定义和编译用于服务契约的协议缓冲区、实现带有业务逻辑的服务处理器、进行同步和异步RPC调用、处理错误和状态码、以及与GoFrame的配置和日志系统集成。主要功能包括:完整的服务器和客户端设置、协议缓冲区集成、服务接口实现、请求-响应模式、错误处理最佳实践、生产级代码结构。非常适合gRPC新手开发者、使用GoFrame构建微服务、学习协议缓冲区使用、实现服务间通信模式的场景。通过本示例可以学习gRPC在GoFrame中的基础用法、微服务通信的最佳实践、以及如何构建高效的RPC服务。
hide_title: true
sidebar_position: 0
---

# `gRPC` - 基础示例

## 介绍

本示例展示了在 `GoFrame` 应用程序中使用 `gRPC` 的基础示例。



## 目录结构

```text
.
├── client/         # 客户端示例
│   └── client.go   # 客户端实现
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
