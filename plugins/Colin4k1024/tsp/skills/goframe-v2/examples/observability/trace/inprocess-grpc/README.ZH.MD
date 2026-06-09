---
title: 进程内服务 (gRPC导出器)
slug: /examples/observability/trace/inprocess-grpc
keywords: [链路跟踪, 进程内, grpc, goframe, otlp-grpc]
description: 演示在单进程应用中使用GoFrame和高性能gRPC基础的OpenTelemetry导出器实现分布式跟踪。本示例展示了使用gRPC OTLP导出器配置的进程内函数调用跟踪、内部操作的span创建和管理、单进程内的trace上下文传播、高效的基于gRPC的trace数据导出到OpenTelemetry收集器、嵌套函数调用的父子span关系、以及高吞吐量trace数据传输。主要功能包括:高性能gRPC导出器设置、自动span埋点、流式trace导出、高效二进制序列化、生产级性能、企业级模式。非常适合大量trace数据生成、性能关键应用、生产监控系统、需要高效trace导出的应用、以及构建可扩展的可观测性解决方案。通过本示例可以学习如何实现高性能链路跟踪、gRPC导出器的最佳实践、以及构建企业级监控系统。
hide_title: true
sidebar_position: 1
---

# 链路跟踪 - 进程内服务 (gRPC导出器)

## 简介

本示例演示了如何使用GoFrame和基于gRPC的OpenTelemetry导出器在进程内服务中实现分布式跟踪。主要展示：
- 使用gRPC导出器配置单进程跟踪
- 跟踪函数调用和操作
- 通过gRPC传播跟踪上下文
- 可视化分布式跟踪

## 环境要求

- Go `1.22` 或更高版本
- GoFrame框架
- GoFrame OpenTelemetry gRPC跟踪

## 目录结构

```
.
├── main.go         # 带gRPC跟踪的主应用程序
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```


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

## 使用说明

1. 运行应用程序：
   ```bash
   go run main.go
   ```

2. 查看跟踪：
   在浏览器中打开 http://localhost:16686 查看Jaeger UI中的跟踪信息。

## 实现说明

本示例演示了：

1. 用户数据操作
   ```go
   GetUser(ctx, id)       // 检索完整的用户数据
   ├── GetInfo(ctx, id)   // 获取基本用户信息
   ├── GetDetail(ctx, id) // 获取详细用户信息
   └── GetScores(ctx, id) // 获取用户成绩
   ```

2. 跟踪上下文流程
   ```go
   // 创建带gRPC上下文的根span
   ctx, span := gtrace.NewSpan(ctx, "main")
   defer span.End()

   // 创建带gRPC元数据的子span
   ctx, span := gtrace.NewSpan(ctx, "GetUser")
   defer span.End()
   ```

3. 错误处理
   ```go
   // 处理不存在的用户ID
   if id == 100 {
       return g.Map{
           "id":     100,
           "name":   "john",
           "gender": 1,
       }
   }
   return nil
   ```

4. 基于gRPC的跟踪导出
   ```go
   // 初始化gRPC跟踪导出器
   shutdown, err = otlpgrpc.Init(serviceName, endpoint, traceToken)
   if err != nil {
       g.Log().Fatal(ctx, err)
   }
   defer shutdown(ctx)
   ```


## 示例输出

对于用户ID 100：
```go
{
    "id":      100,
    "name":    "john",
    "gender":  1,
    "site":    "https://goframe.org",
    "email":   "john@goframe.org",
    "math":    100,
    "english": 60,
    "chinese": 50
}
```

对于不存在的用户ID：
```go
{}
```
