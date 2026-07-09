# ルーティングルール — Security Review

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

1. キーワード指定なし → `security-basic`
2. 認証・認可ファイルの変更 → `trust-boundaries-authz` を追加
3. 個人情報の取り扱い → `security-privacy-design` を追加
4. 複数該当 → 全スキル実行
