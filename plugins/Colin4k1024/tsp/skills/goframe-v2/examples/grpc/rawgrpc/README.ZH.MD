---
title: 原生 gRPC 示例
slug: /examples/grpc/rawgrpc
keywords: [grpc, 原生, 实现, goframe]
description: 演示在GoFrame中不使用框架抽象层直接实现原生gRPC，提供最大的控制力和灵活性。本示例展示了如何直接使用原生gRPC库创建gRPC服务器和客户端、不使用额外封装直接使用协议缓冲区、通过直接gRPC API访问实现服务处理器、进行具有完全控制权的低级RPC调用、处理流式RPC和高级模式、以及有选择地集成GoFrame组件。主要功能包括:直接创建gRPC服务器和客户端、无抽象的协议缓冲区使用、手动连接管理、自定义拦截器和中间件、流式支持(单向、客户端流、服务器流、双向流)、生产级错误处理。非常适合需要细粒度控制的高级用户、实现自定义gRPC模式、优化性能关键应用、以及集成第三方gRPC库。通过本示例可以学习如何在GoFrame中使用原生gRPC、深入理解gRPC工作原理、以及实现高度定制化的RPC通信方案。
hide_title: true
sidebar_position: 9
---

# `gRPC` - 原生示例

## 介绍

本示例展示了如何在 `GoFrame` 中实现原生 `gRPC` 服务，不使用额外的抽象层。



## 目录结构

```text
.
├── client/           # 客户端示例
│   └── client.go     # 原生 gRPC 客户端实现
├── helloworld/       # protobuf协议定义
│   └── helloworld.proto # 服务和消息定义
├── server/           # 服务器示例
│   └── server.go     # 原生 gRPC 服务器实现
├── go.mod            # Go 模块文件
└── go.sum            # Go 模块校验和
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

