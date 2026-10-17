# Fixture 05 — テスト検出力だけの指摘は minor（Downgrade）

self-check 8 の canary。実装のガードは効いていて、テストがそのガードを外しても通る
ことだけを示す finding は、`major` ではなく `minor` にします。降格の判定は、欠けている
テスト入力を実装に与えて確かめます。

## Description

`isSafeReturnUrl` は WHATWG URL で解決したうえで、スキーム判定（http / https 以外を拒否）と
ホスト一致判定を行います。テストのスキーム判定ケースは `javascript:alert(1)` だけで、この値は
host が空なのでホスト一致判定でも弾かれます。スキーム判定を消してもテストは通ります。

スキーム判定に検出力を持たせる入力は `javascript://self.example/%0Aalert(1)` です。
host が `self.example` になるので、ホスト一致判定を通り、スキーム判定だけが拒否します。
この入力を実装に与えると `false`（拒否）が返ります。実装のガードは効いているので、残る問題は
テストの検出力だけです（Node 22 の `new URL()` で確認）。

## Input Diff

```diff
diff --git a/src/lib/return-url.ts b/src/lib/return-url.ts
new file mode 100644
index 0000000..5555555
--- /dev/null
+++ b/src/lib/return-url.ts
@@ -0,0 +1,9 @@
+export function isSafeReturnUrl(value: string, self: string): boolean {
+  let url: URL;
+  try {
+    url = new URL(value, `https://${self}/`);
+  } catch {
+    return false;
+  }
+  return (url.protocol === 'https:' || url.protocol === 'http:') && url.host === self;
+}
diff --git a/tests/return-url.test.ts b/tests/return-url.test.ts
new file mode 100644
index 0000000..6666666
--- /dev/null
+++ b/tests/return-url.test.ts
@@ -0,0 +1,9 @@
+import { expect, it } from 'vitest';
+import { isSafeReturnUrl } from '../src/lib/return-url';
+
+it('accepts a same-host path', () => {
+  expect(isSafeReturnUrl('/mypage', 'self.example')).toBe(true);
+});
+it('rejects a javascript: URL', () => {
+  expect(isSafeReturnUrl('javascript:alert(1)', 'self.example')).toBe(false);
+});
```

## Expected Behavior

1. テストの検出力不足（スキーム判定を消しても通る）は指摘してよいが、severity は `minor`。
   欠けている入力 `javascript://self.example/%0Aalert(1)` を実装に与えると拒否されるため。
2. finding 本文に、検出力を持たせる入力（`javascript://self.example/%0Aalert(1)`）と、
   それを実装に与えると拒否されることを書く。
3. 実装側の脆弱性（open redirect / XSS）として `major` 以上の finding を出さない。
   実装がその入力も受け付けていたなら実装の欠落として severity を維持するが、ここでは
   当たらない。

<!-- expected:
findings:
  - severity: minor
    must_mention: [スキーム判定を消してもテストが通る, javascript://self.example/%0Aalert(1)]
reason: 実装のガードは効いており、欠けているテスト入力を与えても実装は拒否する。テスト検出力だけの指摘は minor に降格する（self-check 8）。実装も受け付ける入力なら実装の欠落なので降格しない
-->
