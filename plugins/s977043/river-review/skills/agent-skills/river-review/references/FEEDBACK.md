# Feedback Taxonomy / フィードバック分類

レビュー結果に対して人間（または別エージェント）から返ってきたフィードバックを、
**「リポジトリのどこに durable な変更として残すか」** が一意に決まるよう分類する。

ad hoc な prompt 修正で済ませず、**fixture / suppression / reference / routing のいずれか** へ確実に降ろすことが目的。

## Feedback types / フィードバック種別

各 feedback は以下のいずれか 1 つに分類する。複数該当する場合は最も重い repository action を伴う方を選ぶ。

| type             | 意味                                          | repository action                                                                      |
| ---------------- | --------------------------------------------- | -------------------------------------------------------------------------------------- |
| `accepted`       | finding は妥当で実際に修正された / されるべき | 必要に応じて positive fixture を追加（同パターンを「正しく検出できた」事例として残す） |
| `false_positive` | finding は誤検知                              | guard fixture（誤検知を再現させない条件）または suppression 追加                       |
| `missed_issue`   | レビューが見落とした重要な問題が後から判明    | happy-path fixture（次回検出すべき pattern）を追加                                     |
| `not_actionable` | 内容は正しいが修正案が不明 / 適用できない     | fix template または reference example を更新（修正手順を明文化）                       |
| `duplicate`      | 同じ問題を別 finding として複数出した         | dedupe policy / owner skill / priority を見直す（routing or merge ロジックの調整）     |
| `accepted_risk`  | 問題は認識しているがプロジェクト判断で許容    | suppression に rationale 付きで登録                                                    |
| `unclear`        | 何を言いたいか伝わらない / evidence が薄い    | wording 改善（VERIFICATION.md の自己点検を強化、もしくは reference example 追加）      |

## Mapping rules / 振り分けルール

判断に迷ったら以下の優先順で振り分ける。

1. **動作の誤り** → `false_positive` か `missed_issue` を最優先（ground truth に直結）
2. **内容は正しいが伝達不足** → `not_actionable` または `unclear`
3. **構造的な重複・優先度の問題** → `duplicate`
4. **プロジェクト判断による受容** → `accepted_risk`
5. **明確に妥当 + 採用された** → `accepted`

## Repository actions / 残し方の詳細

### accepted

- 同パターンが今後も検出されるべきなら fixture へ昇格。
- 単発の妥当指摘で再発確率が低ければ何も追加しない（無理に fixture を作らない）。

### false_positive

- まず **guard fixture**: 同じ入力で finding を出さないことを保証する eval ケース。
- guard が現実的に書けない場合のみ **suppression** を使う（理由とスコープを記録）。
- 修正は対象 skill の SKILL.md / reference / pre-execution gate を更新する。

### missed_issue

- 該当パターンを再現する **happy-path fixture**（"next time, detect this") を追加。
- どの skill が拾うべきだったか routing 観点で確認し、必要なら ROUTING.md を更新。

### not_actionable

- 修正手順が「コード補完だけで書ける」状態になるよう **fix template / example** を追加する。
- 既存の reference に追記する形が望ましい（新規ファイル乱立を避ける）。

### duplicate

- どの skill が owner なのか曖昧なケース → ROUTING.md を更新。
- 同 skill 内の重複 → 出力統合ロジック / dedupe key を見直す。
- severity が分散している場合 → 上位 severity に統合する基準を VERIFICATION.md に追加。

### accepted_risk

- suppression エントリには **理由・スコープ・期限** を必ず記録する。
- 期限なしの永続 suppression は最小化する。

### unclear

- evidence の取り方を VERIFICATION.md でアップデート。
- wording 改善の例を該当 skill の reference に追加する。

## Anti-patterns / やってはいけないこと

- prompt のみを書き換えて「直した」とすること（次のレビューで再発する）。
- 1 件のフィードバックで複数 skill の SKILL.md を同時に大幅改訂すること（影響範囲が読めなくなる）。
- suppression を最初の選択肢にすること（guard fixture でカバーできるなら必ずそちらを優先）。

## 関連リソース

- 検証手順: [VERIFICATION.md](./VERIFICATION.md)
- 改善ループ全体像: [IMPROVEMENT_LOOP.md](./IMPROVEMENT_LOOP.md)
- 出力形式: `docs/review/output-format.md`
