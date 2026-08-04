# Fixture 03 — コメントと実装が矛盾する（Should Detect）

Non-goal の境界を守る canary。self-check 7 は「コメントを常に信用する」ルール
ではない。コメントの記述が実装と矛盾している場合、severity を下げず、矛盾自体を
finding にする。コメントを追記するだけで指摘が消える抜け道を作らないための guard。

## Description

コメントは「この関数は DB に触れない」「呼び出し側で検証済みの `userId` を渡す」と
主張しているが、実装は検証されていない値を文字列連結で SQL に埋め込んでいる。
コメントの主張は実装の担保になっておらず、SQL インジェクションが成立する。

## Input Diff

```diff
diff --git a/src/db/profile.ts b/src/db/profile.ts
index 5555555..6666666 100644
--- a/src/db/profile.ts
+++ b/src/db/profile.ts
@@ -8,6 +8,11 @@ import { db } from './client';
+
+// Callers must pass an already-validated `userId`; this helper never touches the DB
+// directly, it only builds a cached view.
+export async function getProfile(userId: string): Promise<Profile | null> {
+  return db.query(`SELECT * FROM profiles WHERE user_id = '${userId}'`);
+}
```

## Expected Behavior

The reviewer MUST still flag this:

1. Severity は `critical`（内部語彙 `blocker`）。コメントの存在を理由に severity を
   下げない。
2. コメントの「never touches the DB directly」は実装（`db.query`）と矛盾しており、
   「呼び出し側で検証済み」という前提もコード上で強制されていない。矛盾自体を
   Evidence に含める。
3. Fix はプレースホルダを使うパラメータ化クエリへの置き換え。あわせてコメントを
   実装に合わせて修正することを提案する。

<!-- expected:
findings:
  - severity: critical
    must_mention: [SQL インジェクション, コメントと実装の矛盾]
reason: コメントが実装と矛盾する場合は self-check 7 の降格対象外。コメント追記で指摘を抑止する抜け道を塞ぐ（#1685 Non-goals）
-->
