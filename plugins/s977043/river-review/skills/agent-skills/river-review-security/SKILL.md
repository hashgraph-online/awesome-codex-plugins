---
id: river-review-security
name: river-review-security
description: |
  セキュリティ観点のレビューエージェント。
  基本的なセキュリティチェック、認証・認可設計、プライバシー設計の個別スキルへルーティングする。
category: midstream
phase: [midstream]
severity: critical
applyTo:
  - 'src/**/*.{ts,tsx,js,jsx,mjs}'
  - '**/*.env*'
  - '**/auth/**/*'
  - '**/middleware/**/*'
inputContext: [diff, fullFile]
outputKind: [findings, actions]
tags: [security, entry, routing]
version: 0.1.0
license: MIT
---

# Security Review（セキュリティレビュー）

セキュリティに影響する変更を検出し、適切な個別スキルで検証する。

## When to Use / いつ使うか

- 認証・認可に関わるコード変更時
- 外部入力の処理ロジック変更時
- 機密データの取り扱い変更時
- セキュリティ関連の設定変更時

## Routing / ルーティング

| キーワード                          | スキルID                  | 説明                     |
| ----------------------------------- | ------------------------- | ------------------------ |
| 脆弱性, XSS, SQLi, インジェクション | `security-basic`          | 基本セキュリティチェック |
| プライバシー, 個人情報, GDPR        | `security-privacy-design` | プライバシー設計         |
| 認可, 権限, アクセス制御            | `trust-boundaries-authz`  | 信頼境界・認可設計       |

### デフォルト動作

- キーワード指定なし → `security-basic` を実行
- セキュリティ関連ファイル（auth/, middleware/）→ 全スキル実行

## Execution Flow / 実行フロー

```text
1. 変更内容の分類
   ├─ 認証・認可コード → trust-boundaries-authz を優先
   ├─ データ処理コード → security-privacy-design を優先
   └─ 一般コード → security-basic を実行

2. 各スキルの実行
   ├─ security-basic: OWASP Top 10チェック
   ├─ security-privacy-design: プライバシー影響分析
   └─ trust-boundaries-authz: 認可モデル検証

3. 統合サマリの生成
```

## Output Format / 出力形式

```text
<file>:<line>: <message>
```

- **Finding**: 何が問題か（1文）
- **Severity**: critical / major / minor
- **Impact**: 何が困るか（短く）
- **Fix**: 次の一手（最小の修正案）

## 他スキルとの関係

| スキル                          | 関係 | 棲み分け                                                   |
| ------------------------------- | ---- | ---------------------------------------------------------- |
| `adversarial-review` (War Game) | 補完 | security は既知パターン検出、War Game は未知の攻撃経路発見 |
| `river-review-architecture`     | 補完 | security は「脆弱性」、architecture は「構造的安全性」     |

## References

- [ROUTING.md](./references/ROUTING.md): 詳細なルーティングルール
