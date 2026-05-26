# dev-code-review · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实的 before/after,让实际报告对齐这里的笔法。

每个例子结构:**[场景] → [Diff 节选] → [关键检查] → [期望报告]**。

---

## 例 1 — 未闭环(P0 BLOCK)

**场景**:Dart 项目里新增了 `OrderService.placeOrder()`,但没有任何 UI / route / test 调用它。

**Diff 节选**

```dart
// lib/services/order_service.dart  (新文件)
class OrderService {
  Future<Order> placeOrder(Cart cart) async {
    return await _api.post('/orders', cart.toJson());
  }
}
```

**关键检查**

```bash
git grep -n "OrderService" -- ':!lib/services/order_service.dart'
# 0 条匹配
```

`OrderService` 不在框架豁免清单(不是 test、不是 lifecycle override、不是注解 DI),应判 P0 未闭环。

**期望报告**

```
━━━ Dev Code Review ━━━
Verdict   : ❌ BLOCK
Scope     : 1 file · +18 / −0 · staged
Intent    : 新增下单服务
Languages : Dart                    Lint config : analysis_options.yaml

Axis Check
  规范   ✓
  功能   ✓
  闭环   ✗   OrderService 无任何 caller,且不在框架豁免清单
  注释   ✓
  废码   ✓

Findings
  [P0] lib/services/order_service.dart:3   闭环   OrderService 无 caller(grep 0 匹配),非框架豁免
       → 在 checkout 流程接入,或本次 commit 暂不引入该 service
```

---

## 例 2 — Scope creep(P1 FIX)

**场景**:用户说「修复 cart 计算总价 off-by-one」,diff 里却顺手把整个文件的 import 顺序重排了。

**Diff 节选(主改动)**

```dart
// lib/cart/cart.dart  line 84
- total += items.length - 1;
+ total += items.length;
```

**Diff 节选(夹带的改动)**

```dart
// lib/cart/cart.dart  line 1-12
- import 'package:flutter/foundation.dart';
- import '../models/item.dart';
- import 'cart_item.dart';
+ import 'cart_item.dart';
+ import '../models/item.dart';
+ import 'package:flutter/foundation.dart';
```

**关键检查**

应用 baseline「外科手术式改动」原则:import 排序与 off-by-one 修复无因果关系,应拆。

**期望报告**

```
━━━ Dev Code Review ━━━
Verdict   : ⚠ FIX P1
Scope     : 1 file · +14 / −13 · staged
Intent    : 修复 cart 总价 off-by-one
Languages : Dart                    Lint config : analysis_options.yaml

Axis Check
  规范   ⚠   import 重排夹带在 bug fix commit 中,违反 surgical 原则
  功能   ✓
  闭环   ✓
  注释   ✓
  废码   ✓

Findings
  [P1] lib/cart/cart.dart:1-12   规范   import 重排与 off-by-one 修复无关,应拆 commit
       → 本 commit 仅保留 line 84 的修改;import 重排单独成一个 chore commit
```

---

## 例 3 — 意图存疑(显式标出歧义)

**场景**:diff 同时改了 `auth.service.ts` 和 `payment.service.ts`,各自都是大改。仅看代码无法判断本次 commit 的「主轴」是哪一个。

**关键检查**

应用 baseline「不假设」原则:不替用户决定 commit 的主题,在报告里点名歧义。

**期望报告(节选)**

```
━━━ Dev Code Review ━━━
Verdict   : ⚠ FIX P1
Scope     : 2 files · +120 / −34 · both
Intent    : ⚠ 意图不明 —— 同时改了 auth 和 payment,二者无明显耦合
            可能是 (a) 一次性补两块的鉴权链路,或 (b) 应拆成两个 commit
Languages : TypeScript              Lint config : .eslintrc.cjs

Axis Check
  规范   ✓
  功能   ✓
  闭环   ✓
  注释   ✓
  废码   ✓

Findings
  [P1] (跨文件)   规范   两个无耦合模块同 commit,违反 surgical 原则
       → 请确认意图:(a) 同一改动两面 → 给一个统一的 subject;(b) 两件事 → 拆 commit
```

注意 Verdict 在 Intent 不明时**不出 Commit message** —— 等用户在下一轮明确意图。

---

## 例 4 — 调试输出残留(P1 FIX)

**场景**:小改动,只新增了一个 helper。但 helper 里残留了 `console.log` 调试输出。

**Diff 节选**

```ts
// src/utils/format.ts
export function formatCurrency(n: number): string {
  console.log('[formatCurrency]', n);   // ← 残留
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
}
```

**期望报告**

```
━━━ Dev Code Review ━━━
Verdict   : ⚠ FIX P1
Scope     : 1 file · +3 / −0 · staged
Intent    : 新增 formatCurrency 工具函数
Languages : TypeScript              Lint config : .eslintrc.cjs

Axis Check
  规范   ⚠   含 console.log
  功能   ✓
  闭环   ✓
  注释   ✓
  废码   ⚠   见规范

Findings
  [P1] src/utils/format.ts:3   规范   残留 console.log 调试输出
       → 删除该行;若需日志请用项目统一 logger

Cleanup
  - src/utils/format.ts:3  console.log  — 调试输出,提交前删除
```

---

## 例 5 — 全部通过(✅ READY)

**场景**:小修一个 typo + 加一个测试覆盖。所有轴都过。

**期望报告**

```
━━━ Dev Code Review ━━━
Verdict   : ✅ READY
Scope     : 2 files · +14 / −1 · staged
Intent    : 修复 README 拼写,补一条单测
Languages : Markdown, Dart          Lint config : analysis_options.yaml

Axis Check
  规范   ✓
  功能   ✓
  闭环   ✓
  注释   ✓
  废码   ✓

Findings
  none

Commit
  docs: fix typo in README and add coverage for empty cart
```

---

## 反模式备忘(不要这样写报告)

- ❌ 「这是一个不错的改动,建议合并」 —— skill 不输出鼓励语,只输出结构化结论。
- ❌ 「我猜你是想做 X」 —— 当意图不明时**说出歧义并要求确认**,不要替用户猜。
- ❌ 「整个文件需要重构」 —— 超出 diff 范围的建议放 Cleanup 段最多一行,不要展开。
- ❌ 在 Verdict ≠ READY 时输出 Commit message —— 还没到提交时机。
- ❌ 把每个 ✓ 后面都写「无问题」「检查通过」 —— 留空即可。
