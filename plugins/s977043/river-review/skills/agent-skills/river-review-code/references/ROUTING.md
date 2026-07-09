# ルーティングルール — Code Quality Review

## キーワードマッチング

### TypeScript strict

- 日本語: 型, TypeScript, strict, 型安全
- 英語: type, TypeScript, strict, type safety
- → `typescript-strict`

### null チェック

- 日本語: null, undefined, optional, 未定義
- 英語: null, undefined, optional, nullable
- → `typescript-nullcheck`

### 型駆動設計

- 日本語: 型駆動, 設計, 型で表現
- 英語: type-driven, design, express with types
- → `type-driven-design`

### ロギング

- 日本語: ログ, 監視, トレース
- 英語: log, monitoring, trace
- → `logging-observability`

### レビュー自動化

- 日本語: 自動化, 境界, 人間判断
- 英語: automation, boundary, human judgment
- → `review-automation-boundary`

### コメントトリアージ

- 日本語: コメント, トリアージ, 優先度
- 英語: comment, triage, priority
- → `review-comment-triage`

### アクセシビリティ

- 日本語: a11y, アクセシビリティ, スクリーンリーダー
- 英語: a11y, accessibility, screen reader, aria
- → `a11y-accessible-name`

### アクセシビリティ（アクセシブルネーム）

- 日本語: alt属性, aria-label, アクセシブルネーム, ボタンラベル, フォームラベル
- 英語: alt text, aria-label, accessible name, button label, form label
- → `a11y-accessible-name`

### デザインシステム コンポーネント再利用

- 日本語: デザインシステム, コンポーネント再利用, Button, Input, Modal, Card
- 英語: design system, component reuse, Button, Input, Modal, Card
- → `design-system-component-reuse`

### デザイントークン

- 日本語: デザイントークン, 色の直書き, 余白, フォントサイズ, 角丸
- 英語: design token, hardcoded color, spacing, font size, border radius
- → `design-token-enforcement`

### レビュー統合（マルチエージェント）

- 日本語: レビュー統合, 複数レビュー, マージ推奨, ハルシネーション検証
- 英語: review synthesis, multi-agent, merge recommendation, hallucination guard
- → `independent-review-synthesis`

### インタラクティブ UI アクセシビリティ

- 日本語: キーボード操作, フォーカス管理, ARIA role, ライブリージョン
- 英語: keyboard navigation, focus management, ARIA role, live region, interactive UI
- → `modern-web-a11y-interactive`

### ブラウザ互換性・Baseline

- 日本語: ブラウザ互換, Baseline, プログレッシブエンハンスメント, feature detection
- 英語: browser compatibility, Baseline, progressive enhancement, feature detection, @supports
- → `modern-web-browser-compat`

### セマンティック HTML・プラットフォームネイティブ

- 日本語: セマンティック, div クリック, ネイティブ要素, Web Platform
- 英語: semantic HTML, div onclick, platform-native, Web Platform, native API
- → `modern-web-semantic`

### Next.js App Router 境界

- 日本語: Next.js, App Router, サーバーコンポーネント, クライアントコンポーネント, use client
- 英語: Next.js, App Router, server component, client component, use client directive
- → `nextjs-app-router-boundary`

## 自動判定ルール

1. `.ts`/`.tsx` ファイル → `typescript-strict` + `typescript-nullcheck`
2. React コンポーネント → `a11y-accessible-name` を追加
3. `app/` ディレクトリ（Next.js）→ `nextjs-app-router-boundary` を追加
4. 設定・型定義ファイル → `type-driven-design`

## フォールバックルール

1. キーワード指定なし → 変更ファイルの拡張子とパスで自動判定
2. 複数該当 → 関連する全スキル実行
3. 判定不能 → 一般的なコード品質チェックリスト（SKILL.md のチェックリスト）を適用
