# Test Case: Evidence Sufficient → pass (GO)

## Description

必要な証拠が差分・テスト・PR 本文に揃っており、Blocking Unknown が残っていないケース。Unknown Coverage Review は解消済み Unknown を記録し、`verdict: pass`（`GO`）へ写像する。過剰な Unknown を出さないこと（低リスク・十分証拠の canary）。

## Input Diff

```diff
diff --git a/src/config/loader.mjs b/src/config/loader.mjs
index 1111111..2222222 100644
--- a/src/config/loader.mjs
+++ b/src/config/loader.mjs
@@ -10,1 +10,5 @@ export function loadConfig(raw) {
-  return normalizeV2(raw);
+  // 旧 v1 形式との後方互換を維持する（利用箇所は repo 全体を grep 済み）
+  if (raw.schemaVersion === 1) {
+    return normalizeV2(migrateV1toV2(raw));
+  }
+  return normalizeV2(raw);
diff --git a/test/config/loader.test.mjs b/test/config/loader.test.mjs
index 3333333..4444444 100644
--- a/test/config/loader.test.mjs
+++ b/test/config/loader.test.mjs
@@ -20,0 +21,3 @@ describe('loadConfig', () => {
+  it('v1 形式を v2 へ移行して読み込む', () => {
+    expect(loadConfig({ schemaVersion: 1, legacy: true })).toEqual(expectedV2);
+  });
```

## PR 本文 / Artifacts

- plan: 「v1→v2 移行の互換テストを追加する」を Known Unknown として記録し、本 PR で解消。
- review-self: `git grep schemaVersion` で利用箇所を全数確認した記録あり。

## Expected Behavior

本観点は以下を満たすこと。

1. Blocking Unknown を検出しない（互換テスト・利用箇所検索の証拠が揃っている）。
2. 解消済み Unknown（U: v1 互換）を Good Points 節に根拠（追加テスト・grep 記録）付きで記録する。
3. `verdict: pass`（`gate.decision: GO`）へ写像する。
4. 過剰な質問・低確信の Unknown を出さない。
