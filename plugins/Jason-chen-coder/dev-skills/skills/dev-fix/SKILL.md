---
name: dev-fix
description: 'Use when the user reports a bug, broken behavior, regression, failing test, or asks to investigate/root-cause/debug. Trigger on: 修个 bug, 这个 bug, 排查一下, 复现, 这个错怎么回事, 为什么 X 不工作, debug, RCA, fix this bug, investigate, reproduce. Guides root-cause debugging: reproduce with a failing test, list hypotheses, trace backward, fix only the confirmed cause, verify red-green-red, and leave a regression test. Does not symptom-patch or write commit messages.'
---

# Dev Fix

Hypothesis-driven debugging & fix workflow with **No fix without root cause**. Replaces guess-and-patch with: reproduce → hypothesize → diagnose (backward trace) → fix → defense-in-depth → verify → regress.

This skill **only debugs and fixes**. It does not gather requirements (that's `dev-spec`), does not plan large refactors (that's `dev-plan`), and does not write commit messages on its own (that's `dev-code-review` / `dev-commit-writer` after the fix is in).

---

## Trigger routing

Use this skill when the user reports a bug, asks why something is broken, or wants a structured root-cause-driven fix.

Trigger phrases include:

- `修个 bug`
- `这个 bug`
- `排查一下`
- `复现`
- `这个错怎么回事`
- `为什么 X 不工作`
- `debug`
- `RCA`
- `fix this bug`
- `investigate`
- `reproduce`

Output goes to `.claude/artifacts/fixes/<bug-slug>.md`.

Optional arguments:

- `--quick`: small bugs such as typo, off-by-one, or single-function fixes
- `--deep`: hairy bugs such as heisenbugs, race conditions, cross-system bugs, or production incidents; forces 3-5 hypotheses, tagged instrumentation, defense-in-depth, and pattern analysis
- default: mid-depth investigation

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联点(本 skill 的核心):

- **不假设** —— Hypothesis 阶段强制列出多个假设并显式排除,不许直接「我觉得是 X」就动手。
- **外科手术式** —— Fix 阶段只改 root cause 路径,不许夹带「顺手优化」邻近代码。如果发现需要重构,**单独提建议**让用户决定。
- **可验证成功标准** —— Verify 阶段强制 red → green → red 三步循环。test 不能验证 bug 真被抓到 = 没修完。

---

## Step 1 — Triage(选模式 + capture 上下文)

按 `$ARGUMENTS` 或自动判断。下表是**所有 phase 在三档模式下的差异**:

| 模式 | 触发场景 | Hypothesis(Step 3) | Instrument(Step 4) | Defense-in-depth(Step 6b) | RCA(Step 8) |
|---|---|---|---|---|---|
| `--quick` | typo / off-by-one / 单文件单函数 / 用户已点出疑似行 | 跳过形式化(写一句怀疑即可) | 不做 | 跳过 | 简短摘要 |
| 默认 | 多文件 / 中等复杂度 / 用户描述含糊 | 1-2 条(置信度 H/M/L) | 可选(IDE breakpoint 或现有 logger) | 跳过 | 标准 artifact |
| `--deep` | heisenbug / race / 跨系统 / 生产事故 / 间歇性失败 | **强制 3-5 条跨多维**(代码逻辑 / 数据 / 并发 / 环境 / 误解需求) | **必做** + tagged log | **可选**(blocker 强烈建议) | 完整 RCA + 预防措施 |

**Verify 三步循环(red→green→red)和 failing test 入仓** 是任何模式都不能跳的硬门槛。

### 模式自动升级建议

如果用户输入 `--quick` 但 Capture 阶段出现以下任一信号,**主动建议升级到 `--deep`**(让用户确认):

- Severity 是 blocker / 财务影响 / 数据破坏
- 「First seen」描述含「**间歇性 / 偶发 / ~N% 概率 / heisenbug**」
- Symptom 涉及多服务 / 跨进程 / 跨线程 / 跨 host
- Repro 在 Step 2c 显示 flaky(< 3/3 失败)

输出形式:「检测到 race / blocker / 跨系统 信号,建议升 `--deep` 走完整 hypothesis + instrument + RCA。继续 quick / 升级 deep / 你的版本?」

**Capture(任何模式都要做)**:

```
## Triage

- **Symptom**:用户描述的现象,一句话
- **Expected**:正常应该怎样
- **Repro 起点**:用户给的命令 / 输入 / URL / 触发动作
- **Environment**:OS / runtime version / 相关 service 版本(只列与 bug 可能相关的)
- **First seen**:何时开始出现 / 关联近期改动
- **Severity**:阻塞 / 影响功能 / 视觉小瑕疵
```

如果以上信息缺关键项(尤其 Repro 起点 / Symptom),**直接向用户追问补全**,不要自己猜。补全前不进 Step 2。

### Clean-tree worktree checkpoint(进入任何文件写入前)

dev-fix 通常会在 Step 2b 写 failing test,之后在 Step 6 写修复。**第一次写文件前**必须检查:

```bash
git status --short
git branch --show-current
```

判定:

- 如果 `git status --short` 为空,且本次 bug fix 会写测试 / 代码 / 配置,先询问用户是否创建独立 worktree。
- 当前分支是 `main` / `master` / `release/*` 时,默认推荐 worktree。
- 可跳过询问的场景:用户已明确说当前目录改 / 当前已经在专用 worktree 或任务分支 / 纯单文件 typo。
- 当前 working tree 已经 dirty 时,不要把本次 fix 混进已有改动;先说明已有改动,由用户决定继续当前目录 / 清理 / 另建基于 HEAD 的 worktree。

推荐命令:

```bash
git worktree add -b codex/<bug-slug> ../<repo>-<bug-slug>
```

创建后在新 worktree 内确认 `git status --short` 为空,再写 failing test。

---

## Step 2 — Reproduce(失败测试入仓的硬门槛)

**目标**:把 bug 编码成一个**自动测试**,跑会失败。

### Step 2a — 最小复现

剥离无关因素,留下**触发 bug 的最小输入 + 最小代码路径**。能用单测就别开浏览器,能用 unit test 就别开 e2e。

### Step 2b — 写 failing test

在仓库适当位置(同模块的 test 文件 / 新建 `<module>.bug.test.<ext>`)写一个测试,**断言期望行为**。

```bash
# 跑测试
<run test cmd>

# 必须 FAIL ❌
# 如果 PASS,说明你没真复现 bug,或测试断言写错了 → 回 Step 2a
```

### Step 2c — 防 flaky

跑 test 至少 **3 次连续都失败**,才算 reliably reproduces。如果偶尔通过偶尔失败,这是 race / timing 问题,**升级到 `--deep` 模式**。

**涉及时序 / race 的 repro,用 condition-based-waiting 替代固定 sleep**(借鉴自 obra/superpowers `condition-based-waiting`):

```ts
// ❌ 反例:固定 sleep,会 flaky
await sleep(500);
expect(await getOrderStatus(id)).toBe('confirmed');

// ✅ 正例:condition polling,等条件成立而非等时间
await waitFor(() => getOrderStatus(id).then(s => s === 'confirmed'), { timeout: 5000 });
```

固定 sleep 要么产生假阴性,要么拖慢测试,且真正的 race 永远抓不稳。condition polling 让 test 等**真实状态**,不是凭运气等够时间。

> **Hard rule**:Step 2 不通过(无 reliably failing test)**禁止进 Step 3**。这条是 baseline「可验证成功标准」的最强落地。

---

## Step 3 — Hypothesize(列假设,先别动手)

每个 hypothesis 必须能**解释 Step 2 的 failing test** —— 即「如果 H 成立,test 应当呈现什么观察」。这是「可证伪」的根 —— 没法预测观察的假设跟「我感觉是 X」没区别。

### Hypothesis 格式(所有模式统一)

```
H<n>: <一句话 root cause 假设>
   预测观察:<如果 H<n> 成立,test / log / behavior 应当呈现什么>
   证据收集方式:<怎么验证 — log / breakpoint / git bisect / 阅读 X 函数>
   置信度(confidence):H / M / L  ← 你看到 evidence 后,觉得这条多大可能是真
   prior probability:<在看到任何 evidence 之前,这条假设有多大可能成立> ←0-100% 估值
   优先级:1, 2, 3...(本轮 diagnose 顺序,从 H 优先)
```

**confidence vs prior 区分**:
- `confidence` 是「**已经看了一些 evidence 之后**的判断」—— 通常 H1 confidence 较高,因为是你最直觉的假设
- `prior` 是「**完全没看 evidence 时**这条假设的客观可能性」—— 反映场景多样性
- 区分两者可以**揭穿凑数 hypothesis**:列了 H4「环境差异」prior < 10%(因为代码是同环境跑的)只是为了凑「跨多维度」 → 这种就是凑数

### Hypothesis 质量门(`--deep` 必查)

`--deep` 列了 3-5 个 hypothesis 后,自检 prior probability 分布:

- 如果 ≥ 3 个 hypothesis 的 prior < 20% → **假设池质量不够**,回 Step 3 重列
- contrarian 视角不能放 prior < 10% 的「凑数项」 —— 必须是真有可能,只是不是第一直觉

### `--quick` 模式

不强制完整模板,但在 artifact 里至少写一句「怀疑 root cause: <一句话> + 一句预测观察」。

### 默认模式

列 **1-2 个**,按格式填全 4 个字段。

### `--deep` 模式

**强制列 3-5 个**,跨**不同维度**(避免单一思路盲点):

- 代码逻辑 bug(条件 / off-by-one / 类型错误)
- 数据问题(异常输入 / 缺失字段 / 编码)
- 并发 / 时序(race / 锁 / 重入)
- 环境差异(版本 / 配置 / 依赖)
- 误解需求(代码按规范跑,但规范本身错)

≥ 3 个差异化方向。**绝不省略 contrarian 视角**(devil's advocate:「会不会根本不是这块的问题?」)。
---

## Step 4 — Instrument(`--deep` only,默认可选)

目的:为 Step 5 Diagnose 收集 evidence。加 **tagged debug log** 到代码,**用唯一字符串 `bug-<slug>` 作为 grep 锚点**,事后一键移除:

```python
# bug-<slug> DEBUG START
print(f"[bug-<slug>] relevant_state at line 42: {state}")
# bug-<slug> DEBUG END
```

约束:
- **唯一锚点 `bug-<slug>`** 必须出现在每条 log + 每个 START/END 注释里(便于 Step 7d `grep -rn "bug-<slug>" .` 一发命中,**不依赖空格数 / region 关键字 / 注释风格**)
- 不许 `console.log` / `print` 没锚点 —— 那种是「污染」,Step 7d grep 抓不到
- 不在 hot path 里加无 throttle 的 log
- 模式差异:`--deep` 必做(通常需要事后回看完整日志);默认 / quick 可选(用 IDE breakpoint 或现有 logger 也行)。

---

## Step 5 — Diagnose(逐个排除假设,直到锁定)

按 hypothesis 排好的概率从高到低:

1. 跑 instrumented 代码或调试器,**收集证据**
2. 对每个 hypothesis 标记 `confirmed` / `eliminated` / `inconclusive`
3. **eliminated 的要附一行证据**(不是「直觉觉得不是」)
4. confirmed 即停 —— 不要继续「确认」其他假设

### 反向 call-stack 追溯(借鉴自 obra/superpowers `root-cause-tracing`)

**当 hypothesis 看起来 confirmed 时,不要在第一个可疑帧就修**。从观察到的失败点,沿调用栈**反向追溯**,问每一帧:

- 这个 bad value / bad state 是在**这一层**第一次出现的吗?
- 还是从**上一层**传进来的?

一直追到 bad value / bad state **被首次引入**的那一帧,**在那里修**。

**为什么重要** —— 在中间帧打补丁(把异常 swallow 掉、把 NaN 兜底成 0、把 null 当空数组)只是把 bug 推回上游,**根因仍在,下次会从另一条路径再爆**。`defense-in-depth`(见 Step 6b)是**在 root cause 修完后**额外加多层兜底,不是替代 root cause 修复。

**反例**:
```ts
// 报错点:line 88,user.email is undefined
// ❌ 在 line 88 加 if 守卫(把症状包起来)
if (!user?.email) return;

// ✅ 反向追溯:user 从哪来?→ getUserById() → DB query 漏字段
//    在 getUserById 修 select 语句,补 email 列。
```

### Escalation 阶梯(累计跨模式跨轮)

跨整个 dev-fix 调用周期,维护两个累计计数器:

- **`hypothesis_busted_count`**:**高置信(H)**hypothesis 被 evidence 证伪的次数(L/M 不计)
- **`fix_attempt_failed_count`**:Step 6 + Step 7 完整跑过 + Step 7a 仍 RED 或 Step 7b stash 后 GREEN(test 没真抓 bug)的次数

**两个计数都跨模式累计** —— 默认模式列 2 个 H 假设全 fail,升 deep 再列 1 个 H 假设 fail,累计就到 3,触发升级,而非每次升模式重新计 0。

**触发动作**:

| 状态 | 建议 |
|---|---|
| `hypothesis_busted_count == 默认模式上限(2)` 且仍未 confirm | 提示用户**升 `--deep`** 多列假设、做 instrument、反向追溯。**95% 的「找不到 root cause」其实是 investigation 不完整**(借鉴 superpowers)—— 不放弃,先升级 |
| `hypothesis_busted_count >= 3`(deep 模式列了 3 个 H 假设全 fail) | 这通常**不是 implementation bug,是架构 / 设计问题**。**STOP 假设循环**,升级 `dev-plan --deliberate` |
| `fix_attempt_failed_count >= 3` | 同上,但更确定 —— 每次都 confirm 假设了仍修不对,期望的不变量在当前架构里站不住。**STOP fix 尝试**,升级 `dev-plan --deliberate` |

升级时:

- artifact 标 `Status: BELOW_CONFIDENCE_THRESHOLD`(假设全 fail)或 `NEEDS_DESIGN_CHANGE`(fix 多次 fail)
- 把当前发现(symptom + 已 eliminated 的 hypothesis + evidence + 失败的 fix 尝试摘要)整理完整
- **不要硬猜下一个假设或下一次 fix** —— 把决策权交回用户

> 「找不到 root cause」≠ 没有 root cause。但「3 次高置信 fail / 3 次 fix attempt fail」是不同性质的卡点 —— 这时放下 keyboard 找架构问题,比再列第 4 个假设更可能解决。

---

## Step 6 — Fix(只动 root cause 路径)

应用 baseline「外科手术式改动」:

- **只改与 confirmed root cause 直接相关的行**
- 发现邻近代码也有问题?**单独列出建议拆 commit**,不在本次 fix 里夹带
- 改动尽量小,能改 1 行别改 5 行

### Stop & handoff to dev-plan(fix 涉及结构性改动)

如果根因分析显示 fix **必须**改架构 / 类设计 / 模块边界 / 跨服务契约,**立刻 STOP dev-fix,不要勉强写小补丁**:

1. artifact 标 `Status: NEEDS_DESIGN_CHANGE`
2. 把 root cause 分析整理完整(Symptom / Reproduction / Hypotheses / Root cause / 已尝试的 fix 思路)
3. **明确告知用户**:

   > 「Root cause 已锁定为 X,但 fix 需要改 Y 模块设计。建议跑 `dev-plan` 评估改动方案,plan 通过后再回 dev-fix Step 6 做实施。当前 dev-fix 暂停,artifact 已落 `.claude/artifacts/fixes/<slug>.md`(Status: NEEDS_DESIGN_CHANGE)。」

4. **不要继续往下走 Step 6b / 7 / 8 末尾的 RCA**(没修完 RCA 段填不完整)
5. dev-fix 进入挂起状态,等用户回来恢复

判断标准:**改动会动到** ≥ 2 个文件的公共接口 / DB schema / 跨服务消息格式 / 类继承层级 / 主要数据流向 —— 任一就是结构性。如果只是同一函数内换实现 / 同一类内补字段 / 单文件加守卫,不算结构性,继续 Step 6。

---

## Step 6b — Defense-in-depth(`--deep` 可选,默认 / quick 跳过)

借鉴自 obra/superpowers `defense-in-depth`。Root cause 已修完后,**有针对性地**在多层边界加 validation,防止同类问题在其他入口或未来 regression 再现。

### 这一步与 baseline「外科手术式」的边界

**Defense-in-depth ≠ 顺手 refactor**。两者必须严格区分:

| Defense-in-depth(允许加) | 顺手 refactor(禁止加) |
|---|---|
| 在调用 root cause 函数的 boundary 加 input validation | 把 root cause 函数本身重写 |
| 在 DB 层加 NOT NULL constraint(本次 root cause 是 NULL 误处理) | 把整张表 schema 重设计 |
| 在 API 入口加 schema 校验(本次 root cause 是异常输入) | 把整套 validation 框架替换 |
| 加一条 unit test 覆盖刚 fix 的 case 的相邻 case | 把整个 test 套件从 jest 迁到 vitest |

**判定标准**:加的每一行都能直接关联到「**防止本次 root cause 类型问题再现**」。否则就是 refactor,不许加。

**行数硬上限(防 LLM 把 refactor 包装成 defense)**:

- Defense-in-depth 加的代码行数 ≤ **root cause fix 代码行数 × 2**
- 例:fix 改了 8 行,defense 最多加 16 行
- 超过这个比例,**强制拒绝**,把多余的丢进 Follow-up(`dev-plan` 评估架构)

理由:LLM 在「想让代码更好」的状态下容易把整个调用链加 schema 校验、把整个相关函数加 logging 等说成 defense。**用客观行数门把判断转成可量化阈值**,断绝主观开脱空间。

> 例外:仅 **DB constraint / type schema** 这类「单条声明性配置」(例如 `ALTER TABLE ... ADD CONSTRAINT`)即使逻辑上重要也只算 1 行 effective。不要为了卡上限砍掉真正必要的 constraint。

### 典型 defense layers(选 1–3 层加,不要全加)

- **Input boundary**:对外 API / CLI / queue 消费的入口加输入校验
- **Type / Schema**:DB constraint / TypeScript strict / Pydantic / runtime schema
- **Assertion**:在关键函数入口 / 出口加 assert(state invariants)
- **Monitoring**:加 metric / alert,让下次出问题更快发现

### 跳过 Step 6b 的判断

- `--quick` / 默认模式 **默认跳过**,只修 root cause
- `--deep` 模式 **可选**,根据 bug 严重度决定:
  - blocker / 财务影响 / 数据破坏 → 强烈建议加
  - functional / minor → 修 root cause 即够,Defense 进 Follow-up

加完 Step 6b 后,**所有新加的 validation / assertion 也要被 test 覆盖**(否则就是没真正生效的兜底)。

---

## Step 7 — Verify(red → green → red 三步循环)

**任何模式都不能跳过这步**。这是 dev-fix 与「随手 fix」的根本区别。

### Step 7a

```bash
<run failing test>
# 期望:GREEN ✓ (fix 生效)
```

### Step 7b — 反向证明 test 真的能抓 bug

```bash
git stash               # 临时移除 fix
<run failing test>
# 期望:RED ✗ (test 仍能捕获 bug,没误绿)
git stash pop           # 恢复 fix
<run failing test>
# 期望:GREEN ✓
```

> **如果 7b 第一步是 GREEN**(stash 后 test 还能过)—— 说明 test 没真测到 bug,**回 Step 2 重写 test**。这是常见陷阱(test 写得太宽松)。

### Step 7c — 跑 wider suite 防回归

最低范围:**修改文件所在 package / 模块的全部 test**(不只跑你刚加的 regression test)。具体识别方式按语言:

```bash
# Python
pytest <module-dir>/                 # e.g. pytest src/orders/
# TypeScript / Node
pnpm test <pkg>                      # 或 jest <module-pattern>
# Go
go test ./<pkg>/...                  # e.g. go test ./internal/cart/...
# Rust
cargo test --package <pkg>
# Java / Kotlin
gradle :<module>:test
```

整库 test 慢则**至少跑修改文件所在 package**。期望:全 GREEN ✓。

### Step 7d — 移除 instrumentation(`--deep` 必做)

用 Step 4 加的唯一锚点 `bug-<slug>` 一发命中所有 instrumentation:

```bash
grep -rn "bug-<slug>" .             # 找出所有需要删除的行
# 删除每条命中(START / END 注释 + 中间的 log 调用一起)
grep -rn "bug-<slug>" .             # 期望:0 条匹配
```

**重要**:必须 **0 匹配** 才算 instrumentation 干净。任何残留(包括 START/END 注释)都属污染。

---

## Step 8 — Write artifact

落到 `.claude/artifacts/fixes/<bug-slug>.md`(目录不存在则创建)。

模板:

```markdown
# Bug: <一句话标题>

> Status: FIXED | BELOW_CONFIDENCE_THRESHOLD | NEEDS_DESIGN_CHANGE
> Mode: --quick | (default) | --deep
> Severity: blocker | functional | minor
> Author: <user>
> Last updated: <YYYY-MM-DD>

## Symptom
<用户报的现象>

## Expected
<应该怎样>

## Reproduction
- 命令 / 步骤:...
- 测试位置:`tests/<file>.test.ts:42`
- 复现稳定性:3/3 reliably fails(stash fix 后)

## Hypotheses & diagnosis
| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| H1 | ... | confirmed (root cause) | log 显示 X / git bisect 指向 commit Y |
| H2 | ... | eliminated | 反向测试,X 状态正常 |
| H3 | ... | eliminated | 代码路径根本没走 |

## Root cause
<2–3 句:为什么会发生,因果链是什么>

## Fix
- 改动文件:`path/to/x.ts:88-92`
- 一句话改了什么:...
- 代码 diff 摘要(关键行,不要贴整个 diff)

## Verification
> 用 V- 前缀(verification log)而非 AC-,避免与 dev-spec 的 acceptance criteria 混淆。

- V-1: failing test → GREEN ✓
- V-2: stash fix → test 重新 RED ✓(证明 test 真捕获 bug)
- V-3: 修改文件所在 package 全部 test → all GREEN ✓
- (deep) V-4: instrument 已全部移除(`grep -rn "bug-<slug>" .` → 0 匹配)

## Regression test
- 路径:`tests/<file>.test.ts:42`
- 名称:`should not <bug 描述> when <trigger condition>`

## Defense-in-depth(deep 模式且加了兜底时填)
- 加在哪几层:input boundary / DB constraint / assertion / monitoring(选 1–3 项)
- 每条对应的「防止 root cause 类型问题再现」的因果说明
- 兜底是否被 test 覆盖

## Pattern analysis(必填,借鉴 obra/superpowers)
本次 root cause 的**模式形状**(例:错误吞没 / null 路径未守 / 数据竞争 / 边界假设错 / 异常输入未校验)是否在仓库其他位置也存在?

| 搜索方式 | 命中数 | 是否本次同类隐患 |
|---|---|---|
| `git grep -n "<关键 pattern>"` | N | 是 / 否,各 M 处 |

**如有同类**,在下方 Follow-ups 列出每处的 file:line + 一句话描述。本次**不修**(违反 surgical),作为单独 issue / 后续 commit 处理。

## Open questions / Follow-ups
<本次没修但发现的相关问题,例如「同一函数另一分支也有类似风险」「需要追溯何时引入(git bisect)」;Pattern analysis 命中的同类隐患也列在这里;无则省略>

## RCA(deep 模式必填)
- **何时引入**:commit hash + 日期(git bisect 结果)
- **为什么没被发现**:测试覆盖盲区 / staging 与 prod 差异 / etc
- **预防措施**:加什么 test / 加什么 lint / 改什么流程
```

---

## Hard rules

- **不要** 没 reliably failing test 就进 Step 3 —— Step 2 是入门门槛。
- **不要** symptom-patch —— 必须有 confirmed root cause 才能进 Step 6。confirm 不了就标 `BELOW_CONFIDENCE_THRESHOLD` 让用户决策,不要硬猜。
- **不要** 在 Diagnose 阶段于「第一个可疑帧」就修 —— 反向追溯到 bad value 被首次引入的那一帧再修(参见 Step 5 反向追溯段)。
- **不要** 跳过 Step 7b(stash → red 反向证明)—— test 写不严就是没修完。
- **不要** 在 fix 里夹带 refactor / 邻近优化 —— 违反 baseline,直接拒。**Defense-in-depth(Step 6b)是例外**,但加的每一行都必须能直接关联到「防止本次 root cause 类型问题再现」,否则就是 refactor。
- **不要** 在 `--deep` 模式 hypothesis 少于 3 个 —— 单一思路有视野盲点。
- **不要** 在 `--deep` 模式漏 instrumentation 移除步骤 —— 留下 tagged log = 污染代码。
- **不要** 在累计 3 个高置信 hypothesis 都被证伪 / 3 次 fix attempt 都失败时硬撑 —— 这是架构问题信号,STOP 升 `dev-plan`,artifact 标 `Status: NEEDS_DESIGN_CHANGE`。计数跨模式累计,见 Step 5 Escalation。
- **不要** 用固定 sleep 防 flaky —— 时序敏感的 repro 必须用 condition-based-waiting(Step 2c)。
- **Evidence before claims**:在 artifact 任何「passed / fixed / verified」声明,必须**在本轮真实跑过对应命令**并读过 output。没跑就别声称 —— 没有「应该过」,只有「跑了 + 看了 output + 真过」。
- **「找不到 root cause」≠ 没有 root cause**(借鉴 obra/superpowers):95% 是 investigation 不完整 —— 升 `--deep` 多列假设、加 instrument、反向追溯,**比放弃更可能找到**。真正放下的标准是 Step 5 escalation 三次失败,不是「我看了一会觉得没有」。
- **不要** 把 dev-fix artifact 写得像「日志流水账」—— 模板里每段必填,Hypothesis 表必有 verdict + evidence,Pattern analysis 段必须实际 grep 过仓库。
- **不要** 主动调起其他 skill —— dev-skills 间松耦合,修完用户自己决定下一步(走 dev-code-review / 直接 commit / 是否需要 dev-plan)。

---

## Multi-Agent Profile

Recommended agent_type: worker

Use when:
- The bug report or failing test is bounded.
- The sub-agent owns a clear failure path, module, or reproduction target.
- The main agent can integrate the resulting fix and evidence.

Do:
- Reproduce first and keep the failing test meaningful.
- Trace backward to the confirmed root cause before changing code.
- Keep the fix surgical and inside the assigned ownership.
- Follow `../../docs/multi-agent-policy.md` for concurrent-work boundaries.

Do not:
- Patch symptoms without a confirmed root cause.
- Mix broad refactors into the bug fix.
- Edit outside the assigned failure path.
- Skip regression-test evidence.

Output:
- Reproduction
- Confirmed root cause
- Changed files
- Regression test and verification commands
- Pattern-analysis follow-ups
