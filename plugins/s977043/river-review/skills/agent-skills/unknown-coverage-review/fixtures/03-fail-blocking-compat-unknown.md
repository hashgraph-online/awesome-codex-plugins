# Test Case: Blocking Compatibility Unknown → fail (NO_GO)

## Description

旧設定形式との互換性が検証されていないまま設定パーサーを差し替えたケース。旧形式を読み込む利用箇所を検索した証拠がなく、互換テストもない。互換破壊は不可逆的な障害につながるため重大な Blocking Unknown。Unknown Coverage Review は `severity: critical`・`blocking: true` で出し、`verdict: fail`（`NO_GO`）へ写像する。

## Input Diff

```diff
diff --git a/src/config/parser.mjs b/src/config/parser.mjs
index 6666666..7777777 100644
--- a/src/config/parser.mjs
+++ b/src/config/parser.mjs
@@ -1,5 +1,4 @@
-// 旧 YAML 形式と新 TOML 形式の両方を受け付ける
-export function parseConfig(text, format) {
-  if (format === 'yaml') return parseYaml(text);
-  return parseToml(text);
-}
+// TOML のみを受け付ける
+export function parseConfig(text) {
+  return parseToml(text);
+}
```

## PR 本文 / Artifacts

- plan: なし。
- review-self: なし。
- 旧 YAML 形式を渡す利用箇所の検索記録なし。互換テストなし。

## Expected Behavior

本観点は以下を満たすこと。

1. Repository / Impact Unknown を Blocking で検出する（旧 YAML 形式の利用箇所を検索した証拠が不足＝evidence_missing: repository-wide usage search, migration compatibility test）。
2. `blocking: true`・`severity: critical` とし、resolution（旧形式を読み込む利用箇所を検索し、互換テストを追加する）を添える。
3. `verdict: fail`（`gate.decision: NO_GO`）へ写像する。
4. `parseYaml` 呼び出し元の残骸そのものは `cross-file-leakage` へ委譲し、本観点は「互換性を確認した証拠の不在」に限定して指摘する。
