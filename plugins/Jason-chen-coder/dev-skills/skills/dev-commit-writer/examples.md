# dev-commit-writer · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实 diff → message 的样例,让实际输出对齐这里的笔法。

---

## 例 1 — 单一意图,清晰 message

**Diff(节选)**

```diff
--- a/src/utils/format.ts
+++ b/src/utils/format.ts
+ export function formatCurrency(n: number): string {
+   return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
+ }
```

**`git log --oneline -10` 采样**

```
3a8b2c1 feat: add cart total breakdown component
b4c9d3e fix: handle empty product list in carousel
f5e6a8b chore: bump react-intl to 6.5
1d2c4ef refactor: extract pricing logic from Cart.tsx
...
```

**采样结论**:仓库用 conventional commits(`feat:` / `fix:` / `chore:` / `refactor:`),英文,祈使,subject < 60 字符。

**期望输出**

```
feat: add formatCurrency utility for USD amounts
```

不加 body —— 改动只有一个公共函数,没什么 *why* 要解释。

---

## 例 2 — 意图歧义,输出多候选(不默默选)

**Diff(节选)**

```diff
--- a/src/auth/jwt.ts            (大改 +50 / -20)
+++ b/src/auth/jwt.ts
- ... [refresh token 逻辑重写]

--- a/src/payment/stripe.ts      (大改 +35 / -15)
+++ b/src/payment/stripe.ts
- ... [webhook 验签逻辑加固]
```

两个无耦合模块同时大改,意图不明显。

**期望输出(不直接给 message)**

```
意图判断存在歧义,本次改动可以理解为:

(a) 一次性补两块的安全加固:
    chore(security): harden auth refresh and stripe webhook verification

(b) 应拆成两个 commit:
    auth.ts:    fix(auth): rebuild refresh token rotation
    stripe.ts:  fix(payment): verify stripe webhook signature

(c) 你的版本

请选 a/b/c。
```

不要替用户决定主轴。这是 baseline「不假设」的最强落地。

---

## 例 3 — Scope creep 检测,body 用 `Incidental:` 显式列

**用户原意**:修一个 cart 总价 off-by-one。

**Diff(节选)**

```diff
--- a/lib/cart/cart.dart
+++ b/lib/cart/cart.dart

@@ -1,12 +1,12 @@
- import 'package:flutter/foundation.dart';
- import '../models/item.dart';
- import 'cart_item.dart';
+ import 'cart_item.dart';
+ import '../models/item.dart';
+ import 'package:flutter/foundation.dart';

@@ -84 +84 @@
- total += items.length - 1;
+ total += items.length;
```

**期望输出**(用户坚持合并不拆 commit 时):

```
fix(cart): correct off-by-one in total calculation

Incidental:
- Reorder imports in cart.dart (alphabetic)

Note: incidental changes are unrelated to the bug fix; consider splitting
to a chore commit if reviewer prefers.
```

**首选方案应该是建议拆 commit**:

```
检测到 1 处与主意图无关的改动(import 重排)。建议拆:

Commit A — bug fix(本次主意图)
  fix(cart): correct off-by-one in total calculation

Commit B — chore(顺手改的)
  chore(cart): reorder imports alphabetically

要拆 / 要合(我用 Incidental 段标出)/ 你的版本?
```

---

## 例 4 — 仓库风格采样不足,退回 conventional commits

**`git log --oneline -10` 输出**

```
init.
add code.
asdf
更新.
```

**采样结论**:< 3 条有意义 message,风格混乱。**显式说明**采样不足,退回 conventional commits。

**期望输出**

```
仓库 git log 采样不足(< 3 条规整 message),按 conventional commits 默认输出:

feat: add user profile edit form
```

不要假装识别出仓库风格。

---

## 例 5 — 中文项目跟随仓库语言

**`git log --oneline -10` 采样**

```
e3a8b2c 添加购物车空状态展示
b4c9d3e 修复优惠券计算精度问题
f5e6a8b 文档:补充 README 部署说明
1d2c4ef 重构:把 cart 业务逻辑抽到 service 层
```

**采样结论**:中文 + 类 conventional 前缀(添加 / 修复 / 文档 / 重构),无 scope。

**期望输出**(diff 是「为下单流程加超时重试」)

```
添加下单接口超时重试,最多重试 3 次

主流程超时(默认 10s)后自动重试,使用指数退避(1s/2s/4s)。
连续 3 次失败返回原始错误,用户侧 UI 维持现状。
```

跟随中文,subject + body,贴合采样到的「动词开头 + 描述」风格。

---

## 反模式备忘(不要这样写 message)

- ❌ **AI 套话** —— 「This commit refactors the cart module to improve performance and maintainability」。看到 "This commit" / "We will now" / "Comprehensive improvements" 就是没采样仓库风格。
- ❌ **subject 塞两件事** —— `fix typo and add tests`。两件事就是两个 commit,要么拆要么 body 用 Incidental。
- ❌ **意图不明时硬给 message** —— 多模块大改不问就写,违反 baseline「不假设」。必须输出多候选。
- ❌ **body 复述 subject** —— body 只解释 *why*,不复读 *what*。
- ❌ **subject > 72 字符** —— GitHub UI 会截断。jamais。
- ❌ **subject 加句号** —— 祈使语气不带句号。
- ❌ **加 emoji 除非仓库就这风格** —— 不要单方面引入 commit emoji 风(`✨ feat: ...`)。
- ❌ **声称仓库风格但其实没采样** —— git log < 3 条规整 message 时必须显式说明退回默认。
- ❌ **替用户评审代码** —— 这是 dev-code-review 的事,本 skill 只写 message。
