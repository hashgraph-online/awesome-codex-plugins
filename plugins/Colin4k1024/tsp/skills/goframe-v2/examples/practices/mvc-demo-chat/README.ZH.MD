---
title: 'MVC开发实例'
slug: '/docs/practices/mvc-demo-chat'
description: '基于GoFrame v2.10.0 MVC模式构建的实时聊天应用，展示WebSocket双向通信、会话管理、HTML模板渲染、昵称唯一性验证和消息限流等功能。'
keywords: [GoFrame, MVC模式, WebSocket, 实时聊天, 会话管理, 模板引擎, HTML渲染, WebSocket聊天, 消息广播, 昵称验证, 限流, 消息节流, 并发安全, 缓存管理, 前后端集成, 全栈应用, Go Web框架, 交互式应用, 用户管理, 实时通信]
hide_title: true
---

# MVC开发示例

## 简介

`mvc-demo-chat`是一个展示`GoFrame MVC(Model-View-Controller)`模式实现的实时聊天应用，采用`WebSocket`技术。它提供了完整的聊天室体验，包括昵称唯一性验证、实时消息广播、用户列表管理和消息发送限流等功能。该示例展示了如何使用`GoFrame`的模板引擎、会话管理和`WebSocket`支持构建交互式全栈`Web`应用。

## 项目结构

```text
mvc-demo-chat/
├── api/                         # API接口定义
│   └── v1/
│       └── chat.go              # 聊天API定义
├── internal/                    # 内部实现
│   ├── cmd/
│   │   └── cmd.go               # 服务器初始化和路由
│   ├── consts/
│   │   ├── consts.go            # 通用常量
│   │   └── consts_chat.go       # 聊天专用常量
│   ├── controller/
│   │   └── chat.go              # 聊天控制器及WebSocket逻辑
│   └── model/
│       └── chat.go              # 聊天消息模型
├── manifest/                    # 交付清单
│   ├── config/
│   │   └── config.yaml          # 服务器和日志配置
│   ├── deploy/                  # 部署配置
│   └── docker/                  # Docker配置
├── resource/                    # 静态资源和模板
│   ├── public/                  # 静态文件（CSS、JavaScript、图片）
│   │   ├── plugin/              # 前端插件
│   │   └── resource/            # 静态资源
│   └── template/                # HTML模板
│       └── chat/
│           ├── include/         # 局部模板
│           └── index.html       # 主页模板
├── main.go                      # 应用程序入口
└── go.mod                       # Go模块定义
```

## 特性

- **实时WebSocket通信**：双向通信实现即时消息传递
- **MVC架构**：使用`Model-View-Controller`模式清晰分离关注点
- **会话管理**：用户会话处理实现昵称持久化
- **模板渲染**：服务端HTML模板渲染与动态内容
- **昵称唯一性验证**：确保聊天室内无重复昵称
- **用户列表广播**：用户加入/离开时实时更新用户列表
- **消息限流**：1秒速率限制防止消息刷屏
- **并发安全操作**：线程安全的用户和昵称管理
- **HTML消毒**：通过`HTML`实体编码防止`XSS`攻击
- **错误处理**：为验证和速率限制提供友好的错误消息
- **OpenAPI文档**：自动生成API文档和`Swagger UI`
- **静态文件服务**：从`resource/public`提供前端资源

## 要求

- `Go 1.23.0`或更高版本

## 安装

```bash
cd /path/to/examples/practices/mvc-demo-chat
go mod tidy
```

## 使用

**启动服务：**

```bash
go run main.go
```

服务将在`http://localhost:8199`启动。

**访问应用：**

- 聊天应用: http://localhost:8199/chat
- `Swagger UI`: http://localhost:8199/swagger
- `OpenAPI`规范: http://localhost:8199/api.json

## 工作原理

### 用户流程

1. **输入昵称**：用户首先输入唯一昵称（`3-21`个字符）
2. **加入聊天**：验证通过后，用户进入聊天室
3. **发送消息**：用户可以发送消息，有1秒限流
4. **实时更新**：所有用户即时看到新消息和用户列表变化
5. **离开聊天**：关闭浏览器标签页会从聊天室移除用户

### 消息类型

应用处理三种类型的消息：

- **`send`**：用户发送的常规聊天消息
- **`list`**：有人加入或离开时的用户列表更新
- **`error`**：验证失败或速率限制的错误消息

### 会话管理

用户昵称存储在会话存储中：

- `ChatName`：验证后的确认昵称
- `ChatNameTemp`：验证期间的临时昵称
- `ChatNameError`：昵称已被占用时的错误消息

## API参考

### GET /chat

显示聊天主页。如果用户未设置昵称则显示昵称输入表单，否则显示聊天界面。

```bash
curl http://localhost:8199/chat
```

### POST /chat/name

设置用户昵称。验证唯一性和长度（最多21个字符）。

**请求：**

```bash
curl -X POST http://localhost:8199/chat/name \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john"
  }'
```

**验证规则：**

- 必填字段
- 最多`21`个字符
- 必须唯一（未被其他用户占用）

**重复时的响应：**

```json
{
  "code": 51,
  "message": "Nickname \"john\" is already token by others",
  "data": null
}
```

### GET /chat/websocket

建立`WebSocket`连接用于实时聊天通信。

**WebSocket URL：**

```
ws://localhost:8199/chat/websocket
```

**消息格式：**

```json
{
  "type": "send",
  "data": "大家好！",
  "name": "john"
}
```

**服务器响应（广播给所有用户）：**

```json
{
  "type": "send",
  "data": "大家好！",
  "name": "john"
}
```

**用户列表更新：**

```json
{
  "type": "list",
  "data": ["alice", "bob", "john"],
  "name": ""
}
```

**错误响应（速率限制）：**

```json
{
  "type": "error",
  "data": "Message sending too frequently, why not a rest first",
  "name": ""
}
```

## 实现细节

### 控制器架构

`hChat`控制器管理所有聊天操作：

```go
type hChat struct {
    Users *gmap.Map    // 聊天中的所有用户（websocket -> 昵称映射）
    Names *gset.StrSet // 所有昵称用于唯一性检查
}
```

**关键特性：**

- **并发安全集合**：使用`gmap.Map`和`gset.StrSet`实现线程安全操作
- **WebSocket管理**：维护活跃的`WebSocket`连接
- **广播机制**：向所有连接的客户端发送消息

### WebSocket生命周期

1. **连接**：用户通过`/chat/websocket`连接
2. **注册**：昵称添加到用户列表，广播给所有客户端
3. **消息循环**：持续从客户端读取消息
4. **断开连接**：从列表中移除用户，通知所有客户端
5. **清理**：连接关闭时清除会话数据

### 速率限制

消息限流使用`GoFrame`的缓存和`TTL`：

```go
cacheKey := fmt.Sprintf("ChatWebSocket:%p", ws)
gcache.SetIfNotExist(ctx, cacheKey, struct{}{}, consts.ChatIntervalLimit)
```

- **限制**：消息间隔1秒
- **方法**：基于指针键的缓存
- **反馈**：违反限制时向用户发送错误消息

### HTML消毒

用户输入经过消毒以防止`XSS`攻击：

- **昵称**：`ghtml.Entities()`转换特殊字符
- **消息**：`ghtml.SpecialChars()`转义HTML实体
- **保护**：防止恶意脚本注入

### 模板渲染

应用使用`GoFrame`的模板引擎：

- **主模板**：`resource/template/chat/index.html`
- **包含文件**：基于会话状态的条件渲染
  - `resource/template/chat/include/main.html`：昵称输入表单
  - `resource/template/chat/include/chat.html`：聊天界面

## 配置

配置通过`manifest/config/config.yaml`管理：

```yaml
server:
  address: ":8199"
  serverRoot: "resource/public"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"
  dumpRouterMap: true
  routeOverWrite: true
  accessLogEnabled: true

logger:
  level: "all"
  stdout: true
```

**关键设置：**

- **serverRoot**：从`resource/public`提供静态文件
- **accessLogEnabled**：记录所有`HTTP`请求
- **dumpRouterMap**：启动时显示路由映射

## 前端集成

应用使用从`resource/public/`提供的静态资源：

- **CSS**：聊天界面样式
- **JavaScript**：`WebSocket`客户端逻辑和`DOM`操作
- **Images**：图标和头像
- **Plugins**：第三方前端库
