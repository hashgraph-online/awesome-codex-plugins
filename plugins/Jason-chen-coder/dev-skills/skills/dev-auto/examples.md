# dev-auto · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实「需求 → 推荐链 → 失败恢复」的样例,让实际输出对齐这里的笔法。

模式覆盖:

- 例 1:**默认模式 + complex feature**(用户 0 起步,需要完整链)
- 例 2:**`--status` + 中途**(用户跑完 spec 来问位置)
- 例 3:**`--next` + 极简**(用户只要下一句命令)
- 例 4:**`--recover` + 失败**(dev-code-review 给 FIX P1,推荐回 dev-tdd / 写代码 step)
- 例 5:**unclear 路径**(列选项让用户选)

---

## 例 1 — 默认模式,complex feature 完整链

**用户**:「用 dev-auto 帮我做用户自助导出功能,GDPR 合规要的。」

**dev-auto 内部**:

- Path 检测:「做」「功能」→ feature
- 复杂度:GDPR / 异步任务 / 邮件 / S3 / PII → **complex**
- Slug 推断:`user-export`
- 扫 `.claude/artifacts/`:designs/ / plans/ / fixes/ 下都没有 `user-export.md` → Phase 0

**期望输出**:

```
━━━ Dev Auto ━━━
路径   : feature
复杂度 : complex(涉及 PII / 异步任务 / 邮件投递 / S3 存储)
Slug   : user-export(自动推断,你可纠正)

完整推荐链
  1. dev-spec --default user-export      把模糊需求拆成结构化 spec(带 AC)
  2. dev-plan --deliberate user-export   complex 需求强制走 deliberate(pre-mortem + expanded test plan)
  3. dev-tdd                              红绿重构写代码
  4. dev-verify                           完成前证据门禁
  5. dev-code-review                      commit 前 5 轴评审
  6. dev-finish                           验证和 review 后的分支收尾

当前位置
  Phase 0:尚未开始
  已完成 artifacts:none

下一步
  $ 用 dev-spec --default user-export
  为什么:dev-spec 多 wave 访谈会把「自助 vs 后台代导」「同步 vs 异步」
         「字段白名单」等歧义拆出。complex 需求不需要 deep,但要 default 走完。
```

注意:
- **不替用户决定 simple 跳过 dev-plan** —— complex 默认推荐走 plan
- **不调起 dev-spec** —— 只输出命令让用户敲

---

## 例 2 — `--status` 中途定位

**场景**:用户跑完 `dev-spec --default user-export`,artifact 已落 `.claude/artifacts/designs/user-export.md`(无论 Status 是 DRAFT / ALIGNED / IMPLEMENTED,dev-auto 都视作 spec 已存在),plan 还没跑。用户来问。

**用户**:「`dev-auto --status user-export`」(显式带 slug,准确)

**dev-auto 内部**:

- $ARGUMENTS 含 slug `user-export`,直接用
- 扫 designs/:看到 `user-export.md`(spec 只看存在性,**不看 lifecycle status**)
- 扫 plans/:无 `user-export.md`
- 扫 fixes/:无
- 推断:Phase 1(spec 已存在,可进 plan / dev-tdd)

**期望输出**:

```
━━━ Status ━━━
Slug:user-export
Phase 1:spec 已存在(.claude/artifacts/designs/user-export.md)
已完成:dev-spec
未完成:plan(可选,complex 推荐) / dev-tdd / dev-verify / dev-code-review / dev-finish
```

**不要**输出「下一步该跑 dev-plan」 —— 那是 `--next` 的事。`--status` 只定位。
**也不要**输出 spec 的 lifecycle status(DRAFT/ALIGNED/IMPLEMENTED)—— 那是用户手动管理的字段,dev-auto 不关心。

---

## 例 3 — `--next` 极简下一步

**用户**:「`dev-auto --next user-export`」(显式带 slug,即使仓库只有这一个 in-flight,也建议显式以防误匹配)

**dev-auto 内部**:同例 2 的状态推断。

**期望输出**:

```
$ dev-plan --deliberate user-export
(complex feature spec 已存在,下一步 plan;deliberate 自带 pre-mortem,user-export 涉及 PII 强烈建议)
```

仅此。两行。

---

## 例 4 — `--recover` 处理 dev-code-review FIX P1

**用户**:「`dev-auto --recover user-export` —— 我跑 dev-code-review 给我 FIX P1,说有个 console.log 残留 + 一处 cart edge case 没处理。怎么办?」(显式 slug 让 recover 输出能精确指出 commit 该关联哪个 spec/plan,有助于修完后重跑 dev-code-review 自动加 Refs)

**dev-auto 内部**:

- 失败 skill:dev-code-review
- 失败信号:Verdict = FIX P1(2 处问题)
- 路径决策:**不该 commit**,但也**不该回 dev-plan**(plan 没问题,代码漏了);回 dev-tdd / 写代码 step

**期望输出**:

```
━━━ Recover ━━━
失败 skill : dev-code-review
失败信号   : Verdict = FIX P1(2 处:console.log 残留 / cart edge case 未处理)

推荐恢复:
  → 回 dev-tdd / 写代码 step
  原因   :P1 是「应修」级别,不阻塞 commit 但建议处理。当前不该硬 commit。
  操作建议:
    1. 删除 console.log(参考 dev-code-review 的 Cleanup 段定位)
    2. 在 cart 边界 case 处理 + 写一个 unit test 覆盖
    3. 改完重跑 dev-code-review,期望 Verdict = ✅ READY

如果上述方式无效:
  - 如果 P1 你认为不该改(误报),在 commit message body 显式覆盖 + 解释,
    并打开 issue 反馈给 calibration session。
```

注意:
- **绝不建议「再跑一次 dev-code-review 看看」** —— 不修代码再跑结果一样
- **明确说「不该硬 commit」** —— 防止用户绕过 review

---

## 例 5 — Unclear 路径,列选项问用户

**用户**:「dev-auto 帮我看看 inventory 这块。」

**dev-auto 内部**:

- Path 检测:「看看 X」语义模糊。可能是 (a) 想加新功能 / (b) 报 bug / (c) 想 review 现有代码
- 不假设,问

**期望输出**:

```
━━━ Dev Auto ━━━
你的需求路径不确定,请选一种:

  (a) 新功能 / 增强 inventory
      → dev-spec(对齐你想加什么)→ dev-tdd → dev-verify → dev-code-review → ...
  (b) 修 inventory 的某个 bug
      → dev-fix(先复现 + regression test + root cause fix)→ dev-verify → dev-code-review → ...
  (c) 现有 inventory 代码我准备改 / 已改完想 review
      → 直接 dev-code-review(改完 commit 前)
  (d) 想了解 inventory 现状(不修改)
      → 这不在 dev-skills scope,自己 grep / 读代码

请选 a/b/c/d 或描述你想做的事。
```

注意:
- 选项 d 是「不在 scope」,直接说,不勉强塞进流程
- 选项 a/b 都给一句**链头**让用户能预览,不只是空选项

---

## 反模式备忘(不要这样跑 dev-auto)

- ❌ **替用户调起其他 skill** —— dev-auto 永远是建议器,违反就成了 orchestrator,破坏松耦合原则
- ❌ **深读 artifact 内容做精细推断** —— 例如读 spec 的 AC 表来判断「应不应该升 plan」。**只读存在性 + frontmatter status**,深推断让用户做
- ❌ **维护跨调用的 state file** —— 没有 `.claude/artifacts/workflows/` 这种东西。每次调用从仓库现状重扫
- ❌ **在 `--next` / `--status` 模式里输出 50 行说明** —— 这两个模式追求极简,3-5 行就够
- ❌ **在 `--recover` 推荐「再试一次」** —— 失败有因,必须修复或换路径
- ❌ **把 hotfix 推荐给 complex 改动** —— 例如用户说「线上紧急,加个跨多服务的鉴权」,这不是 hotfix,警告并建议升 complex feature
- ❌ **假装看到代码改动** —— dev-auto 不读源码。「代码状态」靠 artifacts(spec/plan/fix 文件)+ 用户告知
- ❌ **路径 unclear 时硬猜** —— 模糊就列选项问,这是 baseline「不假设」的最低落地
