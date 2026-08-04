# Fixture 01 — 近傍コメントが指摘内容を解消している（Should NOT Detect）

False-positive canary（#1685）: 指摘対象行の直前に設計意図が明記されており、
それを読めば意図的な挙動だと分かるケース。VERIFICATION.md の self-check 7
「近傍の設計意図コメントを確認済み」が働けば finding は出ない。

## Description

`evaluateCandidates` は候補にスコアを付けるだけで、選定（割当）は行わない。
直前のコメントが「選定はしない」「検証ボード表示用の opt-in」「本番の割当ロジック
からは呼ばれない」と明記しているため、「選定処理が欠落している」「閾値が検証され
ていないため誤った候補が選ばれる」という指摘はいずれも成立しない。

## Input Diff

```diff
diff --git a/app/Services/CandidateScoring.php b/app/Services/CandidateScoring.php
index 1111111..2222222 100644
--- a/app/Services/CandidateScoring.php
+++ b/app/Services/CandidateScoring.php
@@ -18,6 +18,15 @@ class CandidateScoring
     }
+
+    // 候補の評価のみを行う（選定はしない。検証ボード表示用のため opt-in）。
+    // 本番の割当ロジックからは呼ばれず、閾値は運用者が画面で調整する。
+    public function evaluateCandidates(array $candidates, float $threshold): array
+    {
+        return array_map(
+            fn (Candidate $c) => ['id' => $c->id, 'score' => $this->score($c, $threshold)],
+            $candidates
+        );
+    }
 }
```

## Expected Behavior

The reviewer should NOT flag this:

1. 「スコア算出後に選定処理がない」— コメントが「選定はしない」と明記しており、
   欠落ではなく設計上の境界。
2. 「`$threshold` が未検証のまま使われ、誤った候補が選定される」— 選定しない以上、
   この impact は成立しない。opt-in の表示用途であることもコメントに明記されている。
3. 意図に触れずに同じ提案を繰り返すこと自体が reject 条件（VERIFICATION.md
   「近傍コメントの意図に触れない再提案」）。

床（floor）との関係: ここで取り下げられるのは、**コメントによって指摘の前提そのものが
事実として崩れる**ケース（選定しないので「誤った候補が選定される」が起こり得ない）で
あって、「実リスクはあるが intentional だから見逃す」ではない。後者は fixture 04 のとおり
取り下げ禁止。

<!-- expected:
findings: []
reason: 指摘行の直前コメントが「選定はしない・検証ボード表示用の opt-in」と設計意図を明記しており、選定欠落・閾値未検証の指摘はいずれも意図で解消済み（#1685）
-->
