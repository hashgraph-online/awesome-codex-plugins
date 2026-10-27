---

name: boss:qa
description: "从测试开始：QA 执行核心用户路径测试与质量门禁，默认自动续跑部署环节。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:qa — 测试与质量门禁（QA）

`/boss:qa` 是专家小队的**测试入口**。以 QA 身份执行测试，产出 `qa-report.md`，并运行质量门禁。

**默认行为**：测试完成后自动续跑 ship（部署），除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:qa`           | 不适合                           |
| ------------------------- | -------------------------------- |
| 对已实现功能跑测试 + 门禁 | 还没有可测代码（用 `/boss:dev`） |
| 上线前质量检查            | 只想看代码不想跑测试             |

## 前置输入

- 可运行的代码
- 优先读取 `.boss/<slug>/prd.md` 作为测试依据
- 若 `prd.md` 不存在，可用用户描述的需求替代

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **确定被测目标**：feature slug 或代码路径。
3. **派发 QA Agent**：读取 `agents/boss-qa.md`，执行测试并产出 `.boss/<slug>/qa-report.md`。
   - 必须包含：核心用户路径、真实 payload、越权/分页/旧数据验证、P0/P1 Bug。
4. **运行质量门禁**（参考 `references/quality-gate.md`）：
   - 单元测试全部通过
   - 测试覆盖率 ≥ 70%
   - 无 P0/P1 Bug
   - E2E 测试已编写并通过
5. **自检**：门禁不通过则修复后重跑，或向用户报告。
6. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（ship），除非用户叫停。

## 用法

```
/boss:qa
/boss:qa user-auth
/boss:qa --stop-after qa
```

## 选项

| 参数                  | 说明                                                  |
| --------------------- | ----------------------------------------------------- |
| `--stop-after <环节>` | 跑到指定环节后停（如 `--stop-after qa` 只测试不部署） |
| `--lang <zh\|en>`     | QA 报告语言（默认 zh）                                |
