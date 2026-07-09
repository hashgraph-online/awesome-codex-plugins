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
  - 'src/**/*.{ts,tsx,js,jsx,mjs}'
  - '**/*.sql'
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

| キーワード             | スキルID                      | 説明                   |
| ---------------------- | ----------------------------- | ---------------------- |
| キャッシュ, TTL        | `cache-strategy-consistency`  | キャッシュ戦略の一貫性 |
| 障害, 監視, メトリクス | `failure-modes-observability` | 障害モードと可観測性   |
| ログ, トレース         | `logging-observability`       | ロギング・可観測性     |
| SLO, レイテンシ        | `operability-slo`             | 運用性・SLO            |

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
