# セキュリティポリシー (Security Policy)

## 脆弱性の報告 (Reporting a Vulnerability)

River Review に関する脆弱性の可能性を見つけた場合は、公開 Issue や PR には投稿せず、GitHub のプライベート脆弱性報告機能から非公開で報告してください。

- 報告フォーム: [https://github.com/s977043/river-review/security/advisories/new](https://github.com/s977043/river-review/security/advisories/new)
- UI から辿る場合: リポジトリの `Security` タブ → `Advisories` → `Report a vulnerability`
- 公開済みセキュリティアドバイザリ: [https://github.com/s977043/river-review/security/advisories](https://github.com/s977043/river-review/security/advisories)

可能であれば、PoC、影響範囲、再現手順、想定される悪用シナリオ、暫定回避策を含めてください。

If you believe you have found a security vulnerability, please do not file a public issue or pull request. Instead, report it privately via GitHub's private vulnerability reporting:

- Report form: [security/advisories/new](https://github.com/s977043/river-review/security/advisories/new)

## 対応方針 (Our Process)

- 受領確認と初期トリアージを行い、必要に応じて追加情報をお願いする場合があります
- 影響範囲と深刻度に応じて、修正版の準備と公開（リリースノート等）を行います
- 公開前の情報共有は、最小限の関係者のみに限定します

## サポート範囲 (Supported Versions)

- 現時点では、`main` ブランチと最新リリースを優先して対応します

## 静的・動的解析 (Static and Dynamic Analysis)

このプロジェクトでは、以下のオープンソースツールによるコード品質・セキュリティチェックを継続的に実施しています。

### 静的解析 (Static Analysis)

- `npm audit` — npm レジストリの Advisory データベースを用いた依存関係の脆弱性スキャン（nightly CI で自動実行）
- `markdownlint` — Markdown ソースの静的解析
- `textlint` — ドキュメントの文章品質チェック
- `prettier` — コードフォーマット一貫性の検証

### 動的解析 (Dynamic Analysis)

- `node --test` — Node.js 組み込みテストランナーによる自動テスト。Node.js/V8 のメモリ管理（GC・バッファ境界チェック）に依存し、実行時のメモリ安全性を確保している。
