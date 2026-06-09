---
title: HTTP服务器
slug: /examples/observability/metric/http_server
keywords: [指标, http服务器, prometheus, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry和Prometheus收集全面的HTTP服务器指标以监控入站HTTP请求。本示例展示了自动HTTP服务器埋点、请求延迟直方图、按端点和方法分类的吞吐量指标、HTTP状态码分布、并发请求跟踪、以及错误率监控。主要功能包括:通过中间件自动收集指标、详细的请求属性(路径、方法、状态)、与GoFrame HTTP服务器集成、可自定义的指标桶、Prometheus端点暴露、生产级监控模式。非常适合监控API性能、跟踪服务健康、分析流量模式、识别性能瓶颈、实现SLA监控、以及确保生产环境中HTTP服务的高可用性。通过本示例可以学习如何监控HTTP服务器、分析请求性能、以及构建完整的服务监控体系。
hide_title: true
sidebar_position: 1
---

# 指标收集 - HTTP服务器

## 简介

本示例演示了如何在 `GoFrame` 中使用 `OpenTelemetry` 和 `Prometheus` 集成来收集和监控HTTP服务器指标。主要展示：
- 监控HTTP服务器请求
- 跟踪请求延迟
- 收集错误率
- 导出服务器端指标

## 目录结构

```text
.
├── go.mod            # Go模块文件
├── go.sum            # Go模块校验和
└── main.go           # 主程序，演示HTTP服务器指标收集
```

## 功能特性

本示例展示了以下端点和指标：

1. 端点（Endpoints）
   - `/`: 基础端点，返回"ok"
   - `/error`: 触发错误的端点
   - `/sleep`: 带5秒延迟的端点
   - `/metrics`: Prometheus指标端点

2. 请求指标
   - 总请求数（Total Requests Count）
   - 活跃请求数（Active Requests）
   - 请求持续时间（Request Duration）
   - 请求大小（Request Size）

3. 响应指标
   - 响应状态码（Response Status Codes）
   - 响应大小（Response Size）
   - 错误计数（Error Count）
   - 响应延迟（Response Latency）

4. 服务器指标
   - 协程数量（Goroutine Count）
   - 内存使用（Memory Usage）
   - GC统计（GC Statistics）
   - 连接统计（Connection Stats）

## 环境要求

- `Go` `1.22` 或更高版本
- `GoFrame` 框架
- `GoFrame OpenTelemetry Metric` 扩展

## 使用说明

1. 运行示例：
   ```bash
   go run main.go
   ```

2. 测试不同端点：
   ```bash
   # 基础请求
   curl http://localhost:8000/
   
   # 错误请求
   curl http://localhost:8000/error
   
   # 慢请求
   curl http://localhost:8000/sleep
   ```

3. 查看指标：
   ```bash
   # 使用curl
   curl http://localhost:8000/metrics
   
   # 或在浏览器中打开
   http://localhost:8000/metrics
   ```

4. 指标输出示例：
   ```text
   # HELP goframe_http_server_requests_total HTTP请求总数
   goframe_http_server_requests_total{method="GET",path="/",status="200"} 1
   
   # HELP goframe_http_server_request_duration_seconds HTTP请求持续时间
   goframe_http_server_request_duration_seconds_bucket{method="GET",path="/sleep",status="200",le="5.0"} 1
   
   # HELP goframe_http_server_panics_total 导致panic的HTTP请求总数
   goframe_http_server_panics_total{method="GET",path="/error"} 1
   ```

## 实现说明

1. 配置指标导出器
   ```go
   // 创建Prometheus导出器，用于指标数据的导出
   exporter, err := prometheus.New(
       prometheus.WithoutCounterSuffixes(), // 移除计数器后缀以保持指标名称简洁
       prometheus.WithoutUnits(),           // 移除单位后缀以保持指标名称简洁
   )
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

3. 配置HTTP服务器端点
   ```go
   s := g.Server()

   // 基础端点
   s.BindHandler("/", func(r *ghttp.Request) {
       r.Response.Write("ok")
   })

   // 错误端点
   s.BindHandler("/error", func(r *ghttp.Request) {
       panic("error")
   })

   // 慢请求端点
   s.BindHandler("/sleep", func(r *ghttp.Request) {
       time.Sleep(time.Second * 5)
       r.Response.Write("ok")
   })

   // 指标端点
   s.BindHandler("/metrics", otelmetric.PrometheusHandler)
   ```
