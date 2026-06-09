---
title: HTTP带数据库
slug: /examples/observability/trace/http-with-db
keywords: [链路跟踪, http, 数据库, goframe]
description: 演示在GoFrame中使用OpenTelemetry实现HTTP服务与数据库操作的全面分布式跟踪。本示例展示了从HTTP请求到数据库查询的端到端trace埋点、包括MySQL和Redis操作的自动数据库操作跟踪、贯穿整个请求生命周期的trace上下文传播、HTTP处理器与数据库调用之间的span关系、数据库查询的性能监控、以及与GoFrame的ORM和缓存组件集成。主要功能包括:全栈trace可见性、自动数据库查询埋点、慢查询检测、连接池监控、缓存操作跟踪、生产级可观测性。非常适合监控全栈应用性能、调试数据库相关问题、优化查询性能、确保数据驱动应用的端到端可观测性、以及构建全面的监控解决方案。通过本示例可以学习如何实现全链路跟踪、数据库性能优化、以及构建高性能可观测的数据应用。
hide_title: true
sidebar_position: 1
---

# 链路跟踪 - HTTP带数据库

## 简介

本示例演示了如何在 `GoFrame` 中实现HTTP服务与数据库交互的分布式跟踪。主要展示：
- 配置HTTP服务的跟踪
- 跟踪数据库操作
- 传播跟踪上下文
- 可视化分布式跟踪

## 环境要求

- `Go` `1.22` 或更高版本
- `GoFrame` 框架
- `GoFrame MySQL` 驱动
- `GoFrame Redis` 驱动
- `GoFrame OpenTelemetry` 跟踪

## 目录结构

```text
.
├── client/          # 客户端示例
│   └── client.go    # 带跟踪的客户端
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

## 配置说明

服务端配置在`server/config.yaml`中定义：

```yaml
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

1. 启动服务端：
   ```bash
   cd server
   go run server.go
   ```

2. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```

3. 查看跟踪：
   在浏览器中打开 http://localhost:16686 查看 `Jaeger` UI中的跟踪信息。

## API接口

服务器提供以下HTTP接口：

1. 插入用户
   ```text
   POST /insert
   请求: {"Name": "string"}
   响应: {"ID": number}
   ```

2. 查询用户
   ```text
   GET /query
   请求: {"ID": number}
   响应: {"User": object}
   ```

3. 删除用户
   ```text
   DELETE /delete
   请求: {"Id": number}
   响应: {}
   ```

## 实现说明

1. 服务端实现
   ```go
   // 配置Redis作为ORM缓存适配器
   g.DB().GetCache().SetAdapter(gcache.NewAdapterRedis(g.Redis()))

   // 启动HTTP服务器
   s := g.Server()
   s.Use(ghttp.MiddlewareHandlerResponse)
   s.Group("/", func(group *ghttp.RouterGroup) {
       group.ALL("/user", new(cTrace))
   })

   // 查询用户信息
   func (c *cTrace) Query(ctx context.Context, req *QueryReq) (res *QueryRes, err error) {
       one, err := g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
           Duration: 5 * time.Second,
           Name:     c.userCacheKey(req.ID),
           Force:    false,
       }).WherePri(req.ID).One()
       if err != nil {
           return nil, err
       }
       res = &QueryRes{
           User: one,
       }
       return
   }
   ```

2. 客户端实现
   ```go
   // 创建新的跟踪span
   ctx, span := gtrace.NewSpan(gctx.New(), "StartRequests")
   defer span.End()

   // 发送HTTP请求
   err = client.PostVar(ctx, "http://127.0.0.1:8000/user/insert", g.Map{
       "name": "john",
   }).Scan(&insertRes)
   ```
