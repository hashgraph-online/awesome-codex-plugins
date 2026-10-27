---

name: devops/deploy-cloudflare
description: Cloudflare 部署方法论，使用 wrangler CLI 部署 Cloudflare Pages（前端/静态站点）和 Workers（Serverless 边缘函数）
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署到 Cloudflare 时
- 项目需要边缘计算（Workers）时
- 项目是静态站点或前端 SPA 时
  metadata:
  internal: true

---

# Cloudflare 部署

## 适用场景

- **Cloudflare Pages**：前端应用（Next.js、React、Vue、SvelteKit、静态站点）
- **Cloudflare Workers**：边缘 Serverless 函数、API、Webhooks
- 需要全球边缘网络低延迟的场景
- 对冷启动和全球分发有要求的应用

## 前置条件

1. 安装 Wrangler CLI：`npm i -g wrangler`
2. 登录 Cloudflare：`npx wrangler login`（需要用户交互完成授权）
3. 验证登录状态：`npx wrangler whoami`

## 部署模式选择

| 项目类型                  | 部署模式             | 命令                    |
| ------------------------- | -------------------- | ----------------------- |
| 前端应用 / SPA            | Cloudflare Pages     | `wrangler pages deploy` |
| 静态站点                  | Cloudflare Pages     | `wrangler pages deploy` |
| Serverless API / 边缘函数 | Workers              | `wrangler deploy`       |
| Next.js SSR               | Pages (Next adapter) | `wrangler pages deploy` |

## 一、Cloudflare Pages 部署

### 1. 构建项目

```bash
npm run build
# 产物目录通常为 dist/、build/ 或 .next/
```

### 2. 首次部署

```bash
# 部署静态产物到 Cloudflare Pages
npx wrangler pages deploy dist --project-name=my-app
```

**首次部署输出示例**：
```
✨ Compiled Worker successfully
🌍  Uploading... (20.4 MB)
✨ Deployment complete! Take a peek over at https://my-app.pages.dev
```

### 3. 配置 wrangler.toml（Pages 项目）

Pages 项目可以使用 `wrangler.toml` 或命令行参数管理配置：

```toml
name = "my-app"
compatibility_date = "2024-01-01"
pages_build_output_dir = "dist"

[env.production]
name = "my-app"

[env.staging]
name = "my-app-staging"
```

### 4. 环境变量

```bash
# 设置环境变量（Pages）
npx wrangler pages secret put DATABASE_URL

# 列出 secrets
npx wrangler pages secret list

# 删除 secret
npx wrangler pages secret delete DATABASE_URL
```

### 5. 自定义域名

```bash
# 绑定自定义域名到 Pages 项目
npx wrangler pages domain add example.com --project-name=my-app
```

## 二、Cloudflare Workers 部署

### 1. wrangler.toml 配置

```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]

# 路由绑定
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" }
]

# KV 命名空间绑定
[[kv_namespaces]]
binding = "MY_KV"
id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# R2 存储桶绑定
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-bucket"

# D1 数据库绑定
[[d1_databases]]
binding = "DB"
database_name = "my-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 2. 部署 Worker

```bash
# 部署（首次会自动创建）
npx wrangler deploy

# 部署到特定环境
npx wrangler deploy --env staging

# 本地预览
npx wrangler dev
```

### 3. Workers 环境变量与 Secrets

```bash
# 添加 secret
npx wrangler secret put API_KEY

# 列出 secrets
npx wrangler secret list

# 删除 secret
npx wrangler secret delete API_KEY
```

### 4. 创建 KV 命名空间

```bash
# 创建 KV 命名空间
npx wrangler kv namespace create MY_KV

# 写入 KV 数据
npx wrangler kv key put --namespace-id=<ID> mykey myvalue

# 读取 KV 数据
npx wrangler kv key get --namespace-id=<ID> mykey
```

### 5. 创建 R2 存储桶

```bash
# 创建 R2 存储桶
npx wrangler r2 bucket create my-bucket

# 上传文件到 R2
npx wrangler r2 object put my-bucket/file.txt --file=./file.txt
```

## CI/CD 集成

### GitHub Actions 自动部署 Pages

```yaml
name: Deploy to Cloudflare Pages
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
      - run: npm run build
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: my-app
          directory: dist
```

### GitHub Actions 自动部署 Workers

```yaml
name: Deploy Worker
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
      - name: Deploy
        run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

**需要的 Secrets**：
- `CLOUDFLARE_API_TOKEN`：Cloudflare API Token（My Profile → API Tokens → Create Token，选 "Edit Cloudflare Workers" 模板）
- `CLOUDFLARE_ACCOUNT_ID`：账户 ID（Workers 页面右侧栏可获取）

## 项目类型适配

| 项目类型                   | 配置要点                          | 产物目录 |
| -------------------------- | --------------------------------- | -------- |
| Vite (React/Vue)           | `pages_build_output_dir = "dist"` | dist     |
| Next.js 静态导出           | `output: 'export'` in next.config | out      |
| Astro                      | 自动检测                          | dist     |
| SvelteKit                  | 使用 `adapter-cloudflare`         | build    |
| Workers (Hono/itty-router) | `main = "src/index.ts"`           | -        |

## 检查清单

- [ ] `wrangler.toml` 配置正确（项目名、产物目录、绑定）
- [ ] 登录状态有效（`wrangler whoami`）
- [ ] 环境变量与 Secrets 已配置
- [ ] 构建产物存在（dist/ 等）
- [ ] 部署 URL 可访问（`*.pages.dev` 或自定义域名）
- [ ] KV/R2/D1 绑定正确（如使用）
- [ ] CI/CD Secrets 已配置
