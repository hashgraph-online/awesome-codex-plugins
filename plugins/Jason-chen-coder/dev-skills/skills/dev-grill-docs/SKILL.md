---
name: dev-grill-docs
description: 'Use as the main intake for fuzzy or under-specified feature work before coding. Trigger on: dev-grill-docs, grill-with-docs, grill with docs, 拷问需求, 拷问方案, 压测方案, 术语沉淀, 帮我设计, 写个方案, spec 一下, design this, scope this out. Reads existing docs/code first, asks one focused question at a time, produces the spec artifact at .claude/artifacts/designs/<feature>.md, and may also update CONTEXT.md or docs/adr/ for stable domain language and durable decisions. Does not implement code, fix bugs, or write implementation plans.'
---

# Dev Grill Docs

Pressure-test the user's idea **before implementation**, produce the feature intent contract, and keep shared domain language from disappearing into chat.

This is the primary requirement-alignment entry point. It absorbs the former `dev-spec` workflow while adding optional documentation updates:

- Always produce or update `.claude/artifacts/designs/<feature>.md` when the user is aligning a feature.
- Update `CONTEXT.md` only for stable domain glossary material.
- Write `docs/adr/<nnnn>-<slug>.md` only for durable decisions that pass the ADR gate.

It does not write production code, debug bugs, review diffs, or create implementation plans.

---

## Trigger routing

Use this skill when the user wants to align, grill, scope, or pressure-test a feature / requirement / domain model before coding.

Trigger phrases include:

- `dev-grill-docs`
- `grill-with-docs`
- `grill with docs`
- `拷问需求`
- `拷问方案`
- `压测方案`
- `术语沉淀`
- `帮我设计`
- `写个方案`
- `这个需求要怎么做`
- `spec 一下`
- `设计文档`
- `design this`
- `scope this out`

Compatibility:

- `dev-spec` is now a compatibility alias for the spec-only path of this workflow.
- If a user explicitly asks for `dev-spec`, follow this workflow with `CONTEXT.md` / ADR writes disabled unless the user also asks to update docs.

Route elsewhere when:

| User intent | Use instead |
|---|---|
| Wants concrete implementation steps after scope is clear | `dev-plan` |
| Wants to implement after scope is clear | `dev-tdd` |
| Reports broken behavior or regression | `dev-fix` |
| Wants visual product design context | `dev-design-context` |
| Wants commit review or commit message | `dev-code-review` / `dev-commit-writer` |

Output targets:

- `.claude/artifacts/designs/<feature>.md` for the feature intent contract.
- `CONTEXT.md` for stable domain glossary only.
- `docs/adr/<nnnn>-<slug>.md` for durable decisions only when the ADR gate passes.
- chat for each focused question, rationale, round report, and handoff.

Optional arguments:

- `--quick`: ask one highest-leverage question, then write a compact spec when the answer is enough.
- `--deep`: multi-wave grill with challenge modes and stricter ambiguity threshold.
- `--spec-only`: write only `.claude/artifacts/designs/<feature>.md`; do not update `CONTEXT.md` or ADR.
- default: mid-depth wave loop, with optional `CONTEXT.md` / ADR writes only when warranted.

---

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。以下行为准则全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

本 skill 对 baseline 的落地:

- **不假设**:先读现有代码 / 文档,再问一个最关键的问题;多解必须显式列出。
- **最小代码**:spec 只覆盖这次 delivery;`CONTEXT.md` / ADR 只写未来会复用的稳定信息。
- **外科手术式改动**:只写相关 artifact / glossary / ADR,不顺手改代码或重排文档。
- **可验证成功标准**:spec 必须以二值、可执行的 acceptance criteria 收尾。

---

## Step 1 — Brownfield pre-flight

如果当前目录有源码 / 包文件 / git 历史,且用户请求涉及修改 / 扩展现有系统,Wave 1 之前做轻量探索。

优先只读这些入口,按存在性选择:

```bash
test -f CONTEXT.md && sed -n '1,220p' CONTEXT.md
test -d docs && find docs -maxdepth 3 \( -iname '*adr*' -o -path 'docs/adr/*' \)
find . -maxdepth 3 -type f \( -name 'README*' -o -name '*.md' \) | head -40
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git ls-files | head -80
```

如有明显语言 / 框架入口,再轻量查看相关 model、schema、route、DTO、test 名称。

记录两组事实:

```text
codebase_facts: framework / modules / likely change surface / existing tests
project_terms: Term / Existing wording / Evidence / Confidence
```

之后所有问题必须引用这些证据。不要问代码或文档已经能回答的问题。

---

## Step 2 — Choose mode

按 `$ARGUMENTS` 或自动判断:

| 模式 | 触发 | 行为 |
|---|---|---|
| `--quick` | 用户加 `--quick`,或请求已经非常具体 | 只问一个最高杠杆问题;若用户回答后信息足够,直接写 compact spec |
| default | 大多数情况 | 多 wave + 打分,最多 3 wave |
| `--deep` | 用户加 `--deep`,或检测到高风险 / 大改动 / 跨多个模块 | 多 wave + 打分 + Challenge modes,最多 6 wave |
| `--spec-only` | 用户显式跑 `dev-spec`,或不希望写持久 docs | 仍按所选深度访谈,但禁用 `CONTEXT.md` / ADR 写入 |

高风险信号:鉴权 / 支付 / 数据迁移 / 不可逆操作 / 公开 API breakage / PII / 高写并发。

---

## Step 3 — Grill loop

### 3.1 Score clarity

Wave 2 起,对累计上下文打 4 个维度,各 0-1:

| 维度 | 权重(greenfield) | 权重(brownfield) | 含义 |
|---|---|---|---|
| Goal Clarity | 0.43 | 0.40 | 主目标能否一句话说清?核心实体能否命名? |
| Scope Clarity | 0.28 | 0.25 | in/out boundary 能列出来吗? |
| AC Clarity | 0.29 | 0.25 | 能写出二值、可验证的 acceptance criteria 吗? |
| Context Clarity | - | 0.10 | 这次改动落在系统哪里、影响哪些已有部分? |

`ambiguity = 1 - sum(score * weight)`

每个分数必须有具体 anchor。拿不出 anchor 的维度,评分上限 0.6。用户催促时不调高分数,只能提前退出并把风险写进 spec。

### 3.2 Pick one focus

每轮只问一个问题。按最弱维度或术语漂移选择焦点:

| Focus | 问法 | 示例 |
|---|---|---|
| Goal | 什么时候算成功 / 什么不算? | 「用户导出」指自助导出,还是后台代导? |
| Scope | 边界在哪? | 只做 v1,还是兼容旧数据? |
| AC | 怎么验证? | P95 延迟有数字目标吗? |
| Context | 现有系统怎么挂? | 我看到 `services/auth/` 已有 JWT,本功能扩展它还是另起? |
| Term identity | 这东西到底叫什么、是什么? | 你前面叫 Task,现在叫 Item。哪个才是核心实体? |
| Lifecycle | 状态怎么流转? | ExportJob 失败后是 terminal 还是可重试? |
| Invariant | 什么必须永远为真? | 一个 Customer 能否有多个 billing account? |
| Reversibility | 以后改起来贵不贵? | 这个方案是否需要数据迁移才能回退? |

输出格式:

```text
Wave {n} | Focus:{weakest/focus} | Ambiguity:{pct}%
Why this matters:<one sentence>
Recommended answer:<your evidence-backed recommendation>

Question:<exactly one question>
```

### 3.3 Track ontology and drift

用户回答后,提取核心实体并与上一轮比较:

- stable:同名同概念出现
- renamed:换名但语义同
- new:新出现

`stability_ratio = (stable + renamed) / total_entities`

需要立刻指出的 drift:

- 同一概念出现两个名字:`Task` vs `Item`
- 同一名字指向两个概念:`Account` 既像 billing account 又像 login user
- 新词绕开已有领域词:用户说 `client`,代码里长期叫 `Customer`
- 过泛词没有边界:`resource`, `record`, `thing`, `flow`, `job`

### 3.4 Round report

每轮结束输出:

```text
Wave {n} complete.

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.7 | 0.40 | 0.28 | 主流程步骤未拆 |
| Scope | 0.4 | 0.25 | 0.10 | in/out 未列出 |
| AC | 0.5 | 0.25 | 0.125 | 缺数字目标 |
| Context | 0.6 | 0.10 | 0.06 | clear |
| Ambiguity | | | 43.5% | |

Ontology: User, Order, ExportJob (vs previous: 1 stable, 1 renamed, 1 new)
Next focus: Scope, because in/out boundary is still incomplete.
```

### 3.5 Exit conditions

任一满足即进入 Step 4:

- `--quick`:用户回答最高杠杆问题,且已足够写 compact spec。
- default: ambiguity <= 0.30。
- `--deep`: ambiguity <= 0.20。
- 用户在 Wave 3+ 说「够了 / 直接来」,给 warning 后继续。
- 达到模式上限(default 3 / deep 6)。
- Ontology 连续 2 轮 stability >= 90%。

---

## Step 4 — STUCK gate

达到 wave 上限时,强制对照以下硬条件。任一满足则 spec status 标 `STUCK`:

- Goal 维度下无法写出至少 2 条 acceptance criteria。
- Open questions 至少 1 条需要产品 / 设计 / 数据 / stakeholder 决策。
- `In scope` 或 `Out of scope` 为空。
- 连续 2 wave ontology stability < 50%。

`STUCK` 不是失败,只是信息不足以继续。仍然写 spec artifact,但 `Open questions` 必须点名具体阻塞项和需要找谁。

不要写「需要更多信息」「细节后续再定」这种空话。

---

## Step 5 — Write or update CONTEXT.md

跳过条件:

- 用户显式跑 `dev-spec`。
- 用户加了 `--spec-only`。
- 本轮没有稳定领域术语。

`CONTEXT.md` 是领域词汇表,不是 spec、plan、meeting notes 或 implementation diary。

如果没有 `CONTEXT.md`,创建最小文件:

```markdown
# Context

## Glossary

| Term | Meaning | Notes |
|---|---|---|
```

允许写入:

- stable domain terms
- meaning / boundary
- known aliases or rejected names
- short notes that help future agents avoid drift

不要写入:

- implementation steps
- task checklist
- unresolved ideas
- raw conversation transcript
- temporary UI copy
- long architecture rationale
- guesses not confirmed by user or code

有现有 `Glossary` 表时,只追加或修正相关行。每次更新后在 chat 列出 changed terms。

---

## Step 6 — ADR gate

跳过条件:

- 用户显式跑 `dev-spec`。
- 用户加了 `--spec-only`。
- 决策只是命名确认、实现细节、可随时回退的小选择,或还没有定论。

只有同时满足以下条件,才写 ADR:

- 决策未来读者会合理疑惑:为什么不是另一个方案?
- 决策有真实 tradeoff。
- 决策跨 feature 或跨模块会复用,不是只服务本次 implementation plan。
- 决策回退成本中等或较高。
- 用户已经确认或已有 source artifact 支持。

如果 ADR 主要回答「这次功能怎么实现」,不要在这里写,交给 `dev-plan` 的 plan ADR。

ADR 路径:

```text
docs/adr/0001-short-slug.md
```

编号取 `docs/adr/` 下最大编号 + 1。格式:

```markdown
# ADR 0001: <Decision Title>

Status: Accepted
Date: YYYY-MM-DD

## Context
<2-4 sentences>

## Decision
<1-3 sentences>

## Consequences
- <positive consequence>
- <negative consequence / tradeoff>
- <follow-up constraint>
```

---

## Step 7 — Write spec artifact

最终落到 `.claude/artifacts/designs/<feature>.md`。目录不存在则创建。

文件结构:

```markdown
# <feature name> Spec

> Status: DRAFT | ALIGNED | IMPLEMENTED | STUCK
> Author: <user>
> Last updated: <YYYY-MM-DD>

## Background
<2-3 sentences>

## In scope
- ...

## Out of scope
- ...

## Assumptions
- ...

## Solution
<minimal viable solution sketch, <= 1 page>

## Edge cases & risks
| Category | Notes |
|---|---|
| Boundary conditions | ... |
| Failure modes | ... |
| Risks | ... |
| Mitigation | ... |

## Acceptance criteria
- AC-1 <input / condition> -> <expected behavior>
- AC-2 ...

## Open questions
<omit if none>

## Core entities (ontology)
<omit in --quick mode unless needed>

| Entity | Type | Key fields | Relationship |
|---|---|---|---|

## Interview metadata
<omit in --quick mode>

- Mode: --quick | default | --deep | --spec-only
- Waves: N
- Final ambiguity: X%
- Status: PASSED | EARLY_EXIT_BY_USER | CAP_REACHED

### Clarity breakdown
| Dimension | Score | Weight | Weighted |
|---|---|---|---|

### Ontology convergence
<deep mode only>
```

Spec requirements:

- `In scope` and `Out of scope` must both be non-empty unless status is `STUCK`.
- `Acceptance criteria` must be binary and executable.
- `Solution` is a sketch, not an implementation plan.
- `Open questions` must list concrete blockers, not vague uncertainty.

---

## Step 8 — Handoff

输出:

```text
━━━ Dev Grill Docs ━━━
Spec
  - .claude/artifacts/designs/<feature>.md
  - Status:<DRAFT | ALIGNED | STUCK>

Confirmed terms
  - <Term>:<meaning>

Updated docs
  - CONTEXT.md:<what changed, or "not changed">
  - docs/adr/0001-x.md:<decision, or "not written">

Still open
  - <specific unanswered question, or "None">

Recommended next step
  - <dev-plan / dev-tdd / stop> because <one sentence>
```

If status is `STUCK`, recommend resolving `Open questions` before `dev-plan`.

---

## Hard rules

- Do not bulk-question the user.
- Do not skip ambiguity surfacing, even in `--quick`.
- Do not ask questions the repo can answer.
- Do not silently accept wording that conflicts with project vocabulary.
- Do not write code.
- Do not turn `CONTEXT.md` into a dumping ground.
- Do not create ADRs for every decision.
- Do not use this skill for bugs; use `dev-fix`.
- Do not route to `dev-plan` while the spec status is `STUCK`.
- Do not write unverifiable acceptance criteria such as "works correctly" or "looks good".

---

## Multi-Agent Note

`dev-grill-docs` is main-agent-first because it negotiates scope and language with the user.

Explorers may gather codebase facts, existing terminology, ADRs, and similar features, but the main agent owns the grill loop, ambiguity scoring, scope confirmation, and all writes to `.claude/artifacts/designs/`, `CONTEXT.md`, and `docs/adr/`. Follow `../../docs/multi-agent-policy.md` for delegation boundaries.

## SDD Contract

`dev-grill-docs` produces the feature intent contract for the rest of the workflow.

Required downstream anchors:

- `In scope`: what later agents may implement.
- `Out of scope`: what later agents must not expand into without user approval.
- `Assumptions`: accepted defaults that must stay visible during implementation and review.
- `Open questions`: blockers or known uncertainty; do not route to `dev-plan` while status is `STUCK`.
- `Acceptance criteria`: the checklist consumed by `dev-plan`, `dev-tdd`, `dev-verify`, and `dev-code-review`.
- `CONTEXT.md` / ADR: durable project language and decisions that later work must respect when present.

If implementation later changes behavior beyond the spec, update the spec or explicitly report spec drift before commit.
