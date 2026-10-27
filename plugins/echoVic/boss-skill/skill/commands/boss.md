---

name: boss
description: "专家小队完整流程入口。从需求分析开始，自动跑完所有环节：PM → Architect → UI → Tech Lead → Scrum Master → Frontend/Backend → QA → DevOps。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# /boss — 专家小队完整流程

`/boss` 是专家小队的**完整流程入口**。从 PM 需求分析开始，自动跑完所有环节直到部署交付。

**默认行为**：一路跑到 ship 终点，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss`                       | 不要用 `/boss`                               |
| ---------------------------------- | -------------------------------------------- |
| 新 feature，从需求到部署全流程     | 单文件修改、小 bug、解释代码                 |
| 需要 `.boss/<feature>/` 可追溯产物 | 用户只补充技术约束（先问应用到哪个 feature） |

只想跑部分环节时，用对应的切片入口（见下节）。

## 执行步骤

1. **Feature slug 归一化**：把用户需求归一化为简短英文 kebab-case slug，创建 `.boss/<slug>/` 目录。
2. **需求澄清**（除非 `--quick`）：检查需求是否包含"做什么 + 给谁用 + 核心场景"，缺失时一次问一个问题。
3. **按续跑链执行**：读取 `references/continuation-chain.md`，从 `pm` 环节开始依次执行：
   - pm → architect → ui（除非 `--skip-ui`）→ review → tasks → dev → qa → ship
4. 每个环节完成后自检硬性要求，不满足则修复。
5. 遇到用户叫停或 `--stop-after` 指定的环节则停止。

## 用法

```
/boss [需求描述] [选项]
```

### 示例

```
/boss 做一个 Todo 应用
/boss 用户认证 --skip-ui
/boss 快速搭建 API 服务 --skip-ui --quick
/boss 轻量模式 --skip-ui --quick
```

### 选项

| 参数                  | 说明                                           |
| --------------------- | ---------------------------------------------- |
| `--skip-ui`           | 跳过 UI 设计环节（纯 API/CLI 项目）            |
| `--quick`             | 跳过常规确认节点；高 Blast Radius 变更仍需确认 |
| `--stop-after <环节>` | 跑到指定环节后停（如 `--stop-after dev`）      |
| `--lang <zh\|en>`     | 交付文档语言（默认 `zh`）                      |

## 专家小队入口

不需要从需求开始时，可用以下独立入口（每个入口都会自动续跑后续环节，除非叫停）：

| 命令              | 起点     | 自动续跑到                                        |
| ----------------- | -------- | ------------------------------------------------- |
| `/boss:pm`        | 需求分析 | Architect → UI → Review → Tasks → Dev → QA → Ship |
| `/boss:architect` | 架构设计 | UI → Review → Tasks → Dev → QA → Ship             |
| `/boss:ui`        | UI 设计  | Review → Tasks → Dev → QA → Ship                  |
| `/boss:review`    | 技术评审 | Tasks → Dev → QA → Ship                           |
| `/boss:tasks`     | 任务拆解 | Dev → QA → Ship                                   |
| `/boss:dev`       | 开发     | QA → Ship                                         |
| `/boss:qa`        | 测试     | Ship                                              |
| `/boss:ship`      | 部署     | 终点                                              |
