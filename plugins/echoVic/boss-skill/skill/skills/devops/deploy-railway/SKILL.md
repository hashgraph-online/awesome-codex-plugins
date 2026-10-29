---

name: devops/deploy-railway
description: Railway 部署方法论，使用 railway CLI 部署后端服务（Node.js、Python、Go、Java、Docker）和托管数据库（PostgreSQL、MySQL、Redis）
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署后端服务到 Railway 时
- 项目需要托管数据库（PostgreSQL/MySQL/Redis）时
- 项目是多语言后端应用时
  metadata:
  internal: true

---

# Railway 部署

## 适用场景

- **后端 API 服务**：Node.js、Python、Go、Java、Ruby、PHP、Rust
- **全栈应用**：后端 + 托管数据库
- **Docker 化应用**：通过 Dockerfile 部署
- **需要托管数据库**：PostgreSQL、MySQL、Redis、MongoDB
- **多服务项目**：一个 project 下管理多个服务 + 数据库

## 前置条件

1. 安装 Railway CLI：`npm i -g @railway/cli`
2. 登录 Railway：`railway login`（需要用户交互完成授权）
3. 验证登录：`railway whoami`

## 部署流程

### 1. 初始化 Railway 项目

```bash
# 在项目根目录初始化（交互式，选择创建新项目或链接已有项目）
railway init
```

### 2. 自动构建检测

Railway 使用 **Nixpacks** 自动检测项目类型并构建，无需手动配置：

| 项目类型 | 检测依据                              | 构建命令                          | 启动命令                       |
| -------- | ------------------------------------- | --------------------------------- | ------------------------------ |
| Node.js  | `package.json`                        | `npm install` + `npm run build`   | `npm start`                    |
| Python   | `requirements.txt` / `pyproject.toml` | `pip install -r requirements.txt` | `python main.py` 或 `gunicorn` |
| Go       | `go.mod`                              | `go build`                        | 编译产物                       |
| Java     | `pom.xml` / `build.gradle`            | `mvn package`                     | `java -jar target/*.jar`       |
| Ruby     | `Gemfile`                             | `bundle install`                  | `rails s` 或 `ruby app.rb`     |
| Docker   | `Dockerfile`                          | Docker build                      | Docker CMD                     |

### 3. 配置启动命令（如自动检测失败）

创建 `railway.json` 或 `railway.toml`：

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "node dist/server.js",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 4. 部署

```bash
# 部署到 Railway
railway up

# 部署并指定环境
railway up --environment production

# 查看部署日志
railway logs
```

**部署输出示例**：
```
✔ Connected to project my-api
✔ Deploying...
✔ Build completed
✔ Deployed to production
🔗 https://my-api-production.up.railway.app
```

### 5. 添加托管数据库

```bash
# 添加 PostgreSQL
railway add --plugin postgresql

# 添加 MySQL
railway add --plugin mysql

# 添加 Redis
railway add --plugin redis

# 添加 MongoDB
railway add --plugin mongodb
```

数据库连接串会自动注入为环境变量（如 `DATABASE_URL`、`REDIS_URL`）。

### 6. 环境变量管理

```bash
# 设置环境变量
railway variables set DATABASE_URL "postgres://..."

# 批量设置（从 .env 文件）
railway variables import .env

# 列出环境变量
railway variables

# 删除环境变量
railway variables unset DATABASE_URL
```

### 7. 自定义域名

```bash
# 添加自定义域名
railway domain add api.example.com
```

## Docker 部署

如果项目有 `Dockerfile`，Railway 会自动使用 Docker 构建：

```dockerfile
# 多阶段构建示例
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
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

指定 Docker 构建：

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  }
}
```

## 多服务项目

一个 Railway project 可以包含多个服务：

```bash
# 后端服务
cd backend && railway init --name my-backend

# 前端服务
cd ../frontend && railway init --name my-frontend

# 数据库（共享给所有服务）
railway add --plugin postgresql
```

## CI/CD 集成

### GitHub 自动部署

Railway 原生支持 Git 集成，连接仓库后 push 自动部署。

### GitHub Actions 手动触发

```yaml
name: Deploy to Railway
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
      - name: Deploy to Railway
        run: railway up --environment production
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**需要的 Secrets**：
- `RAILWAY_TOKEN`：Railway API Token（Account Settings → API Tokens）

## 项目类型适配

| 项目类型               | builder    | startCommand 示例                        |
| ---------------------- | ---------- | ---------------------------------------- |
| Express/Koa (Node)     | NIXPACKS   | `npm start`                              |
| FastAPI/Flask (Python) | NIXPACKS   | `uvicorn main:app` 或 `gunicorn app:app` |
| Gin/Fiber (Go)         | NIXPACKS   | `./server`                               |
| Spring Boot (Java)     | NIXPACKS   | `java -jar target/app.jar`               |
| Rails (Ruby)           | NIXPACKS   | `rails s -b 0.0.0.0`                     |
| Docker 应用            | DOCKERFILE | (Dockerfile CMD)                         |

## 检查清单

- [ ] `railway.json` 或 `railway.toml` 配置正确（如需要）
- [ ] 启动命令正确（`startCommand` 或 Nixpacks 自动检测）
- [ ] 数据库已添加（如需要）
- [ ] 环境变量已配置（`railway variables set`）
- [ ] 健康检查端点可访问
- [ ] 部署 URL 可访问（`*.up.railway.app` 或自定义域名）
- [ ] CI/CD Secrets 已配置
