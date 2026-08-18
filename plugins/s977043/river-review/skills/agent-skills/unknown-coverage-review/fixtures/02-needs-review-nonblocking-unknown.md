# Test Case: Non-blocking Operational Unknown → needs_review (ESCALATE)

## Description

実装は妥当だが、運用系の証拠が不足しているケース。ロールバック手順が PR 本文にも運用文書にもない。データ損失や互換破壊ではないため Blocking ではないが、人間判断が必要。Unknown Coverage Review は非 Blocking Unknown を `severity: major` で出し、§4 残リスクに明記して `verdict: needs_review`（`ESCALATE`）へ写像する。

## Input Diff

```diff
diff --git a/migrations/2026_07_add_index.sql b/migrations/2026_07_add_index.sql
new file mode 100644
index 0000000..5555555
--- /dev/null
+++ b/migrations/2026_07_add_index.sql
@@ -0,0 +1,2 @@
+-- 大規模テーブルへのインデックス追加
+CREATE INDEX CONCURRENTLY idx_orders_status ON orders (status);
```

## PR 本文 / Artifacts

- plan: なし（PlanGate 非依存で動作すること）。
- review-self: なし。
- PR 本文にロールバック手順の記載なし。

## Expected Behavior

本観点は以下を満たすこと。

1. Runtime / Operational Unknown を 1 件検出する（ロールバック手順の証拠が不足＝evidence_missing: rollback procedure）。
2. `blocking: false`・`severity: major` とし、resolution（PR 本文または運用文書へ手順を追記する）を添える。
3. plan / review-self 欠損を `skippedSkills` に記録し、Plan / Assumption 観点では finding を出さない（デグレード）。
4. `verdict: needs_review`（`gate.decision: ESCALATE`）へ写像し、§4「Unverified / Residual Risk」へ残リスクを明記する。
5. migration そのものの安全性（`CONCURRENTLY` の是非等）は `migration-safety` へ委譲し、重複指摘しない。
