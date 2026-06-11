---
name: dev-tdd
description: Use when implementing a feature, refactor, direct hotfix, or scoped behavior change before writing production code. For bug reports that need root-cause investigation, use dev-fix instead; dev-fix already owns failing regression tests.
---

# Dev TDD

Implementation workflow for behavior-changing code. The goal is to prevent "tests after" from becoming optimistic coverage that never proved it could catch the bug.

This skill only governs the coding loop. It does not gather requirements (`dev-grill-docs`; `dev-spec` is a compatibility alias), design implementation strategy (`dev-plan`), investigate root cause (`dev-fix`), or review the final diff (`dev-code-review`).

---

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联:
- **可验证成功标准** —— 每个行为先有会失败的测试,再写实现。
- **最小代码** —— Green 阶段只写足以通过当前测试的代码,不顺手加未来扩展。
- **外科手术式改动** —— 每轮只覆盖一个行为,不要把无关重构混进来。

---

## Step 1 — Applicability gate

默认适用:
- 新功能
- 重构但需要保持行为不变
- 直接编码的 simple hotfix
- 任何会改变用户可见行为、API 行为、数据语义的改动

不要用于需要 root cause investigation 的 bug 报告。那条路径走 `dev-fix`,因为 `dev-fix` 已经内置 failing regression test、root-cause fix 和 red→green→red 验证。

可跳过,但必须在输出里说明原因:
- 纯文档
- 纯图片 / 资产
- 生成代码
- 只改注释或格式
- 纯配置且没有本地可运行验证入口

如果用户要求跳过 TDD,只在他们明确接受风险时跳过,并把后续验证升级为 `dev-verify` 的完整检查。

---

## Step 2 — Pick the smallest behavior

把当前任务切成最小行为单元。每轮只选一个:

```
Behavior: <一句话说明>
Expected: <可断言的结果>
Test target: <测试文件 / 测试命令>
Production target: <实现文件>
```

如果写不出 `Expected`,说明需求还没清楚,回 `dev-grill-docs` 或向用户澄清。

### SDD source check

如果存在匹配的 `.claude/artifacts/designs/<slug>.md` 或 `.claude/artifacts/plans/<slug>.md`,本轮 behavior 应从其中一个来源选择:

- spec acceptance criteria
- plan implementation step
- plan verification step

输出时标明 `Source: spec/<slug> AC-<n>` 或 `Source: plan/<slug> step <n>`。如果没有 artifact,用用户当前请求作为 source,但不要把未确认的范围扩成额外行为。

---

## Step 3 — RED: write the failing test first

先写测试,不要写生产代码。

测试要求:
- 名字描述行为,不是实现细节
- 一次只测一个行为
- 优先测真实代码路径,只有外部系统不可控时才 mock
- 对 bug 修复,测试必须复现原始症状或最小 root cause

运行最窄命令:

```bash
<test command for the specific test>
```

必须确认:
- 测试失败
- 失败原因是预期行为缺失,不是拼写、导入、fixture 错误
- 如果测试直接通过,说明没有证明任何东西,需要重写测试

---

## Step 4 — GREEN: minimal implementation

只写让当前 RED 测试通过的最小生产代码。

禁止:
- 同轮实现多个未测试行为
- 新增未被要求的 option / strategy / abstraction
- 顺手重构邻近代码
- 为了让测试过而改弱断言

运行:

```bash
<same narrow test command>
```

必须确认当前测试通过。若失败,修实现,不是先改测试。

---

## Step 5 — REFACTOR: clean while green

仅在测试已通过后整理:
- 改名让意图更清楚
- 去除当前改动引入的重复
- 抽取已有第二个调用点真正需要的 helper

每次整理后重新运行同一测试。不要在 refactor 阶段加入新行为。

---

## Step 6 — Expand verification

当前行为通过后,根据风险扩大验证:

| 改动范围 | 追加验证 |
|---|---|
| 单函数 / 单模块 | 相关测试文件 |
| 多文件协作 | 相关测试目录 / package test |
| 公开 API / 数据迁移 / 鉴权 / 支付 | 单测 + 集成测试 + 项目标准 lint/build |
| regression / hotfix | red → green → 临时反转实现确认 test 会再 fail → 恢复 green |

输出时列明运行过的命令和结果。不能只说“应该通过”。

---

## Step 7 — Handoff

全部行为实现后:
1. 跑 `dev-verify` 做完成前证据门禁。
2. 跑 `dev-code-review` 做提交前评审。
3. 需要结束分支时跑 `dev-finish`。

---

## Hard rules

- 没有先失败的测试,不写生产代码。
- 测试没有按预期失败,不进入 Green。
- Green 阶段不加未测试功能。
- 不能通过削弱测试让它变绿。
- 完成声明必须带新鲜命令输出,否则交给 `dev-verify` 补齐。

---

## Multi-Agent Profile

Recommended agent_type: worker

Use when:
- The behavior to implement is already scoped.
- The assigned write scope is clear and disjoint from other agents.
- The sub-agent can prove red -> green with a narrow command.

Do:
- Work only inside the assigned ownership.
- Preserve unrelated edits and adapt to concurrent changes.
- Report changed files, test commands, and red / green evidence.
- Follow the ownership rules in `../../docs/multi-agent-policy.md`.

Do not:
- Edit files outside the assigned scope.
- Weaken tests to make them pass.
- Add unrequested abstractions or future-proofing.
- Claim completion without fresh command output.

Output:
- Summary
- Changed files
- RED command and failure reason
- GREEN command and result
- Risks / follow-ups
