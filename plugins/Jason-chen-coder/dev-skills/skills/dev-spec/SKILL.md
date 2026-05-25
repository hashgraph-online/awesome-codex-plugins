---
name: dev-spec
description: 'Use when the user has a fuzzy or under-specified feature request and wants to align on what to build before coding. Trigger on: 帮我设计, 写个方案, 这个需求要怎么做, spec 一下, 设计文档, design this, scope this out. Surfaces ambiguities first, asks before choosing among interpretations, and produces a structured spec with scope, solution sketch, risks, and verifiable acceptance criteria. Does not write code, plan implementation, fix bugs, or review commits.'
---

# Dev Spec

Convert a fuzzy request into a structured design document **before any code is written**.

This skill **must surface ambiguities first** and let the user resolve them, then produce the spec. It does not write code, and it does not silently pick interpretations.

---

## Trigger routing

Use this skill when the user has a fuzzy or under-specified request and wants to align on what to build before writing code.

Trigger phrases include:

- `帮我设计`
- `写个方案`
- `这个需求要怎么做`
- `spec 一下`
- `设计文档`
- `design this`
- `scope this out`

Output goes to `.claude/artifacts/designs/<feature>.md`.

Optional arguments:

- `--quick`: single-round ambiguity list
- `--deep`: multi-wave interview with challenge modes
- default: mid-depth wave loop

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。以下行为准则在本 skill 全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

baseline 与本 skill 的关联点(本 skill 的核心):
- **不假设** —— 这是本 skill 的**入口动作**。Step 1 的全部职责就是把模糊点显式化。
- **最小代码** —— spec 必须有一段 `Out of scope`,强制写出「这次明确不做的东西」,对抗顺手设计「未来灵活性」的倾向。
- **可验证成功标准** —— spec 以**可验证的验收条件**收尾,不是泛泛描述方案。这些验收条件后续会成为 dev-code-review「功能」轴的对齐真值。

---

## Step 1 — Interview (waves)

把 baseline「不假设」原则升级成 **多 wave 渐进式访谈 + 数学化清晰度评分**(灵感来自 oh-my-claudecode 的 deep-interview)。访谈强度自适应,简单需求一轮就走,复杂需求逐 wave 加深。

**所有模式都不允许跳过列歧义** —— baseline 第 1 条「不假设」是硬性表达,任何模式不得例外。差异只在「问几轮、要不要打分、要不要 challenge」。

### Step 1.0 — 选模式

按 `$ARGUMENTS` 或自动判断:

| 模式 | 触发 | 行为 |
|---|---|---|
| `--quick` | 用户加 `--quick`,或请求已经非常具体 | 单轮列歧义,不打分,直接进 Step 2 |
| `--default`(默认) | 大多数情况 | 多 wave + 打分,简单需求 Wave 1 即达标退出;最多 3 wave |
| `--deep` | 用户加 `--deep`,或检测到高风险 / 大改动 / 跨多个模块 | 多 wave + 打分 + Challenge modes;最多 6 wave |

### Step 1.1 — Brownfield pre-flight(若 cwd 是有代码的 repo)

如果当前目录有源码 / 包文件 / git 历史,且用户请求涉及修改 / 扩展现有系统,**Wave 1 之前**做一次轻量探索:

```bash
ls -la
find . -name "*.config.*" -o -name "package.json" -o -name "pubspec.yaml" -o -name "pyproject.toml" | head
git ls-files | head -30
```

把识别到的文件结构 / 主要框架 / 命名约定记为 `codebase_facts`。

**之后所有 wave 的问题必须引用这些证据**,不许问代码能直接告诉你的事(「你用什么数据库?」「auth 怎么做的?」等等)。

### Step 1.2 — Wave loop(`--default` / `--deep`)

`--quick` 模式跳过本步骤,走 Step 1.5 的简化格式。

**每 wave 严格按以下流程**:

**a. 打分(Wave 2 起,Wave 1 跳过)** —— 对累计对话内容打 4 个维度,各 0–1:

| 维度 | 权重(greenfield) | 权重(brownfield) | 含义 |
|---|---|---|---|
| Goal Clarity | 0.43 | 0.40 | 主目标能否一句话说清?核心实体能否命名? |
| Scope Clarity | 0.28 | 0.25 | in/out boundary 能列出来吗? |
| AC Clarity | 0.29 | 0.25 | 能写出二值、可验证的 acceptance criteria 吗? |
| Context Clarity | — | 0.10 | 这次改动落在系统哪里、影响哪些已有部分? |

`ambiguity = 1 - Σ(score × weight)`

**评分必须给 anchor**(防 LLM 往阈值方向收敛):**每个维度的分数必须列出具体证据**,例:

```
Goal: 0.85
  anchor: 用户已回答「自助导出 vs 后台代导」「字段白名单」「同步 vs 异步」3 个核心问题
Scope: 0.4
  anchor: in scope 仅「单用户导出 + 邮件链接」明确;out of scope 完全没列
AC: 0.5
  anchor: 有 2 条 AC(行数 / 字段),但 P95 延迟 / 失败重试 / 超时阈值 0 个数字目标
Context: 0.6
  anchor: 已确认接现有 notification-service,但没说 S3 bucket 权限模型
```

**拿不出 anchor 列表的维度,评分上限 0.6**。这是反 LLM「自评宽松倾向」的硬性矫正。

**用户施压「够了快点」时**,**不调高分数**让 ambiguity 假性达标。正确做法走「提前退出 + 标 STUCK」路径(见 退出条件 f)。

**b. 找最弱维度** —— 哪一项分数最低,作为下一题的瞄准对象。

**c. 一句 rationale + 一个问题(永远只问一个)**:

```
Wave {n} | 瞄准: {weakest} | 当前 ambiguity: {pct}%
为什么瞄这里: {一句话 rationale,说明为什么这维度是当前瓶颈}

问题: {一个具体问题}
```

问题风格按维度选:

| 维度 | 问法 | 示例 |
|---|---|---|
| Goal | 「具体什么时候算成功 / 什么不算?」 | 「『用户导出』指自助导出,还是后台代导?」 |
| Scope | 「边界在哪?」 | 「只做 v1,还是要兼容旧数据?」 |
| AC | 「怎么验证?」 | 「P95 延迟有数字目标吗?多少?」 |
| Context | 「现有系统怎么挂?」 | 「我看到 `services/auth/` 已有 JWT,本功能扩展它还是另起?」 |
| 概念漂移 | 「这玩意儿到底叫什么、是什么?」 | 「你前两轮叫 Tasks,刚才叫 Items。哪个才是核心实体?」 |

**绝不批量问** —— 一次一个,保证回答深度和打分准确性。

**d. 用户回答后,提取核心名词(实体名),与上一轮对比**:

- **stable**:同名同概念出现 → 累计 stable 计数
- **renamed**:换名但语义同 → 累计 renamed,显式标注
- **new**:新出现 → 累计 new

`stability_ratio = (stable + renamed) / total_entities`(Wave 2 起计算)

**e. 输出 round report**:

```
Wave {n} 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.7 | 0.40 | 0.28 | 主流程步骤未拆 |
| Scope | 0.4 | 0.25 | 0.10 | in/out 未列出 |
| AC | 0.5 | 0.25 | 0.125 | 缺数字目标 |
| Context | 0.6 | 0.10 | 0.06 | clear |
| **Ambiguity** | | | **43.5%** | |

Ontology: User, Order, ExportJob (vs Wave {n-1}: 1 stable, 1 renamed, 1 new — stability 67%)

下一目标: Scope (0.4) — 因为 in/out 边界还没列出
```

**f. 退出条件**(任一满足即进 Step 2):

- `--default`: ambiguity ≤ 0.30
- `--deep`: ambiguity ≤ 0.20
- 或:用户在 Wave 3+ 说「够了 / 直接来」(给 warning,显示当前未达标维度)
- 或:达到模式上限(default 3 / deep 6)—— 给 warning 后进 Step 2,未达标项进 Open questions,**spec status 标 STUCK**(见下)
- 或:Ontology 连续 2 轮 stability ≥ 90%(核心概念稳定到这种程度通常说明大问题已聊清)

**STUCK 终止状态**(借鉴 dev-plan / dev-fix 的 terminal status 模式):

如果达 wave 上限(default 3 / deep 6)仍 ambiguity > 阈值,spec 视为「卡住」 —— 不是失败,只是**信息不足以继续**(通常需要外部澄清:产品 / 设计 / 数据 / stakeholder)。这时:

- spec **照常生成**(不要丢弃用户已经回答的)
- artifact 顶部 `Status: STUCK`(而不是 DRAFT)
- `## Open questions` 段必须列出**具体阻塞了什么**(不是泛泛「需要更多信息」),例:
  - 「需要产品确认:是给 admin 还是 self-service?」
  - 「需要数据团队提供:历史导出量级,决定是否需要异步」
- 在 chat 给用户:「spec 标 STUCK,需要外部信息。建议先去拿:[列出具体 unblock 项],拿到后回来跑 `dev-spec --deep <slug>` 续 wave。」

dev-auto 看到 spec status STUCK → Phase 1-blocked → 推荐用户处理 Open questions 而非进 dev-plan。

### STUCK 触发的客观判据(防 LLM 软通过)

达 wave 上限时,**强制对照以下硬条件**。任一项满足 → 自动标 STUCK,**不允许标 ALIGNED 凑出通过**:

- **Goal anchor 缺失**:Goal 维度 ≥ 2 个 acceptance criteria 写不出
- **Open questions 含外部决策项**:Open questions 段 ≥ 1 条以「需要产品 / 设计 / 数据 / stakeholder 决策」开头
- **Scope 未对齐**:`In scope` 或 `Out of scope` 段任一为空
- **Ontology 未收敛**:连续 2 wave stability < 50%(核心概念漂移持续)

**Open questions 段的反模式**(LLM 倾向):写「需要更多信息」「细节后续再定」这种空话 —— 不算具体阻塞,**视作 STUCK 不通过**。必须每条**点名具体待澄清项 + 找谁拿**。

### Step 1.3 — Challenge modes(`--deep` only)

固定 wave 触发,每个 mode 用一次:

- **Wave 3 — Contrarian**:挑战核心假设。
   > 「你说要支持 10K 并发。如果只需要 100 呢?这是测过的需求还是默认假设?」

- **Wave 5 — Simplifier**:逼出最小可行版本。
   > 「v1 里哪些功能其实可以砍?砍了会损失什么?」

激活后下一题用对应视角问;问完一次该 mode 就用完,后续回到普通 socratic 提问。

如果两个 mode 都用完仍未达阈值,**且 ontology 漂移持续**(连续 2 轮 stability < 50%),启用 ad-hoc **Ontologist**:回到「这玩意儿到底是什么」的根问题。

### Step 1.4 — Assumption ledger(全程维护)

```
Verified (✓):  用户显式确认的
Assumed (⚠):   用户没否决的默认假设(默认入场)
Open (?):      用户明确说「不知道 / 待定」的
```

**Assumed → 进 spec 的 `## Assumptions`**
**Open → 进 spec 的 `## Open questions`**

### Step 1.5 — `--quick` 模式格式(单轮)

读用户原始请求,列出**多解 / 隐含假设 / 缺失约束**,让用户勾选 / 修正,**不打分、不多 wave**:

```
执行 dev-spec 之前,我对以下 N 点不确定,请确认:

1. <一句话描述歧义>
   选项:(a) ... (b) ... (c) 其他:你说
2. ...

回答后我会进入 Step 2。
```

参考维度(只列你确实不确定的):输入 / 输出 / 范围 / 性能 / 错误 / 权限 / UX / 兼容 / 部署 / 时间。

---

## Step 2 — Confirm scope(in / out)

依据用户回答,明确写出:

- **In scope**:本次明确要做的事(条目化,每条一句话)。
- **Out of scope**:本次明确**不做**的事(条目化)。这一段是 baseline「最小代码」的强制落地。
- **Assumptions**:仍带一些假设入场(因用户接受默认值),逐条列出来。

---

## Step 3 — Solution sketch

只写**最小可行方案**,不超过 1 页。

- **数据模型**:新增 / 修改的表 / 类型 / 接口。
- **流程**:核心调用链(可用 1–3 步描述,不要 sequence diagram 除非确实需要)。
- **变更面**:本方案会动到哪些文件 / 模块 / API surface。
- **替代方案**(可选):如果有第二方案,**只列差异和取舍**,不要写完整版。

> 写完后自检:能压到一半篇幅吗?如果能,压。

---

## Step 4 — Edge cases & risks

| 类目 | 内容 |
|---|---|
| 边界条件 | null / 空 / 0 / 负数 / 超大输入 / 并发 |
| 失败模式 | 上游挂 / 网络丢 / 超时 / 部分写入 |
| 风险 | 性能回退 / 数据迁移失败 / 兼容性破坏 |
| 缓解 | 每条风险对应一行缓解措施(feature flag / rollback plan / monitoring) |

无可写的类目**整段省略**,不写「无」。

---

## Step 5 — Verifiable acceptance criteria

这是 baseline「可验证成功标准」的落地,也是本 skill 的**终点**。每条验收条件必须满足:

- **二值** —— 通过 / 不通过,不存在「部分通过」。
- **可执行** —— 能被人或测试用例直接验证。
- **覆盖核心路径 + 至少一个边界**。

### 模板

```
AC-1  <一句话的输入条件> → <一句话的预期输出/行为>
AC-2  ...
AC-N  ...
```

### 例

- ❌ 「订单导出功能可用」(不可验证)
- ✅ 「输入:user-id 包含 1000 条订单 → 输出:CSV 文件,行数 = 1000,首列为 order_id,P95 < 3s」

---

## Step 6 — Write artifact

最终落到 `.claude/artifacts/designs/<feature>.md`(目录不存在则创建)。

文件结构:

```markdown
# <feature 名> Spec

> Status: DRAFT | ALIGNED | IMPLEMENTED | STUCK
> Author: <user>
> Last updated: <YYYY-MM-DD>

## Background
<2–3 句:为什么做这件事>

## In scope
- ...

## Out of scope
- ...

## Assumptions
- ...

## Solution
<Step 3 内容>

## Edge cases & risks
<Step 4 内容>

## Acceptance criteria
- AC-1 ...
- AC-2 ...

## Open questions
<Step 1 中未拍板、需后续讨论的项;无则省略>

## Core entities (ontology)
<只在 default / deep 模式输出;quick 模式省略>

| Entity | 类型 | 关键字段 | 关系 |
|---|---|---|---|
| User | core | id, email, locale | has many Order |
| Order | core | id, user_id, status, total | belongs to User |
| ExportJob | supporting | id, user_id, status, file_url | references User |

## Interview metadata
<只在 default / deep 模式输出;quick 模式省略>

- Mode: --default | --deep
- Waves: N
- Final ambiguity: X%
- Status: PASSED | EARLY_EXIT_BY_USER | CAP_REACHED

### Clarity breakdown(最终一轮)
| 维度 | 分数 | 权重 | 加权 |
|---|---|---|---|

### Ontology convergence(deep 模式)
| Wave | Entities | New | Renamed | Stable | Stability% |
|---|---|---|---|---|---|
```

### Spec footer(可选,建议在 spec 末尾追加)

```markdown
---
> **Next step**: 本 spec 已完成需求对齐。复杂功能建议下一步跑 `dev-plan`,
> 把本 spec 转成 Critic-approved 的实施 plan(产出至 `.claude/artifacts/plans/<feature>.md`);
> 简单功能可直接进入编码,commit 前用 `dev-code-review` 把关。
```

只是提示,不主动调起 dev-plan(skill 之间松耦合)。

---

## Hard rules

- **不要** 跳过 Step 1 的列歧义部分。任何模式(包括 `--quick`)都必须显式列出多解,不能默默选。
- **不要** 在 default / deep 模式下批量提问 —— 每 wave **只问一个问题**,等回答后再打分、再选下一题。
- **不要** 在 default / deep 模式下省略 round report —— 用户必须看见每轮的分数表 + 下一目标 + rationale。
- **不要** 在 brownfield 项目跳过 Step 1.1 的 pre-flight —— 不许问代码自答的事。
- **不要** 在 ambiguity 仍高于阈值时强行进 Step 2,除非用户明确说「够了」并接受 warning。
- **不要** 写代码 —— 本 skill 只产 spec,代码由用户后续动作触发。
- **不要** 默默替用户做技术选型(框架 / 库 / 协议)—— 列出选项让用户选。
- **不要** 把方案写成「未来五年路线图」—— spec 的范围是**这一次** delivery。
- **不要** 在 Acceptance criteria 里写「looks good」「works correctly」之类不可验证的话。
- **不要** 输出超过两屏的 spec —— 超出多半是把不该做的东西也写进来了,回 Step 2 删 in scope。

---

## Multi-Agent Note

`dev-spec` is main-agent-first because it negotiates scope with the user.

Explorers may gather codebase facts before or during spec work, but the main agent owns the interview, ambiguity scoring, assumptions ledger, and final scope confirmation. Apply `../../docs/multi-agent-policy.md` only for bounded read-only exploration.
