---
id: river-review
name: river-review
description: |
  River Review のメインエントリポイント。
  レビュー依頼の intent classification → 専門 skill 選択 → 実行 → finding verification →
  feedback classification → fixture / reference / suppression への還元までを束ねる
  improvement-loop orchestrator。
phase: [upstream, midstream, downstream]
severity: minor
applyTo: ['**/*']
tags: [entry, routing, orchestrator, improvement-loop]
version: '0.1.0'
license: MIT
---

# River Review

River Review は「流れに寄り添う」AI レビューエージェントです。
**単にレビューを実行するだけでなく、レビュー結果を検証し、フィードバックを分類して
fixture / reference / suppression / routing へ還元する継続改善ループ** を担います。

## When to Use / いつ使うか

- コードレビューを依頼したいとき
- PR の品質を確認したいとき
- 設計やアーキテクチャのフィードバックが欲しいとき
- レビュー結果に対するフィードバックを skill 改善へつなぎたいとき

## Responsibilities / 責務

このエントリ skill は以下を担う。順序は実行フローと一致する。

1. **Classify input intent**: ユーザー意図 / phase / artifact / risk から target カテゴリを決める。
2. **Select specialist skills**: routing 表と優先度ルールで専門 skill を選ぶ。複数該当なら併用する。
3. **Create review execution plan**: input 優先度に従って artifact を集め、実行プランを作る。
4. **Verify findings**: 専門 skill の生成 finding に対して [VERIFICATION.md](./references/VERIFICATION.md) の self-check を適用する。
5. **Classify feedback**: 返ってきたフィードバックを [FEEDBACK.md](./references/FEEDBACK.md) の taxonomy で分類する。
6. **Hand off learnings**: 分類結果を fixture / reference / suppression / routing 更新へ降ろす（[IMPROVEMENT_LOOP.md](./references/IMPROVEMENT_LOOP.md)）。

## Input priority / 入力優先度

review 実行プランを組むときに参照する入力は、以下の優先順で扱う。
上位の入力が下位を上書きする。

1. **user intent** — 「セキュリティ観点で」「パフォーマンスのみ」など明示的な依頼
2. **phase** — upstream / midstream / downstream の指定
3. **artifacts**
   - `plan` / `diff` / `test-cases` / `junit` / `coverage` / `review-self` / `review-external`
4. **changed files** — 対象差分のファイル一覧
5. **`.river/rules.md`** — リポジトリ固有のレビュー規則
6. **`.river/risk-map.yaml`** — リスクマップ
7. **available contexts / dependencies** — repo-wide context、依存 skill の宣言

`.river/` 系が見つからない場合は `.claude/rules/` を fallback として使う。

## Routing / ルーティング

入力に応じて、以下の専門スキルへ案内します。詳細な優先度規則は [ROUTING.md](./references/ROUTING.md)。

| キーワード                 | 専門スキル                | 説明                         |
| -------------------------- | ------------------------- | ---------------------------- |
| 設計, アーキテクチャ, ADR  | river-review-architecture | 設計・アーキテクチャレビュー |
| セキュリティ, 脆弱性       | river-review-security     | セキュリティ観点レビュー     |
| パフォーマンス, 最適化     | river-review-performance  | パフォーマンス観点レビュー   |
| テスト, カバレッジ         | river-review-testing      | テスト観点レビュー           |
| 敵対的, 壁打ち, バイアス   | adversarial-review        | 敵対的レビュー（3手法統合）  |
| ドキュメント, README, i18n | river-review-docs         | ドキュメント整合性レビュー   |
| (上記以外)                 | river-review-code         | 一般コード品質レビュー       |

> **デフォルト動作**: キーワードがどれにも当てはまらない場合は一般コードレビュー (river-review-code) にフォールバックします。
>
> **複数カテゴリ該当時**: severity重み → キーワード数 → 入力内位置の順で優先度を解決します。同点時は併用実行します。

## Execution Flow / 実行フロー

```text
1. 入力の intent classification
   ├─ 明示的なキーワード指定あり → 該当する専門スキルへルーティング
   ├─ 複数カテゴリに該当 → severity重み → キーワード数 → 入力内位置で優先度解決
   └─ キーワードなし → river-review-code（デフォルト）へフォールバック

2. 専門スキルの実行
   ├─ river-review-architecture: 設計・アーキテクチャ観点
   ├─ river-review-security: セキュリティ観点
   ├─ river-review-performance: パフォーマンス観点
   ├─ river-review-testing: テスト観点
   ├─ adversarial-review: 敵対的レビュー（3手法統合）
   ├─ river-review-docs: ドキュメント整合性観点
   └─ river-review-code: 一般コード品質（フォールバック）

3. Finding verification
   └─ VERIFICATION.md の 6 項目 self-check を全件通過したものだけ出力

4. Feedback classification（人間/エージェント返答受領後）
   └─ FEEDBACK.md の 7 type で分類

5. Improvement loop handoff
   └─ IMPROVEMENT_LOOP.md の 9 ステップに従って fixture / reference / suppression / routing を更新
```

## Output Contract / 出力コントラクト

Finding は以下のフィールドを満たすこと。詳細条件は [VERIFICATION.md](./references/VERIFICATION.md)。

| フィールド | 内容                                                                                   |
| ---------- | -------------------------------------------------------------------------------------- |
| Finding    | 何が問題か（1 文）                                                                     |
| Evidence   | `file:line` か artifact 参照。差分外の推測は不可                                       |
| Impact     | 何が壊れる / 誰が困るか（具体的に）                                                    |
| Fix        | 次の最小一手。1 ファイル / 1 関数 / 1 設定値の粒度を起点に                             |
| Confidence | high / medium / low / unknown                                                          |
| Severity   | critical / major / minor / info（出力スキーマでは critical→major→minor→info に正規化） |
| Skill ID   | どの専門 skill が出した finding か（routing 透明化）                                   |

シンプルな出力フォーマット:

```text
<file>:<line>: <Finding>
  Impact: <Impact>
  Fix: <Fix>
  Severity: <severity> / Confidence: <confidence> / Skill: <skill-id>
```

## How to Invoke / 呼び出し方

### Claude Code エージェントとして（`agents/river-review.md`）

Claude Code プラグインとしてインストールされている場合、`river-review` エージェントがこのスキルを読み込んで実行する。
エージェントは薄いラッパーであり、すべての手順・ルーティング・検証ロジックはこのスキルが SSoT となる。

利用可能なツール: `Read`, `Grep`, `Glob`, `Bash`

スキルのパス解決:

```bash
# Claude Code plugin 環境
${CLAUDE_PLUGIN_ROOT}/skills/agent-skills/river-review/SKILL.md

# リポジトリ内で直接実行する場合（フォールバック）
./skills/agent-skills/river-review/SKILL.md
```

### Codex スキルとして

Codex では `skills/agent-skills/` 配下のスキルとして直接利用できる。
このスキルを読み込み、手順に従ってレビューを実行する。

### CLI アクセラレータ（任意）

`river` CLI が PATH 上にある場合、構造化 finding のブートストラップに使える:

```bash
river run . --reviewers auto --output json
```

JSON には `findings` / `autoSelectedRoles` / `score` が含まれる。
CLI は必須でない。absent または失敗した場合はスキル駆動のレビューで継続すること。

## References

- [ROUTING.md](./references/ROUTING.md) — 詳細なルーティングルールと優先度
- [VERIFICATION.md](./references/VERIFICATION.md) — finding 出力前の self-check 条件
- [FEEDBACK.md](./references/FEEDBACK.md) — 人間/エージェントフィードバックの 7 分類と repository action
- [FEEDBACK_TO_FIXTURE.md](./references/FEEDBACK_TO_FIXTURE.md) — フィードバックを fixture / suppression / reference / routing 更新へ変換する運用フロー（eval コマンド付き）
- [IMPROVEMENT_LOOP.md](./references/IMPROVEMENT_LOOP.md) — 9 ステップ改善ループ
