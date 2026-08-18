---
name: dev-code-review
description: 'Use when reviewing uncommitted or staged git changes before commit. Trigger on: 帮我 commit, 我要 commit, commit 一下, 准备提交, pre-commit, 提交前检查, 看下这次修改, commit 前看一下, I want to commit, let''s commit, review my changes. Checks conventions, functional correctness, security/reliability/performance hotspots, wiring, comments, and dead code; emits a commit message only when READY. Does not mutate the working tree. Route to dev-commit-writer only when the user explicitly asks to skip review or wants only a commit message.'
---

# Dev Code Review

IRON LAW: NO READY VERDICT WITHOUT WIRING EVIDENCE, AND NO COMMIT MESSAGE UNLESS READY.

Focused review on the **current git working tree** right before a commit.
Goal: catch 规范、功能、安全/可靠性风险、闭环、注释、废代码 problems **before** they enter history.

This is NOT a full architecture review. Stay scoped to what actually changed in this diff.

---

## Trigger routing

Use this skill when the user is preparing to commit code or asks to review the current git working tree before committing.

Trigger phrases include:

- `帮我 commit`
- `我要 commit`
- `commit 一下`
- `commit 这个改动`
- `准备 commit`
- `准备提交`
- `pre-commit`
- `提交前检查`
- `这次改动 review 一下`
- `看下这次修改`
- `commit 前看一下`
- `I want to commit`
- `let's commit`
- `check before commit`
- `review my changes`

Ambiguous commit requests such as `帮我 commit` / `commit 一下` mean "go through the full commit flow: review first, commit message only if ready". This is the safer default path because team policy requires review before commit.

Only route to `dev-commit-writer` when the user explicitly says `skip review`, `跳过 review`, `我自审过了`, `only message`, or `只要 message`.

For other workflow stages, route to the matching skill:

- Fuzzy requirements before code → `dev-grill-docs` (`dev-spec` remains a compatibility alias)
- Spec to implementation plan → `dev-plan`
- Bug investigation / root cause fix → `dev-fix`

Optional arguments:

- `--staged`: limit to staged changes only
- `--path=<glob>`: limit scope to a path glob

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。以下行为准则在本 skill 全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

baseline 与本 skill 的关联点:
- **不假设** —— diff 意图不明确时,在报告里以一句话标注「我对意图的理解可能是 A 或 B,请确认」,而不是默默选一个写进 commit message。
- **外科手术式改动** —— 评审时**额外做一道 scope check**:diff 是否夹带与主改动无关的「顺手优化」(格式化、邻近重构、无关注释清理)?若有,作为 P1 finding 提示拆 commit。
- **可验证成功标准** —— 「闭环」轴的 grep 验证就是这条准则的具体应用:新符号必须有可见 caller,这是「完成」的可验证判据。

skill 内部规则在与 baseline 冲突时**以局部为准**(例如严重度 rubric)。

---

## Red flags — backtrack if any appear

If any red flag appears, stop and correct the review before reporting:

- You judged 闭环 without running the required `git grep` evidence command or naming an exemption.
- A finding has no concrete `path:line`, no clear axis, or no actionable fix.
- You are about to report an architecture/style preference as P0/P1 without a concrete functional, security, reliability, performance, wiring, or maintainability risk.
- The diff is large or mixed-concern, but you have not done the scope check.
- Verdict is not `✅ READY`, but you are about to output a `Commit` section.

---

## Step 1 — Gather the change set

Run these read-only commands. They never mutate the working tree:

```bash
git status --short
git diff --stat
git diff                  # unstaged
git diff --cached         # staged
git log --oneline -10     # recent commit message style
```

### Scope rules

- If both staged and unstaged changes exist, review **both** but call out which is which in the report.
- If `$ARGUMENTS` contains `--staged` / `staged` / `--cached` → restrict to `git diff --cached`.
- If `$ARGUMENTS` contains `--path=<glob>` (or a bare path) → restrict to that path.
- If there are zero changes → stop and tell the user. Do not invent findings.

### Diff size / concern grouping

- If the diff is large (>500 changed lines), summarize changed files by module/feature area before judging findings, then review in batches. Keep the final report ≤60 lines; do not downgrade concrete blockers just because the diff is large.
- If the diff mixes unrelated concerns, group your reasoning by logical feature area and apply the baseline scope check. Unrelated drive-by changes that should be split remain a P1 scope finding.
- For generated, lockfile, or pure data-heavy diffs, review the human-authored source of truth first and mention skipped generated/data files in Scope.

### File-reading rules

For each modified file, read the **full file** (not just the hunks) when the diff touches logic, so you can judge whether the change is closed-loop. Skim-only is acceptable for pure config / lockfile / generated code.

### Skip / flag patterns

Skip these files' contents (mention they exist in Scope, but don't review):

- Binary files (images, fonts, archives, compiled artifacts)
- Lockfiles: `*.lock`, `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Gemfile.lock`, `poetry.lock`, `go.sum`
- Generated code: `*.g.dart`, `*.freezed.dart`, `*.pb.go`, `*.pb.ts`, `*_pb2.py`, `*.gen.ts`
- Pure data files > 500 lines

If the diff includes paths that are usually gitignored (`node_modules/`, `.next/`, `target/`, `dist/`, `build/`, `.venv/`, `__pycache__/`, `.DS_Store`), emit a **P1 finding (axis: 废码)** prompting the user to check `.gitignore`.

---

## Step 2 — Severity rubric (read this BEFORE judging findings)

Use this rubric to keep severity consistent across runs:

- **P0 (BLOCK)** — any of:
  - 未闭环 (new symbol / route / component / config key with no consumer)
  - Secret / credential / API key / token leaked
  - Clear functional defect that will fail on the first real call (null-deref guaranteed, inverted condition, broken auth check, injection)
  - Security flaw with direct exploitability or data exposure (auth bypass, missing tenant/ownership check, unsafe command/file path from user input)
  - Destructive change that breaks others' working tree (broken migration, deleted public API still in use)
- **P1 (FIX)** — any of:
  - Unhandled edge case (null / empty / 0 / negative / overflow / concurrent re-entry) where the path is reachable
  - Silently swallowed errors (`catch {}`, `except: pass`, `_ = err`)
  - Residual debug output (`console.log`, `print`, `debugPrint`, `println!`, `fmt.Println`, `NSLog`, `debugger`)
  - Project lint config violation
  - Naming / style severely inconsistent with surrounding file
  - Missing input validation at a trust boundary
  - Reachable reliability/performance regression (race condition, missing transaction/idempotency, N+1/hot-path loop, unbounded memory/IO)
- **P2 (NIT)** — any of:
  - Redundant / stale / decorative comments
  - Small duplicated block (one helper would do)
  - Style preference, formatting, ordering
  - `TODO` / `FIXME` without owner or ticket

When uncertain, prefer the lower severity. Don't inflate to look thorough.

---

## Step 3 — Review along 5 axes

For every finding, cite `path:line` and tag severity using the rubric above.

### SDD artifact check

Before judging the functional axis, scan `.claude/artifacts/{designs,plans,fixes}/` when it exists:

- If exactly one relevant artifact or one shared slug exists, use it as the review contract.
- If both `designs/<slug>.md` and `plans/<slug>.md` exist, check the diff against both the spec acceptance criteria and the plan ADR.
- If `fixes/<slug>.md` exists, check the diff against the recorded root cause, fix summary, regression test, and verification evidence.
- If multiple unrelated slugs exist, do not guess; mention that artifact alignment could not be determined.

Clear divergence from an active spec, ADR, or fix artifact is a functional finding. If the implementation is reasonable but the artifact is stale, report artifact drift instead of silently accepting the mismatch.

### Risk checklist loading

Load `references/risk-checklist.md` **only when relevant**:

- Diff touches auth/authz, tenant or ownership boundaries, network/API handlers, database writes/queries, file paths, shell commands, deserialization, crypto, logging of payloads, dependency/source changes, concurrency, caching, pagination, or hot-path loops.
- Diff adds/removes public endpoints, background jobs, migrations, feature flags, SDK/API clients, or code that handles untrusted input.
- You suspect a security/reliability/performance issue but need a compact checklist to avoid missing common cases.

Keep findings mapped to the existing axes. Security, reliability, and performance problems normally belong to **功能**, unless the issue is purely unused/dead code.

### 1. 规范 (Code style & conventions)

**先识别本次 diff 涉及的语言**,再用该语言的官方/社区规范评审。**详细的逐语言检查清单见 `references/lang-conventions.md`** —— 只加载与本次 diff 实际涉及语言相关的小节,不要把整个文件读进来。

**项目配置优先级最高**:如果项目根目录存在 lint 配置(`.eslintrc*`、`analysis_options.yaml`、`pyproject.toml`、`.golangci.yml`、`clippy.toml`、`rustfmt.toml`、`.editorconfig`、`tsconfig.json`、`.swiftlint.yml` 等),**以项目配置为准**,覆盖 references 中的通用条目。

**通用项(语言无关,所有语言都查)**:

- Naming **跟随同文件/同模块邻居** —— 改动的命名风格必须和周围一致,不要一个文件里混用 camelCase 和 snake_case。
- Function size sane (< ~50 行)、file size sane (< ~800 行)。仅当**本次 diff 让它变得更糟**时才 flag。
- No deep nesting (>4) introduced by this change.
- No hardcoded secrets, API keys, tokens, absolute local paths, personal info.
- No 调试输出残留 (`console.log` / `print` / `debugPrint` / `println!` / `fmt.Println` / `NSLog` / `debugger` 等)。
- Imports / use / require 被实际使用,没有新增未使用的导入。
- Errors handled explicitly at boundaries; no silently swallowed `catch {}` / `except: pass` / `_ = err`。
- Immutability respected where the surrounding codebase uses it.

### 2. 功能 (Functional correctness)

Read the diff as if you have to ship it:

- Does the change actually do what its commit/PR intent suggests?
- Are edge cases handled? (null / empty / error / loading / 0 / negative / very large)
- Any obvious off-by-one, wrong operator, swapped argument, copy-paste bug?
- Async / await / Future / Promise correctness — no fire-and-forget that should be awaited.
- State updates: are they safe under concurrent calls / re-entry?
- Inputs from network / user / disk validated at the boundary?
- Security boundaries: auth/authz/tenant checks preserved; no injection, SSRF, path traversal, unsafe deserialization, weak crypto, or sensitive logging introduced.
- Reliability/data integrity: transactions/idempotency/retry semantics remain correct; no check-then-act race, lost update, partial write, or resource leak.
- Performance: no new N+1 query, unbounded pagination/load, expensive hot-path loop, cache without invalidation/TTL, or main-thread blocking work.

### 3. 闭环 (Is the change actually wired up end-to-end?)

This is the most commonly skipped check. **Two-valued — there is no "partially closed loop".**

For every new public symbol introduced in this diff (function / class / method / route / component / config key / event type / DB column / error type), verify a consumer exists:

```bash
git grep -n "<symbol>" -- ':!<defining_file>'
```

**Evidence before claims(必做)**:必须**真正调用 bash 跑 `git grep`**,**在报告里展示 command + output**(完整粘贴,或简洁引用「N matches in M files: ...」),不能只说「grep 验证通过」。这是 baseline「Evidence before claims」在闭环轴的最严落地 —— **没真跑 grep 就不算闭环检查**。

Decision tree:

1. **Has external callers** → ✓ closed loop
2. **No external callers, but symbol is one of the framework-invoked exemptions below** → ✓ closed loop
3. **Exported / public, 0 callers, not exempt** → **P0 未闭环 (dangling)**, name the missing wire-up
4. **Private / file-local, 0 callers** → **P1 废码** (unused private symbol)

**Framework-invoked exemptions (count as closed loop even with 0 grep hits)**:

- Test functions in test files (`*_test.*`, `*.test.*`, `*.spec.*`, `test_*.py`)
- Framework lifecycle / override methods (Flutter `build()` / `initState()` / `dispose()`, React component default exports, Vue `setup()`, Android `onCreate()`, iOS `viewDidLoad()`, etc.)
- Symbols invoked via reflection / annotations / DI (`@Override`, `@Autowired`, `@Component`, `@Injectable`, Spring beans, etc.)
- CLI entry points (`main()`, files declared as `bin` in package.json / pubspec.yaml)
- Public API surface of a library package (anything re-exported from the package's index file)

Other things to verify in this axis:

- New API endpoints / routes / handlers are **registered** in the router/module.
- New UI components are **rendered** by a parent (or are top-level routes).
- New config keys are **read** by the consuming code.
- New event/message types are **handled** on the receiving side.
- New DB migrations are **used** by queries and have a working **rollback**.
- Tests for new logic exist, OR the user explicitly opted out.

### 4. 多余注释 (Excess / stale comments)

Comments should explain **why**, not **what**. Flag:

- Comments that just restate the next line (`// increment counter` above `i++`).
- Commented-out code blocks. (Remove — git already has the history.)
- AI-style narrating comments (`// We will now loop through...`, `// This function...`).
- `TODO` / `FIXME` without an owner or ticket.
- Stale comments that no longer match the code below them.
- Boilerplate banners / decorative separators added by this diff.
- Translation drift (e.g. a Chinese comment describing English code that no longer matches).

**Keep**: comments that document a non-obvious *why*, an invariant, a known bug workaround, or a subtle constraint.

### 5. 多余/无用代码 (Dead code introduced or left behind)

- Unused variables, parameters, private methods, helper functions added by this diff.
- Unreachable branches (`if (false)`, code after `return`).
- Duplicated logic — same block copied across files when one helper would do.
- Re-exports / shims / "for backwards compat" wrappers added without a real consumer.
- Empty files, empty classes, placeholder stubs that this diff didn't actually fill in.
- Old code path the new code replaced — should it be deleted in this same commit?
- Deletion candidates: distinguish **safe delete now** from **defer with plan**.
  - Safe delete now → list in `Cleanup` only when evidence shows no active consumers and deletion is within this commit's scope.
  - Defer with plan → report as a P2/P1 finding instead of `Cleanup`, naming the missing evidence/precondition (telemetry, migration, external consumer check, rollback path).

---

## Step 4 — Report

输出语言跟随用户提问语言(中文提问出中文报告)。**严格按下列模板**,不要加寒暄、不要复述用户原话、不要解释自己在做什么。

Before output, run this self-check:

- Verdict matches the rubric: P0 / 闭环 ✗ / secret → `❌ BLOCK`; P1 only → `⚠ FIX P1`; no P0/P1/debug/dead-code → `✅ READY`.
- Scope includes file count, added/removed lines, and staged/unstaged/both.
- Every new public symbol has `git grep` evidence or an explicit framework/public-API exemption.
- Every finding has `path:line`, one of `规范 / 功能 / 闭环 / 注释 / 废码`, and one actionable fix sentence.
- `Commit` is omitted unless Verdict is `✅ READY`.
- Full report stays ≤60 lines.

```
━━━ Dev Code Review ━━━
Verdict   : ✅ READY  /  ⚠ FIX P1  /  ❌ BLOCK
Scope     : <N> files · +<added> / −<removed> · <staged|unstaged|both>
Intent    : <一句话,基于 diff 自己判断改动在做什么>
Languages : <按 diff 行数降序,例如:Dart, TypeScript>   Lint config : <analysis_options.yaml | none>

Axis Check
  规范   ✓ / ⚠ / ✗   <一行说明,仅在非 ✓ 时填>
  功能   ✓ / ⚠ / ✗   ...
  闭环   ✓ / ✗        ...   ← 二值,不存在"部分闭环"
  注释   ✓ / ⚠
  废码   ✓ / ⚠

Findings  (P0 阻塞 · P1 应修 · P2 可选)
  [P0] path/to/file.dart:42         <axis>   <一句话问题>
       → <一句话修复建议>
  [P1] path/to/other.ts:117         <axis>   ...
       → ...
  [P2] ...

Cleanup   (建议在本次 commit 内一并删除)
  - path:line  <注释 / 死代码 / 调试输出>  — <一句话原因>

Commit
  <type>(<scope>): <subject ≤72 chars>
  <空行>
  <body 可选,列要点;无要点则省略 body>
  <空行>
  Refs: spec/<slug>      ← 自动追溯,见规则 11
  Refs: plan/<slug>      ← 同 slug 的 spec + plan 都列
```

### 模板填写规则(非常重要)

1. **Verdict 三选一**,判定逻辑:
   - `❌ BLOCK` ← 闭环 ✗ 或 存在 P0 或 检出 secret/credential
   - `⚠ FIX P1` ← 闭环 ✓ 且 无 P0 且 存在 P1
   - `✅ READY` ← 闭环 ✓ 且 无 P0/P1 且 无残留调试输出 且 无明显废码
2. **Languages 排序**:按本次 diff 中各语言的修改行数降序排列,让用户一眼看出主要改动在哪种语言。
3. **Axis Check** 用 `✓ / ⚠ / ✗` 单字符,**仅在非 ✓ 时**追加一行说明。全部 ✓ 时整张表保留但说明列留空。
4. **Findings** 严格按 `[P?] path:line  <axis>  <问题>` 单行 + 缩进 `→ <修复>` 单行 的两行结构。axis 取值固定:`规范 / 功能 / 闭环 / 注释 / 废码`。
5. **没有 P0/P1/P2 时**,整段 `Findings` 写一行 `  none` 即可,不要写"无"、"暂无问题"这类废话。
6. **Cleanup 段** 仅列出**可一次性删除**的内容。如无可清理项,整段省略(连标题一起省)。需要迁移、遥测、外部消费者确认或 rollback plan 的删除项不要放 Cleanup,改写成 Finding。
7. **Commit 段** 仅在 Verdict = `✅ READY` 时输出。其他 Verdict 下整段省略 —— 还没到提交时机。
8. Commit message 格式:跟随仓库 `git log --oneline -10` 观察到的风格;仓库无明显风格时退回 conventional commits(`feat|fix|refactor|docs|test|chore|perf|ci|style|build`)。subject 不加句号,祈使语气,≤72 字符。
9. 同一文件多个 finding 按行号升序排列。跨文件按 P0 → P1 → P2 排列,同级别内按文件路径字典序。
10. 报告**全文** ≤ 60 行;超过则压缩 Findings 描述,不要省略 Verdict / Axis / Cleanup 结构。
11. **Refs 自动追溯**(仅 Verdict = `✅ READY` 时):扫 `.claude/artifacts/{designs,plans,fixes}/`,按以下规则在 commit message footer 自动加 `Refs:` 行:
    - 0 个 in-flight artifact → 不加 Refs
    - 1 个 → 自动加(`Refs: <type>/<slug>`,type ∈ {spec, plan, fix})
    - 同 slug 的 spec + plan 都存在 → 两条都加
    - 多个不同 slug → **不擅自选**,在 Commit 段下方加一行 `> 检测到多个 in-flight artifact: [...],请告诉我这次 commit 关联哪个,我会把 Refs 加进去`
    - `.claude/artifacts/` 目录不存在 → 不加(用户没用 dev-skills 流程)

### 极简示例(用户参考用,实际填真实数据)

```
━━━ Dev Code Review ━━━
Verdict   : ⚠ FIX P1
Scope     : 3 files · +84 / −12 · staged
Intent    : 给 prepAll transfer 增加 aspirate 流速参数并透传到底层 SDK
Languages : Dart                    Lint config : analysis_options.yaml

Axis Check
  规范   ✓
  功能   ⚠   新参数未做 null/负值校验
  闭环   ✓
  注释   ⚠   保留了一行 // TODO: refine later 无 owner
  废码   ✓

Findings
  [P1] lib/.../prepAll_transfer_aspirate_setting.dart:88   功能   flowRate 允许传入负值,会让底层抛异常
       → 在 setter 里 clamp 到 [0, maxFlow] 或 throw ArgumentError
  [P2] lib/.../prepAll_transfer_aspirate_setting.dart:14   注释   `// TODO: refine later` 无 owner/ticket
       → 删除该 TODO 或改成 `// TODO(jason, #123): ...`

Cleanup
  - lib/.../prepAll_transfer_aspirate_setting.dart:14  TODO 注释  — 无 owner/ticket,应删除
```

---

## Hard rules

- **不要** mutate working tree(不要 `git add` / `git commit` / `git stash` / 改文件),除非用户在确认报告后明确说"帮我修"。
- **不要** 编造 line number —— 没把握就只引用文件名。
- **不要** 把"代码能跑"等同于"闭环" —— 必须验证调用方存在(或属于豁免清单)。
- **不要** 把架构洁癖当成阻塞问题 —— 只有造成具体功能、安全、可靠性、性能、闭环或维护风险时才报 finding。
- **不要** 输出超长报告。没问题的轴线一句话带过即可,把篇幅留给真问题。
- **不要** 一次性把整个 `references/lang-conventions.md` 读进来,只读本次 diff 涉及的语言小节。
- **不要** 默认加载 `references/risk-checklist.md`;只有命中 Risk checklist loading 条件时才读。
- 用户说"只看 staged" / "只看某路径"时严格遵守,不要扩大范围。
- 评审与实现分开:本 skill 只评审,不写实现代码。如需修复,由用户在下一轮明确指示后进行。

---

## Multi-Agent Profile

Recommended agent_type: worker

Use when:
- A diff is ready for independent review.
- The reviewer did not author the implementation being reviewed.
- The main agent needs a verdict before commit or handoff.

Do:
- Stay read-only.
- Review only the requested scope.
- Prioritize bugs, regressions, missing wiring, missing tests, secrets, and dead code.
- Apply reviewer independence from `../../docs/multi-agent-policy.md`.

Do not:
- Mutate the working tree.
- Re-review implementation choices already outside the requested scope unless they create concrete risk.
- Emit a commit message unless the verdict is READY.

Output:
- Verdict
- Scope
- Findings ordered by severity
- Test gaps
- Commit message only when READY
