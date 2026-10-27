---

name: boss:dev
description: "从开发开始：Frontend + Backend 按任务实现代码，默认自动续跑后续环节（测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep, LSP
---

# /boss:dev — 开发（Frontend + Backend）

`/boss:dev` 是专家小队的**开发入口**。派发 Frontend 和/或 Backend Agent 实现代码。

**默认行为**：开发完成后自动续跑 QA → Ship，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:dev`              | 不适合                        |
| ----------------------------- | ----------------------------- |
| 已有任务/架构，直接开始写代码 | 需求还不清晰（用 `/boss:pm`） |
| 给已有项目加新功能            | 只想做测试（用 `/boss:qa`）   |

## 前置输入

- 优先读取 `.boss/<slug>/tasks.md` + `.boss/<slug>/architecture.md`
- 若不存在，可用 `prd.md` 或用户直接描述的需求替代

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **读取输入**：优先读 `tasks.md` + `architecture.md`，其次 `prd.md`，最后用户需求。
3. **写集冲突检测**：若有 `tasks.md`，检查任务间写集冲突，确定并行安全组。
4. **风险确认**：若 Blast Radius 命中强制确认 trigger，向用户确认后再派发。
5. **派发开发 Agent**：
   - 有前端任务 → 读取 `agents/boss-frontend.md`，派发 Frontend Agent
   - 有后端任务 → 读取 `agents/boss-backend.md`，派发 Backend Agent
   - 前后端无写集冲突 → 可并行派发
   - **开发 Agent 必须遵循 TDD**：先写失败测试（RED）→ 最小实现（GREEN）→ 重构（REFACTOR）
6. **Wave 边界校验**：每个 Wave 完成后运行类型检查、lint、测试，不通过则修复。
7. **自检**：对照 Frontend/Backend 的硬性要求检查：
   - TDD 验证清单全部勾选（RED 已验证、最小实现、全绿）
   - 测试必须编写、覆盖率达标
   - E2E 测试已编写
8. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（qa），除非用户叫停。

## 用法

```
/boss:dev user-auth
/boss:dev 给现有项目加支付功能
/boss:dev --stop-after dev
```

## 选项

| 参数                  | 说明                                                   |
| --------------------- | ------------------------------------------------------ |
| `--stop-after <环节>` | 跑到指定环节后停（如 `--stop-after dev` 只开发不测试） |
| `--lang <zh\|en>`     | 产物语言（默认 zh）                                    |
