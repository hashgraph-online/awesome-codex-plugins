---
title: HTTP客户端
slug: /examples/observability/metric/http_client
keywords: [指标, http客户端, prometheus, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry和Prometheus收集全面的HTTP客户端指标以监控出站HTTP请求。本示例展示了自动HTTP客户端埋点、请求持续时间直方图、按状态码和方法分类的请求计数指标、错误率跟踪、连接池指标、以及重试尝试监控。主要功能包括:无需代码更改的自动指标收集、详细的请求/响应属性、与GoFrame HTTP客户端集成、可自定义的指标标签、Prometheus导出器配置、生产级可观测性模式。非常适合监控外部API调用、跟踪HTTP客户端性能、调试连接问题、分析请求模式、以及确保微服务架构中出站HTTP通信的可靠性。通过本示例可以学习如何监控HTTP客户端、分析外部依赖、以及优化API调用性能。
hide_title: true
sidebar_position: 1
---

# 指标收集 - HTTP客户端

## 简介

本示例演示了如何在 `GoFrame` 中使用 `OpenTelemetry` 和 `Prometheus` 集成来收集和监控HTTP客户端指标。主要展示：
- 监控HTTP客户端请求
- 跟踪请求持续时间
- 收集响应状态码
- 导出客户端指标数据

## 目录结构

```text
.
├── go.mod            # Go模块文件
├── go.sum            # Go模块校验和
└── main.go           # 主程序，演示HTTP客户端指标收集
```

## 功能特性

本示例展示了以下指标：

1. 请求指标
   - 总请求数（Total Requests Count）
   - 活跃请求数（Active Requests）
   - 请求持续时间（Request Duration）
   - 请求大小（Request Size）

2. 响应指标
   - 响应状态码（Response Status Codes）
   - 响应大小（Response Size）
   - 错误计数（Error Count）
   - 响应持续时间（Response Duration）

3. 连接指标
   - 连接池统计（Connection Pool Stats）
   - DNS查询持续时间（DNS Lookup Duration）
   - TLS握手持续时间（TLS Handshake Duration）
   - 连接建立时间（Connection Establishment Time）

## 环境要求

- `Go` `1.22` 或更高版本
- `GoFrame` 框架
- `GoFrame OpenTelemetry Metric` 扩展

## 使用说明

1. 运行示例：
   ```bash
   go run main.go
   ```

2. 访问指标：
   ```bash
   # 使用curl
   curl http://localhost:8000/metrics
   
   # 或在浏览器中打开
   http://localhost:8000/metrics
   ```

3. 指标输出示例：
   ```text
   # HELP goframe_http_client_request_duration_seconds HTTP请求的持续时间
   goframe_http_client_request_duration_seconds_bucket{method="GET",status="200",url="https://goframe.org",le="0.1"} 1
   
   # HELP goframe_http_client_requests_total HTTP请求的总数
   goframe_http_client_requests_total{method="GET",status="200",url="https://goframe.org"} 1
   
   # HELP goframe_http_client_response_size_bytes HTTP响应的大小
   goframe_http_client_response_size_bytes{method="GET",status="200",url="https://goframe.org"} 12345
   ```

## 实现说明

1. 配置指标导出器
   ```go
   // 创建Prometheus导出器，用于指标数据的导出
   exporter, err := prometheus.New(
       prometheus.WithoutCounterSuffixes(), // 移除计数器后缀以保持指标名称简洁
       prometheus.WithoutUnits(),           // 移除单位后缀以保持指标名称简洁
   )
   if err != nil {
       g.Log().Fatal(ctx, err)
   }
   ```

2. 初始化OpenTelemetry提供者
   ```go
   // 初始化并配置OpenTelemetry提供者
   provider := otelmetric.MustProvider(
       otelmetric.WithReader(exporter),     // 配置指标读取器
       otelmetric.WithBuiltInMetrics(),     // 启用内置指标收集
   )
   provider.SetAsGlobal()                   // 设置为全局指标提供者
   defer provider.Shutdown(ctx)             // 确保程序退出时正确关闭提供者
   ```

3. 使用HTTP客户端
   ```go
   // 发起HTTP请求并自动收集指标
   url := `https://goframe.org`
   content := g.Client().GetContent(ctx, url)  // 发起HTTP GET请求
   ```
