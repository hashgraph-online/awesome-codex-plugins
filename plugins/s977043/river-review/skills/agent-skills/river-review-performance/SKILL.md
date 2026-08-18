---
id: river-review-performance
name: river-review-performance
description: |
  パフォーマンス観点のレビューエージェント。
  N+1クエリ、メモリ効率、キャッシュ戦略、可観測性の観点でコード変更を評価する。
category: midstream
phase: [midstream]
severity: major
applyTo:
  # logging-observability（app/lib/packages + src の cjs 拡張）と
  # modern-web-performance（app/components/pages/styles/public、html/css 拡張）の
  # applyTo 包含検査 warning 解消（#1508 系）。modern-web-performance は frontend 側の
  # exemption が「実行は performance」と宣言済みのため、本エントリで到達させる。
  - 'src/**/*.{ts,tsx,js,jsx,mjs,cjs,html,css}'
  - 'app/**/*.{ts,tsx,js,jsx,mjs,cjs,html,css}'
  - 'components/**/*.{ts,tsx,js,jsx,html,css}'
  - 'pages/**/*.{ts,tsx,js,jsx,html,css}'
  - 'lib/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'packages/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'styles/**/*.css'
  - 'public/**/*.html'
  - '**/*.sql'
# applyTo 包含検査（#1508）の意図的除外。ルーティング表に載るが本エントリの
# applyTo には含めないルーティング先を、理由付きで宣言する。
applyToExemptions:
  - skill: cache-strategy-consistency
    reason: 参照のみ。cache-strategy-consistency は docs 向け設計文書レビュー（phase upstream、applyTo が docs/**/*.md 等のみ）で、code/sql 実行観点の本エントリ（phase midstream）とはドメインが異なる。実行は river-review-architecture に据置く（本 SKILL.md「cache-strategy-consistency の帰属について」）。本エントリの applyTo には含めない。
  - skill: operability-slo
    reason: 参照のみ。実行は river-review-architecture に据置く（ドメイン不一致。operability-slo は upstream/docs 系、本エントリは midstream/code 系。architecture 経由で完全到達済み）。cache-strategy-consistency exemption（#1522）の様式を踏襲。
inputContext: [diff, fullFile]
outputKind: [findings, actions]
tags: [performance, optimization, entry, routing]
version: 0.1.0
license: MIT
---

# Performance Review（パフォーマンスレビュー）

パフォーマンスに影響する変更を検出し、適切な個別スキルで検証する。

## When to Use / いつ使うか

- データベースクエリの追加・変更時
- ループ処理やバッチ処理の変更時
- キャッシュ戦略の変更時
- 大量データの処理ロジック変更時

## Routing / ルーティング

| キーワード             | スキルID                      | 説明                                                                                               |
| ---------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| キャッシュ, TTL        | `cache-strategy-consistency`  | 参照のみ。実行は `river-review-architecture`（[理由](#cache-strategy-consistency-の帰属について)） |
| 障害, 監視, メトリクス | `failure-modes-observability` | 障害モードと可観測性                                                                               |
| ログ, トレース         | `logging-observability`       | ロギング・可観測性                                                                                 |
| SLO, レイテンシ        | `operability-slo`             | 運用性・SLO                                                                                        |

### `cache-strategy-consistency` の帰属について

`cache-strategy-consistency` はキャッシュ戦略という語感から performance の懸念に見えるが、実体は設計ドキュメント（docs/spec/RFC 等）のキャッシュ戦略記述をレビューする upstream スキル（`applyTo` が `docs/**/*.md` 等の docs 系のみ、Pre-execution Gate も「差分に設計ドキュメントの変更がある」ことを要求）である。本エントリ（phase midstream、`applyTo` が code/sql）とはドメインが異なるため、ドメイン一貫性を優先し実行は `river-review-architecture`（phase upstream、docs 系 applyTo を保有）に据え置く。本表には**到達性のための参照行**として掲載するのみで、performance 側に重複するアクティブなキーワードルートは追加しない。

### デフォルト動作

- キーワード指定なし → 以下のヒューリスティクスで判定:
  - ループ内I/O → N+1クエリ検出
  - 大量データ処理 → メモリ効率チェック
  - 外部API呼び出し → タイムアウト・リトライ検証

## Execution Flow / 実行フロー

```text
1. 変更内容の分析
   ├─ ループ内I/O → N+1クエリ検出を優先
   ├─ 大量データ処理 → メモリ効率チェックを優先
   ├─ 外部API呼び出し → タイムアウト・リトライ検証を優先
   └─ キーワード指定あり → 該当スキルを直接選択

2. スキルの実行
   ├─ cache-strategy-consistency: キャッシュ戦略の一貫性
   ├─ failure-modes-observability: 障害モードと可観測性
   ├─ logging-observability: ロギング・可観測性
   └─ operability-slo: 運用性・SLO

3. 統合
   ├─ 重複する指摘の除去
   └─ Checklistに基づくパフォーマンスチェックの補完
```

## Checklist / チェックリスト

パフォーマンスレビューでは以下を確認する:

### クエリ効率

- N+1クエリが発生していないか
- 必要なeager loadingが設定されているか
- 不要なカラムを取得していないか（SELECT \*）

### メモリ効率

- ループ内での不要なオブジェクト生成がないか
- 大量データのストリーム処理が適切か
- メモリリークのパターンがないか

### I/O効率

- 外部API呼び出しのタイムアウト設定
- リトライ戦略の妥当性
- 並列化可能なI/Oの逐次実行

### キャッシュ

- キャッシュキーの設計が適切か
- TTLが妥当か
- キャッシュの無効化戦略

## Output Format / 出力形式

```text
<file>:<line>: <message>
```

- **Finding**: 何が問題か（1文）
- **Impact**: 推定される影響（レイテンシ増加、メモリ消費等）
- **Fix**: 次の一手（最小の修正案）

## 他スキルとの関係

| スキル                      | 関係 | 棲み分け                                                                |
| --------------------------- | ---- | ----------------------------------------------------------------------- |
| `river-review-architecture` | 補完 | performance は「実行時効率」、architecture は「構造的スケーラビリティ」 |
| `river-review-code`         | 補完 | performance は「速度・効率」、code は「可読性・保守性」                 |

## References

- [ROUTING.md](./references/ROUTING.md): 詳細なルーティングルール
