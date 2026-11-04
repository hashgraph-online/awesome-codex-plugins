---

name: boss:ship
description: "部署环节：DevOps 构建部署 + 上线前门禁 + 部署报告。专家小队终点环节。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:ship — 构建部署（DevOps）

`/boss:ship` 是专家小队的**部署入口**。以 DevOps 身份完成构建、部署、健康检查，产出 `deploy-report.md`。

**这是专家小队的终点环节**，完成后不再续跑。

## 适合 / 不适合

| 适合 `/boss:ship`    | 不适合                               |
| -------------------- | ------------------------------------ |
| 已过测试、要构建部署 | 还没开发（用 `/boss:dev`）           |
| 补一份可追溯部署报告 | 只是本地跑一下（直接 `npm run dev`） |

## 前置输入

- 可部署的代码
- 建议有 `.boss/<slug>/qa-report.md`（缺失时警告但可强制继续）

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **前置检查**：确认 `qa-report.md` 是否存在。不存在则警告"建议先跑 /boss:qa"，用户可选择强制继续。
3. **部署平台选择（先检测现有配置）**：
   - **第一步：检测现有部署配置**（优先级最高）。扫描根目录：
     - `vercel.json` / `.vercel/` → Vercel
     - `wrangler.toml` → Cloudflare
     - `render.yaml` / `render.yml` → Render
     - `netlify.toml` → Netlify
     - `railway.json` / `railway.toml` → Railway
     - `fly.toml` → Fly.io
     - `Dockerfile`（无上述配置）→ Fly.io 或 Render
     - 检测到则**直接复用该平台**，不重复推荐
   - **第二步：无现有配置时**，按项目类型推荐（见下表）
   - 如用户指定平台（`--platform`），覆盖以上自动检测
   - 加载对应平台方法论 Skill

   | 项目类型                | 推荐平台         | Skill                      |
   | ----------------------- | ---------------- | -------------------------- |
   | Next.js / React / Vue   | Vercel           | `devops/deploy-vercel`     |
   | 静态站点                | Vercel / Netlify | `devops/deploy-vercel`     |
   | 边缘计算 / Workers      | Cloudflare       | `devops/deploy-cloudflare` |
   | 全栈 + 数据库           | Render / Railway | `devops/deploy-render`     |
   | Node.js 后端 API        | Railway          | `devops/deploy-railway`    |
   | Python/Django/FastAPI   | Railway          | `devops/deploy-railway`    |
   | Go/Rust 后端            | Fly.io           | `devops/deploy-flyio`      |
   | Java/Spring Boot        | Railway          | `devops/deploy-railway`    |
   | Docker 化应用           | Fly.io           | `devops/deploy-flyio`      |
   | 有状态服务（需 Volume） | Fly.io           | `devops/deploy-flyio`      |

4. **派发 DevOps Agent**：读取 `agents/boss-devops.md`，执行构建 + 部署 + 健康检查，产出 `.boss/<slug>/deploy-report.md`。
5. **上线前门禁**（参考 `references/quality-gate.md` Gate 2）：
   - 构建成功
   - 服务可访问（HTTP 2xx）
   - 前端 Lighthouse Performance ≥ 80（如适用）
   - 后端 API P99 < 500ms（如适用）
6. **收尾**：输出部署 URL、健康检查结果、门禁结果。

## 用法

```
/boss:ship
/boss:ship user-auth
/boss:ship --platform vercel
/boss:ship --platform cloudflare
/boss:ship --platform render
/boss:ship --platform netlify
/boss:ship --platform railway
/boss:ship --platform flyio
```

## 选项

| 参数                                                               | 说明                             |
| ------------------------------------------------------------------ | -------------------------------- |
| `--platform <vercel\|cloudflare\|render\|netlify\|railway\|flyio>` | 指定部署平台（不指定则自动检测） |
| `--lang <zh\|en>`                                                  | 部署报告语言（默认 zh）          |
