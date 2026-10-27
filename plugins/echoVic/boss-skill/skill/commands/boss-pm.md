---

name: boss:pm
description: "从需求分析开始：PM 需求穿透产出 PRD，默认自动续跑后续所有环节（架构 → UI → 评审 → 任务 → 开发 → 测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# /boss:pm — 需求分析（PM）

`/boss:pm` 是专家小队的**需求分析入口**。以 PM 身份穿透用户需求，产出 `prd.md`。

**默认行为**：PM 完成后自动续跑后续所有环节，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:pm`              | 不适合                                             |
| ---------------------------- | -------------------------------------------------- |
| 有想法但需求不清晰，需要穿透 | 已经有 PRD，直接从架构开始（用 `/boss:architect`） |
| 想拿到可验收的需求文档       | 只想改个小 bug                                     |

## 执行步骤

1. **Feature slug 归一化**：把用户需求归一化为简短英文 kebab-case slug，创建 `.boss/<slug>/` 目录。
2. **需求澄清**（除非 `--quick`）：检查需求是否包含"做什么 + 给谁用 + 核心场景"，缺失时一次问一个问题。
3. **派发 PM Agent**：读取 `agents/boss-pm.md`，执行需求穿透，产出 `.boss/<slug>/prd.md`。
   - 必须满足 PM 的硬性要求（需求分层、可验收、边界明确、无 TBD）。
4. **自检**：对照 `agents/boss-pm.md` 的硬性要求表逐项检查，不满足则修复。
5. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（architect），除非用户叫停。

## 用法

```
/boss:pm 做一个面向设计师的素材管理工具
/boss:pm 用户认证模块 --quick
```

## 选项

| 参数                  | 说明                                            |
| --------------------- | ----------------------------------------------- |
| `--quick`             | 跳过需求澄清                                    |
| `--skip-ui`           | 续跑时跳过 UI 设计环节                          |
| `--stop-after <环节>` | 跑到指定环节后停（如 `--stop-after architect`） |
| `--lang <zh\|en>`     | 产物语言（默认 zh）                             |
