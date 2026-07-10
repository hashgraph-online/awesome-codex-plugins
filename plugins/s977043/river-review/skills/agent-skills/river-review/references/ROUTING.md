# ルーティングルール

River Review のルーティングロジックの詳細です。

## キーワードマッチング

以下のキーワードに基づいて専門スキルを選択します：

### 設計・アーキテクチャ (river-review-architecture)

- 日本語: 設計, アーキテクチャ, ADR, 構成, モジュール, 依存関係
- 英語: design, architecture, ADR, structure, module, dependency

### セキュリティ (river-review-security)

- 日本語: セキュリティ, 脆弱性, 認証, 認可, 暗号化
- 英語: security, vulnerability, auth, authorization, encryption

### パフォーマンス (river-review-performance)

- 日本語: パフォーマンス, 最適化, 高速化, メモリ, キャッシュ
- 英語: performance, optimization, speed, memory, cache

### テスト (river-review-testing)

- 日本語: テスト, カバレッジ, 単体テスト, 結合テスト
- 英語: test, coverage, unit test, integration test

### 敵対的レビュー (adversarial-review)

- 日本語: 敵対的, 壁打ち, プレモーテム, 失敗分析, 攻撃, ウォーゲーム, 論理検証, バイアス
- 英語: adversarial, challenge, pre-mortem, war-game, logic, bias, devil's advocate

### ドキュメント (river-review-docs)

- 日本語: ドキュメント, ドキュメンテーション, README, 翻訳, i18n, 用語, 整合性, 使い方
- 英語: docs, documentation, README, translation, i18n, terminology, consistency, usage

### 一般コード (river-review-code) - デフォルト

上記のいずれにも該当しない場合、一般コードレビューを実行します。

## 優先度解決ルール

### 1. 明示指定（最優先）

ユーザーが観点名を直接指定した場合、そのカテゴリを最優先で選択する。

判定基準: 入力に「〜観点で」「〜の視点で」「〜を重点的に」が含まれ、かつ特定カテゴリのキーワードと結合している場合。

### 2. 複数カテゴリ該当時の重み付け

キーワードが複数カテゴリにマッチした場合、以下の順で優先度を決定する:

| 優先度 | 条件                                   | 例                                           |
| ------ | -------------------------------------- | -------------------------------------------- |
| 1      | severityがcritical/majorのカテゴリ     | セキュリティ(major) > テスト(minor)          |
| 2      | マッチしたキーワード数が多いカテゴリ   | 「脆弱性と認証」(2) > 「設計」(1)            |
| 3      | 入力テキスト内で後方に出現するカテゴリ | 「設計の**セキュリティ**」→ セキュリティ優先 |

同点の場合: 両カテゴリのスキルを併用実行する。

### 3. フォールバック

上記いずれにも該当しない場合 → `river-review-code`（一般コードレビュー）。

### 4. ルーティング通知

ルーティング結果をユーザーに1行で通知する:

```text
→ [river-review-security] にルーティングしました（理由: 「脆弱性」キーワード検出）
```

ユーザーが修正を求めた場合は即座にリルートする。
