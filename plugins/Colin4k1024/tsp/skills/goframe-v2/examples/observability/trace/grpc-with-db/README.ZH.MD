---
title: gRPC带数据库
slug: /examples/observability/trace/grpc-with-db
keywords: [链路跟踪, grpc, 数据库, opentelemetry, goframe]
description: 演示在GoFrame中使用OpenTelemetry实现gRPC服务与数据库操作的全面分布式跟踪。本示例展示了从gRPC调用到数据库查询的端到端trace埋点、自动gRPC方法和数据库操作跟踪、RPC通信中的trace上下文传播、服务调用与数据库操作之间的span关系、与tracing集成的服务发现、以及分布式系统的性能监控。主要功能包括:全栈gRPC trace可见性、自动数据库查询埋点、服务网格可观测性、分布式事务跟踪、跨服务trace关联、生产级模式。非常适合监控微服务架构性能、调试分布式gRPC系统、优化数据库查询性能、确保服务网格环境的可观测性、以及构建企业级监控解决方案。通过本示例可以学习如何实现gRPC全链路跟踪、分布式系统性能优化、以及构建高可观测的微服务架构。
hide_title: true
sidebar_position: 1
---

# 链路跟踪 - gRPC带数据库

## 简介

本示例演示了如何在 `GoFrame` 中实现gRPC服务与数据库交互的分布式跟踪。主要展示：
- 配置gRPC服务的跟踪
- 跟踪数据库操作
- 传播跟踪上下文
- 可视化分布式跟踪

## 环境要求

- `Go` `1.22` 或更高版本
- `GoFrame` 框架
- `GoFrame gRPCx`
- `GoFrame MySQL` 驱动
- `GoFrame Etcd` 注册中心
- `GoFrame OpenTelemetry` 跟踪

## 目录结构

```text
.
├── client/          # 客户端示例
│   └── client.go    # 带跟踪的客户端
├── controller/      # 服务控制器
├── protobuf/        # 协议定义
│   └── user/        # 用户服务proto文件
├── server/          # 服务端示例
│   ├── server.go    # 带跟踪的服务端
│   └── config.yaml  # 服务端配置
├── sql.sql         # 数据库模式
├── go.mod          # Go模块文件
└── go.sum          # Go模块校验和
```


## 前置条件

1. 运行 `MySQL` 实例：
   ```bash
   docker run -d --name mysql \
   -p 3306:3306 \
   -e MYSQL_DATABASE=test \
   -e MYSQL_ROOT_PASSWORD=12345678 \
   mysql:5.7
   ```

2. 初始化数据库模式：
   ```bash
   # 连接MySQL容器
   docker exec -i mysql mysql -uroot -p12345678 test < sql.sql
   ```

3. 运行 `Redis` 实例：
   ```bash
   docker run -d --name redis \
   -p 6379:6379 \
   redis:6.0
   ```

4. 运行 `Jaeger` 实例：
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

5. 安装 `Protocol buffer` 编译器：
   ```bash
   # macOS
   brew install protobuf
   
   # 安装protoc-gen-go和protoc-gen-go-grpc
   go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
   ```

## 配置说明

服务端配置在 `server/config.yaml` 中定义：

```yaml
grpc:
  name:            "demo"            # 服务名称
  logStdout:        true            # 启用标准输出日志
  errorLogEnabled:  true            # 启用错误日志
  accessLogEnabled: true            # 启用访问日志
  errorStack:       true            # 启用错误堆栈跟踪

database:
  logger:
    level: "all"                    # 记录所有SQL操作
    stdout: true                    # 打印到标准输出
  default:
    link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
    debug: true                     # 启用调试模式

redis:
  default:
    address: 127.0.0.1:6379        # 默认Redis实例
    db:      0
  cache:
    address: 127.0.0.1:6379        # 缓存Redis实例
    db:      1
```

## 使用说明

1. 生成协议代码：
   ```bash
   cd protobuf
   protoc --go_out=paths=source_relative:. --go-grpc_out=paths=source_relative:. ./user/*.proto
   ```

2. 启动服务端：
   ```bash
   cd server
   go run server.go
   ```

3. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```

4. 查看跟踪：
   在浏览器中打开 http://localhost:16686 查看 `Jaeger` UI中的跟踪信息。

## 实现说明

1. 服务端实现
   ```go
   // 配置服务发现
   grpcx.Resolver.Register(etcd.New("127.0.0.1:2379"))

   // 初始化跟踪
   shutdown, err := otlpgrpc.Init(serviceName, endpoint, traceToken)
   
   // 配置Redis作为ORM缓存适配器
   g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))
   ```

2. 客户端实现
   ```go
   // 创建新的跟踪span
   ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
   defer span.End()

   // 设置跟踪的baggage值
   ctx = gtrace.SetBaggageValue(ctx, "uid", 100)

   // 创建gRPC客户端
   client := user.NewUserClient(grpcx.Client.MustNewGrpcClientConn("demo"))
   ```
