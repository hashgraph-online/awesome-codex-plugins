---

name: devops/deploy-flyio
description: Fly.io 部署方法论，使用 flyctl CLI 通过 Docker 部署全球边缘后端服务，支持任意语言、PostgreSQL、Redis、Volumes
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署到 Fly.io 时
- 项目使用 Docker 容器部署时
- 需要全球边缘低延迟后端时
  metadata:
  internal: true

---

# Fly.io 部署

## 适用场景

- **Docker 化后端服务**：任意语言（Node.js、Python、Go、Java、Rust、Elixir）
- **全球边缘部署**：需要低延迟、靠近用户的后端
- **有状态服务**：需要持久化存储（Volumes）
- **托管 PostgreSQL**：Fly Postgres
- **后台 Worker / Cron Job**：Machines 模式

## 前置条件

1. 安装 flyctl CLI：

   ```bash
   # macOS
   brew install flyctl
   # Windows（PowerShell）
   iwr https://fly.io/install.ps1 -useb | iex
   # Linux 及其他平台请参考 fly.io 官方文档安装 flyctl
   ```
2. 登录 Fly.io：`fly auth login`（需要用户交互完成授权）
3. 验证登录：`fly auth whoami`

## 部署流程

### 1. 准备 Dockerfile

Fly.io 是 **Docker 优先**的平台，项目必须有 `Dockerfile`。

**多阶段构建示例（Node.js）**：
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

**Python 示例**：
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Go 示例**：
```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/server .
EXPOSE 8080
CMD ["./server"]
```

### 2. 初始化 Fly 应用

```bash
# 交互式初始化（会生成 fly.toml）
fly launch

# 非交互式初始化
fly launch --name my-api --region iad --no-deploy
```

`fly launch` 会自动检测 Dockerfile 并生成 `fly.toml` 配置。

### 3. fly.toml 配置

```toml
app = "my-api"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  [http_service.concurrency]
    type = "requests"
    soft_limit = 200
    hard_limit = 400

[[vm]]
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1

[env]
  NODE_ENV = "production"
  PORT = "3000"

# 健康检查
[http_service.checks]
  [http_service.checks.health]
    path = "/health"
    interval = "30s"
    timeout = "5s"
    grace_period = "10s"
```

### 4. 部署

```bash
# 部署
fly deploy

# 部署到指定 region
fly deploy --region iad

# 查看部署状态
fly status

# 查看实时日志
fly logs
```

**部署输出示例**：
```
==> Verifying app config
Validating /path/to/fly.toml
==> Building image
Remote builder fly-builder-xxx ready
==> Creating build context
==> Building image with Docker
...
==> Pushing image to fly
==> Creating release
Release v1 created
--> You can detach the terminal anytime without stopping the deployment

1 desired, 1 placed, 1 healthy, 0 unhealthy
--> v1 deployed successfully
```

### 5. 环境变量与 Secrets

```bash
# 设置 secret（加密存储，不会出现在配置中）
fly secrets set DATABASE_URL="postgres://..."
fly secrets set API_KEY="xxx"

# 列出 secrets
fly secrets list

# 删除 secret
fly secrets unset API_KEY
```

普通环境变量放在 `fly.toml` 的 `[env]` 中。

### 6. 添加 PostgreSQL

```bash
# 创建 Fly Postgres 集群
fly postgres create --name my-db --region iad

# 连接数据库到应用（自动注入 DATABASE_URL）
fly postgres attach my-db --app my-api
```

### 7. 添加 Redis

Fly.io 没有原生 Redis，但可以部署 Upstash Redis 或自己跑 Redis 容器：

```bash
# 使用 Upstash Redis（推荐）
# 在 Fly.io 控制台集成 Upstash，获取 REDIS_URL
```

### 8. Volumes（持久化存储）

```bash
# 创建 Volume
fly volumes create my_data --region iad --size 1

# 在 fly.toml 中挂载
[[mounts]]
  source = "my_data"
  destination = "/data"
```

### 9. 自定义域名

```bash
# 添加自定义域名
fly certs add api.example.com

# 查看证书状态
fly certs list
```

## Machines 模式（后台 Worker / Cron）

Fly Machines 适合运行后台任务：

```toml
# fly.worker.toml
app = "my-worker"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.worker"

[processes]
  app = "node dist/worker.js"
```

```bash
# 部署 worker
fly deploy --config fly.worker.toml
```

## 多区域部署

```bash
# 查看当前 regions
fly regions list

# 添加 region
fly regions add nrt sgd

# 设置自动伸缩
fly autoscale set min=1 max=5
```

## CI/CD 集成

### GitHub Actions 自动部署

```yaml
name: Deploy to Fly.io
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: npm ci
      - run: npm test
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**需要的 Secrets**：
- `FLY_API_TOKEN`：Fly.io API Token（Account → Access Tokens）

## 项目类型适配

| 项目类型                  | Dockerfile 基础镜像                              | 启动命令              |
| ------------------------- | ------------------------------------------------ | --------------------- |
| Node.js (Express/Fastify) | `node:20-alpine`                                 | `node dist/server.js` |
| Python (FastAPI/Flask)    | `python:3.12-slim`                               | `uvicorn main:app`    |
| Go (Gin/Fiber)            | `golang:1.22-alpine` (builder) → `alpine`        | `./server`            |
| Java (Spring Boot)        | `eclipse-temurin:21-jre`                         | `java -jar app.jar`   |
| Rust (Axum/Actix)         | `rust:1.75` (builder) → `debian:bookworm-slim`   | `./server`            |
| Elixir (Phoenix)          | `elixir:1.16` (builder) → `debian:bookworm-slim` | `./start`             |

## 检查清单

- [ ] `Dockerfile` 存在且多阶段构建正确
- [ ] `fly.toml` 配置正确（app、region、port、health check）
- [ ] 环境变量已配置（`[env]` + `fly secrets`）
- [ ] 健康检查端点可访问（`/health`）
- [ ] 数据库已连接（如需要）
- [ ] Volumes 已挂载（如有状态服务）
- [ ] 部署 URL 可访问（`*.fly.dev` 或自定义域名）
- [ ] CI/CD Secrets 已配置
