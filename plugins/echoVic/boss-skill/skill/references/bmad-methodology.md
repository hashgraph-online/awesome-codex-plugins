# BMAD 方法论参考文档

## 概述

BMAD（Breakthrough Method of Agile AI-Driven Development）是一种突破性的敏捷 AI 驱动开发方法论，专为人机协作设计，通过专业化的 AI Agent 团队完成完整的软件开发生命周期。

**核心特性**：
- 专业化角色分工
- 产物驱动的协作链
- 三层质量门禁
- 可从任意环节切入的专家小队

---

## 核心理念

### 1. 专业化分工

BMAD 将软件开发流程分解为 9 个专业化角色，每个角色由专门的 AI Agent 承担：

| 角色          | Agent 文件             | 职责                         | 输出产物                                |
| ------------- | ---------------------- | ---------------------------- | --------------------------------------- |
| 产品经理 (PM) | `boss-pm.md`           | 需求分析、PRD 编写           | `prd.md`                                |
| 系统架构师    | `boss-architect.md`    | 技术架构、选型决策、API 契约 | `architecture.md`                       |
| UI/UX 设计师  | `boss-ui-designer.md`  | 界面设计、用户体验           | `ui-spec.md` + `ui-design.json`（可选） |
| 技术负责人    | `boss-tech-lead.md`    | 技术评审、风险评估、实施计划 | `tech-review.md` + `plan.md`            |
| Scrum Master  | `boss-scrum-master.md` | 任务拆解、开发规划           | `tasks.md`                              |
| 前端开发      | `boss-frontend.md`     | 前端代码实现                 | 源代码                                  |
| 后端开发      | `boss-backend.md`      | 后端代码实现                 | 源代码                                  |
| QA 工程师     | `boss-qa.md`           | 测试验证                     | `qa-report.md`                          |
| DevOps        | `boss-devops.md`       | 部署运维                     | `deploy-report.md`                      |

### 2. 产物驱动

产物之间的依赖关系形成协作链，而非简单线性流：

```
prd.md ─┬→ architecture.md → tech-review.md → plan.md → tasks.md → [code] → qa-report.md → deploy-report.md
        ├→ ui-spec.md(opt) ┘
        └→ ui-design.json(opt) ┘
```

> `plan.md`（实施计划）由 Tech Lead 在评审通过后产出，定义模块划分、里程碑和任务拆解指引。Scrum Master 基于 `plan.md` 细化为文件级别的 `tasks.md`。

**规则**：
- 每个产物有明确的上游输入
- 上游产物缺失时，可用用户直接描述的需求替代
- `qa-report.md` 依赖代码 + `prd.md`（QA 需要对照 PRD 验收标准）

### 3. 专家小队

区别于传统的分步确认模式，Boss 采用专家小队模式：
- 可从任意环节切入（需求、架构、开发、测试、部署）
- 默认自动续跑后续所有环节，除非用户主动叫停
- 每个角色有硬性质量要求 + 禁止清单
- 质量门禁在环节间自检

---

## 工作流

### 环节 1：规划（Planning）

**目标**：将用户想法转化为可执行规格

**参与 Agent**：
- PM Agent → 创建 `prd.md`
- Architect Agent → 设计 `architecture.md`（包含 API 契约定义）
- UI Designer Agent → 创建 `ui-spec.md` 和 `ui-design.json`（可选，`--skip-ui` 时跳过）

### 环节 2：拆解（Decomposition）

**目标**：将规格转化为可实施的开发计划

**参与 Agent**：
- Tech Lead Agent → 技术评审 + 实施计划，产出 `tech-review.md` + `plan.md`
- Scrum Master Agent → 基于 `plan.md` 创建详细任务 `tasks.md`

**串行执行**：Tech Lead 评审完成后，Scrum Master 才能拆解任务

**Tech Lead 职责**（非故事分解）：
- 评审架构设计的合理性
- 识别技术风险和依赖
- 可发起 `REVISION_NEEDED` 请求架构师修订

### 环节 3：开发（Development）

**目标**：实现代码并持续验证

**参与 Agent**：
- Frontend Agent + Backend Agent → 并行实现代码
- QA Agent → 对照 PRD 验收标准验证

**工作模式**：
1. 按任务顺序实现代码（前后端并行）
2. 实现中允许 Agent 通过执行中会话层做点对点对齐或小范围 huddle
3. 代码完成后 QA 进行验证
4. 发现问题时，先落执行会话结论，再进入修复或正式修订循环

**质量门禁**：Gate 1（测试门禁）、Gate 2（性能门禁）

### 环节 4：部署（Deployment）

**目标**：部署应用并生成报告

**参与 Agent**：
- DevOps Agent → 部署应用

**产物**：
- `deploy-report.md`
- 可访问的 URL

---

## 质量门禁（Quality Gates）

### 三层门禁体系

| 门禁   | 执行时机   | 检查内容                                                       |
| ------ | ---------- | -------------------------------------------------------------- |
| Gate 0 | 开发完成后 | TypeScript 编译、Lint、npm audit、敏感信息扫描、不安全代码模式 |
| Gate 1 | QA 执行后  | 单元测试、覆盖率（≥70%）、E2E 测试                             |
| Gate 2 | 部署前     | Lighthouse 性能分数（≥80）、API P99 延迟（<500ms）             |

### Gate 0 默认安全检查

Gate 0 内置两类安全检查：
1. **敏感信息扫描**（secrets-scan）：检测 AWS Key、Private Key、GitHub Token、OpenAI Key 等
2. **不安全代码模式**（unsafe-patterns）：检测 `eval()`、`dangerouslySetInnerHTML`、`innerHTML =` 等

### 门禁判断标准

问自己：
- **如果现在把这个代码交给用户，他能正常使用吗？**
- **核心流程有没有遗漏的测试？**
- **有没有明显的性能或安全问题？**

未通过的门禁必须修复后才能进入下一环节，用户强制跳过除外。

---

## 产物管理

### 目录结构

```
.boss/
├── <feature-name>/
│   ├── prd.md              # 产品需求文档
│   ├── architecture.md     # 系统架构文档（含 API 契约）
│   ├── ui-spec.md          # UI/UX 规范（可选）
│   ├── ui-design.json      # 可渲染 UI 设计（可选）
│   ├── tech-review.md      # 技术评审报告
│   ├── plan.md             # 实施计划（模块划分、里程碑、任务拆解指引）
│   ├── tasks.md            # 开发任务（基于 plan.md 细化到文件级别）
│   ├── qa-report.md        # QA 测试报告
│   └── deploy-report.md    # 部署报告
```

### 模板

每种产物都有对应的模板文件，位于 `templates/` 目录：

| 模板                                  | 产物           |
| ------------------------------------- | -------------- |
| `templates/prd.md.template`           | 产品需求文档   |
| `templates/architecture.md.template`  | 架构设计文档   |
| `templates/ui-spec.md.template`       | UI/UX 规范     |
| `templates/ui-design.json.template`   | 可渲染 UI 设计 |
| `templates/tech-review.md.template`   | 技术评审报告   |
| `templates/plan.md.template`          | 实施计划       |
| `templates/tasks.md.template`         | 任务拆解       |
| `templates/qa-report.md.template`     | QA 测试报告    |
| `templates/deploy-report.md.template` | 部署报告       |

---

## Agent 协作协议

### 状态报告

每个 Agent 任务完成后必须在输出末尾声明终态：

```markdown
## 状态

**STATUS**: [DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED | REVISION_NEEDED]
**REASON**: <一句话总结>
```

`STATUS` ∈ `DONE` | `DONE_WITH_CONCERNS` | `NEEDS_CONTEXT` | `BLOCKED` | `REVISION_NEEDED`。
补充字段（concerns / missing / blocker / revision_target 等）在正文中给出证据，
不参与状态判定。详见 `agents/prompts/subagent-protocol.md`。

### 执行中会话闭环

- 任意 Agent 可发起 `ask`、`challenge`、`propose`、`request_change`、`escalate`、`huddle`、`resolve`
- 每条会话都必须 anchored 到 `artifact`、`task`、`scope` 或 `decision`
- 每次 `resolve` 都必须 materialize 为至少一个 executable、single-owner todo，或升级为正式 `REVISION_NEEDED` 修订循环

### 修订循环

当 Tech Lead 发现架构问题时：
1. Tech Lead 输出 `REVISION_NEEDED`，指明 `revision_target` 和 `revision_reason`
2. Architect 接收修订请求，针对性修改
3. 修订最多 2 轮，避免无限循环

### API 契约管理

- Architect 在 `architecture.md` §5 定义 API 契约
- Backend Agent 严格实现契约，偏差需记录
- Frontend Agent 基于契约实现统一 API 服务层
- 类型定义由后端导出，前端对齐

---

## 最佳实践

### 1. 需求描述

好的需求描述应该包含：
- 功能目标
- 用户类型
- 核心场景
- 技术约束（如有）

### 2. 环节选择

- 全新项目 → 从 PM 开始（`/boss` 或 `/boss:pm`）
- 已有需求 → 从架构开始（`/boss:architect`）
- 已有架构 → 从开发开始（`/boss:dev`）
- 只想测试 → `/boss:qa`
- 只想部署 → `/boss:ship`

### 3. 质量门禁

- Gate 0 是基线，所有项目都适用
- 门禁失败时必须修复，不得绕过
- 用户可强制跳过，但需明确告知风险
