# Fixture 02 — 意図は理解した上でなお問題が残る（Downgrade + 反証）

指摘行の近傍に設計意図が書かれているが、その意図を満たしたままでも解消できる
別の問題が残っているケース。finding を取り下げるのではなく、severity を下げ、
**コメントに記載の意図**と**それでもなお問題と考える理由**を本文に書く。

## Description

コメントは「アナリティクスの失敗でリクエストパスを壊さない」という意図を明記して
おり、`await` しないこと自体は設計どおり。ただし catch が完全な無音であるため、
アナリティクス送信が恒常的に壊れても誰も気づけない。意図（リクエストパスを
壊さない）を保ったまま `logger.warn` を足せば解消できるので、意図と両立する。

## Input Diff

```diff
diff --git a/src/api/checkout.ts b/src/api/checkout.ts
index 3333333..4444444 100644
--- a/src/api/checkout.ts
+++ b/src/api/checkout.ts
@@ -22,6 +22,12 @@ export async function checkout(cart: Cart): Promise<Receipt> {
   const receipt = await submitOrder(cart);
+
+  // Analytics must never break the request path, so failures are swallowed here.
+  try {
+    await track('checkout_completed', { total: receipt.total });
+  } catch {
+    // ignored
+  }
+
   return receipt;
 }
```

## Expected Behavior

The reviewer should downgrade rather than drop or escalate:

1. Severity は `major` ではなく `minor` 以下。コメントが明記する意図（リクエスト
   パスを壊さない）に反する指摘は成立しないため。
2. finding 本文に「コメントの意図（アナリティクス失敗でリクエストを壊さない）は
   理解した上で」という要約と、「無音の catch では送信の恒常故障を検知できない」
   という反証を含める。
3. Fix は意図と両立する最小一手（`catch (err) { logger.warn(...) }`）。
   `await` を外す・throw する等、コメントの意図を覆す提案はしない。

<!-- expected:
findings:
  - severity: minor
    must_mention: [コメントに記載の意図, 無音の catch で恒常故障を検知できない]
reason: 意図（リクエストパスを壊さない）はコメントで明記済みだが、可観測性ゼロの問題は意図と両立したまま残る。取り下げず severity を下げ、意図への言及と反証を必須とする（#1685）
-->
