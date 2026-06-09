---
title: 动态属性
slug: /examples/observability/metric/dynamic_attributes
keywords: [指标, 动态属性, prometheus, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry和Prometheus管理动态指标属性以实现运行时属性更新。本示例展示了运行时属性修改、基于上下文的属性注入、请求作用域的指标标签、动态属性值解析、每请求指标自定义、以及灵活的标签模式。主要功能包括:在指标记录时更新属性、从请求上下文提取属性、注入用户/租户/会话ID、动态标签值计算、属性值缓存、生产级模式。非常适合实现每请求指标标签、跟踪用户特定指标、支持多租户、使用运行时上下文丰富指标、按动态维度分析行为、以及构建适应应用状态的灵活监控系统。通过本示例可以学习动态属性管理、上下文注入、以及灵活的指标标签实践。
hide_title: true
sidebar_position: 1
---

# 指标收集 - 动态属性

## 简介

本示例演示了如何在 `GoFrame` 中使用 `OpenTelemetry` 和 `Prometheus` 集成来实现动态指标属性。主要展示：
- 在运行时为指标添加动态属性
- 组合使用常量属性和动态属性
- 在常规指标和可观察指标中使用属性
- 导出带有动态属性的指标

## 目录结构

```text
.
├── go.mod            # Go模块文件
├── go.sum            # Go模块校验和
└── main.go           # 主程序，演示动态属性使用
```

## 功能特性

本示例展示了以下功能：

1. 动态属性
   - 运行时属性赋值
   - 属性组合使用
   - 基于值的属性
   - 灵活的标签管理

2. 带属性的指标类型
   - 带动态属性的计数器
   - 带动态属性的可观察计数器
   - 常量属性基线
   - 属性继承机制

3. 属性管理
   - 属性创建
   - 值类型处理
   - 属性作用域
   - 属性生命周期

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
   # HELP goframe_metric_demo_counter 这是Counter使用的简单演示
   goframe_metric_demo_counter{const_attr_1="1",dynamic_attr_2="2"} 11
   
   # HELP goframe_metric_demo_observable_counter 这是ObservableCounter使用的简单演示
   goframe_metric_demo_observable_counter{const_attr_4="4",dynamic_attr_1="1"} 10
   ```

## 实现说明

1. 常规指标的动态属性
   ```go
   counter := meter.MustCounter(
       "goframe.metric.demo.counter",
       gmetric.MetricOption{
           Help: "计数器示例",
           Unit: "bytes",
           Attributes: gmetric.Attributes{
               gmetric.NewAttribute("const_attr_1", 1), // 常量属性
           },
       },
   )
   
   // 添加动态属性
   counter.Add(ctx, 10, gmetric.Option{
       Attributes: gmetric.Attributes{
           gmetric.NewAttribute("dynamic_attr_2", 2), // 动态属性
       },
   })
   ```

2. 可观察指标的动态属性
   ```go
   observableCounter := meter.MustObservableCounter(
       "goframe.metric.demo.observable_counter",
       gmetric.MetricOption{
           Help: "可观察计数器示例",
           Unit: "%",
           Attributes: gmetric.Attributes{
               gmetric.NewAttribute("const_attr_4", 4), // 常量属性
           },
       },
   )
   
   // 在回调中添加动态属性
   meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
       obs.Observe(observableCounter, 10, gmetric.Option{
           Attributes: gmetric.Attributes{
               gmetric.NewAttribute("dynamic_attr_1", 1), // 动态属性
           },
       })
       return nil
   }, observableCounter)
   ```
