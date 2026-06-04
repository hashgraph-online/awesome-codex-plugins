---
name: dev-commit-writer
description: 'Use only when the user explicitly asks for a commit message without review. Trigger on: 帮我写 commit message, 给个 commit message, 生成 commit message, 这次 commit message 怎么写, write a commit message, skip review, 跳过 review, 我自审过了, only message, 只要 message. Writes a message from the current git diff in repository style. Does not review code quality or mutate the working tree; ambiguous commit requests like 帮我 commit route to dev-code-review.'
---

# Dev Commit Writer

Generate a commit message for the current git working tree, in the style of the branch's existing history.

This skill **only writes the message**, it does not evaluate code quality. If the user wants a quality check, route them to `dev-code-review` instead.

---

## Trigger routing

Use this skill only when the user explicitly asks for only a commit message and explicitly skips review.

Trigger phrases include:

- `帮我写 commit message`
- `给个 commit message`
- `生成 commit message`
- `write a commit message`
- `这次 commit message 怎么写`
- `skip review just give me the message`
- `跳过 review 只要 message`
- `我自审过了只要 message`
- `only message no review`

Ambiguous phrases such as `帮我 commit`, `commit 一下`, or `I want to commit` do **not** trigger this skill. Route them to `dev-code-review`, because team policy requires review before commit.

Optional arguments:

- `--staged`: use staged changes only
- `--path=<glob>`: limit scope to a path glob

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。以下行为准则在本 skill 全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

baseline 与本 skill 的关联点:
- **不假设** —— 当 diff 意图存在多解,**输出 2–3 个候选 message 让用户选**,或反问「主轴是 A 还是 B」,绝不默默挑一个写。
- **外科手术式改动** —— 在生成 message 前先做 **scope check**:diff 是否含与主改动无关的内容(格式化、邻近重构、无关注释)?若有,要么单独成 commit 建议拆,要么在 body 用 `Incidental:` 段落显式列出,不能埋在 subject 里。
- **最小代码** —— commit message 自身也要最小:subject ≤ 72 chars,body 仅在需要解释 *why* 时出现,**禁止 AI 套话**(「This commit refactors...」「We will now...」「Comprehensive improvements...」)。

---

## Step 0.5 — 用户意图确认(防止误派)

**触发本 skill 之前的入门检查**:如果用户原话是**模糊表达**(例 `帮我 commit`、`commit 一下`、`commit 这个改动`、`I want to commit`),并不是显式说「skip review / 跳过 review / 只要 message」,**先回问意图**:

```
你是想要:
  (a) 完整流程 — 先过 dev-code-review 评审,READY 后顺带出 commit message(默认推荐,符合团队约定 CLAUDE.md.template §2)
  (b) 只要 commit message,跳过 review(我自审过了 / 是 hotfix / 改动很小)

回答 a / b。如果 a,我退出,你跑 dev-code-review;如果 b,我继续生成 message。
```

**模糊请求默认走 a 路径**(让用户改换 dev-code-review),不要替用户选 b 跳过 review。这是 baseline「不假设」的硬性落地。

仅当用户原话**显式**表达 b 意图(关键词:「skip review」「跳过 review」「我自审过了」「only message」「hotfix 不要 review」),才直接进 Step 1。

---

## Step 1 — Gather the change set

只读命令,**不修改 working tree**:

```bash
git status --short
git diff --stat
git diff                  # unstaged
git diff --cached         # staged
git log --oneline -20     # 风格采样
git log -5 --pretty=format:"%H%n%s%n%n%b%n---END---"   # 完整 message 采样,看 body 风格
```

### Scope rules

- 默认审视 staged + unstaged。
- 若 `$ARGUMENTS` 含 `--staged` / `staged` / `--cached` → 仅 `git diff --cached`。
- 若 `$ARGUMENTS` 含 `--path=<glob>`(或裸路径)→ 限定该路径。
- 若无任何改动 → 停止并告知用户,**不要编造**。

---

## Step 2 — Sample the existing commit style

从 `git log` 采样,识别仓库的 commit 风格特征:

| 维度 | 观察点 |
|---|---|
| 前缀 | `feat:` / `fix:` / 中文「添加 / 修复」 / 无前缀 |
| Scope | `feat(auth):` 这种带 scope?是否常用? |
| 语气 | 祈使句(Add X)/ 陈述句(Added X)/ 中文 |
| 长度 | subject 平均长度,有无 body |
| Issue ref | `#123` / `JIRA-456` / 无 |
| 大小写 | subject 首字母大小写 |

**仓库风格优先于 conventional commits**。仅当采样出的风格不一致或 commit 数 < 3 时,退回 conventional commits(`feat|fix|refactor|docs|test|chore|perf|ci|style|build`)。

---

## Step 3 — Determine intent

读 diff,问自己:**用户这次想做的「一件事」是什么?**

### 单一意图(常见路径)

如果 diff 围绕一个清晰的目标(修一个 bug、加一个 feature、改一处配置),直接进 Step 4。

### 多意图 / 意图不明(必须显式处理)

应用 baseline「不假设」原则。出现以下任一情况时,**不要默默选一个 subject**,而是**列出候选并请用户选**:

1. diff 同时改了多个无耦合模块(例如 auth 和 payment 各自大改)。
2. diff 既含主改动又含明显 scope creep(例如 bug fix + 整个文件 reformat)。
3. 同一改动可以从不同角度概括(例如「重构 X 类」 vs 「修 X 类的 Y 行为」)。

**输出形式**:

```
意图判断存在歧义,本次改动可以理解为:

(a) <候选 message 1>
(b) <候选 message 2>
(c) 拆成两个 commit:<拆分建议>

请选 a/b/c 或给我你的版本。
```

不要替用户决定。

---

## Step 4 — Scope check

在产出 message 之前,扫一遍 diff 看是否含夹带改动:

- **格式化 / import 重排 / 空白调整** —— 与主意图无逻辑因果?
- **邻近代码的「顺手优化」** —— 不是这次任务要求的?
- **无关注释 / TODO 清理** —— 不是这次任务要求的?
- **lockfile / generated code 改动** —— 与主意图相关吗?

发现夹带时,有三个选择:

1. **建议拆 commit**(推荐):「检测到 N 处与主意图无关的改动,建议拆。subject 是…,拆出来的另一个 commit subject 是…」
2. **在 body 中以 `Incidental:` 显式列出**:适用于改动很小、单独成 commit 不值的场景。
3. **若用户坚持合并**:照做,但 body 必须列出 incidental 项,不能藏。

---

## Step 4b — Artifact references 检测(自动追溯)

在 commit message footer 自动加 `Refs:` 行,关联 spec / plan / fix 产物。

### 扫描流程

```bash
ls .claude/artifacts/designs/   # spec
ls .claude/artifacts/plans/     # plan
ls .claude/artifacts/fixes/     # fix
```

按以下规则:

| 找到的 artifact 数量 | 行为 |
|---|---|
| 0 个 | 不加 Refs(可能是 docs / chore / 不走流程的小改) |
| 1 个 + **subject 与 slug 语义匹配** | **自动加 Refs**,例 `Refs: spec/user-export` 或 `Refs: fix/cart-total-off-by-one` |
| 1 个 + **subject 与 slug 语义不匹配** | **不擅自加**,回问:「我看到唯一 in-flight 是 `<slug>`,但 commit 主题像是 `<subject>`(语义不重叠)。这个 commit 关联吗?(yes / no / 你给的关联)」 |
| 同 slug 的 spec + plan | 两条都加:`Refs: spec/<slug>` + `Refs: plan/<slug>` |
| 多个不同 slug | **回问用户**:「我看到这些 in-flight: [...],这次 commit 关联哪个?(可多选 / 或不关联)」 |

### 语义匹配判断(关键!)

判断 commit subject 与 slug 是否语义匹配,看以下 signal:

- **关键词重叠**:`subject` 含 slug 中的核心名词 / 动词?(例 subject `feat: add CSV export` ↔ slug `user-export` ✓ 重叠 export)
- **改动文件路径相关性**:diff 涉及的目录 / 模块和 slug 暗示的功能区相关?(例 slug `auth-refresh-token` ↔ 改 `src/auth/`/✓ 相关)
- **commit type 反向信号**:subject 类型 `fix(auth)` 但 slug 是 `user-export` 这种 feature → 大概率不关联(用户在 feature 开发期间顺手修了无关 bug)

**任一信号显示不匹配时,不要硬加 Refs** —— 错误的 Refs 比没 Refs 更糟糕(误导后续追溯)。宁愿问一下用户。

### Footer 格式

```
<subject>

<body 可选>

Refs: spec/<slug>
Refs: plan/<slug>
```

- 一行一个 Refs(便于 `git log --grep="Refs:"` 检索)
- type 用 `spec` / `plan` / `fix`(对应 designs/plans/fixes 目录)
- 如果用户回答「不关联」(例如 docs commit),不加

### 不加 Refs 的场景

- 用户显式说「这个 commit 不关联 artifact」
- 改动只涉及 README / CHANGELOG / 配置等流程外文件
- `.claude/artifacts/` 目录不存在(用户没用过 dev-skills)

---

## Step 5 — Output

### 默认输出(单一意图,无歧义,无 scope creep)

```
<type>(<scope>): <subject ≤ 72 chars>

<body 可选,仅在需要解释 why 或列 incidental 时出现>

<footer 可选,如 Refs: #123>
```

格式细则:
- subject **祈使语气**,不加句号。
- subject **不超过 72 字符**(常见仓库的硬约束)。
- subject 与 body 之间**空一行**。
- body 每行 ≤ 72 字符,bullet 用 `-`。
- 输出语言**跟随仓库 git log 的语言**(中文项目就出中文 message)。

### 多候选输出(意图歧义)

按 Step 3 的形式输出 a/b/c 让用户选,**不输出最终 message**。

### 反模式(禁止)

- ❌ 「This commit refactors the cart module to improve...」(AI 套话)
- ❌ 「Various improvements」(无信息量)
- ❌ subject 里塞两件事(`fix typo and add tests` —— 应拆)
- ❌ body 里复述 subject(冗余)
- ❌ 加表情 emoji,除非 git log 采样表明仓库就这风格

---

## Hard rules

- **不要** mutate working tree(不 `git add` / `git commit` / `git stash`)。
- **不要** 评审代码质量 —— 那是 dev-code-review 的职责。本 skill 只写 message。
- **不要** 在意图不明时强行输出最终 message —— 必须先要用户确认。
- **不要** 假装识别出仓库风格 —— 若 `git log` 不足 3 条或风格混乱,显式说「采样不足,使用 conventional commits 默认」。
- **不要** 输出超长 message —— 简单改动用单行 subject 就够,没要求别加 body。

---

## Multi-Agent Note

`dev-commit-writer` is a single-step tool, not a delegated agent lane.

Use it only when the user explicitly wants a commit message without review. In a multi-agent workflow, reviewer and verifier lanes should finish first; then the main agent may run this skill if the user still wants only message generation. See `../../docs/multi-agent-policy.md` for the ownership model.
