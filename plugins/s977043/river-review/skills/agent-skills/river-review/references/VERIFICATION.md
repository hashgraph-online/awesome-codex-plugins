# Finding Verification / 指摘の自己検証

River Review が出した finding を確定させる前に、必ずこのチェックを通す。
失敗した finding は出力しない（または `severity: info` に下げる）。

## 必須条件 / Hard requirements

各 finding は以下を全て満たすこと。1 つでも欠ければ reject する。

### 1. Evidence が具体物に紐づく

- `file:line` 形式の引用、もしくは PR の `artifact / diff hunk / test name / log line` を持つ。
- 「一般論として〜」「ベストプラクティス的に〜」のみで根拠が示せない finding は reject。
- 引用する line/range は **diff に含まれていなければならない**（差分外の推測は禁止、`review-core` ルール参照）。

### 2. Impact が具体的

- 「読みにくい」「保守性が下がる」のような抽象表現のみは不可。
- 何が壊れる / 誰が困る / どの状況で問題化するかを 1 文で書ける。

### 3. Fix が「次の最小一手」

- 修正案は **1 ファイル / 1 関数 / 1 設定値** に収まる粒度を起点にする。
- リファクタや別 Issue で扱うべき粒度の提案は、明示的に follow-up として切り出す。

### 4. Severity と Confidence が calibrated

| severity | 意味                                             | confidence の扱い           |
| -------- | ------------------------------------------------ | --------------------------- |
| critical | merge してはならない（セキュリティ・データ破損） | confidence high のみ許可    |
| major    | merge 前に解消が望ましい                         | confidence medium 以上      |
| minor    | follow-up でよい                                 | confidence low でも許可     |
| info     | 観察 / 議題提示のみ                              | confidence low / unknown 可 |

- `critical` を出すなら確証がある evidence を伴うこと。
- 自信がなければ `info` か `confidence: low` にする（`major` の安易な乱発を抑制）。

### 5. 重複していない

- 同じ file / 同じ修正粒度の指摘を別 finding として分けない。
- 指摘点が複数ファイルに渡る場合は **代表 1 つにまとめる + 他は同 finding 内で言及** する。
- `findingId` または `file:line` でマージできるなら必ずマージする。

### 6. 一般論ではなく差分への指摘

- `review-core` ルールに従い、PR の目的と差分に紐づかない一般論の助言は reject。
- 「将来的に〜」「他のリポジトリでは〜」は finding ではなく `actions` / follow-up へ切り出す。

## Reject conditions / 却下条件

以下に該当する finding は出力しない。

| 条件                                   | 対処                              |
| -------------------------------------- | --------------------------------- |
| evidence なし（差分参照ゼロ）          | 出力しない                        |
| diff に含まれない行への指摘            | 出力しない                        |
| 「〜した方が良い」のみで impact 未提示 | 出力しない                        |
| critical なのに confidence low         | severity を major / info に下げる |
| 同一 file:line で別 severity の重複    | 上位 severity に統合              |
| PR 目的と無関係（チケット範囲外）      | 出力しない or follow-up issue へ  |

## 自己点検フロー / Self-check flow

finding 出力前にエージェントが内部で実行する手順。

```text
for each candidate_finding:
  1. evidence?       → no  → reject
  2. impact concrete?→ no  → reject
  3. fix actionable? → no  → downgrade or reject
  4. severity calibrated against confidence? → no → adjust
  5. duplicate of earlier finding? → yes → merge
  6. tied to diff?   → no  → reject (general advice)
emit only findings that survived all six checks
```

## 関連リソース

- 重要度ラベルと出力スキーマ: `docs/review/output-format.md`
- レビュー観点: `docs/review/viewpoints.md`
- 内部ルール: `.claude/rules/review-core.md`
- フィードバック取り扱い: [FEEDBACK.md](./FEEDBACK.md)
- 改善ループ: [IMPROVEMENT_LOOP.md](./IMPROVEMENT_LOOP.md)
