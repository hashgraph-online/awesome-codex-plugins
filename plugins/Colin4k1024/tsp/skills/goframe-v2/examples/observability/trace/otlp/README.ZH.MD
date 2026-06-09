---
title: OpenTelemetry示例
slug: /examples/observability/trace/otlp
keywords: [链路跟踪, otlp, grpc, http, goframe]
description: 演示在GoFrame中使用OTLP协议通过gRPC和HTTP导出器实现全面的OpenTelemetry链路跟踪数据导出方法。本示例展示了用于trace导出的OTLP（OpenTelemetry协议）配置、gRPC和HTTP导出器的设置与比较、trace数据的序列化和传输、连接管理和重试逻辑、批处理和性能优化、以及与OpenTelemetry收集器的集成。主要功能包括:灵活的导出器配置、高效的trace数据传输、自动批处理和压缩、错误处理和重试机制、生产级导出模式、协议选择指导。非常适合实现生产trace导出、选择合适的导出协议、优化trace数据传输、确保可靠的trace交付、以及构建符合OpenTelemetry标准的企业级可观测性基础设施。通过本示例可以学习OTLP协议的使用、导出器选型、以及构建高效的trace数据导出系统。
hide_title: true
sidebar_position: 8
---

# OpenTelemetry链路跟踪示例

## 简介

本目录包含了演示在GoFrame应用程序中使用不同方法导出OpenTelemetry链路跟踪数据的示例。包括：

1. 基于gRPC的导出 (`grpc/`)
   - 使用gRPC协议传输链路跟踪数据
   - 适用于高性能、流式链路跟踪数据导出
   - 支持双向流和连接复用

2. 基于HTTP的导出 (`http/`)
   - 使用HTTP协议传输链路跟踪数据
   - 适用于有HTTP代理或防火墙限制的环境
   - 配置和调试更简单

## 目录结构

```
.
├── grpc/           # 基于gRPC的链路跟踪示例
│   └── main.go     # gRPC链路跟踪导出器实现
├── http/           # 基于HTTP的链路跟踪示例
│   └── main.go     # HTTP链路跟踪导出器实现
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```

## 环境要求

- Go `1.22` 或更高版本
- GoFrame框架
- GoFrame OpenTelemetry gRPC链路跟踪
- GoFrame OpenTelemetry HTTP链路跟踪

## 前置条件

1. 运行Jaeger实例：
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

## 导出方法对比

### gRPC导出 (grpc/)
1. 优势：
   - 更高性能
   - 双向流传输
   - 连接复用
   - 更适合大量链路跟踪数据

2. 配置：
   - 需要gRPC端点
   - 支持认证令牌
   - 可配置连接设置

3. 使用场景：
   - 大量链路跟踪数据
   - 微服务架构
   - 性能关键系统

### HTTP导出 (http/)
1. 优势：
   - 设置更简单
   - 可通过HTTP代理
   - 更易调试
   - 更好的防火墙兼容性

2. 配置：
   - 需要HTTP端点
   - 支持路径配置
   - 标准HTTP设置

3. 使用场景：
   - 有HTTP代理的环境
   - 简单部署要求
   - 开发和测试

## 使用说明

### gRPC导出示例
1. 进入gRPC示例目录：
   ```bash
   cd grpc
   ```

2. 运行示例：
   ```bash
   go run main.go
   ```

### HTTP导出示例
1. 进入HTTP示例目录：
   ```bash
   cd http
   ```

2. 运行示例：
   ```bash
   go run main.go
   ```

3. 查看链路跟踪：
   在浏览器中打开 http://localhost:16686 查看Jaeger UI中的链路跟踪信息。

## 实现说明

两个示例都演示了：

1. 链路跟踪上下文管理
   ```go
   // 创建新的链路跟踪span
   ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
   defer span.End()

   // 设置链路跟踪的baggage值
   ctx = gtrace.SetBaggageValue(ctx, "name", "john")
   ```

2. 错误处理
   ```go
   // 初始化导出器
   shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
   if err != nil {
       g.Log().Fatal(ctx, err)
   }
   defer shutdown(ctx)
   ```

3. 配置管理
   ```go
   // gRPC配置
   const (
       serviceName = "otlp-grpc-client"
       endpoint    = "tracing-analysis-dc-bj.aliyuncs.com:8090"
       traceToken  = "******_******"
   )

   // HTTP配置
   const (
       serviceName = "otlp-http-client"
       endpoint    = "tracing-analysis-dc-hz.aliyuncs.com"
       path        = "adapt_******_******/api/otlp/traces"
   )
   ```
