---
name: dev-auto
description: Use ONLY when the user explicitly wants end-to-end guided workflow through the dev-skills toolchain. Triggers on phrases like "用 dev-auto / 帮我串起来 / 从需求到 commit / 完整跑 / end to end / 走完整流程 / 下一步该做什么 / what's next". Reads `.claude/artifacts/{designs,plans,fixes}/` and `.design-context.md` existence to detect current phase (no deep parsing) and recommends next step across dev-design-context, dev-grill-docs, dev-plan, dev-tdd, dev-fix, dev-verify, dev-code-review, dev-commit-writer, and dev-finish. Does NOT invoke other skills, write code, or produce artifacts. Optional arguments — `[slug]`; `--status [slug]`; `--next [slug]`; `--recover [slug]`.
---

# Dev Auto

**指路,不替用户跑**。`dev-auto` 是 dev-skills 工具链的**入口推荐器** —— 接需求 / 接「下一步该做什么」的问题,**只输出建议**,绝不调起其他 skill,绝不写代码,绝不产出 artifact。

它服务的是「我有个需求,该怎么走完整流程」「UI 工作要不要先沉淀设计上下文」「我跑完 X 了,该跑什么」「X skill 给我返回 BLOCK / REJECT,我该回哪一步」这几类场景。

在 SDD 视角下,`dev-auto` 只做阶段导航:读取 `.design-context.md` 和 `.claude/artifacts/{designs,plans,fixes}/` 的存在性 / status,推荐下一步。它不生成 spec,不更新 plan,不替用户选择 artifact slug,也不自动启动其他 skill。

---

## Trigger routing

Use this skill only when the user explicitly wants end-to-end guided workflow through the dev-skills toolchain.

Trigger phrases include:

- `用 dev-auto`
- `帮我串起来`
- `从需求到 commit`
- `完整跑`
- `end to end`
- `走完整流程`
- `下一步该做什么`
- `what's next`

Do not trigger this skill when the user asks for a specific skill directly, such as `帮我设计`, `修个 bug`, or `commit review`; route those to the corresponding skill.

Optional arguments:

- `[slug]`: specify which feature or bug when multiple items are in flight
- `--status [slug]`: detect only the current phase
- `--next [slug]`: output only the next command
- `--recover [slug]`: recover after a failed or blocked skill result

---

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联:

- **不假设** —— 路径(feature / bug / hotfix)和复杂度模糊时,**列选项让用户选**,不替用户拍板。
- **最小代码** —— **dev-auto 自己也是最小流程**:不深读 artifacts、不维护 state file、不产出 doc。每次调用都从仓库现状现扫现答。

---

## Step 1 — 选模式

按 `$ARGUMENTS`(所有模式都可选 `[slug]` 后缀,例 `dev-auto --status user-export`):

| 模式 | 触发 | 行为 |
|---|---|---|
| 默认 | 用户给原始需求 / 不确定该做什么 | 完整流程:分类 → 扫现状 → 推荐链 + 下一步 |
| `--status [slug]` | 「现在我在哪一步」 | 只输出当前 phase 检测,不推荐 |
| `--next [slug]` | 「下一步跑什么」 | 只输出一条命令 + 一句 rationale,不展开 |
| `--recover [slug]` | 用户报告某 skill 失败(BLOCK / REVISE / NEEDS_DESIGN_CHANGE / 验证失败) | 推荐回到哪一步 + 为什么 + 怎么修 |

**slug 处理**:

- 若 `$ARGUMENTS` 显式给了 slug → 用它
- 若没给 + 仓库只有 1 个 in-flight 项目(designs/plans/fixes 加起来只有 1 个文件)→ 默认用那一个
- 若没给 + 多个 in-flight → **回问**:「我看到这些 in-flight: [...],你这次指哪个 slug?」
- 若没给 + 0 个 in-flight(Phase 0,新需求)→ 走默认模式 Step 2 起,**Step 3 propose slug 让用户确认**(见下)

---

## Step 2 — 分类请求(默认模式)

读用户原话,判断两个维度:

### 路径(path)

| 路径 | 信号 |
|---|---|
| **feature** | 「做个 X」「实现 Y」「加一个 Z」「新功能」 |
| **bug** | 「修个 bug」「这个错」「为什么 X 不工作」「排查」「报错」 |
| **hotfix** | 「线上紧急」「user impact」「赶时间」「一行修」+ 复杂度 simple |
| **unclear** | 信息不足 |

`unclear` 时**列选项问用户**(不假设):

```
你的需求路径不确定,请选一种:
  (a) 新功能 / 增强(走 dev-grill-docs → 可选 dev-plan → dev-tdd → dev-verify → dev-code-review)
  (b) 修 bug(走 dev-fix → dev-verify → dev-code-review)
  (c) Hotfix 紧急(跳过 spec/plan,仍过 dev-tdd → dev-verify → dev-code-review)
  (d) 其他:你说
```

### 复杂度(complexity)

| 复杂度 | 信号 |
|---|---|
| **simple** | 单文件 / 一句话改 / typo / 一个函数内 / 用户已经点出疑似行 |
| **moderate** | 多文件 / 单模块 / 中等 |
| **complex** | 跨多模块 / 跨服务 / 涉及鉴权 / 支付 / 数据迁移 / 公开 API breakage / PII / 高写并发 |

复杂度直接决定推荐模式参数(见 Step 4)。模糊时**默认 moderate**,但在输出里说明假设让用户纠正。

### 设计上下文(design context)

如果原始请求明显是 UI / landing page / 产品界面 / 品牌视觉 / 组件体验类工作,检查项目根目录是否已有 `.design-context.md`:

| 情况 | 行为 |
|---|---|
| 是设计类工作,且 `.design-context.md` 不存在 | 在 feature 推荐链最前面加 `dev-design-context` |
| 是设计类工作,且 `.design-context.md` 已存在 | 输出「设计上下文:已有」,不重复推荐 |
| 不是设计类工作 | 不推荐 `dev-design-context` |

`dev-design-context` 是一次性前置步骤,不是每个 feature 都必须跑。

---

## Step 3 — 扫描现状(只读 artifacts 存在性 + frontmatter status)

扫以下目录(都在用户当前 cwd 下,不在 dev-skills 仓库下):

```bash
ls -la .claude/artifacts/designs/   # dev-grill-docs / dev-spec 产物
ls -la .claude/artifacts/plans/     # dev-plan 产物
ls -la .claude/artifacts/fixes/     # dev-fix 产物
test -f .design-context.md && echo "design context: present"
```

### 文件名匹配 + Slug 确认

**Slug 命名空间约定**:
- `designs/<slug>.md` 和 `plans/<slug>.md` **同名 = 同一个 feature**(spec → plan 链路)
- `fixes/<slug>.md` 是**独立工作单元**(每个 bug 一个 slug),不与 feature slug 共享命名空间

**命名空间冲突检测**:扫描时如果**同一 slug** 同时出现在 `designs/` 和 `fixes/` 两处(例如 designs/auth-refresh.md + fixes/auth-refresh.md 共存)→ **报错并要求用户改名**:

```
检测到 slug 命名空间冲突:
  - .claude/artifacts/designs/<slug>.md (feature 路径)
  - .claude/artifacts/fixes/<slug>.md   (bug 路径)

这两条记录会让 phase 推断混乱(同时是 Phase 1 和 Phase 3)。
请改其中一个的名字让它们分开,例如:
  fixes/<slug>.md → fixes/<slug>-bug.md

改完再来跑 dev-auto。
```

**绝不擅自合并或假设语义**(它们可能是同一工作单元的两面,也可能是凑巧重名)。让用户拍板。

**Slug 推断 + 确认流程**:

| 情况 | 行为 |
|---|---|
| `$ARGUMENTS` 含明确 slug | 用它,直接进 phase 推断 |
| 仓库现有 1 个 in-flight | 用它,**仍向用户确认一句**「我用 `<slug>`,对吧?」 |
| 仓库现有多个 in-flight 但 `$ARGUMENTS` 没指定 | 列出所有,要求用户选 |
| Phase 0(新需求,无现有 artifact) | **propose slug 让用户确认 / 修正**:「我从你的请求推断 slug=`user-export`(动词+名词 kebab-case),你确认 / 改成你想用的名字 / 跳过 slug 概念(适用 hotfix)?」 |

**绝不**自动选 slug 跳过确认 —— slug 直接决定后续 artifact 文件路径,选错会导致 in-flight 项目混淆。

### Terminal status 解析(只读 terminal 信号)

读匹配到的 artifact 文件**第一行 frontmatter / quote block 里的 Status 字段**,只识别以下**对 dev-auto 有意义**的 terminal status:

| 文件 | 关心的 terminal status | 含义 |
|---|---|---|
| `.claude/artifacts/designs/<slug>.md` | `STUCK` | spec 卡住(wave 上限仍 ambiguity 高),blocked,需外部信息(见 Open questions) |
| `.claude/artifacts/designs/<slug>.md` | 其他(DRAFT/ALIGNED/IMPLEMENTED 任一) | spec 已存在,可进下一阶段 |
| `.claude/artifacts/plans/<slug>.md` | `APPROVED` | plan 已通过,可进 dev-tdd |
| `.claude/artifacts/plans/<slug>.md` | `BELOW_CONSENSUS_THRESHOLD` | plan 未达共识,blocked,需用户决策 |
| `.claude/artifacts/fixes/<slug>.md` | `FIXED` | 修复完,待 dev-verify / dev-code-review |
| `.claude/artifacts/fixes/<slug>.md` | `BELOW_CONFIDENCE_THRESHOLD` | root cause 找不到,blocked |
| `.claude/artifacts/fixes/<slug>.md` | `NEEDS_DESIGN_CHANGE` | 需架构改动,blocked,转 dev-plan |

**spec artifact 的 `DRAFT` / `ALIGNED` / `IMPLEMENTED` lifecycle status 不影响 phase 推断** —— spec 只看「文件是否存在」,生命周期 status 留给用户手动管理。

**绝不**深读其他内容(不解析 AC / 不读 hypothesis 表 / 不读 plan body)。读了就违反「最小代码」。

### 推断当前 phase(简化:存在性 + terminal 信号)

```
没找到任何 artifact                 → Phase 0 (尚未开始)
designs/<slug>.md 存在 + 非 STUCK   → Phase 1 (spec 已存在,可进 plan / dev-tdd)
designs/<slug>.md 存在 + STUCK      → Phase 1-blocked (spec 卡住,需外部信息,见 --recover)
plans/<slug>.md 存在 + APPROVED     → Phase 2 (plan 已通过,待 dev-tdd)
plans/<slug>.md 存在 + BELOW...     → Phase 2-blocked (plan 未达共识,见 --recover)
fixes/<slug>.md 存在 + FIXED        → Phase 3 (修复完,待 dev-verify / dev-code-review)
fixes/<slug>.md 存在 + 其他 status   → Phase X-blocked (见 --recover)
```

**无法明确推断时**(例如 fixes/<slug>.md 存在但 status 字段缺失),直接告诉用户「我看到 X 但不确定状态,请说一下你刚跑完什么 / 现在卡在哪」。

### Clean-tree worktree checkpoint(仅当下一步会进入写代码)

如果推荐链的下一步或后续步骤包含「写代码 / 修代码」,在输出建议前先检查:

```bash
git status --short
git branch --show-current
```

判定:

| 情况 | 输出要求 |
|---|---|
| `git status --short` 为空,且任务是 moderate / complex 或会修改代码 / 多文件规则 / 配置 / 测试 | 在「下一步」后追加 worktree checkpoint,推荐用户先创建独立 worktree |
| 当前分支是 `main` / `master` / `release/*` | 默认推荐 worktree;若用户坚持当前目录,提醒会直接修改当前目录 |
| 当前已经 dirty | 不推荐直接创建 worktree;提示已有改动,先让用户决定继续当前目录 / 清理 / 另建基于 HEAD 的 worktree |
| simple typo / 单文件小文档 / 用户明确说当前目录改 | 可省略 checkpoint |

推荐格式:

```
编码前检查
  当前 git tree 干净,且下一步会修改代码/多文件。
  建议先创建 worktree:
  $ git worktree add -b codex/<short-slug> ../<repo>-<short-slug>
```

worktree 命名遵守 `CLAUDE.md.template` 的规范:`codex/<short-slug>` 分支 + 兄弟目录 `<repo>-<short-slug>`。

---

## Step 4 — 输出推荐(默认模式)

**严格按下列三段输出**,不要加寒暄、不要输出多余分析:

```
━━━ Dev Auto ━━━
路径   : feature | bug | hotfix
复杂度 : simple | moderate | complex
Slug   : <feature-slug>(自动推断,你可以纠正)

完整推荐链
  1. <skill> <模式参数>          (一句话该步做什么)
  2. <skill> <模式参数>          (按路径列出,没有就省略)
  3. <skill> <模式参数>          (按路径列出,没有就省略)
  ...

当前位置
  Phase <N>:<一句话当前状态>
  已完成 artifacts:<文件路径列表>

下一步
  $ <精确命令,可复制粘贴>
  为什么:<一句话 rationale,不超过两行>

编码前检查
  <仅当下一步会写代码且 clean tree checkpoint 命中时输出;否则整段省略>
```

### 推荐链对照表

下面是**默认推荐**,用户可以偏离(但偏离时 dev-auto 应在下一次 `--status` 时容忍):

| 路径 \ 复杂度 | simple | moderate | complex |
|---|---|---|---|
| **feature** | dev-grill-docs --quick → dev-tdd → dev-verify → dev-code-review → dev-finish | dev-grill-docs → dev-tdd → dev-verify → dev-code-review → dev-finish | dev-grill-docs --deep → **dev-plan --deliberate** → dev-tdd → dev-verify → dev-code-review → dev-finish |
| **bug** | dev-fix --quick → dev-verify → dev-code-review → dev-finish | dev-fix --default → dev-verify → dev-code-review → dev-finish | **dev-fix --deep** → dev-verify → dev-code-review → dev-finish |
| **hotfix** | 跳过 spec/plan,但仍走 dev-tdd → dev-verify → dev-code-review → dev-finish | n/a — 升 feature/bug moderate | n/a — complex 不允许 hotfix,升 feature/bug complex |

**关键规则**:

- complex feature **强烈建议 dev-plan --deliberate**(自带 pre-mortem + expanded test plan)
- UI / landing page / 产品界面类 feature 且没有 `.design-context.md` 时,在 feature 链路前追加 `dev-design-context`。
- complex bug **强烈建议 dev-fix --deep**(强制 3-5 hypothesis + 反向追溯 + instrument)
- feature / hotfix / refactor 等直接编码路径默认推荐 `dev-tdd`;bug 路径由 `dev-fix` 内置 failing test + red→green→red 验证,不要再追加第二套 `dev-tdd`。
- 任何完成声明前默认推荐 `dev-verify`,避免把局部测试通过包装成完整 ready。
- `dev-finish` 只在验证和 review 后用于 merge / PR / keep / discard,不是 coding step。
- hotfix 只允许 simple,如果用户标 hotfix 但实际是 moderate/complex,**警告并建议升级路径**(具体话术见下)

### Hotfix 升级警告(用户标 hotfix 但实际不是 simple)

输出严格按以下话术,**不要软化**:

```
你标了 hotfix,但 symptoms 含 [具体信号:跨服务 / 鉴权 / 数据迁移 / ...],
实际是 [moderate/complex]。

Hotfix 路径会跳过 dev-grill-docs / dev-plan,但不能跳过 dev-tdd / dev-verify / dev-code-review。否则**很可能让 dev-code-review 抓出 P0 阻塞**
(常见 P0:闭环失败 / 边界没考虑 / 跨模块未对齐),反而比走完整路径更慢。

建议改走:
  → [feature/bug] [moderate/complex] 路径(完整 spec + plan + tdd + verify + review)
  → 完整推荐链:[列具体 skill 序列]

如果你坚持 hotfix(承担 review 阶段被 BLOCK 的风险),回复「继续 hotfix」。
否则我按 [推荐路径] 重新输出推荐。
```

---

## Step 5 — `--status` 模式

只输出当前位置,不推荐:

```
━━━ Status ━━━
Slug:<feature-slug>
Phase <N>:<一句话>
已完成:<artifacts 列表>
未完成:<剩余 phase 列表>
```

---

## Step 6 — `--next` 模式

只一条命令,极简:

```
$ <skill> <args>
(<一句话 rationale>)
```

适合用户已经在流程里,只想问「就告诉我下一句敲什么」。

---

## Step 7 — `--recover` 模式

输入:用户报告某 skill 输出是 BLOCK / REVISE / REJECT / NEEDS_DESIGN_CHANGE / verify 失败 / 别的失败信号。

### Step 7.0 — 输入清晰度检查(必做)

如果用户输入**不含明确 skill 名 + 失败信号**,**不要硬猜**,先回问:

```
要给你恢复建议,我需要两条信息:
  1. 你刚跑了哪个 skill?(dev-grill-docs / dev-spec / dev-plan / dev-tdd / dev-fix / dev-verify / dev-code-review / dev-commit-writer / dev-finish)
  2. 它的输出关键信号是什么?(贴 Verdict / Status / 错误摘要那一行就行)

例如:「dev-code-review 给我 Verdict = ⚠ FIX P1,有 2 处 console.log 残留」
或:「dev-fix 跑了 deep,3 假设全 fail,Status: BELOW_CONFIDENCE_THRESHOLD」
```

得到具体信息后再进 Step 7.1 决策表。

### Step 7.1 — 决策表

按以下决策表推荐恢复路径:

| 失败 skill | 失败信号 | 推荐恢复 |
|---|---|---|
| dev-grill-docs / dev-spec | spec status = STUCK(达 wave 上限仍 ambiguity > 阈值) | 看 spec 的 `Open questions` 段,**逐项**拿外部信息(产品 / 设计 / 数据 / stakeholder)。拿到后回来跑 `dev-grill-docs --deep <slug>` 续 wave。**不要**跳过 STUCK 直接进 dev-plan(plan 会基于残缺 spec 出错) |
| dev-plan | Critic verdict = REVISE | 回 dev-plan,Planner v2 修复 Critic 反馈 |
| dev-plan | Critic verdict = REJECT(深度问题) | 回 dev-plan 重起 Planner,可能要回 dev-grill-docs 拆需求 |
| dev-plan | BELOW_CONSENSUS_THRESHOLD(3 次迭代未达共识) | 标 plan 为 BELOW,把当前最好版本交给用户决策;考虑回 dev-grill-docs 缩小 scope |
| dev-fix | 反向追溯找不到 root cause,3 假设全 fail | 升 `dev-fix --deep`(若已 deep 则进下一行) |
| dev-fix | deep 模式 3 高置信 hypothesis 全 fail / 3 fix attempt fail | 升 `dev-plan --deliberate` 评估架构改动,plan 通过后回 dev-fix Step 6 |
| dev-fix | NEEDS_DESIGN_CHANGE | 同上,转 `dev-plan --deliberate` |
| dev-fix | Verify 7b stash 后仍 GREEN(test 没真测到 bug) | 回 dev-fix Step 2,重写 test 用更精确断言 |
| dev-tdd | RED 阶段测试直接 PASS | 回 dev-tdd Step 3,重写测试直到能证明行为缺失 |
| dev-tdd | GREEN 后相关测试失败 | 回写代码 step,修实现而不是削弱测试 |
| dev-verify | 验证命令 FAIL | 回写代码 / dev-fix,不允许进入 dev-code-review 或 dev-finish |
| dev-verify | claim 无 proof command | 补 proof command 或把该 claim 标为未验证 |
| dev-code-review | Verdict = BLOCK(P0 / secret 泄漏 / 闭环失败) | 回写代码 step 修 P0,**不允许 commit** |
| dev-code-review | Verdict = FIX P1 | 回写代码 step 处理 P1,或在 PR 描述里**显式覆盖 + 解释**(参见 CLAUDE.md.template) |
| dev-commit-writer | 输出多候选(意图歧义) | 回写代码 step 拆 commit;或者用户选定一个候选继续 |
| dev-finish | tests / review 未通过 | 回 dev-verify / dev-code-review,不展示 merge / PR 选项 |
| dev-finish | discard 未精确确认 | 停止,等待用户输入精确 `discard` |

输出形式:

```
━━━ Recover ━━━
失败 skill : <skill>
失败信号   : <一句话>

推荐恢复:
  → 回到 phase <N>(<skill> <args>)
  原因   :<一句话>
  操作建议:<具体下一步,可复制粘贴的命令>

如果上述方式无效:<次选恢复路径>
```

**绝不输出「再试一次相同操作」** —— 失败有原因,要么修要么换路径,不许重复。

---

## Hard rules

- **不要** 调起其他 skill。`dev-auto` 永远是建议器,用户自己跑。
- **不要** 写代码。
- **不要** 产出 artifact 文件(没有 `.claude/artifacts/workflows/` 这种东西)。
- **不要** 深读 artifact 内容 —— 只读存在性 + frontmatter status 字段。读 AC / hypothesis / plan body 就违反「最小代码」。
- **不要** 替用户决定模糊 path / complexity —— 列选项问。
- **不要** 维护跨调用的 state —— 每次调用都从仓库现状重新扫,推断当前 phase。
- **不要** 在 `--next` / `--status` 模式里输出多余信息 —— 这两个模式追求极简。
- **不要** 在 `--recover` 模式建议「再试一次」—— 必须是修复 / 换路径 / 升模式 / 转 skill,不许重复同操作。
- **不要** 把 hotfix 路径用在 complex 改动上 —— 警告并建议升级到 feature/bug 路径。
- **不要** 假装能看到代码改动 —— dev-auto 不读源码,只看 artifacts。代码状态由用户告知。

---

## 与其他 skill 的关系

- **入口侧**:dev-auto 是**所有路径的可选入口**。用户可以直接跑某个 skill,也可以先跑 dev-auto 拿推荐再决定。
- **不调用**:dev-auto 推荐 `dev-grill-docs` 时,**用户**自己执行 `dev-grill-docs`,不是 dev-auto 调起。
- **下游回流**:用户跑完某 skill 后,可以再来 dev-auto 问下一步,也可以自己看流程图直接进。
- **触发竞争**:dev-auto 的 description 严格限制只在用户**显式要求 workflow / 串起来 / 完整跑**时触发,避免和 dev-grill-docs / dev-fix 等具体 skill 抢触发。

---

## Multi-Agent Note

`dev-auto` is main-agent-first. It remains a workflow recommender, not an orchestrator.

When the host runtime supports multi-agent execution, `dev-auto` may recommend a next phase that is suitable for delegation, but it must not spawn sub-agents, invoke other skills, or perform delegated work itself. The main agent applies `../../docs/multi-agent-policy.md` when deciding whether to delegate.
