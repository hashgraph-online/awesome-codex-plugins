# 技术栈运行时检测协议

本文档定义了统一的技术栈检测流程。所有 Agent 在执行任务前，必须先按此协议检测项目技术栈，避免硬编码假设。

---

## 检测流程

### Step 1: 语言/平台检测

扫描项目根目录的标志文件：

| 标志文件 | 语言/平台 |
|---------|----------|
| `package.json` | Node.js / JavaScript / TypeScript |
| `go.mod` | Go |
| `pyproject.toml` / `requirements.txt` / `setup.py` | Python |
| `Cargo.toml` | Rust |
| `pom.xml` / `build.gradle` / `build.gradle.kts` | Java / Kotlin |
| `*.csproj` / `*.sln` | .NET / C# |
| `Package.swift` | Swift |
| `pubspec.yaml` | Dart / Flutter |
| `Gemfile` | Ruby |
| `mix.exs` | Elixir |
| `Anchor.toml` | Solana (Anchor) |

如果同时存在多个标志文件（如 `package.json` + `go.mod`），说明是多语言项目，需要同时支持。

### Step 2: 框架检测

根据 Step 1 检测到的语言，读取对应的 manifest 文件内容：

**Node.js** — 读取 `package.json` 的 `dependencies` + `devDependencies`：

| 依赖名 | 框架 | 类型 |
|--------|------|------|
| `next` | Next.js | 全栈 |
| `nuxt` | Nuxt | 全栈 |
| `react` | React | 前端 |
| `vue` | Vue | 前端 |
| `svelte` / `@sveltejs/kit` | Svelte / SvelteKit | 前端/全栈 |
| `angular` / `@angular/core` | Angular | 前端 |
| `express` | Express | 后端 |
| `fastify` | Fastify | 后端 |
| `@nestjs/core` | NestJS | 后端 |
| `hono` | Hono | 后端 |
| `koa` | Koa | 后端 |

**Python** — 读取 `pyproject.toml` 的 `[project.dependencies]` 或 `requirements.txt`：

| 依赖名 | 框架 |
|--------|------|
| `fastapi` | FastAPI |
| `django` | Django |
| `flask` | Flask |
| `starlette` | Starlette |

**Go** — 读取 `go.mod` 的 `require` 块：

| 模块路径 | 框架 |
|---------|------|
| `github.com/gin-gonic/gin` | Gin |
| `github.com/gofiber/fiber` | Fiber |
| `github.com/labstack/echo` | Echo |
| `github.com/gorilla/mux` | Gorilla Mux |

**Rust** — 读取 `Cargo.toml` 的 `[dependencies]`：

| 依赖名 | 框架 |
|--------|------|
| `actix-web` | Actix Web |
| `axum` | Axum |
| `rocket` | Rocket |
| `yew` | Yew (前端) |

**Java** — 检查 `pom.xml` 或 `build.gradle` 内容：

| 关键字 | 框架 |
|--------|------|
| `spring-boot` | Spring Boot |
| `quarkus` | Quarkus |
| `micronaut` | Micronaut |

### Step 3: 测试框架检测

| 语言 | 检测方式 | 常见框架 |
|------|---------|---------|
| Node.js | `package.json` scripts.test + devDependencies | vitest, jest, mocha, node:test, playwright, cypress |
| Python | pyproject.toml / 命令检测 | pytest, unittest |
| Go | 内置 | `go test` (testing 包) |
| Rust | 内置 | `cargo test` (#[test]) |
| Java | pom.xml / build.gradle | JUnit 5, TestNG |

### Step 4: ORM / 数据库检测

| 依赖 | 工具 | 语言 |
|------|------|------|
| `prisma` / `@prisma/client` | Prisma | Node.js |
| `typeorm` | TypeORM | Node.js |
| `drizzle-orm` | Drizzle | Node.js |
| `sequelize` | Sequelize | Node.js |
| `sqlalchemy` | SQLAlchemy | Python |
| `django.db` | Django ORM | Python |
| `gorm.io/gorm` | GORM | Go |
| `diesel` | Diesel | Rust |

### Step 5: 包管理器检测

| 标志文件 | 包管理器 |
|---------|---------|
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |
| `bun.lockb` | bun |

### Step 6: 构建工具检测

| 标志文件 | 构建工具 |
|---------|---------|
| `vite.config.*` | Vite |
| `webpack.config.*` | Webpack |
| `turbopack.config.*` | Turbopack |
| `esbuild.config.*` / `build.mjs`（含 esbuild import） | esbuild |
| `rollup.config.*` | Rollup |
| `parcel` in package.json scripts | Parcel |
| `.swcrc` | SWC |

### Step 7: 部署环境检测

| 标志文件 | 部署环境 |
|---------|---------|
| `Dockerfile` / `docker-compose.yml` | Docker |
| `vercel.json` / `.vercel/` | Vercel |
| `netlify.toml` | Netlify |
| `fly.toml` | Fly.io |
| `railway.json` / `railway.toml` | Railway |
| `k8s/` / `kubernetes/` / `*.yaml`（含 kind: Deployment） | Kubernetes |
| `serverless.yml` | Serverless Framework |
| `.github/workflows/*.yml`（含 deploy） | GitHub Actions CD |

### Step 8: Monorepo 检测

| 标志文件 | Monorepo 工具 |
|---------|-------------|
| `pnpm-workspace.yaml` | pnpm workspace |
| `lerna.json` | Lerna |
| `nx.json` | Nx |
| `turbo.json` | Turborepo |
| `rush.json` | Rush |
| `workspaces` in package.json | npm/yarn workspaces |

### Step 9: 源码扫描隔离

`.boss/` 是 Boss orchestration artifacts，不是业务源码。任何会自动扫描工作树的工具（构建器、CSS 工具、测试发现器、文档/内容索引器、代码生成器）都必须把 `.boss/` 排除在源码输入之外，避免文档里的代码示例或日志片段被当作真实代码处理。

已知适配器：

| 工具 | 风险 | 处理方式 |
|------|------|----------|
| Tailwind v4 | 自动 source detection 可能把 `.boss/*.md` 里的 utility-like 字面量当作 class 编译 | 在 Tailwind CSS 入口加入 `@source not "<relative-path-to-.boss>";` |

注意：Markdown 里的 fenced code block + 语言标识是文档可读性要求，但不是构建隔离边界；源码扫描隔离必须由工具配置或入口文件明确表达。

---

## 输出格式

检测完成后，将结果整理为以下格式，供后续决策使用：

```markdown
## 技术栈概况

| 维度 | 检测结果 |
|------|---------|
| 语言 | [检测到的语言] |
| 前端框架 | [检测到的框架 或 "无前端"] |
| 后端框架 | [检测到的框架 或 "无后端"] |
| 测试框架 | [检测到的框架] |
| ORM/数据库 | [检测到的工具 或 "无 ORM"] |
| 包管理器 | [检测到的包管理器] |
| 构建工具 | [检测到的工具 或 "未检测到"] |
| 部署环境 | [检测到的环境 或 "未检测到"] |
| Monorepo | [检测到的工具 或 "否"] |
| 源码扫描隔离 | [已排除 .boss/ / 需补充配置 / 不适用] |
```

---

## 使用原则

1. **检测优先，不做假设**：永远基于实际检测结果做决策，不预设项目使用某个特定框架
2. **多语言友好**：如果检测到多种语言/框架，输出中全部列出
3. **缺失容错**：如果某个维度无法检测到（如无 ORM），标记为"未检测到"而非假设一个默认值
4. **增量检测**：如果项目是新建的（无 manifest 文件），由 Agent 根据需求决定技术选型，并在产物中记录选型理由
5. **缓存复用**：首次检测后将结果缓存到 `.boss/<feature>/.meta/tech-stack.json`，后续 Agent 直接读取缓存
