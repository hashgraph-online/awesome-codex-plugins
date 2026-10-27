---

name: boss:architect
description: "从架构设计开始：Architect 产出全栈架构设计，默认自动续跑后续环节（UI → 评审 → 任务 → 开发 → 测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# /boss:architect — 架构设计（Architect）

`/boss:architect` 是专家小队的**架构设计入口**。以 Architect 身份产出 `architecture.md`。

**默认行为**：Architect 完成后自动续跑后续所有环节，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:architect`   | 不适合                              |
| ------------------------ | ----------------------------------- |
| 已有需求，直接做架构设计 | 需求还不清晰（用 `/boss:pm`）       |
| 给已有项目补架构文档     | 只想做技术评审（用 `/boss:review`） |

## 前置输入

- 优先读取 `.boss/<slug>/prd.md` 作为输入
- 若 `prd.md` 不存在，可用用户直接描述的需求替代，但需在架构文档中标注来源

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **读取输入**：优先读 `prd.md`，不存在则用用户需求。
3. **派发 Architect Agent**：读取 `agents/boss-architect.md`，产出 `.boss/<slug>/architecture.md`。
   - 必须满足 Architect 的硬性要求（选型有据、契约完整、与 PRD 对齐、风险可判、无 TBD）。
   - 禁止跳过技术调研直接输出架构。
4. **自检**：对照硬性要求表逐项检查。
5. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（ui 或 review），除非用户叫停。

## 用法

```
/boss:architect 做一个面向设计师的素材管理工具
/boss:architect user-auth --skip-ui
```

## 选项

| 参数                  | 说明                   |
| --------------------- | ---------------------- |
| `--skip-ui`           | 续跑时跳过 UI 设计环节 |
| `--stop-after <环节>` | 跑到指定环节后停       |
| `--lang <zh\|en>`     | 产物语言（默认 zh）    |
