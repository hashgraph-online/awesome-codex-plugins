---

name: devops/deploy-netlify
description: Netlify 部署方法论，使用 netlify CLI 部署前端应用、静态站点和 Serverless Functions
version: 1.0.0
agent: devops
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要部署到 Netlify 时
- 项目是静态站点或前端 SPA 时
- 需要 Serverless Functions 时
  metadata:
  internal: true

---

# Netlify 部署

## 适用场景

- 前端应用（React、Vue、Svelte、Next.js）
- 静态站点（Hugo、Astro、Gatsby、Eleventy）
- Serverless Functions（Netlify Functions）
- 表单处理、身份认证（Netlify Identity）
- 边缘函数（Netlify Edge Functions）

## 前置条件

1. 安装 Netlify CLI：`npm i -g netlify-cli`
2. 登录 Netlify：`netlify login`（需要用户交互完成授权）
3. 验证登录：`netlify status`
4. 项目根目录有 `package.json`（Node.js 项目）

## 部署流程

### 1. 构建项目

```bash
npm run build
# 产物目录通常为 dist/、build/ 或 .next/
```

### 2. 初始化 Netlify 项目

```bash
# 在项目根目录初始化（交互式）
netlify init

# 或链接到已有项目
netlify link
```

`netlify init` 会创建 `netlify.toml` 配置文件。

### 3. netlify.toml 配置

```toml
[build]
  command = "npm run build"
  publish = "dist"
  functions = "netlify/functions"

[build.environment]
  NODE_VERSION = "20"
  NPM_FLAGS = "--no-audit --no-fund"

# SPA 路由重写
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# 自定义响应头
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"

# 边缘函数
[[edge_functions]]
  function = "auth"
  path = "/api/*"
```

### 4. 部署

```bash
# 预览部署（staging）
netlify deploy

# 生产部署
netlify deploy --prod

# 指定产物目录部署
netlify deploy --dir=dist --prod
```

**部署输出示例**：
```
Deploy path:        /path/to/project/dist
Configuration:      /path/to/project/netlify.toml
Deploying to main site URL...
✔ Finished hashing 32 files
✔ CDN requesting 12 files
✔ Finished uploading 12 assets
✔ Deploy is live!

Logs:              https://app.netlify.com/sites/my-site/deploys/xxx
Website URL:       https://my-site.netlify.app
Unique Deploy URL: https://xxx--my-site.netlify.app
```

### 5. 环境变量管理

```bash
# 设置环境变量
netlify env:set DATABASE_URL "postgres://..."

# 导入 .env 文件
netlify env:import .env

# 列出环境变量
netlify env:list

# 删除环境变量
netlify env:unset DATABASE_URL

# 拉取环境变量到本地
netlify env:pull .env
```

### 6. 域名绑定

```bash
# 添加自定义域名
netlify domains:add example.com

# 列出域名
netlify domains:list
```

## Netlify Functions

### 创建 Serverless Function

在 `netlify/functions/` 目录下创建函数：

```javascript
// netlify/functions/hello.js
exports.handler = async (event) => {
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'Hello from Netlify Functions!' }),
  };
};
```

```typescript
// netlify/functions/api.ts
import type { Handler } from '@netlify/functions';

const handler: Handler = async (event) => {
  return {
    statusCode: 200,
    body: JSON.stringify({ path: event.path }),
  };
};

export { handler };
```

### 本地测试 Functions

```bash
# 启动本地开发服务器（含 Functions）
netlify dev
```

## CI/CD 集成

### Git 自动部署

Netlify 原生支持 Git 集成，连接仓库后：
- push 到 `main` 分支 → 自动生产部署
- push 到其他分支或 PR → 自动预览部署

### GitHub Actions 手动触发

```yaml
name: Deploy to Netlify
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
      - run: npm run build
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v3
        with:
          publish-dir: dist
          production-deploy: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

**需要的 Secrets**：
- `NETLIFY_AUTH_TOKEN`：Netlify Personal Access Token（User Settings → Applications → Personal access tokens）
- `NETLIFY_SITE_ID`：站点 ID（Site Settings → General → Site ID）

## 项目类型适配

| 项目类型         | publish 目录 | build 命令                  | 说明                                |
| ---------------- | ------------ | --------------------------- | ----------------------------------- |
| Vite (React/Vue) | dist         | `npm run build`             | 需配置 SPA redirect                 |
| Next.js 静态导出 | out          | `next build && next export` | next.config 配置 `output: 'export'` |
| Create React App | build        | `npm run build`             | 需配置 SPA redirect                 |
| Gatsby           | public       | `npm run build`             | -                                   |
| Hugo             | public       | `hugo`                      | 需设置 HUGO_VERSION 环境变量        |
| Astro            | dist         | `npm run build`             | -                                   |

## 检查清单

- [ ] `netlify.toml` 配置正确（build command、publish dir）
- [ ] 环境变量已配置（`netlify env:set`）
- [ ] 构建命令本地验证通过（`npm run build`）
- [ ] SPA 路由重写已配置（如需要）
- [ ] 生产部署 URL 可访问
- [ ] 自定义域名已绑定（如需要）
- [ ] Functions 测试通过（`netlify dev`）
- [ ] CI/CD Secrets 已配置
