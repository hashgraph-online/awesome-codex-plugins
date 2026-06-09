---
title: 全局属性
slug: /examples/observability/metric/global_attributes
keywords: [指标, 全局属性, prometheus, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry和Prometheus管理全局指标属性以实现一致的指标标签。本示例展示了全局属性配置和管理、跨所有指标自动应用属性、服务级元数据(service.name、service.version)、环境识别属性、一致的指标标签、以及属性继承模式。主要功能包括:集中式属性管理、自动属性传播、语义约定支持、多租户标签、部署环境标签、生产级模式。非常适合实现一致的指标标签、管理服务元数据、实现跨服务的指标聚合、支持多环境部署、便于指标过滤和分组、以及建立企业监控标准。通过本示例可以学习全局属性管理、一致性标签实践、以及企业级监控规范。
hide_title: true
sidebar_position: 1
---

# 指标收集 - 全局属性

## 简介

本示例演示了如何在 `GoFrame` 中使用 `OpenTelemetry` 和 `Prometheus` 集成来实现全局指标属性。主要展示：
- 设置和管理全局属性
- 在多个指标中应用全局属性
- 配置属性作用域和匹配模式
- 组合使用全局属性和局部属性

## 目录结构

```text
.
├── go.mod            # Go模块文件
├── go.sum            # Go模块校验和
└── main.go           # 主程序，演示全局属性使用
```

## 功能特性

本示例展示了以下功能：

1. 全局属性
   - 全局属性配置
   - 属性继承机制
   - 基于模式的应用
   - 版本控制支持

2. 带全局属性的指标类型
   - 带全局属性的计数器
   - 带全局属性的可观察计数器
   - 局部属性组合
   - 属性优先级

3. 属性管理
   - 全局属性作用域
   - 基于版本的过滤
   - 基于模式的过滤
   - 属性继承规则

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
   goframe_metric_demo_counter{const_attr_1="1",global_attr_1="1"} 11
   
   # HELP goframe_metric_demo_observable_counter 这是ObservableCounter使用的简单演示
   goframe_metric_demo_observable_counter{const_attr_2="2",global_attr_1="1"} 10
   ```

## 实现说明

1. 设置全局属性
   ```go
   gmetric.SetGlobalAttributes(gmetric.Attributes{
       gmetric.NewAttribute("global_attr_1", 1), // 全局属性
   }, gmetric.SetGlobalAttributesOption{
       Instrument:        instrument,        // 仅应用于特定的instrument
       InstrumentVersion: instrumentVersion, // 仅应用于特定版本
       InstrumentPattern: "",               // 空模式表示应用于所有指标
   })
   ```

2. 带全局属性的指标
   ```go
   counter := meter.MustCounter(
       "goframe.metric.demo.counter",
       gmetric.MetricOption{
           Help: "计数器示例",
           Unit: "bytes",
           Attributes: gmetric.Attributes{
               gmetric.NewAttribute("const_attr_1", 1), // 局部常量属性
           },
       },
   )
   ```

3. 在可观察指标中使用全局属性
   ```go
   meter.MustRegisterCallback(func(ctx context.Context, obs gmetric.Observer) error {
       obs.Observe(observableCounter, 10) // 全局属性会自动添加
       return nil
   }, observableCounter)
   ```
