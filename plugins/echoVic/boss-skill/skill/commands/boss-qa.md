---
name: boss:qa
description: "只跑测试环节：QA 测试执行 + 门禁校验。对已有代码单独可用，产出 qa-report.md 与 Gate 结果，测试真跑、门禁不可绕过。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:qa — 单环节：测试与门禁（QA）

`/boss:qa` 是 Boss 流水线的**测试环节独立入口**。以 QA 身份对已有代码执行核心用户路径测试、真实 payload 验证、越权/分页/旧数据检查，产出 `qa-report.md`，并运行质量门禁。

> 与 gstack `/qa` 的关键区别：Boss 的门禁**不可绕过**且**可验证**——测试是否真跑、门禁是否真过，都进事件流（有 CLI 时）或写入 STATE.md（无 CLI 时），不是 agent 自报「测过了」。

## 适合 / 不适合

| 适合 `/boss:qa` | 不适合 |
|-----------------|--------|
| 对已实现功能补测试证据 | 还没有可测代码（先 `/boss` 开发） |
| 上线前跑门禁 checklist | 只想看代码不想跑测试 |
| 验证「测试真的跑过了」 | — |

## 执行步骤

1. 读取 `SKILL.md` 不变量与 `references/testing-standards.md`、`references/quality-gate.md`。
2. 确定被测目标（feature slug 或代码路径）。
3. 读取 `agents/boss-qa.md` 与 `skills/qa/test-strategy/SKILL.md`、`skills/qa/test-execution/SKILL.md`、`skills/qa/e2e-playwright/SKILL.md`。
4. 以 QA 身份执行测试并产出 `qa-report.md`（模板 `templates/qa-report.md.template`）：核心路径、真实 payload、越权/分页/旧数据、P0/P1 Bug。
5. 运行门禁：`boss runtime evaluate-gates <feature> <gate-name>`（Gate 0/1，见 `references/quality-gate.md`）。无 CLI 时按 `references/no-cli-fallback.md` 记录门禁结果到 STATE.md。
6. **门禁失败不得宣布通过**（不变量 4）。输出：测试摘要、覆盖率、门禁结果、未过项、下一步（可接 `/boss:ship`）。

## 用法

```
/boss:qa                    # 对当前项目跑测试 + 门禁
/boss:qa user-auth          # 对已有 feature 跑 QA
```

## 选项

| 参数 | 说明 |
|------|------|
| `--lang <zh\|en>` | QA 报告语言（默认 zh） |
