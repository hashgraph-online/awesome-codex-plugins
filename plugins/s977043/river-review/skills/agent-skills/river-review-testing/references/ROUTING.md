# ルーティングルール — Testing Review

## キーワードマッチング

### カバレッジギャップ

- 日本語: カバレッジ, 網羅, 未テスト, テスト不足
- 英語: coverage, gap, untested, missing test
- → `coverage-gap`

### フレーキーテスト

- 日本語: フレーキー, 不安定, ランダム失敗, タイムアウト
- 英語: flaky, unstable, random failure, timeout
- → `flaky-test`

### テスト存在確認

- 日本語: テスト有無, テスト存在, テスト漏れ
- 英語: test existence, test presence, missing test
- → `test-existence`

### テスト命名・構造

- 日本語: 命名, 構造, describe, it, テスト名
- 英語: naming, structure, describe, it, test name
- → `test-naming`

### テスト観点レビュー

- 日本語: テスト観点, テスト計画, テスト戦略, エッジケース
- 英語: test plan, test strategy, edge case, test perspective
- → `test-plan-review`

## 自動判定ルール

1. テストファイルのみ変更 → `test-naming` + `flaky-test`
2. ソースファイルのみ変更 → `test-existence` + `coverage-gap`
3. テスト + ソース両方 → 全スキル実行
4. 10ファイル以上の変更 → `test-plan-review` を追加

## フォールバックルール

1. キーワード指定なし → 変更ファイルの種類で自動判定
2. 複数該当 → 全スキル実行
3. テスト関連ファイルなし → `test-existence` のみ実行
