---
name: dev-plan
description: 'Use only after a spec or clearly scoped requirement exists and the user wants a concrete implementation plan before coding. Trigger on explicit implementation-planning requests such as 基于这个 spec 出 plan, 需求已经清楚了给实施方案, 技术实施方案, 出个 plan, 做个实施方案, plan this, make a plan, consensus plan, ralplan. If the user says 写个方案, 给我个方案, 怎么做这件事, 帮我设计, or the requirement is still fuzzy, route to dev-grill-docs first. Produces a RALPLAN-DR plan with principles, decision drivers, viable options, ADR, and Planner-Architect-Critic validation. Does not gather requirements, fix bugs, review code, or write code.'
---

# Dev Plan

Convert a spec / scoped requirement into a **Critic-approved implementation plan** before coding. Single-agent in-context consensus loop:**Planner → Architect → Critic**, with iteration cap.

This skill **only plans**. It does not gather requirements (`dev-grill-docs` does that; `dev-spec` is a compatibility alias) and does not review or write code (`dev-code-review` / your editor / a coding skill do that).

---

## Trigger routing

Use this skill when a spec or scoped requirement exists and the user wants a concrete implementation plan with cross-perspective validation before writing code. If the user is still asking to clarify what the requirement should be, route to `dev-grill-docs`.

Trigger phrases include:

- `基于这个 spec 出 plan`
- `需求已经清楚了给实施方案`
- `技术实施方案`
- `出个 plan`
- `做个实施方案`
- `plan this`
- `make a plan`
- `consensus plan`
- `ralplan`

Ambiguous phrases such as `写个方案`, `给我个方案`, `怎么做这件事`, or `帮我设计` belong to `dev-grill-docs` unless the user says the requirement/spec is already clear and wants implementation steps.

Output goes to `.claude/artifacts/plans/<feature>.md`.

Optional arguments:

- `--quick`: single-pass plan for small changes
- `--deliberate`: high-risk plan with pre-mortem and expanded test plan
- default: full Planner → Architect → Critic loop

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联点:
- **不假设** —— 最强落地是 RALPLAN-DR 强制 ≥ 2 个 viable options + 显式 invalidation rationale。绝不只给 1 个方案。
- **最小代码** —— Planner 默认走最小可行实现,Architect 才有资格提架构升级,且必须给 tradeoff tension。
- **外科手术式改动** —— 实施步骤里每一行都 cite 具体文件 / 模块,不许「优化整体架构」类抽象目标。
- **可验证成功标准** —— Critic 必须对每条 AC 检查可验证性,否则打回。

---

## Step 1 — Source check

**优先从 spec 入手**。检查 `.claude/artifacts/designs/` 下是否有相关 spec(或用户明示 spec 路径):

| 情况 | 行为 |
|---|---|
| 找到匹配 spec | 加载,把 `In scope` / `Out of scope` / `Acceptance criteria` / `Core entities` 全部读入,作为本 plan 的 source of truth |
| 没有 spec,但请求范围清晰 | 直接进 Step 2,先在 plan 里写一节 `Requirements summary` 概括用户请求 |
| 没有 spec,且请求模糊 | **停止本 skill,提示用户先跑 `dev-grill-docs`**,不要硬上 |

**判断「请求模糊」的标准**:与 `dev-grill-docs` clarity / ambiguity 维度对照,若 ≥ 2 个维度无法确认,视为模糊。

---

## Step 2 — 选模式

按 `$ARGUMENTS` 或自动判断:

| 模式 | 触发 | 行为 |
|---|---|---|
| `--quick` | 用户加 `--quick`,或改动面 < 3 个文件 / < 100 行 | 单 pass,Planner 直接出最小 plan,无 Architect/Critic |
| (默认) | 大多数情况 | 完整 Planner → Architect → Critic loop,**最多 3 次迭代** |
| `--deliberate` | 用户加 `--deliberate`,或检测到高风险信号(见下) | 完整 loop + Pre-mortem(3 场景)+ Expanded test plan(unit/integration/e2e/observability)+ ADR 强制项更细 |

**高风险信号**(自动升 deliberate):鉴权 / 支付 / 数据迁移 / 不可逆破坏性操作 / 生产事故修复 / 公开 API breakage / PII 处理。

---

## Step 3 — Planner pass

**身份**:你现在是 Planner。目标是产出**最小可行实施方案**,且**必须**列 ≥ 2 个 viable options。

输出节(写在 plan draft 里):

```
## Planner draft

### Principles (3-5)
- 跟随 baseline「最小代码」:能压到一半就压
- 跟随 spec 的 In scope,不擅自扩
- ...

### Decision drivers (top 3)
- 上线时间 / 团队熟悉度 / 维护成本 / 性能要求 / ...

### Viable options
**Option A: <一句话名字>**
- 实现思路:1-2 句
- 改动文件:`path/x.ts`, `path/y.ts`
- Pros: ...
- Cons: ...

**Option B: <一句话名字>**
- ...

(如果只有 1 个 viable option,必须显式列 invalidation rationale 解释其他选项为什么被砍)

### Implementation steps (基于 favored option)
1. <步骤> — `path/to/x.ts:42-60` 新增 X 函数
2. <步骤> — `path/to/y.ts` 改 Y 行为
...

### Workspace setup
- 实施前运行 `git status --short` 和 `git branch --show-current`。
- 如果 working tree 干净,且本 plan 会修改代码 / 多文件规则 / 配置 / 测试,先询问用户是否创建 worktree。
- worktree 默认命名:`git worktree add -b codex/<short-slug> ../<repo>-<short-slug>`。
- 如果当前分支是 `main` / `master` / `release/*`,默认推荐 worktree。
- 如果 working tree 已经 dirty,先保护现有改动,不要把本 plan 的改动混进去。

### Open questions (留给后续)
- ...
```

**强约束**:
- 实施步骤 80%+ **必须 cite 具体文件路径 / 行号**(没有具体目标的「重构 cart 模块」是空话)。
- 不写「未来可扩展」之类的延伸 —— spec out-of-scope 的事就不该出现在 plan 里。

`--quick` 模式到此结束,直接跳 Step 7 写 artifact;不做 Architect / Critic。

---

## Step 4 — Architect pass(默认 / deliberate)

**身份切换**:你现在是 Architect。**读上面 Planner 的 draft**,从架构角度挑战。

输出节(追加到 plan draft):

```
## Architect challenge

### Steelman against favored option
针对 Planner 选定的 Option <X>,给出**最强反驳**:
- 反方核心论点:...
- 如果反驳成立,plan 应改成什么样:...

### Tradeoff tensions
列出 plan 内部的真实矛盾(至少 1 条):
- 速度 vs 可维护性 / 简单 vs 灵活 / 性能 vs 一致性 / ...
- 每条 tension 给 Planner 的取舍依据

### Synthesis path(可选)
如果发现两个 option 各有合理处,提出**综合方案**,简述如何融合。

### Principle violations(deliberate 模式必填)
逐条对比 plan 与 Step 3 的 Principles,标出违反项。
```

**Architect 的硬约束**:
- 必须给 steelman(最强反方),不许敷衍。
- 必须找 ≥ 1 条 tradeoff tension。
- 不许只「点头」—— 没意见就退回 Planner 重写,直到 Architect 找到真问题。

---

## Step 5 — Critic pass

**身份切换**:你现在是 Critic。**读 Planner draft + Architect challenge**,做质量评审。

判定标准(每条都打分,任一不达标则 REJECT):

| 维度 | 标准 |
|---|---|
| Principle-option consistency | favored option 与 Principles 一致,无矛盾 |
| Fair alternative exploration | options 是真候选,不是陪跑(被砍的有 invalidation rationale) |
| Risk mitigation clarity | 每条 risk 对应一行 mitigation,不是「以后再说」 |
| AC testability | 每条 AC 二值可验证,无「looks good」之类 |
| Verification concreteness | 验证步骤可执行(命令 / 测试名 / metric 阈值) |
| File/line coverage | 实施步骤 ≥ 80% cite 具体文件 |
| **Pre-mortem present**(deliberate) | 至少 3 个 failure scenarios + trigger + mitigation |
| **Expanded test plan present**(deliberate) | unit / integration / e2e / observability 各一段 |

输出节:

```
## Critic verdict

| 维度 | 状态 | 备注 |
|---|---|---|
| Principle consistency | ✓ / ✗ | ... |
| Alternative exploration | ✓ / ✗ | ... |
| ...

### Verdict: APPROVED / REVISE / REJECT

REVISE / REJECT 时:
- 列出**具体待改项**(对应 plan 的 section)
- 拒收原因(一句话)

### Reservations(必填,即使 APPROVED 也要列 ≥ 1 条)
- <对 plan 某 section 的具体保留意见,带 file/section 引用>
- ...
```

**Critic 的硬约束**:
- 不许接受 shallow alternatives(A 和 B 看起来同质)。
- 不许接受 vague risks(「可能性能不好」)。
- 不许接受弱 verification(「跑一下看看」)。
- deliberate 模式额外检查 pre-mortem 和 expanded test plan,缺则 REJECT。
- **至少 1 条 RESERVATION**(防 Critic 软通过)—— 即使最终 verdict = APPROVED,也**必须列出 ≥ 1 条「我对此项仍有保留」**。例:
   - 「Plan 用了 Redis 做幂等存储。我有保留:Redis 单点故障时幂等失效。Mitigation 段没具体说怎么 fallback。」
   - 「Implementation step 3 `services/cart.ts:88-92` —— 我没看到回滚路径如果 step 4 失败。」
- **拿不出 ≥ 1 条 RESERVATION 时,verdict 强制改为 REVISE**(说明 Critic 没真在挑刺,要么再过一遍要么承认本 plan 有未发现的隐患)。这是反 LLM「礼貌倾向 / 自洽倾向」的硬性矫正。

---

## Step 6 — Iteration loop

如果 Critic verdict ≠ APPROVED:

1. 收集 Architect + Critic 的所有反馈(去重 + 归类)
2. **回到 Step 3,重新跑一次 Planner**,把反馈作为约束输入
3. 重新跑 Step 4(Architect)
4. 重新跑 Step 5(Critic)
5. 重复直到 APPROVED 或达到 **3 次迭代上限**

**达到 3 次仍未 APPROVED**:
- 把当前最好版本保存到 artifact
- 在 ADR 顶部加显式标注:`Status: BELOW_CONSENSUS_THRESHOLD —— 已达 3 次迭代,Critic 仍有 N 处保留意见,见下方 Critic notes`
- 不要继续硬循环

每次迭代都要在最终 plan 的 `## Review trail` 段记录:迭代次数 / 每轮 Critic 拒收原因 / 这一轮做了什么修复。

---

## Step 7 — Apply improvements & finalize ADR

将 Architect / Critic 中**接受**的改进合入主体 plan,然后写 ADR(Architecture Decision Record):

```
## ADR

- **Decision**: 一句话总结最终选定方案
- **Drivers**: 来自 Step 3 的 Decision drivers,标出哪些起了决定性作用
- **Alternatives considered**: 列 Step 3 的所有 options,逐一标 chosen / rejected + rationale
- **Why chosen**: 2-3 句
- **Consequences**: 接受这个方案带来的正负影响(对其他模块、性能、维护、团队)
- **Follow-ups**: 本次明确不做但应该做的后续(进 spec 的 Open questions / 进 backlog)
```

ADR 是最终决定的**单一入口**,后续 dev-code-review 评审时如果 diff 与 ADR 不符,应作为 P1 finding。

---

## Step 8 — Write artifact

落到 `.claude/artifacts/plans/<feature>.md`(目录不存在则创建)。

文件结构:

```markdown
# <feature> Implementation Plan

> Status: APPROVED | BELOW_CONSENSUS_THRESHOLD
> Source: <spec path 或 "user request">
> Mode: --quick | (default) | --deliberate
> Iterations: N / 3
> Author: <user>
> Last updated: <YYYY-MM-DD>

## Requirements summary
<2-3 句:本 plan 服务什么需求>

## Acceptance criteria
- AC-1 <从 spec 继承,或本次新加>
- AC-2 ...

## RALPLAN-DR
### Principles
- ...

### Decision drivers
- ...

### Viable options
**Option A**: ...
**Option B**: ...

## Implementation steps
1. <步骤> — `path:line`
2. ...

## Workspace setup
- Run `git status --short` and `git branch --show-current` before implementation.
- If the tree is clean and this plan will modify code / multi-file rules / config / tests, ask whether to create a worktree before the first file write.
- Recommended worktree command: `git worktree add -b codex/<short-slug> ../<repo>-<short-slug>`.
- If the current branch is `main` / `master` / `release/*`, recommend the worktree path by default.
- If the tree is already dirty, protect existing changes and do not mix this plan into them without user confirmation.

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| ... | ... |

## Verification steps
- 怎么验证 AC-1: ...
- ...

## Pre-mortem (deliberate only)
1. **Scenario**: ...
   **Trigger**: ...
   **Mitigation**: ...
2. ...
3. ...

## Expanded test plan (deliberate only)
- **Unit**: ...
- **Integration**: ...
- **E2E**: ...
- **Observability**: metrics / logs / alerts

## ADR
<Step 7 内容>

## Review trail
- Planner draft v1: <一行摘要>
- Architect challenge v1: <关键 tension>
- Critic verdict v1: REJECT — <原因>
- Planner draft v2: <修复了什么>
- Architect challenge v2: ...
- Critic verdict v2: APPROVED with N improvements applied
- Final iterations: 2 / 3
```

`--quick` 模式产出**精简结构**:省略 Planner draft 详细 / Architect challenge / Critic verdict 全部段落,只保留 Requirements / AC / Implementation steps / Risks / Verification + 一段「Quick mode rationale」说明为什么够轻量。

---

## Hard rules

- **不要** 在 Step 1 检测到模糊请求时硬上 —— 提示用户先 `dev-grill-docs`,不要拼凑 spec。
- **不要** 默认模式只列 1 个 option —— RALPLAN-DR 强制 ≥ 2,只有 1 个时必须显式 invalidation rationale。
- **不要** 把 Architect / Critic 跑成形式主义。Architect 必须 steelman、必须找 tension;Critic 必须按 7 维度逐项打分。
- **不要** 让 Planner / Architect / Critic 在同一段里混着写。每个 pass 必须**单独成节**,用户能看到三方独立观点。
- **不要** 用户没说 `--deliberate` 时强加 pre-mortem(那是重模式特征)。
- **不要** 跨 3 次迭代硬循环 —— 达上限就标 BELOW_CONSENSUS_THRESHOLD 收手,把决策权交回用户。
- **不要** 替用户决定 Out of scope 之外的事 —— ADR 里 Follow-ups 段是「应做未做」,不是「我替你决定下一步做什么」。
- **不要** 写代码 —— 本 skill 只产 plan,代码由后续动作触发。
- **不要** 自动调起其他 skill —— dev-skills 之间松耦合,plan 完成后用户自己决定下一步。
- **不要** 省略 Workspace setup —— 任何会进入代码/配置/测试修改的 plan,都必须写明 clean-tree worktree checkpoint。

---

## 与其他 skill 的协作

- **上游**:`dev-grill-docs` 生成的 spec(`.claude/artifacts/designs/<feature>.md`;兼容入口 `dev-spec` 也写同一路径)是本 skill 的最佳输入。
- **下游**:本 skill 的 plan(`.claude/artifacts/plans/<feature>.md`)是 `dev-code-review` 的对齐参考(若存在,审查时应检查 diff 是否落实了 plan 的 AC 与 ADR;但触发 dev-code-review 仍由用户主动)。
- **不调用**:本 skill 不主动 invoke 其他 skill —— 跨 skill 的衔接由用户控制。

## SDD Contract

`dev-plan` turns an aligned spec into the implementation contract.

Required downstream anchors:

- `ADR`: the decision reviewers should compare the diff against.
- `Implementation steps`: the ownership and sequencing workers should follow.
- `Risks / mitigations`: the issues verifier and reviewer should re-check.
- `Verification steps`: the command plan `dev-verify` should start from.
- `Open questions`: unresolved items that must not be silently implemented.

If code needs to deviate from the ADR or implementation steps, update this plan or call out plan drift before review.

---

## Multi-Agent Profile

Recommended agent_type: default

Use when:
- A spec or scoped requirement already exists.
- The main agent needs an independent planner / architect / critic pass.
- The output can be reviewed as a plan artifact before implementation starts.

Do:
- Stay read-only.
- Produce options, tradeoffs, ADR, risks, and verification steps.
- Flag missing requirements instead of filling them in silently.
- Link follow-up behavior to `../../docs/multi-agent-policy.md`.

Do not:
- Write code or edit project files outside the plan artifact.
- Decide unresolved product scope for the user.
- Trigger downstream skills automatically.

Output:
- Recommended option and rationale
- Implementation steps
- Risks and mitigations
- Verification plan
- Open questions
