# Improvement Loop / 継続改善ループ

River Review を「レビューを実行するだけ」のエージェントから
「レビュー結果の検証・フィードバック分類・skill への還元」を担う運用単位に進化させるための loop。

1 件のフィードバックを **fixture / reference / suppression / routing** のいずれかに必ず降ろす。
ad hoc な prompt 修正で終わらせない。

## Loop steps / 9 ステップ

```text
1. Route          input  → 適切な専門 skill 選択
2. Review         skill  → 候補 finding 群を生成
3. Verify         findings → VERIFICATION.md の自己点検でフィルタ
4. Classify FB    feedback → FEEDBACK.md の taxonomy で分類
5. Patch One Thing 1 PR で 1 件の改善のみ（複合改善は分割）
6. Add Fixture    eval fixture（guard / happy-path）に変換
7. Run Eval       npm run planner:eval / eval:fixtures / eval:repo-context で検証
8. Record Learning AGENT_LEARNINGS.md などに学びを 1 行で記録
9. Promote Rule   再発を防ぐルール / pre-execution gate / 明文化として昇格
```

## 各ステップの詳細

### 1. Route

- `skills/agent-skills/river-review/SKILL.md` の Routing 表と `references/ROUTING.md` の優先度規則に従う。
- 該当 skill が無ければ `river-review-code` にフォールバック。
- 同点なら併用実行。

### 2. Review

- 専門 skill を実行し、候補 finding を集める。
- input artifacts の優先度: user intent > phase > artifact > changed files > rules / risk-map。

### 3. Verify

- [VERIFICATION.md](./VERIFICATION.md) の self-check 6 項目を全て通過した finding のみ出力する。
- Reject 条件に該当した finding は **どこで弾かれたか** を内部 trace に残しておく（後で eval fixture 化に使える）。

### 4. Classify Feedback

- 人間 / 別エージェントから返ったフィードバックは [FEEDBACK.md](./FEEDBACK.md) の 7 type で分類する。
- どの type か即決できないものは `unclear` として扱い、wording 改善で対応する。

### 5. Patch One Thing

- 1 PR で 1 件の改善のみを行う（複数 fixture / reference を同 PR にまとめない）。
- skill の prompt を直接書き換えるよりも、**reference / fixture / suppression** で再現性のある形に降ろす方を優先する。
- 大きな変更が必要な場合は Epic / sub-issue に分割する。

### 6. Add Fixture

- `false_positive` → guard fixture（"このケースで finding を出さないこと"）
- `missed_issue` → happy-path fixture（"このケースで finding を出すこと"）
- `accepted` → 必要なら positive fixture（再発検出を保証）

fixture 配置先（既存運用に合わせる）:

- repo-wide review: `tests/fixtures/repo-context/`
- planner / routing: `tests/fixtures/planner/`
- skill 単体 eval: 該当 skill 配下の `fixtures/`

### 7. Run Eval

該当する eval を必ず通す。

| 対象               | コマンド                                                |
| ------------------ | ------------------------------------------------------- |
| Skill schema       | `npm run skills:validate`                               |
| Agent skill schema | `npm run agent-skills:validate`                         |
| Planner / routing  | `npm run planner:eval` / `npm run planner:eval:dataset` |
| Review fixtures    | `npm run eval:fixtures`                                 |
| Repo-wide context  | `npm run eval:repo-context`                             |

ローカル実行で fail したら commit しない（CI 通過のみに頼らない）。

### 8. Record Learning

- 再発を防ぎたい知見は `AGENT_LEARNINGS.md` または `docs/development/` 配下のドキュメントに 1 行で残す。
- 「なぜそうしたか」「いつ見直すか」を明記する。

### 9. Promote Rule

- 同種の問題が 2 回以上発生したら、ルール化する候補にする（個別 fixture では追いつかない）。
- ルール化先の例:
  - `.claude/rules/review-core.md`（レビュー禁止事項）
  - skill の `Pre-execution Gate`（実行前ガード）
  - `docs/governance.md`（運用手順）

## Trigger / 起動条件

このループは以下のいずれかで回す。

- レビュー結果に対する人間からの返答（PR コメント / Slack / 直接対話）
- `/review-local` などローカル self-review の所感
- eval 結果（`npm run eval:all`）の regression / 新規 failure
- 修正PR / follow-up PR によって、元PRレビューの見落としが判明した
- 月次 / リリース時の振り返り（retrospective）

### Fix PR trigger / 修正PRからの学習

修正PRは「元PRレビューで捕まえられなかった実害の証拠」として扱う。
ただし、修正PRの内容をそのまま rule にしない。まず `missed_issue` feedback として記録し、root cause を分類してから fixture / routing / reference / skill 文言へ落とす。

最小フロー:

1. 修正PRの title / body / diff から、元PRと見落とし内容を特定する。
2. 元PRレビューで期待される owner skill を推定する。
3. `river feedback add` で `trigger=fix-pr`、`feedbackType=missed_issue` として記録する。
4. `npm run feedback:apply` で happy-path fixture scaffold を作る。
5. `npm run feedback:rules` で同種の見落としが再発していないかを見る。
6. 反映は必ず PR レビューを通し、SKILL.md / reference / fixture の自動更新はしない。

例:

```bash
npm run river -- feedback add \
  --type missed_issue \
  --skill rr-midstream-typescript-strict-001 \
  --trigger fix-pr \
  --pr 1234 \
  --evidence "Fix PR #1234 showed that original PR #1200 missed a nullable response edge case."

npm run feedback:apply
npm run feedback:rules
```

## Anti-patterns / 避けるべき進め方

- 1 PR で複数 skill の SKILL.md / reference / fixture を同時に書き換える（影響範囲が読めなくなる）。
- prompt 修正だけで済ませて fixture / reference を作らない（再発する）。
- suppression を最初の手段にする（guard fixture でカバーできるなら必ずそちらを優先）。
- 「再発したらまた直せばよい」と先送りする（promote rule のステップが飛ぶ）。
- 修正PRを見つけた段階で、個別事象をいきなり汎用 rule に昇格しない。

## 関連リソース

- 検証: [VERIFICATION.md](./VERIFICATION.md)
- フィードバック分類: [FEEDBACK.md](./FEEDBACK.md)
- ルーティング: [ROUTING.md](./ROUTING.md)
- レビュー基準 SSoT: `docs/review/`、`pages/reference/review-policy.md`
