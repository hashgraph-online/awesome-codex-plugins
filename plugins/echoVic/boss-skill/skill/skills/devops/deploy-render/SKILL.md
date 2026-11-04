---

name: devops/deploy-render
description: Render 部署方法论，使用 render.yaml 蓝图和 Render CLI 部署全栈应用（Web 服务、Worker、静态站点、数据库）
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署到 Render 时
- 项目是全栈应用且需要数据库时
- 项目使用 Docker 容器部署时
  metadata:
  internal: true

---

# Render 部署

## 适用场景

- **全栈 Web 应用**：Node.js、Python、Go、Ruby、Rust 后端 + 数据库
- **静态站点**：前端 SPA、文档站点
- **后台 Worker**：异步任务处理、定时任务
- **Docker 化应用**：通过 Dockerfile 部署任意语言应用
- 需要托管 PostgreSQL/Redis 的场景

## 前置条件

1. Render 账号：https://render.com
2. 安装 Render CLI（可选，主要通过 render.yaml 蓝图管理）
3. 项目代码托管在 GitHub/GitLab/Bitbucket（Render 通过 Git 集成部署）

## 部署方式

Render 支持两种部署方式：
1. **render.yaml 蓝图（推荐）**：基础设施即代码，一键创建所有服务和数据库
2. **Dashboard 手动创建**：通过 Web 界面逐个创建服务

## 一、render.yaml 蓝图

`render.yaml` 放在项目根目录，定义所有基础设施。

### 完整示例（全栈应用）

```yaml
services:
  # 前端静态站点
  - type: web
    name: my-frontend
    env: static
    buildCommand: npm ci && npm run build
    staticPublishPath: dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

  # 后端 API 服务
  - type: web
    name: my-api
    env: node
    buildCommand: npm ci && npm run build
    startCommand: npm start
    healthCheckPath: /health
    envVars:
      - key: NODE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: my-db
          property: connectionString
      - key: API_KEY
        sync: false # 需要在 Dashboard 手动设置

  # 后台 Worker
  - type: worker
    name: my-worker
    env: node
    buildCommand: npm ci
    startCommand: npm run worker
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: my-db
          property: connectionString

databases:
  - name: my-db
    databaseName: myapp
    user: myapp
    plan: free # free | starter | standard | pro
    ipAllowList:
      - source: 0.0.0.0/0
        description: allow all (仅开发环境)
```

### 各类型服务配置

#### 1. 静态站点

```yaml
services:
  - type: web
    name: my-site
    env: static
    buildCommand: npm run build
    staticPublishPath: dist
    headers:
      - path: /*
        name: X-Frame-Options
        value: DENY
```

#### 2. Node.js Web 服务

```yaml
services:
  - type: web
    name: my-api
    env: node
    plan: standard
    buildCommand: npm ci && npm run build
    startCommand: node dist/server.js
    healthCheckPath: /health
    autoDeploy: true
    branch: main
    numInstances: 1
```

#### 3. Docker 服务

```yaml
services:
  - type: web
    name: my-app
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    dockerCommand: ./start.sh
    healthCheckPath: /health
```

#### 4. Python Web 服务

```yaml
services:
  - type: web
    name: my-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    healthCheckPath: /health
```

#### 5. Go Web 服务

```yaml
services:
  - type: web
    name: my-api
    env: go
    buildCommand: go build -o server
    startCommand: ./server
    healthCheckPath: /health
```

#### 6. 后台 Worker

```yaml
services:
  - type: worker
    name: my-worker
    env: node
    buildCommand: npm ci
    startCommand: npm run worker
```

#### 7. 定时任务（Cron Job）

```yaml
services:
  - type: cron
    name: my-cron
    env: node
    schedule: "0 2 * * *" # 每天凌晨 2 点
    buildCommand: npm ci
    startCommand: npm run cron
```

### 数据库配置

```yaml
databases:
  - name: my-postgres
    databaseName: myapp
    user: myapp
    plan: starter
    version: "16"
    ipAllowList:
      - source: 10.0.0.0/8
        description: internal

  - name: my-redis
    type: redis
    plan: starter
    maxmemoryPolicy: allkeys-lru
```

### 环境变量

```yaml
envVars:
  # 静态值
  - key: NODE_ENV
    value: production

  # 从服务组同步（所有服务共享）
  - key: SHARED_KEY
    sync: true
    value: some-value

  # 从另一个服务获取
  - key: API_URL
    fromService:
      type: web
      name: my-api
      property: host

  # 从数据库获取连接串
  - key: DATABASE_URL
    fromDatabase:
      name: my-db
      property: connectionString

  # 需要手动设置的密钥
  - key: STRIPE_SECRET_KEY
    sync: false
```

## 二、部署流程

### 通过 Git 自动部署

1. 在 Render Dashboard 连接 Git 仓库
2. Render 自动检测 `render.yaml` 并创建服务
3. 每次 push 到指定分支自动触发部署

### 通过 CLI 触发部署

```bash
# 安装 Render CLI
npm install -g render-cli
# 或 brew install render

# 登录（需要用户交互）
render login

# 触发部署
render services deploy <service-id-or-name>

# 查看部署状态
render services list-deploys <service-id-or-name>
```

### 通过 API 触发部署（备选）

如需直接调用 Render REST API，请在受信任的 CI 环境中使用官方 GitHub Action，详见下方 CI/CD 集成。

## CI/CD 集成

### GitHub Actions 触发部署

使用 Render 官方 GitHub Action 触发部署：

```yaml
name: Deploy to Render
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test
      - name: Trigger Render Deploy
        uses: renderinc/deploy-render-action@v1
        with:
          serviceId: ${{ secrets.RENDER_SERVICE_ID }}
          apiKey: ${{ secrets.RENDER_API_KEY }}
```

**需要的 Secrets**：
- `RENDER_API_KEY`：Render API Key（Account Settings → API Keys）
- `RENDER_SERVICE_ID`：服务 ID（Dashboard 服务页面 URL 中 `srv-xxx`）

## 项目类型适配

| 项目类型       | env 类型 | buildCommand                      | startCommand       |
| -------------- | -------- | --------------------------------- | ------------------ |
| Next.js (Node) | node     | `npm ci && npm run build`         | `npm start`        |
| Vite 静态站点  | static   | `npm ci && npm run build`         | -                  |
| Express API    | node     | `npm ci`                          | `npm start`        |
| Django         | python   | `pip install -r requirements.txt` | `gunicorn app:app` |
| FastAPI        | python   | `pip install -r requirements.txt` | `uvicorn main:app` |
| Gin (Go)       | go       | `go build -o server`              | `./server`         |
| Docker 应用    | docker   | (Dockerfile)                      | (Dockerfile CMD)   |

## 检查清单

- [ ] `render.yaml` 放在项目根目录
- [ ] 所有服务的 buildCommand 和 startCommand 正确
- [ ] 数据库已在 `databases` 中定义
- [ ] 环境变量已配置（敏感变量 `sync: false`）
- [ ] healthCheckPath 已配置（Web 服务）
- [ ] 静态站点配置了 SPA rewrite 路由（如需要）
- [ ] CI/CD 中 Render API Key 和 Service ID 已配置
- [ ] 部署日志无错误，服务状态为 "Live"
