---
name: karpathy-guidelines
description: >
  提供一组面向编码行为的轻量约束，帮助代理在动手前暴露假设、优先简单方案、保持改动外科化，并把任务改写成可验证目标。
  当任务容易被误解、过度设计、顺手扩散改动，或需要先锁定成功标准时使用。
---

# Karpathy Guidelines

基于 [`Colin4k1024/andrej-karpathy-skills`](https://github.com/Colin4k1024/andrej-karpathy-skills/tree/main) 的方法论做本地化吸收，用来降低代理在真实代码库里常见的三类失误：替用户做错假设、把实现做重、顺手改到不该碰的地方。

这不是新的编码规范、TDD 或验收框架，而是一层更前置的行为护栏：

- 需要代码风格、命名、通用工程规范时，接 [coding-standards](../coding-standards/SKILL.md)
- 需要测试先行与 RED/GREEN/REFACTOR 时，接 [tdd-workflow](../tdd-workflow/SKILL.md)
- 需要在收尾前给出构建、测试、校验证据时，接 [verification-loop](../verification-loop/SKILL.md)

## 用途

- 把“先理解再动手”变成默认动作，而不是出错后的补救。
- 把“能跑就行”的实现收敛成最小可交付方案，减少过度抽象和未来感设计。
- 把改动边界钉住，避免为了解一个问题顺手重写一片上下文。
- 把含糊任务改写成可验证结果，方便后续接 TDD、验证循环和 handoff。

## 默认做法

1. **Think Before Coding**：先写清当前理解、关键假设、歧义点和更简单备选，不在有歧义时静默选一种解释。
2. **Simplicity First**：只做当前需求闭环所需的最小实现；不要为“以后可能用到”先铺抽象、配置层或扩展点。
3. **Surgical Changes**：只改与当前请求直接相关的文件和代码；如果发现无关坏味道，只记录，不顺手清理。
4. **Goal-Driven Execution**：把“做某件事”改写成“达到什么可验证结果”；优先使用测试、命令输出或明确检查项作为成功标准。

## 触发信号

- 用户目标清楚，但实现解释不止一种，容易靠猜测直接开写。
- 任务范围小，却很容易被做成一层新抽象、框架或配置系统。
- 仓库已有稳定模式，改动只应触及局部逻辑，不应连带整理周边代码。
- 需求里出现“修一下”“加一下”“支持一下”这类宽泛表述，需要先收敛成功条件。
- 开始编码前需要决定：先问清楚、先补测试、还是先做最小实现。

## 配套约束

1. 这是一层前置行为约束，不替代具体实现 skill；进入编码后仍应接对应语言/框架 skill。
2. 一旦决定实现新行为或修复缺陷，继续按 [tdd-workflow](../tdd-workflow/SKILL.md) 走测试先行。
3. 完成实现后，仍需用 [verification-loop](../verification-loop/SKILL.md) 或等价命令给出 fresh evidence。
4. 如果简单方案与用户指定路径冲突，要明确说出 tradeoff，而不是私自改方向。
5. 看到 unrelated dead code、命名问题或旁路重构机会时，默认记录在 handoff / review，不在当前改动里顺手处理。
