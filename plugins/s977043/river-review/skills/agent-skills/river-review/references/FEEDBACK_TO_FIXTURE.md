# Feedback-to-Fixture Conversion Workflow

レビュー結果に対する人間 / エージェントのフィードバックを、**ad hoc な prompt 修正で済まさず、必ず fixture / suppression / reference / routing 更新へ降ろす** ための運用フロー。

[FEEDBACK.md](./FEEDBACK.md) は taxonomy（種別と repository action の対応）を定義する辞書。本文書はその taxonomy を**実行可能な変更**に落とすための運用手順である。

## When to apply / 起動条件

以下のいずれかが発生したとき、必ず本フローを通す。

- レビュー結果に対する人間からの返答（PR コメント / Slack / 直接対話）
- `/review-local` などローカル self-review で気になった出力
- `npm run eval:all` の regression / 新規 failure
- 修正PR / follow-up PR によって、元PRレビューの見落としが判明した
- 月次 / リリース時の振り返り（retrospective）

## 1 PR = 1 改善

[IMPROVEMENT_LOOP.md](./IMPROVEMENT_LOOP.md) の "Patch One Thing" を厳守する。1 件のフィードバックを複数の skill / fixture に同時に展開しない（影響範囲が読めなくなり、後続の eval drift を切り分けにくくなる）。

## Conversion table / 変換表（eval コマンド付き）

各 feedback type は **主 destination（必要なら副 destination）** と、**実行すべき eval コマンド群** にマッピングされる。複数候補が併記されているセルは、どれを選ぶかが本ドキュメント以下で明示される（例: `false_positive` は guard fixture を最優先、不可能なときのみ suppression）。

| feedback type    | 主な destination                                                  | 副 destination                                 | 必須 eval コマンド                                                                     | rationale 必須? |
| ---------------- | ----------------------------------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------- | --------------- |
| `accepted`       | （変更なし）                                                      | positive fixture（必要時）                     | `npm run eval:fixtures`                                                                | 不要            |
| `false_positive` | guard fixture（`<NN>-guard.md` / `*-should-not-detect`）          | suppression（guard 不可時）                    | `npm run eval:fixtures` + `npm run eval:repo-context`                                  | 任意            |
| `missed_issue`   | happy-path fixture（`<NN>-happy.md` / `*-should-detect`）         | routing 更新（後述の root cause 判定で必要時） | `npm run eval:fixtures` + `npm run eval:repo-context` + `npm run planner:eval:dataset` | 不要            |
| `not_actionable` | reference の fix template / example 追記                          | skill SKILL.md の output 例                    | `npm run skills:validate`                                                              | 不要            |
| `duplicate`      | routing 更新（owner skill 明確化）または skill 内 dedupe ロジック | dedupe key の見直し                            | `npm run planner:eval:dataset` + `npm run skills:validate`                             | 不要            |
| `accepted_risk`  | suppression entry（rationale 必須）                               | （なし）                                       | `npm run skills:validate`                                                              | **必須**        |
| `unclear`        | skill SKILL.md / reference の wording 改善                        | VERIFICATION.md への追記                       | `npm run skills:validate`                                                              | 不要            |

`accepted_risk` の rationale は `--rationale` で suppression entry に必ず記録する。**特に `severity: major` / `critical` の指摘を `accepted_risk` で抑止する場合は、なぜ residual risk を許容できるのかを 1 文以上で説明する**（HIGH_SEVERITY guard で `accepted_risk` 以外の type は弾かれるため、結果的にこの型を選ぶこと自体が判断責任を伴う）。

## missed_issue の root cause 分類

`missed_issue` は「レビューが見落とした」事象だが、**なぜ見落としたか** で対処が変わる。fixture を追加するだけでは不十分なケースがある。

| root cause            | 兆候                                                                                                             | 対処                                                                                                                                                                               |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **routing miss**      | 該当 skill が plan に入っていない（`plan.selected` に出ていない）                                                | `tests/fixtures/planner-dataset/cases.json` に対応する case を追加し、`npm run planner:eval:dataset` で再現させる。`applyTo` / `inputContext` / `availableContexts` の組合せを修正 |
| **missing context**   | skill は plan に入ったが、レビュー時に必要な周辺情報（fullFile / tests / usages）が context に含まれていなかった | 該当 skill の `inputContext` を拡張、または `.river-review.yaml` の `context.budget.perSectionCaps` を見直す                                                                       |
| **weak instructions** | skill は plan に入り context も足りていたが、prompt が拾い方を教えていない                                       | skill の SKILL.md / `prompt/system.md` を更新し、happy-path fixture を追加して再現性を保証                                                                                         |

3 つのうち 1 つだけが当てはまるとは限らない。例えば routing miss + missing context が同時に起きていることもあるので、**まず planner:eval で routing 単独を切り分けてから** context / instructions を順に検証する。

## 1 件のフィードバックを動かすステップ

1. [FEEDBACK.md](./FEEDBACK.md) の taxonomy で feedback type を 1 つ確定する（複数候補なら最も重い repository action を伴う方を選ぶ）。
2. 上記 conversion table から destination と eval コマンドを引く。
3. `missed_issue` の場合は root cause 分類を 1 つ確定する。
4. 該当 destination を **1 PR で 1 件だけ** 変更する（複合変更は分割）。
5. 必須 eval コマンドをローカルで実行し、exit 0 を確認する（CI 通過のみに頼らない）。
6. PR 本文に「どの feedback type を / どの destination に / どの eval で検証したか」を 3 行で書く。
7. 再発を防ぐ知見が出たら `AGENT_LEARNINGS.md` または `docs/development/` に 1 行で記録する（[IMPROVEMENT_LOOP.md](./IMPROVEMENT_LOOP.md) Step 8 に対応）。

## suppression を選ぶ前に必ず guard fixture を試す

`false_positive` で suppression を最初の選択肢にしない。

- guard fixture（"このケースで finding を出さないこと"）で再現性のある形に降ろせるなら、**必ずそちらを優先**。suppression は fingerprint 単位の点的な抑止で、根本原因が skill / prompt 側にある場合は再発する。
- guard fixture が現実的に書けない（fingerprint だけがユニークな証拠で、入力 diff にパターン化できる差がない）場合のみ suppression を使う。
- suppression を使う場合は **必ず rationale + scope + 期限** を記録する（期限なし永続 suppression は最小化）。

## 関連リソース

- 親 Epic: [#743 River Review Skill Improvement Loop](https://github.com/s977043/river-review/issues/743)
- 検証フィルタ: [VERIFICATION.md](./VERIFICATION.md)
- フィードバック taxonomy: [FEEDBACK.md](./FEEDBACK.md)
- ループ全体像: [IMPROVEMENT_LOOP.md](./IMPROVEMENT_LOOP.md)
- ルーティング規則: [ROUTING.md](./ROUTING.md)
- レビュー基準 SSoT: `docs/review/`、`pages/reference/review-policy.md`
