---

name: devops/deploy-vercel
description: Vercel 部署方法论，使用 vercel CLI 部署前端和全栈应用（Next.js、React、Vue、静态站点）
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署到 Vercel 时
- 项目使用 Next.js 或 React 框架时
- 需要配置 Vercel 部署配置时
  metadata:
  internal: true

---

# Vercel 部署

## 适用场景

- Next.js / React / Vue / Svelte 等前端框架
- 静态站点（HTML/CSS/JS）
- Serverless Functions（API Routes）
- 全栈应用（Next.js full-stack）

## 前置条件

1. 安装 Vercel CLI：`npm i -g vercel`
2. 登录 Vercel：`vercel login`（需要用户交互完成登录）
3. 项目根目录有 `package.json`

## 部署流程

### 1. 检测 Vercel 配置

```bash
# 检查是否已有 vercel.json
ls vercel.json 2>/dev/null && echo "exists" || echo "missing"
```

### 2. 创建 vercel.json（如不存在）

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "devCommand": "npm run dev",
  "regions": ["iad1"],
  "env": {
    "NODE_ENV": "production"
  }
}
```

**框架自动检测**：Vercel 会自动识别框架，通常无需手动配置 `framework`。

### 3. 首次部署

```bash
# 首次部署（交互式，需要用户确认项目设置）
vercel

# 非交互式部署（CI 环境）
vercel --yes --prod
```

**首次部署输出示例**：
```
Vercel CLI 37.0.0
🔗  Linked to username/project (created .vercel)
🔍  Inspect: https://vercel.com/username/project/xxx
✅  Production: https://project-xxx.vercel.app
```

### 4. 后续部署

```bash
# 预览部署（staging）
vercel

# 生产部署
vercel --prod
```

### 5. 环境变量管理

```bash
# 添加环境变量
vercel env add DATABASE_URL production

# 列出环境变量
vercel env ls

# 删除环境变量
vercel env rm DATABASE_URL production

# 拉取环境变量到本地 .env
vercel env pull .env.local
```

### 6. 域名绑定

```bash
# 添加自定义域名
vercel domains add example.com

# 列出域名
vercel domains ls
```

## CI/CD 集成

### GitHub Actions 自动部署

```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
  pull_request:
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
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: "--prod"
```

**需要的 Secrets**：
- `VERCEL_TOKEN`：Vercel Personal Access Token（Settings → Tokens）
- `ORG_ID`：Vercel 团队/个人 ID
- `PROJECT_ID`：Vercel 项目 ID

## 项目类型适配

| 项目类型         | vercel.json 配置            | 说明                |
| ---------------- | --------------------------- | ------------------- |
| Next.js          | 自动检测                    | 无需额外配置        |
| Vite (React/Vue) | `"outputDirectory": "dist"` | 需指定构建输出      |
| 静态 HTML        | 无需配置                    | 直接部署根目录      |
| SvelteKit        | 自动检测                    | 使用 adapter-vercel |

## 检查清单

- [ ] `vercel.json` 配置正确（buildCommand、outputDirectory）
- [ ] 环境变量已配置（`vercel env add`）
- [ ] 构建命令在本地验证通过（`npm run build`）
- [ ] 生产部署 URL 可访问
- [ ] 自定义域名已绑定（如需要）
- [ ] CI/CD Secrets 已配置
