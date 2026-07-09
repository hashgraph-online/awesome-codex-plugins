---
id: river-review-testing
name: river-review-testing
description: |
  テスト観点のレビューエージェント。
  テスト網羅性、命名規則、フレーキーテスト、カバレッジギャップの個別スキルへルーティングする。
category: downstream
phase: [downstream]
severity: minor
applyTo:
  - '**/*.test.{ts,tsx,js,jsx}'
  - '**/*.spec.{ts,tsx,js,jsx}'
  - 'tests/**/*'
  - 'test/**/*'
  - '__tests__/**/*'
inputContext: [diff, fullFile, tests]
outputKind: [findings, actions]
tags: [testing, coverage, entry, routing]
version: 0.1.0
license: MIT
---

# Testing Review（テストレビュー）

テストコードの品質、網羅性、安定性を検証する。

## When to Use / いつ使うか

- テストファイルの追加・変更時
- テスト対象コードの変更時（テストの更新漏れ検出）
- テスト戦略の見直し時

## Routing / ルーティング

| キーワード           | スキルID           | 説明                   |
| -------------------- | ------------------ | ---------------------- |
| カバレッジ, 網羅     | `coverage-gap`     | カバレッジギャップ検出 |
| フレーキー, 不安定   | `flaky-test`       | フレーキーテストリスク |
| テスト有無, 存在     | `test-existence`   | テスト存在確認         |
| 命名, 構造, describe | `test-naming`      | テスト命名・構造       |
| テスト観点, 計画     | `test-plan-review` | テスト観点レビュー     |

### デフォルト動作

- テストファイルの変更 → `test-naming` + `flaky-test`
- ソースコードの変更 → `test-existence` + `coverage-gap`
- 大規模変更 → 全スキル実行

## Execution Flow / 実行フロー

```text
1. 変更ファイルの分類
   ├─ テストファイル → 品質チェック（命名、フレーキー）
   ├─ ソースファイル → 網羅性チェック（存在、カバレッジ）
   └─ 両方 → 全スキル実行

2. 各スキルの実行
   ├─ test-existence: テストの存在確認
   ├─ coverage-gap: カバレッジギャップ検出
   ├─ test-naming: 命名・構造検証
   ├─ flaky-test: フレーキーリスク検出
   └─ test-plan-review: テスト観点の妥当性

3. 統合サマリの生成
```

## Output Format / 出力形式

```text
<file>:<line>: <message>
```

- **Finding**: 何が問題か（1文）
- **Impact**: 何が困るか（短く）
- **Fix**: 次の一手（最小の修正案）

## 他スキルとの関係

| スキル                  | 関係 | 棲み分け                                                          |
| ----------------------- | ---- | ----------------------------------------------------------------- |
| `river-review-code`     | 補完 | testing は「テストの品質」、code は「プロダクションコードの品質」 |
| `river-review-security` | 補完 | testing は「テスト網羅性」、security は「セキュリティ脆弱性」     |

## References

- [ROUTING.md](./references/ROUTING.md): 詳細なルーティングルール
