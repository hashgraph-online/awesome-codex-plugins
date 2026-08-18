# ルーティングルール — Frontend Review

対象 14 スキル（UI 系 11 + フレームワーク固有 3）の routing 表。Issue #1462 案B（`river-review-frontend` 新設）の実装。

## キーワードマッチング

### アクセシビリティ

- 日本語: a11y, アクセシビリティ, スクリーンリーダー
- 英語: a11y, accessibility, screen reader, aria
- → `a11y-accessible-name`

### アクセシビリティ（アクセシブルネーム）

- 日本語: alt属性, aria-label, アクセシブルネーム, ボタンラベル, フォームラベル
- 英語: alt text, aria-label, accessible name, button label, form label
- → `a11y-accessible-name`

### インタラクティブ UI アクセシビリティ

- 日本語: キーボード操作, フォーカス管理, ARIA role, ライブリージョン
- 英語: keyboard navigation, focus management, ARIA role, live region, interactive UI
- → `modern-web-a11y-interactive`

### セマンティック HTML・プラットフォームネイティブ

- 日本語: セマンティック, div クリック, ネイティブ要素, Web Platform
- 英語: semantic HTML, div onclick, platform-native, Web Platform, native API
- → `modern-web-semantic`

### ブラウザ互換性・Baseline

- 日本語: ブラウザ互換, Baseline, プログレッシブエンハンスメント, feature detection
- 英語: browser compatibility, Baseline, progressive enhancement, feature detection, @supports
- → `modern-web-browser-compat`

### デザインシステム コンポーネント再利用

- 日本語: デザインシステム, コンポーネント再利用, Button, Input, Modal, Card
- 英語: design system, component reuse, Button, Input, Modal, Card
- → `design-system-component-reuse`

### デザイントークン

- 日本語: デザイントークン, 色の直書き, 余白, フォントサイズ, 角丸
- 英語: design token, hardcoded color, spacing, font size, border radius
- → `design-token-enforcement`

### デザイン Source-of-Truth 準拠

- 日本語: DESIGN.md, デザイン定義, デザイン準拠, スケール逸脱
- 英語: design source of truth, design spec conformance, design token scale, design definition
- → `design-source-conformance`
- 注意: リポジトリに `DESIGN.md` やデザイントークン定義が存在しない場合は実行しない（registry description 準拠）。「色・余白の直書き」単体の一般チェックは `design-token-enforcement` が担う。本スキルは**定義済みスケールとの照合**（定義がある場合のみ）に限定する

### Tailwind クラス衛生

- 日本語: Tailwind, クラス衛生, 任意値, 重複ユーティリティ
- 英語: Tailwind, arbitrary value, class hygiene, conflicting utility, hardcoded color
- → `tailwind-class-hygiene`

### ローディング状態遷移

- 日本語: ローディング, 空状態, スピナー, 状態欠落, 読み込み中
- 英語: loading state, empty state, spinner, missing state handling
- → `loading-state`
- 注意: エラー表示は存在するが**回復方法を示さない文言**は UX-SAFEGUARD 観点（[river-review-code/references/UX-SAFEGUARD.md](../../river-review-code/references/UX-SAFEGUARD.md)、`river-review-code` に据置）に委譲済み。本スキルは loading/error/empty state の**表示欠落そのもの**を扱う

### コンポーネント状態の文書化

- 日本語: コンポーネントバリアント, variants, hover, focus, disabled, 状態文書化
- 英語: component variants, interactive states, hover, focus, disabled, loading, error state
- → `component-variants-states`
- 注意: 状態は定義済みだが破壊的操作に確認ステップがないケースは UX-SAFEGUARD 観点に委譲済み。本スキルは variants・インタラクティブ状態の**定義・文書化の欠落**を扱う

### Next.js App Router 境界

- 日本語: Next.js, App Router, サーバーコンポーネント, クライアントコンポーネント, use client
- 英語: Next.js, App Router, server component, client component, use client directive
- → `nextjs-app-router-boundary`

### React Router loader 境界

- 日本語: React Router, loader, useEffect データ取得, ルート境界, server/client リーク
- 英語: React Router, Remix, loader, useEffect data fetching, route boundary, server/client leak
- → `react-router-loader-boundary`

### React Router action 契約

- 日本語: React Router, action, バリデーションエラー, リダイレクト, ErrorBoundary
- 英語: React Router action, validation error, 4xx, redirect on success, ErrorBoundary
- → `react-router-action-contract`
- 注意: React Router action のエラー表示の**回復支援文言**（フレームワーク非依存の部分）は UX-SAFEGUARD 観点に委譲済み。本スキルは action の**規約（4xx / redirect / 3分岐 ErrorBoundary）**を扱う

### Core Web Vitals・Modern Web パフォーマンス（参照のみ）

- 日本語: Core Web Vitals, LCP, INP, CLS, リソースコスト
- 英語: Core Web Vitals, LCP, INP, CLS, resource cost
- → 実行は `river-review-performance`（[river-review-performance/references/ROUTING.md](../../river-review-performance/references/ROUTING.md) の「Core Web Vitals・Modern Web パフォーマンス」節）に据置。ドメイン一貫性（実行効率観点は performance に統一）を優先し、本ルーターにはアクティブなキーワードルートを追加しない。14 候補スキルとしての到達性のみ本表に記載する

## 自動判定ルール

1. React/Vue/Svelte コンポーネントファイル → `a11y-accessible-name` + `modern-web-a11y-interactive` を追加
2. `app/` ディレクトリ（Next.js App Router）→ `nextjs-app-router-boundary` を追加
3. `routes/` ディレクトリ（React Router）→ `react-router-loader-boundary` + `react-router-action-contract` を追加
4. CSS / Tailwind 設定ファイル → `design-token-enforcement` + `tailwind-class-hygiene` を追加

## フォールバックルール

1. キーワード指定なし → 変更ファイルの拡張子とパスで自動判定
2. 複数該当 → 関連する全スキル実行
3. 判定不能 → 一般的な UI 品質チェックリスト（SKILL.md のチェックリスト）を適用

## `river-review-code` からの移設について

以下 7 スキルは `river-review-code`（旧デフォルトフォールバック）の keyword routing から本ルーターへ移設した（二重発火を避けるため `river-review-code/references/ROUTING.md` から該当節を削除済み）:

- `a11y-accessible-name`（2節）
- `modern-web-a11y-interactive`
- `modern-web-semantic`
- `modern-web-browser-compat`
- `design-system-component-reuse`
- `design-token-enforcement`
- `nextjs-app-router-boundary`

SIMPLIFY / UX-SAFEGUARD 観点（report-only 参照観点）は `river-review-code` に据置（#1460、ADR-004）。本 PR では移動しない。
