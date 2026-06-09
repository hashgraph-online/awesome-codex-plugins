---
title: OpenTelemetry Provider
slug: /examples/observability/trace/provider
keywords: [链路跟踪, provider, grpc, http, goframe]
description: 演示在GoFrame中配置包括gRPC和HTTP导出器的全面OpenTelemetry链路跟踪provider配置和不同设置模式。本示例展示了trace provider的初始化和配置、用于服务识别的资源属性管理、采样策略配置和选择、基于gRPC和HTTP的导出器设置与比较、用于批处理和简单处理的span处理器配置、以及provider生命周期管理。主要功能包括:灵活的provider配置模式、资源语义约定、多种采样策略(总是、从不、基于父级、基于比例)、导出器协议选择指导、生产级provider设置、企业部署模式。非常适合理解OpenTelemetry provider架构、配置生产trace管道、选择合适的导出器和采样器、优化trace收集性能、以及构建带有适当provider配置的可扩展可观测性基础设施。通过本示例可以学习OpenTelemetry provider的最佳实践、导出器和采样器选型、以及构建企业级链路跟踪系统。
hide_title: true
sidebar_position: 9
---

# OpenTelemetry Provider链路跟踪示例

## 简介

本目录包含了在GoFrame应用程序中使用不同OpenTelemetry链路跟踪Provider配置的示例。包括：

1. gRPC Provider (`grpc/`)
   - 使用gRPC协议传输链路跟踪数据
   - 配置带gRPC导出器的链路跟踪Provider
   - 演示资源和采样器配置

2. HTTP Provider (`http/`)
   - 使用HTTP协议传输链路跟踪数据
   - 配置带HTTP导出器的链路跟踪Provider
   - 展示资源和采样器配置

3. 内部组件 (`internal/`)
   - 通用Provider初始化代码
   - 共享常量和配置
   - 链路跟踪设置工具函数

## 目录结构

```
.
├── grpc/           # gRPC provider示例
│   └── main.go     # gRPC provider实现
├── http/           # HTTP provider示例
│   └── main.go     # HTTP provider实现
├── internal/       # 共享组件
│   ├── consts.go   # 常量定义
│   ├── provider.go # Provider初始化
│   └── request.go  # 请求工具
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```

## 环境要求

- Go `1.22` 或更高版本
- GoFrame框架
- OpenTelemetry支持

## 功能特性

本示例展示了以下功能：

1. Provider配置
   ```go
   // 资源配置
   res, err = resource.New(ctx,
       resource.WithFromEnv(),
       resource.WithProcess(),
       resource.WithTelemetrySDK(),
       resource.WithHost(),
       resource.WithAttributes(
           semconv.ServiceNameKey.String(internal.GRPCServiceName),
           semconv.HostNameKey.String(serverIP),
       ),
   )

   // 采样器配置
   trace.WithSampler(trace.TraceIDRatioBased(0.1))
   ```

2. 资源属性
   - 服务名称
   - 主机信息
   - 进程详情
   - 自定义属性

3. 采样策略
   ```go
   // 可用的采样策略
   trace.WithSampler(trace.AlwaysSample())      // 总是采样
   trace.WithSampler(trace.NeverSample())       // 从不采样
   trace.WithSampler(trace.ParentBased(...))    // 基于父级的采样
   trace.WithSampler(trace.TraceIDRatioBased()) // 基于跟踪ID的采样
   ```

4. Span处理
   ```go
   // 简单Span处理器
   trace.WithSpanProcessor(trace.NewSimpleSpanProcessor(exporter))
   
   // 批量Span处理器
   trace.WithSpanProcessor(trace.NewBatchSpanProcessor(exporter))
   ```

## Provider对比

### gRPC Provider (grpc/)
1. 特点：
   - 高性能流式传输
   - 双向通信
   - 连接复用
   - 压缩支持

2. 配置：
   ```go
   otlptracegrpc.NewClient(
       otlptracegrpc.WithInsecure(),
       otlptracegrpc.WithEndpoint(internal.Endpoint),
       otlptracegrpc.WithHeaders(map[string]string{
           "Authentication": internal.TraceToken,
       }),
       otlptracegrpc.WithCompressor(gzip.Name),
   )
   ```

3. 使用场景：
   - 大规模链路跟踪
   - 性能关键系统
   - 流式跟踪数据

### HTTP Provider (http/)
1. 特点：
   - 标准HTTP协议
   - 配置简单
   - 防火墙友好
   - 压缩支持

2. 配置：
   ```go
   otlptracehttp.NewClient(
       otlptracehttp.WithEndpoint(internal.HTTPEndpoint),
       otlptracehttp.WithURLPath(internal.HTTPPath),
       otlptracehttp.WithInsecure(),
       otlptracehttp.WithCompression(1),
   )
   ```

3. 使用场景：
   - 基本链路跟踪需求
   - HTTP代理环境
   - 简单部署

## 使用说明

### gRPC Provider示例
1. 进入gRPC示例目录：
   ```bash
   cd grpc
   ```

2. 运行示例：
   ```bash
   go run main.go
   ```

### HTTP Provider示例
1. 进入HTTP示例目录：
   ```bash
   cd http
   ```

2. 运行示例：
   ```bash
   go run main.go
   ```

## 实现说明

两个示例都演示了：

1. Provider设置
   ```go
   // 初始化链路跟踪Provider
   func InitTracer(opts ...trace.TracerProviderOption) (func(ctx context.Context), error) {
       tracerProvider := trace.NewTracerProvider(opts...)
       otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
           propagation.TraceContext{},
           propagation.Baggage{},
       ))
       otel.SetTracerProvider(tracerProvider)
       return func(ctx context.Context) {
           // 优雅关闭
           ctx, cancel := context.WithTimeout(ctx, time.Second)
           defer cancel()
           if err := tracerProvider.Shutdown(ctx); err != nil {
               g.Log().Errorf(ctx, "关闭tracerProvider失败 err:%+v", err)
           }
       }, nil
   }
   ```

2. 资源配置
   - 服务标识
   - 主机信息
   - 进程属性
   - 自定义标签

3. 采样配置
   - 采样策略选择
   - 采样率配置
   - 父级上下文处理

4. 错误处理
   - 连接错误
   - 导出错误
   - 关闭处理
