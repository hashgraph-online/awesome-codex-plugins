---
name: dev-verify
description: Use before claiming work is complete, fixed, ready, passing, or before handing off to commit review, PR, merge, or branch cleanup. Requires fresh verification commands and evidence before any success claim.
---

# Dev Verify

Completion gate for evidence-based status. The goal is to make every “done / fixed / ready” claim traceable to a fresh command or direct inspection.

This skill does not review code quality (`dev-code-review`) and does not decide merge / PR / cleanup (`dev-finish`). It verifies claims before those steps.

---

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联:
- **可验证成功标准** —— 每个成功声明必须有命令或检查证据。
- **不假设** —— 不把局部测试通过外推成整套系统通过。
- **外科手术式改动** —— 验证 scope 必须对应本次实际改动,不伪装成全量质量背书。

---

## Step 1 — List claims

先列你准备声明的内容,不要直接说完成。

格式:

```
Claims to verify:
1. <claim> — proof needed: <command / inspection>
2. <claim> — proof needed: <command / inspection>
```

常见 claim 对照:

| Claim | 需要的 proof |
|---|---|
| Tests pass | fresh test command, exit 0, failure count 0 |
| Build succeeds | fresh build command, exit 0 |
| Lint clean | fresh lint command, exit 0 |
| Bug fixed | original repro / regression test passes |
| Regression test is meaningful | red → green 或临时反转 fix 后会 fail |
| Requirements met | spec / plan AC 逐项对照 |
| Ready for commit | tests/build as appropriate + `dev-code-review` verdict |

---

## Step 2 — Choose verification commands

用最小充分命令组合:

1. 针对本次改动的窄测试。
2. 受影响模块的测试。
3. 项目标准 lint/build/test,如果存在且成本合理。
4. 对文档 / skill 改动,跑仓库提供的结构校验脚本或 grep/JSON parse 检查。

如果找不到验证命令,明确写:

```
无法自动验证: <原因>
手动检查: <检查了什么>
残余风险: <具体风险>
```

---

## Step 3 — Run fresh commands

必须在当前回合运行,不能引用旧输出。

记录:

```
Command: <exact command>
Result: PASS | FAIL
Evidence: <关键输出摘要,含 exit code / tests count / failure count>
```

如果失败:
- 停止完成声明
- 报告真实状态
- 回到实现或 `dev-fix`

---

## Step 4 — Requirement checklist

对照用户请求、spec、plan 或 fix artifact,逐项检查:

```
Requirement checklist:
- [x] <requirement> — verified by <command / file inspection>
- [ ] <requirement> — missing / not verified because <reason>
```

任何未验证项都不能包装成完成。

### SDD artifact mapping

如果存在匹配 artifact,优先按下面顺序映射验证项:

1. `.claude/artifacts/fixes/<slug>.md` 的 `Verification` / `Regression test`。
2. `.claude/artifacts/plans/<slug>.md` 的 `Verification steps` / ADR 风险。
3. `.claude/artifacts/designs/<slug>.md` 的 `Acceptance criteria`。

无法映射的完成声明要单独列为 `Unmapped claim`,并说明它来自用户当前请求、代码检查还是实现过程中的新增发现。

---

## Step 5 — Final statement

只有 Step 3 和 Step 4 支持时,才能说完成。

合格输出:

```
Verified:
- <command>: PASS (<evidence>)
- <command>: PASS (<evidence>)

Status: ready for dev-code-review / ready for dev-finish / blocked by <failure>
```

---

## Hard rules

- 没有新鲜验证,不说完成。
- 局部测试通过不能声称全量通过。
- 不能把“看起来没问题”写成证据。
- agent / 工具报告成功后,仍要独立检查文件或命令输出。
- 验证失败时,如实报告失败,不要弱化措辞。

---

## Multi-Agent Profile

Recommended agent_type: worker

Use when:
- Implementation is complete enough to check.
- The main agent needs independent evidence before claiming done / fixed / ready.
- Verification can run without changing project files.

Do:
- Stay read-only unless the main agent explicitly assigns a fix.
- List claims first, then map each claim to proof.
- Run fresh commands and report exact results.
- Use `../../docs/multi-agent-policy.md` for verifier independence expectations.

Do not:
- Rubber-stamp another agent's claim.
- Turn local success into a broader claim than the commands support.
- Hide or soften failed commands.

Output:
- Claims checked
- Commands run
- PASS / FAIL evidence
- Requirement checklist
- Residual risks
