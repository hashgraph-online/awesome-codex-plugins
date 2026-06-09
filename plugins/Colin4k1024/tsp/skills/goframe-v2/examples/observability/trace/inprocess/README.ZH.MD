---
title: 进程内服务 (HTTP导出器)
slug: /examples/observability/trace/inprocess
keywords: [链路跟踪, 进程内, goframe, otlp-http]
description: 演示在单进程应用中使用GoFrame和基于HTTP的OpenTelemetry导出器实现分布式跟踪以简化可观测性。本示例展示了使用HTTP OTLP导出器配置的进程内函数调用跟踪、内部操作的span创建和管理、单进程内的trace上下文传播、基于HTTP的trace数据导出到OpenTelemetry收集器、嵌套函数调用的父子span关系、以及无需gRPC依赖的简化部署。主要功能包括:轻量级HTTP导出器设置、自动span埋点、内存trace上下文、防火墙友好的HTTP导出、开发友好的配置、生产级模式。非常适合单体应用可观测性、开发和测试环境、简化trace数据导出、仅支持HTTP基础设施的应用、以及学习分布式跟踪概念。通过本示例可以学习如何实现进程内跟踪、简化的可观测性方案、以及轻量级监控部署。
hide_title: true
sidebar_position: 1
---

# 链路跟踪 - 进程内服务 (HTTP导出器)

## 简介

本示例演示了如何使用GoFrame和基于HTTP的OpenTelemetry导出器在进程内服务中实现分布式跟踪。主要展示：
- 使用HTTP导出器配置单进程跟踪
- 跟踪函数调用和操作
- 传播跟踪上下文
- 可视化分布式跟踪

## 环境要求

- Go `1.22` 或更高版本
- GoFrame框架
- GoFrame OpenTelemetry HTTP跟踪

## 目录结构

```
.
├── main.go         # 带HTTP跟踪的主应用程序
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```

## 功能特性

本示例展示了以下功能：

1. 基于HTTP导出器的分布式跟踪
   - 基于HTTP的跟踪数据传输
   - Span管理
   - 跟踪可视化

2. 函数调用跟踪
   - 函数进入/退出跟踪
   - 上下文传播
   - 错误处理

3. 数据操作
   - 用户数据检索
   - 数据聚合
   - 错误处理

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
   // 创建根span
   ctx, span := gtrace.NewSpan(ctx, "main")
   defer span.End()

   // 创建子span并传播上下文
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

4. 基于HTTP的跟踪导出
   ```go
   // 初始化HTTP跟踪导出器
   shutdown, err = otlphttp.Init(serviceName, endpoint, path)
   if err != nil {
       g.Log().Fatal(ctx, err)
   }
   defer shutdown(ctx)
   ```

## 故障排除

1. 应用程序问题：
   - 检查应用程序是否正常运行
   - 验证函数调用输出
   - 查看错误日志

2. 跟踪问题：
   - 验证Jaeger是否运行：`docker ps | grep jaeger`
   - 检查Jaeger UI可访问性：http://localhost:16686
   - 确保配置中的HTTP端点正确

3. HTTP导出问题：
   - 检查HTTP连接状态
   - 验证HTTP端点可访问性
   - 查看HTTP错误消息

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

## 最佳实践

1. 跟踪配置
   - 设置合适的服务名称，便于在Jaeger UI中识别
   - 配置适当的采样率，平衡性能和可观测性
   - 使用有意义的span名称和标签

2. 错误处理
   - 在span中记录错误信息
   - 使用合适的状态码标识错误类型
   - 保持日志和跟踪的一致性

3. 性能优化
   - 避免创建过多的span
   - 及时关闭span
   - 合理使用上下文传播
