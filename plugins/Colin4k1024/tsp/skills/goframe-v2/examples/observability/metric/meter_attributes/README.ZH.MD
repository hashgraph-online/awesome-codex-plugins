---
title: 指标计量器属性
slug: /examples/observability/metric/meter_attributes
keywords: [指标, 计量器属性, prometheus, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry和Prometheus管理仪表级属性以实现作用域指标标签。本示例展示了仪表特定的属性配置、仪表内的属性作用域、隔离的指标标签、仪表级元数据管理、从仪表到指标的属性继承、以及精细的属性控制。主要功能包括:创建带有自定义属性的仪表、将属性作用域限制在特定指标组、隔离的属性命名空间、自动将属性应用于仪表指标、基于仪表的多租户、生产级模式。非常适合按模块或组件组织指标、实现作用域指标标签、管理多个指标命名空间、隔离指标组之间的属性、构建模块化监控系统、以及为复杂应用建立层次化指标组织。通过本示例可以学习仪表级属性管理、作用域标签、以及层次化指标组织。
hide_title: true
sidebar_position: 1
---

# 指标收集 - 计量器属性

## 简介

本示例演示了如何在 `GoFrame` 中使用 `OpenTelemetry` 和 `Prometheus` 集成来配置和管理指标计量器级别的属性。主要展示：
- 配置计量器级别属性
- 在所有指标中应用属性
- 组合计量器和指标属性
- 管理属性继承关系

## 目录结构

```text
.
├── go.mod            # Go模块文件
├── go.sum            # Go模块校验和
└── main.go           # 主程序，演示计量器属性使用
```

## 功能特性

本示例展示了以下功能：

1. 计量器属性
   - 全局计量器配置
   - 计量器级别属性
   - 属性继承机制

2. 带继承属性的指标类型
   - 带组合属性的计数器（Counter）
   - 带组合属性的可观察计数器（Observable Counter）
   - 属性优先级规则

3. 属性管理
   - 计量器属性配置
   - 基于版本的属性
   - 属性组合方式

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
   # HELP goframe_metric_demo_counter 这是Counter用法的简单演示
   goframe_metric_demo_counter{const_attr_1="1",meter_label_1="1",meter_label_2="2"} 11
   
   # HELP goframe_metric_demo_observable_counter 这是ObservableCounter用法的简单演示
   goframe_metric_demo_observable_counter{const_attr_2="2",meter_label_1="1",meter_label_2="2"} 10
   ```

## 实现说明

1. 配置计量器属性
   ```go
   // 创建全局计量器实例，配置计量器级别属性
   meter = gmetric.GetGlobalProvider().Meter(gmetric.MeterOption{
       Instrument:        instrument,        // 指标标识符
       InstrumentVersion: instrumentVersion, // 指标版本
       Attributes: gmetric.Attributes{       // 计量器级别属性
           gmetric.NewAttribute("meter_label_1", 1),
           gmetric.NewAttribute("meter_label_2", 2),
       },
   })
   ```

2. 创建带属性的指标
   ```go
   // 创建Counter指标，包含计量器属性和指标特定属性
   counter = meter.MustCounter(
       "goframe.metric.demo.counter",
       gmetric.MetricOption{
           Help: "这是Counter用法的简单演示",
           Unit: "bytes",
           Attributes: gmetric.Attributes{
               gmetric.NewAttribute("const_attr_1", 1),
           },
       },
   )
   ```

3. 注册可观察指标回调
   ```go
   // 注册回调函数，自动继承计量器属性
   meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
       obs.Observe(observableCounter, 10)
       return nil
   }, observableCounter)
   ```
