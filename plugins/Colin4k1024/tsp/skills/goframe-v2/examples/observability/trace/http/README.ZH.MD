---
title: HTTP服务
slug: /examples/observability/trace/http
keywords: [链路跟踪, http, goframe]
description: 演示在GoFrame中使用OpenTelemetry集成实现HTTP服务的全面分布式链路跟踪。本示例展示了带有自动埋点的HTTP请求和响应跟踪、跨服务边界的trace上下文传播、span创建和属性管理、向OpenTelemetry收集器导出trace数据、与GoFrame HTTP服务器中间件集成、以及分布式trace的可视化。主要功能包括:自动HTTP trace埋点、上下文传播头、自定义span属性、父子span关系、trace采样配置、生产级可观测性模式。非常适合在微服务中实现分布式跟踪、监控HTTP服务性能、调试请求流程、确保云原生应用的可观测性、以及构建生产监控系统。通过本示例可以学习如何在HTTP服务中实现分布式跟踪、OpenTelemetry的最佳实践、以及构建可观测的微服务架构。
hide_title: true
sidebar_position: 1
---

# 链路跟踪 - HTTP服务

## 简介

本示例演示了如何在 `GoFrame` 中实现HTTP服务的分布式跟踪。主要展示：
- 配置HTTP服务的跟踪
- 跟踪HTTP请求和响应
- 传播跟踪上下文
- 可视化分布式跟踪

## 环境要求

- `Go` `1.22` 或更高版本
- `GoFrame` 框架
- `GoFrame OpenTelemetry` 跟踪

## 目录结构

```text
.
├── client/          # 客户端示例
│   └── client.go    # 带跟踪的客户端
├── server/          # 服务端示例
│   └── server.go    # 带跟踪的服务端
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```


## 前置条件

1. 运行 `Jaeger` 实例：
   ```bash
   docker run --rm --name jaeger \
   -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
   -p 6831:6831/udp \
   -p 6832:6832/udp \
   -p 5778:5778 \
   -p 16686:16686 \
   -p 4317:4317 \
   -p 4318:4318 \
   -p 14250:14250 \
   -p 14268:14268 \
   -p 14269:14269 \
   -p 9411:9411 \
   jaegertracing/all-in-one:1.55
   ```

## 使用说明

1. 启动服务端：
   ```bash
   cd server
   go run server.go
   ```

2. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```

3. 查看跟踪：
   在浏览器中打开 http://localhost:16686 查看 `Jaeger` UI中的跟踪信息。

## API接口

服务器提供以下HTTP接口：

1. Hello World
   ```text
   GET /hello
   响应: "Hello World"
   ```

## 实现说明

1. 服务端实现
   ```go
   // 初始化跟踪
   shutdown, err := otlphttp.Init(serviceName, endpoint, path)

   // 创建HTTP服务器
   s := g.Server()
   s.Group("/", func(group *ghttp.RouterGroup) {
       group.GET("/hello", HelloHandler)
   })

   // 处理请求并跟踪
   func HelloHandler(r *ghttp.Request) {
       ctx, span := gtrace.NewSpan(r.Context(), "HelloHandler")
       defer span.End()

       value := gtrace.GetBaggageVar(ctx, "name").String()
       r.Response.Write("hello:", value)
   }
   ```

2. 客户端实现
   ```go
   // 创建新的跟踪span
   ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
   defer span.End()

   // 设置跟踪的baggage值
   ctx = gtrace.SetBaggageValue(ctx, "name", "GoFrame")

   // 发送HTTP请求
   response, err := g.Client().Get(ctx, "http://127.0.0.1:8000/hello")
   ```
