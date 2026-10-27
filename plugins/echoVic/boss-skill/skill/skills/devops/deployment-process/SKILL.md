---

name: devops/deployment-process
description: 部署流程与CI/CD配置，包含部署平台选择、部署策略和环境管理
version: 2.2.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要配置部署流程时
- 需要设置CI/CD时
- 需要选择部署平台时
  metadata:
  internal: true

---

# 部署流程与 CI/CD

## 部署平台选择

**核心原则：先检测现有部署配置，再决定流程。** 项目可能已经有 `vercel.json` / `render.yaml` 等配置，应直接复用，不要重复推荐。

### 现有部署配置检测（第一步）

扫描项目根目录，按以下优先级匹配已有配置：

| 检测到的文件                      | 判定平台         | 对应 Skill                                     |
| --------------------------------- | ---------------- | ---------------------------------------------- |
| `vercel.json` 或 `.vercel/`       | Vercel           | `devops/deploy-vercel`                         |
| `wrangler.toml` / `wrangler.json` | Cloudflare       | `devops/deploy-cloudflare`                     |
| `render.yaml` / `render.yml`      | Render           | `devops/deploy-render`                         |
| `netlify.toml` / `netlify.json`   | Netlify          | `devops/deploy-netlify`                        |
| `railway.json` / `railway.toml`   | Railway          | `devops/deploy-railway`                        |
| `fly.toml`                        | Fly.io           | `devops/deploy-flyio`                          |
| `Dockerfile`（无上述平台配置）    | Render 或 Fly.io | `devops/deploy-render` / `devops/deploy-flyio` |

**检测命令**：
```bash
ls vercel.json wrangler.toml render.yaml render.yml netlify.toml railway.json railway.toml fly.toml Dockerfile 2>/dev/null
```

- 检测到平台配置 → **直接使用该平台**，加载对应 Skill
- 未检测到任何配置 → 进入下一步，按项目类型推荐

### 平台选择决策表（第二步，无现有配置时）

| 项目类型                        | 推荐平台   | 备选平台                   | 对应 Skill                 |
| ------------------------------- | ---------- | -------------------------- | -------------------------- |
| Next.js / React / Vue 前端      | Vercel     | Netlify / Cloudflare Pages | `devops/deploy-vercel`     |
| 静态站点（HTML/CSS/JS）         | Vercel     | Netlify / Cloudflare Pages | `devops/deploy-vercel`     |
| 边缘计算 / Serverless API       | Cloudflare | Vercel                     | `devops/deploy-cloudflare` |
| 全栈应用 + 数据库               | Render     | Railway                    | `devops/deploy-render`     |
| Node.js 后端 API                | Railway    | Render / Fly.io            | `devops/deploy-railway`    |
| Python/Django/FastAPI 后端      | Railway    | Render / Fly.io            | `devops/deploy-railway`    |
| Go/Rust 后端                    | Fly.io     | Railway / Render           | `devops/deploy-flyio`      |
| Java/Spring Boot 后端           | Railway    | Fly.io                     | `devops/deploy-railway`    |
| Docker 化应用                   | Fly.io     | Render                     | `devops/deploy-flyio`      |
| 有状态服务（需 Volume）         | Fly.io     | -                          | `devops/deploy-flyio`      |
| 全球边缘后端                    | Fly.io     | Cloudflare                 | `devops/deploy-flyio`      |
| 静态站点 + Serverless Functions | Netlify    | Vercel                     | `devops/deploy-netlify`    |

### 平台能力对比

| 能力                 | Vercel       | Cloudflare    | Render    | Netlify       | Railway   | Fly.io       |
| -------------------- | ------------ | ------------- | --------- | ------------- | --------- | ------------ |
| 前端 SPA             | ✅ 原生      | ✅ Pages      | ✅ Static | ✅ 原生       | ⚠️ 可部署 | ⚠️ 可部署    |
| Next.js SSR          | ✅ 最佳      | ⚠️ 需 adapter | ✅        | ⚠️ 需 adapter | ✅        | ⚠️ 需 Docker |
| Node.js 后端         | ⚠️ Functions | ✅ Workers    | ✅        | ⚠️ Functions  | ✅ 原生   | ✅           |
| Python 后端          | ❌           | ❌            | ✅        | ❌            | ✅ 原生   | ✅           |
| Go/Rust 后端         | ❌           | ❌            | ✅        | ❌            | ✅ 原生   | ✅ 最佳      |
| Java 后端            | ❌           | ❌            | ✅        | ❌            | ✅ 原生   | ✅           |
| Serverless Functions | ✅           | ✅ Workers    | ✅        | ✅            | ❌        | ❌           |
| 托管 PostgreSQL      | ❌           | ✅ D1         | ✅        | ❌            | ✅        | ✅           |
| 托管 MySQL           | ❌           | ❌            | ❌        | ❌            | ✅        | ❌           |
| 托管 Redis           | ❌           | ❌            | ✅        | ❌            | ✅        | ⚠️ Upstash   |
| Docker 支持          | ❌           | ❌            | ✅        | ❌            | ✅        | ✅ 原生      |
| 持久化 Volume        | ❌           | ❌            | ❌        | ❌            | ❌        | ✅           |
| 边缘计算             | ✅ Edge      | ✅ Workers    | ❌        | ✅ Edge       | ❌        | ✅ 全球      |
| 免费额度             | generous     | generous      | 有限      | generous      | $5 试用   | 有限         |
| 全球 CDN             | ✅           | ✅            | ❌        | ✅            | ❌        | ✅           |

### 选择逻辑

1. **检测现有部署配置**：扫描根目录的 `vercel.json` / `wrangler.toml` / `render.yaml` / `netlify.toml` / `railway.json` / `fly.toml` / `Dockerfile`
2. **命中现有配置** → 直接使用该平台，加载对应 Skill
3. **未命中** → 检测项目类型，按决策表推荐平台
4. **加载平台 Skill**：使用 `Skill(skill: "devops/deploy-<platform>")` 获取具体部署命令
5. **执行部署**：按平台 Skill 的步骤执行

## 部署策略

| 策略       | 说明         | 适用场景       |
| ---------- | ------------ | -------------- |
| 蓝绿部署   | 两套环境切换 | 需要快速回滚   |
| 滚动部署   | 逐步替换实例 | 零停机部署     |
| 金丝雀部署 | 小流量验证   | 风险较高的更新 |

## CI/CD 流程

```
代码提交 → 自动构建 → 自动测试 → 部署到预览环境 → 合并后部署到生产环境
```

### GitHub Actions 通用模板

```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test
      - run: npm run build
      # 部署步骤由平台 Skill 提供
```

## 环境配置

| 环境    | 用途     | 数据         |
| ------- | -------- | ------------ |
| local   | 本地开发 | 测试数据     |
| dev     | 开发测试 | 测试数据     |
| staging | 预发布   | 生产数据副本 |
| prod    | 生产环境 | 真实数据     |

## 环境变量管理原则

1. **模板文件**：确保 `.env.example` 包含所有必需变量（不含真实值）
2. **文档记录**：在 deploy-report.md 中列出所有环境变量及其用途
3. **安全原则**：
   - 敏感变量（数据库密码、API 密钥）必须通过环境变量注入，不得硬编码
   - `.env` 文件必须在 `.gitignore` 中
   - 生产环境使用平台的 Secrets 管理
