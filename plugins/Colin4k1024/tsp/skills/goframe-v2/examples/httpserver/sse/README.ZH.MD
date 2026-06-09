---
title: Server-Sent Events(SSE)
slug: /examples/httpserver/sse
keywords: [http, server, sse, server-sent events, 服务器发送事件, 流式传输, goframe]
description: 演示使用GoFrame实现服务器发送事件(SSE)用于实时服务器到客户端流式传输。本示例展示了带有持久连接的SSE服务器设置、带有数据、事件类型和ID的事件流格式化、带有Last-Event-ID的自动客户端重连处理、发送实时更新和通知、适当的content-type和头配置、以及连接生命周期管理。主要功能包括:从服务器到客户端的单向流式传输、自动重连支持、事件驱动架构、相比WebSocket更轻量级、心跳和keepalive支持、生产级模式。非常适合构建实时通知和更新、实现实时仪表盘和监控、创建聊天和消息功能、无需WebSocket实现服务器推送、以及构建事件驱动应用。通过本示例可以学习SSE的实现原理、与WebSocket的区别、以及构建实时通信应用。
hide_title: true
---

# Server-Sent Events(SSE)

## 描述

本示例演示了如何使用 `GoFrame` 实现服务器发送事件（SSE）。服务器发送事件是一种允许服务器通过`HTTP`连接向客户端推送更新的技术。与`WebSocket`不同，`SSE`是单向的 - 只有服务器可以向客户端发送数据。

本示例实现了一个简单的`SSE`服务端实现，逐字符流式传输响应，模拟现代AI聊天应用程序中常见的实时打字效果。

## 要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 结构

```text
- go.mod: Go模块文件
- main.go: 包含SSE实现的主应用程序入口点
```

## 特性

- 服务器发送事件实现
- 模拟`AI`聊天逐字符流式响应
- 适用于`SSE`的正确`HTTP`头

## 设置

1. 克隆仓库：
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/sse
    ```

2. 安装依赖：
    ```bash
    go mod tidy
    ```

3. 运行应用程序：
    ```bash
    go run main.go
    ```

## 使用方法

1. 运行示例：
   ```bash
   go run main.go
   ```

2. 服务器将在以下地址启动：http://127.0.0.1:8000

3. 访问SSE端点：
   - 在浏览器中，导航至：http://127.0.0.1:8000/ai/chat
   - 您应该会看到单词逐个出现，产生打字效果

## 实现细节

`SSE`实现包括：

- 设置正确的`SSE` HTTP头：
  - `Content-Type: text/event-stream`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

- 使用适当的刷新进行流式响应
- 使用`time.Sleep`模拟打字延迟
- 使用`GoFrame`的路由器进行简单的HTTP路由

## 注意事项

- `SSE`连接保持打开状态，直到客户端明确关闭
- 服务器必须在每条消息后刷新响应缓冲区
- 对于生产环境，请考虑实现重连逻辑和事件ID
- `SSE`通过常规`HTTP/HTTPS`工作，并支持浏览器中的自动重连