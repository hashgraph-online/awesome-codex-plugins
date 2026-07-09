---
name: shared/tech-stack-detection
description: 检测项目技术栈的通用方法，通过分析配置文件识别语言、框架、工具链
version: 1.0.0
agent: shared
type: methodology
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
  - 需要了解项目技术栈时
  - 技术选型前需要检测现有技术时
  - 生成框架特定的代码或配置时
---

# 技术栈检测方法

## 适用场景

在进行技术选型、架构设计、代码生成前，需要先了解项目当前使用的技术栈，以便：
- 遵循项目现有的技术选择
- 生成符合项目规范的代码
- 避免引入不兼容的技术

## 检测方法

### 1. 检测配置文件

使用 `Read` 或 `Glob` 工具检测项目根目录的配置文件：

#### JavaScript/TypeScript 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `package.json` | Node.js 项目配置 | dependencies, devDependencies, scripts |
| `tsconfig.json` | TypeScript 配置 | 确认使用 TypeScript |
| `next.config.js` | Next.js 配置 | 确认使用 Next.js |
| `vite.config.js` | Vite 配置 | 确认使用 Vite |
| `nuxt.config.js` | Nuxt 配置 | 确认使用 Nuxt |

**检测命令**：
```bash
# 检测是否存在
ls package.json tsconfig.json next.config.js vite.config.js 2>/dev/null

# 读取 package.json
Read(file_path: "package.json")
```

**关键依赖识别**：
- `react`: React 项目
- `vue`: Vue 项目
- `next`: Next.js 项目
- `@angular/core`: Angular 项目
- `express`: Express 后端
- `fastify`: Fastify 后端
- `prisma`: Prisma ORM
- `typeorm`: TypeORM

#### Python 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `requirements.txt` | pip 依赖 | 依赖列表 |
| `pyproject.toml` | Poetry/PDM 配置 | 依赖和项目配置 |
| `Pipfile` | Pipenv 配置 | 依赖 |
| `setup.py` | 包配置 | 项目元数据 |

**关键依赖识别**：
- `django`: Django 项目
- `flask`: Flask 项目
- `fastapi`: FastAPI 项目
- `sqlalchemy`: SQLAlchemy ORM
- `pytest`: 使用 pytest 测试

#### Go 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `go.mod` | Go 模块配置 | 依赖和 Go 版本 |
| `go.sum` | 依赖校验和 | 确认依赖锁定 |

**关键依赖识别**：
- `github.com/gin-gonic/gin`: Gin 框架
- `github.com/gofiber/fiber`: Fiber 框架
- `gorm.io/gorm`: GORM ORM

#### Rust 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `Cargo.toml` | Cargo 配置 | 依赖和项目配置 |
| `Cargo.lock` | 依赖锁定 | 确认依赖版本 |

**关键依赖识别**：
- `actix-web`: Actix Web 框架
- `axum`: Axum 框架
- `tokio`: 异步运行时

#### Java/Kotlin 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `pom.xml` | Maven 配置 | 依赖和插件 |
| `build.gradle` | Gradle 配置 | 依赖和任务 |

**关键依赖识别**：
- `spring-boot-starter`: Spring Boot 项目
- `quarkus`: Quarkus 项目
- `micronaut`: Micronaut 项目

#### Ruby 生态

| 文件 | 说明 | 检测内容 |
|------|------|----------|
| `Gemfile` | Bundler 配置 | 依赖 |
| `Gemfile.lock` | 依赖锁定 | 确认依赖版本 |

**关键依赖识别**：
- `rails`: Ruby on Rails 项目
- `sinatra`: Sinatra 项目

### 2. 检测数据库配置

| 文件/目录 | 说明 |
|-----------|------|
| `prisma/schema.prisma` | Prisma 数据库配置 |
| `drizzle.config.ts` | Drizzle ORM 配置 |
| `ormconfig.json` | TypeORM 配置 |
| `alembic/` | Python Alembic 迁移 |
| `migrations/` | 数据库迁移目录 |

**数据库类型识别**：
- `postgresql://`: PostgreSQL
- `mysql://`: MySQL
- `mongodb://`: MongoDB
- `sqlite:`: SQLite
- `redis://`: Redis

### 3. 检测部署配置

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker 容器化 |
| `docker-compose.yml` | Docker Compose 多容器 |
| `vercel.json` | Vercel 部署 |
| `.github/workflows/` | GitHub Actions CI/CD |
| `netlify.toml` | Netlify 部署 |
| `railway.json` | Railway 部署 |

### 4. 检测测试框架

#### JavaScript/TypeScript

| 文件/依赖 | 框架 |
|-----------|------|
| `jest.config.js` | Jest |
| `vitest.config.js` | Vitest |
| `playwright.config.js` | Playwright |
| `cypress.json` | Cypress |

#### Python

| 依赖 | 框架 |
|------|------|
| `pytest` | pytest |
| `unittest` | unittest (内置) |

#### Go

| 文件 | 框架 |
|------|------|
| `*_test.go` | Go 内置测试 |

## 检测流程

### 步骤1：检测项目类型

```bash
# 使用 Glob 查找配置文件
Glob(pattern: "{package.json,go.mod,Cargo.toml,pom.xml,requirements.txt,Gemfile}")
```

### 步骤2：读取配置文件

```bash
# 读取主配置文件
Read(file_path: "package.json")  # 或其他检测到的文件
```

### 步骤3：分析依赖

从配置文件中提取：
- **语言和版本**：如 Node.js 18, Python 3.11, Go 1.21
- **主框架**：如 Next.js 14, Django 5.0, Gin
- **数据库**：如 PostgreSQL, MongoDB
- **ORM**：如 Prisma, SQLAlchemy, GORM
- **测试框架**：如 Jest, pytest
- **构建工具**：如 Vite, Webpack, esbuild

### 步骤4：输出检测结果

以结构化格式输出：

```markdown
## 技术栈检测结果

### 语言和运行时
- **语言**：TypeScript
- **运行时**：Node.js 20.x
- **包管理器**：pnpm

### 前端框架
- **框架**：Next.js 14 (App Router)
- **UI 库**：React 18
- **样式**：Tailwind CSS
- **状态管理**：Zustand

### 后端框架
- **框架**：Next.js API Routes
- **ORM**：Prisma
- **数据库**：PostgreSQL

### 测试
- **单元测试**：Vitest
- **E2E 测试**：Playwright

### 部署
- **容器化**：Docker
- **CI/CD**：GitHub Actions
- **托管**：Vercel
```

## 使用示例

### 示例1：检测 Next.js 项目

```bash
# 1. 检测配置文件
Glob(pattern: "package.json")

# 2. 读取 package.json
Read(file_path: "package.json")

# 3. 分析依赖
# 发现: "next": "14.0.0", "react": "18.2.0", "prisma": "5.0.0"

# 4. 输出结果
技术栈：Next.js 14 + React 18 + Prisma + PostgreSQL
```

### 示例2：检测 Python 项目

```bash
# 1. 检测配置文件
Glob(pattern: "{requirements.txt,pyproject.toml}")

# 2. 读取配置
Read(file_path: "pyproject.toml")

# 3. 分析依赖
# 发现: fastapi, sqlalchemy, pytest

# 4. 输出结果
技术栈：FastAPI + SQLAlchemy + PostgreSQL + pytest
```

## 注意事项

1. **优先检测现有项目**：如果项目已存在配置文件，必须遵循现有技术栈
2. **新项目才选型**：只有在没有配置文件时，才进行技术选型
3. **版本兼容性**：注意依赖之间的版本兼容性
4. **生态一致性**：不要混用不同生态的工具（如 npm + poetry）

## 常见错误

❌ **不检测就假设**：直接假设项目使用某技术，而不检测配置文件
❌ **忽略版本**：只检测框架名称，不检测版本号
❌ **混淆生态**：在 Node.js 项目中推荐 Python 工具
❌ **重复检测**：在同一个任务中多次检测相同的配置文件
