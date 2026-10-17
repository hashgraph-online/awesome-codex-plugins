# ルーティングルール — Security Review

## Audit handoff（最優先）

通常の PR / diff security review と repository / subsystem security audit を分離する。

以下の条件を満たす場合は `river-review-security-audit` へ委譲する。

- repository-wide / repo-wide / full security audit が明示されている
- subsystem / component / bounded path を対象に security audit を依頼している
- 「リポジトリ全体をセキュリティ監査」「認証サブシステムを監査」など、現在の diff を越える audit scope が明示されている

次の場合は委譲しない。

- 「この PR をセキュリティ観点でレビュー」
- 「この差分に脆弱性がないか確認」
- 単に security / vulnerability キーワードがあるだけで audit scope が明示されていない

`security audit` という語だけで `full-audit` を推測しない。
対象範囲が曖昧な場合は通常の `river-review-security` を継続する。

## キーワードマッチング

### 基本セキュリティ

- 日本語: 脆弱性, XSS, SQLインジェクション, CSRF, インジェクション, サニタイズ
- 英語: vulnerability, XSS, SQL injection, CSRF, injection, sanitize
- → `security-basic`

### プライバシー設計

- 日本語: プライバシー, 個人情報, GDPR, PII, データ保護
- 英語: privacy, personal data, GDPR, PII, data protection
- → `security-privacy-design`

### 信頼境界・認可

- 日本語: 認可, 権限, アクセス制御, 信頼境界, RBAC
- 英語: authorization, permission, access control, trust boundary, RBAC
- → `trust-boundaries-authz`

## フォールバックルール

1. 明示的な repository / subsystem audit → `river-review-security-audit` へ委譲
2. キーワード指定なし → `security-basic`
3. 認証・認可ファイルの変更 → `trust-boundaries-authz` を追加
4. 個人情報の取り扱い → `security-privacy-design` を追加
5. 複数該当 → 全スキル実行
