# Dev Baseline

本仓库所有 skill 在执行前**必须先加载本文件**。以下四条行为准则在 skill 全程生效。
准则源自 Andrej Karpathy 对 LLM 编码 pitfall 的观察(forrestchang/andrej-karpathy-skills),针对 dev-skills 工具链做了本地化与精炼。

> 本文件是仓库根目录 `/references/dev-baseline.md` 的**编辑源**。同样内容会复制到每个 skill 的 `skills/<skill>/references/dev-baseline.md`,以保证 skill 单独安装时仍自包含。**修改时改根目录版本,然后同步到九处 skill 副本**(skills/dev-auto / dev-spec / dev-plan / dev-tdd / dev-fix / dev-verify / dev-code-review / dev-commit-writer / dev-finish)。

---

## 1. 不假设(Don't Assume)

- **多解必列出** —— 用户的请求若存在 ≥ 2 种合理解读,**列出来等用户选**,不要默默挑一个。
- **不清楚就停** —— 哪里看不懂,**点名说**「我不清楚 X」,不要绕开继续。
- **假设要显式** —— 任何隐含前提(数据形态、调用方、性能要求、错误语义、边界条件)写出来。

**反例(过度自信)**
> 「我已按 RESTful 风格生成了 endpoint。」(默默选了 REST,但邻居模块全是 GraphQL)

**正例(显式分歧)**
> 「endpoint 风格存在两种解读:(a) REST,沿用项目主流;(b) GraphQL,沿用 user 模块。请选 a/b。」

---

## 2. 最小代码(Simplicity First)

- **没要求的不做** —— 不加未被请求的灵活性、可配置性、「未来扩展」。
- **单次使用不抽象** —— 只有一个 caller 的代码不抽工具函数。
- **自检 50 行原则** —— 写完问自己:能压到一半吗?「资深工程师会不会觉得这过度设计了?」

**反例**:为了「以后可能改」加了 strategy pattern + factory + config injection,实际只有一个调用点。
**正例**:直接调用,等真有第二个 caller 再抽。

---

## 3. 外科手术式改动(Surgical Changes)

- **只动必须动的** —— 不顺手「优化」邻近代码、注释、格式、import 排序。
- **不重构没坏的** —— 即使你觉得旧代码丑,本次任务没让你改它就别动。
- **每行变更可追溯** —— diff 里每一行都能直接关联到用户的原始请求。

如果发现邻近代码确实有问题,**单独提一行建议**(例如「建议拆 commit 单独修 X」),但不要在本次改动里夹带。

---

## 4. 可验证的成功标准(Verifiable Success Criteria)

- 任务必须有「怎样算完成」的明确判据,不模糊承诺「我做完了」。
- 把抽象目标转成可验证的具体目标:
  - 「加校验」 → 「为输入 X / Y / Z 写测试,先红后绿」
  - 「提速」 → 「P95 < 200ms,基准 benchmark 给出对比数据」
  - 「修 bug」 → 「定位失败 case,先复现,再让它通过」
- 强 success criteria → agent 可自我循环到达成,不需要用户每步盯着。

---

## 用法

每个 skill 的 SKILL.md 在 `Step 0 — Load baseline` 段引用本文件:

> 执行前先加载 `references/dev-baseline.md`。以下行为准则在本 skill 全程生效:**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准**。

skill 内部的具体规则**不会与 baseline 冲突**;若局部规则更严(例如 dev-code-review 的「严重度 rubric」),以局部为准。
