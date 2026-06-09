---
title: JWT认证
slug: /examples/httpserver/jwt
keywords: [http, server, jwt, authentication, goframe]
description: 演示在GoFrame HTTP服务器中实现全面的JWT(JSON Web Token)认证，用于安全的API访问控制。本示例展示了带有自定义声明和过期时间的JWT令牌生成、令牌验证和校验中间件、使用HS256/RS256算法进行安全令牌签名、用于延长会话的刷新令牌机制、带有认证中间件的受保护路由实现、对无效或过期令牌的错误处理、以及与GoFrame中间件系统的集成。主要功能包括:用户登录和令牌颁发、无状态认证、令牌刷新模式、基于角色的访问控制(RBAC)集成、安全令牌存储建议、生产级安全实践。非常适合构建带有认证的REST API、实现微服务安全、需要无状态认证的移动应用后端、以及需要可扩展认证且无需服务器端会话的应用程序。通过本示例可以学习JWT认证的最佳实践、如何实现安全的无状态认证、以及构建安全可扩展的Web服务。
hide_title: true
sidebar_position: 0
---

# GoFrame JWT认证示例

本示例展示了如何在`GoFrame`HTTP服务器中使用 `github.com/golang-jwt/jwt` 包实现`JWT(JSON Web Token)`认证。

## 功能特性

- 用户登录接口，生成`JWT`令牌
- 使用`JWT`中间件保护路由
- 令牌验证和解析
- 受保护资源访问示例
- 标准的`GoFrame`项目结构

## 项目结构

```text
jwt/
├── api/
│   └── v1/
│       └── auth.go         # API接口定义
├── internal/
│   ├── controller/
│   │   └── auth.go        # 业务逻辑实现
│   └── middleware/
│       └── jwt.go         # JWT中间件
└── main.go                # 入口文件
```

## API接口

1. 登录接口: `POST /login`
   ```json
   {
       "username": "admin",
       "password": "password"
   }
   ```

2. 受保护资源: `GET /api/protected`
   - 需要在`Authorization`头部携带`Bearer`令牌
   - 示例: `Authorization: Bearer your-token-here`

## 运行示例

1. 启动服务器:
   ```bash
   go run main.go
   ```

2. 服务器将在`8000`端口启动

## 测试API

1. 登录获取令牌:
   ```bash
   curl -X POST http://localhost:8000/login \
   -H "Content-Type: application/json" \
   -d '{"username":"admin","password":"password"}'
   ```

2. 访问受保护的接口:
   ```bash
   curl http://localhost:8000/api/protected \
   -H "Authorization: Bearer your-token-here"
   ```

## 安全注意事项

- 在生产环境中，请替换硬编码的密钥为安全的值
- 将用户凭证存储在数据库中
- 实现适当的密码哈希
- 考虑实现刷新令牌机制
- 为登录尝试添加速率限制

## 参考资料

有关`JWT`实现的更多详细信息，请参考第三方组件文档：
- [github.com/golang-jwt/jwt](https://github.com/golang-jwt/jwt)
