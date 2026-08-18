# ルーティングルール — Architecture Review

## キーワードマッチング

### ADR・意思決定

- 日本語: ADR, 意思決定, 判断, 記録
- 英語: ADR, decision, record
- → `adr-decision-quality`

### API 設計

- 日本語: API, エンドポイント, REST, GraphQL
- 英語: API, endpoint, REST, GraphQL
- → `api-design`

### API バージョニング

- 日本語: API互換, バージョニング, 後方互換
- 英語: versioning, compatibility, breaking change
- → `api-versioning-compat`

### アーキテクチャ境界

- 日本語: 境界, モジュール, レイヤー, 依存方向
- 英語: boundary, module, layer, dependency direction
- → `architecture-boundaries`

### 設計図

- 日本語: 図, ダイアグラム, 構成図
- 英語: diagram, architecture diagram
- → `architecture-diagrams`

### リスク登録

- 日本語: リスク, リスク登録
- 英語: risk, risk register
- → `architecture-risk-register`

### トレーサビリティ

- 日本語: トレーサビリティ, 追跡, 要件紐付け
- 英語: traceability, trace, requirement link
- → `architecture-traceability`

### 検証計画

- 日本語: 検証計画, バリデーション
- 英語: validation plan
- → `architecture-validation-plan`

### 可用性

- 日本語: 可用性, 冗長, HA
- 英語: availability, redundancy, HA
- → `availability-architecture`

### ドメインモデリング

- 日本語: ドメイン, コンテキスト, ユビキタス言語
- 英語: domain, bounded context, ubiquitous language
- → `bounded-context-language`

### キャッシュ

- 日本語: キャッシュ, TTL, 無効化
- 英語: cache, TTL, invalidation
- → `cache-strategy-consistency`

### キャパシティ・コスト

- 日本語: コスト, キャパシティ, スケーリング
- 英語: cost, capacity, scaling
- → `capacity-cost-design`

### データフロー

- 日本語: データフロー, 状態管理, オーナーシップ
- 英語: data flow, state, ownership
- → `data-flow-state-ownership`

### データモデル

- 日本語: データモデル, DB, テーブル, スキーマ
- 英語: data model, database, table, schema
- → `data-model-db-design`

### DR・マルチリージョン

- 日本語: DR, 災害復旧, マルチリージョン
- 英語: DR, disaster recovery, multi-region
- → `dr-multiregion`

### イベント駆動

- 日本語: イベント駆動, メッセージ, Pub/Sub
- 英語: event-driven, message, pub/sub
- → `event-driven-semantics`

### 外部依存

- 日本語: 外部依存, サードパーティ, ライブラリ
- 英語: external dependency, third-party, library
- → `external-dependencies`

### 障害モード

- 日本語: 障害, 可観測性, アラート
- 英語: failure mode, observability, alert
- → `failure-modes-observability`

### 結合コントラクト

- 日本語: 結合, コントラクト, インターフェース
- 英語: integration, contract, interface
- → `integration-contracts`

### マイグレーション

- 日本語: マイグレーション, ロールアウト, ロールバック
- 英語: migration, rollout, rollback
- → `migration-rollout-rollback`

### マルチテナント

- 日本語: マルチテナント, テナント分離
- 英語: multi-tenant, tenant isolation
- → `multitenancy-isolation`

### OpenAPI

- 日本語: OpenAPI, Swagger, API仕様
- 英語: OpenAPI, Swagger, API spec
- → `openapi-contract`

### SLO・運用性

- 日本語: SLO, 運用性, オンコール
- 英語: SLO, operability, on-call
- → `operability-slo`

### 要件・受入

- 日本語: 要件, 受入条件, ストーリー
- 英語: requirement, acceptance criteria, story
- → `requirements-acceptance`

## フォールバックルール

1. 複数カテゴリに該当 → 最も変更量が多い領域を優先
2. 明示的指定あり → そのスキルを優先
3. 不明な場合 → `architecture-boundaries`（最も汎用的）
