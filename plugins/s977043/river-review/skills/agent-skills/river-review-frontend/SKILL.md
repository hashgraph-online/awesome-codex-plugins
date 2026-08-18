---
id: river-review-frontend
name: river-review-frontend
description: |
  フロントエンド観点のレビューエージェント。
  アクセシビリティ、デザインシステム準拠、Tailwind クラス衛生、UI 状態設計、
  Next.js / React Router のフレームワーク境界を個別スキルへルーティングする。
category: midstream
phase: [midstream]
severity: minor
applyTo:
  # ルーティング先 14 スキルの registry 上の applyTo の和集合（過剰に広いものは除く）。
  # app/ と src/routes/ は Next.js Route Handlers（route.ts）/ React Router resource
  # routes（JSX を含まない .ts/.js）を含むため拡張子を広げる（nextjs-app-router-boundary /
  # react-router-loader-boundary / react-router-action-contract の applyTo に一致）。
  # src/** 全体は {tsx,jsx,vue,svelte} に留める — .ts/.js へ広げるとバックエンド系 TS 差分
  # でも frontend エントリが発火し、river-review-code との二重発火を再導入するため。
  - 'src/**/*.{tsx,jsx,vue,svelte}'
  - 'src/routes/**/*.{ts,tsx,js,jsx}'
  - 'app/**/*.{ts,tsx,js,jsx}'
  - 'components/**/*.{ts,tsx,js,jsx}'
  - '**/*.{css,scss,less}'
  # loading-state（lib/packages）を完全解消、modern-web-a11y-interactive /
  # modern-web-semantic / modern-web-browser-compat の pages/** 分（ts/tsx/js/jsx）を
  # 部分解消（applyTo 包含検査 warning、#1508 系）。html/astro 系は意図的に据置き
  # （tailwind-class-hygiene 等、C 判定 — 追加しない）。
  - 'pages/**/*.{ts,tsx,js,jsx}'
  - 'lib/**/*.{ts,tsx,js,jsx}'
  - 'packages/**/*.{ts,tsx,js,jsx}'
# applyTo 包含検査（#1508）の意図的除外。ルーティング表に載るが本エントリの
# applyTo には含めないルーティング先を、理由付きで宣言する。
applyToExemptions:
  - skill: modern-web-performance
    reason: 参照のみ。Core Web Vitals の実行は river-review-performance に据置く（ROUTING.md「modern-web-performance の帰属について」）。本エントリの applyTo には含めない。
inputContext: [diff, fullFile]
outputKind: [findings, actions]
tags: [frontend, ui, accessibility, design-system, entry, routing]
version: 0.1.0
license: MIT
---

# Frontend Review（フロントエンドレビュー）

UI/コンポーネント変更に影響するアクセシビリティ、デザインシステム準拠、フレームワーク境界を検出し、適切な個別スキルで検証する。

> **`frontend-reviewer`（review-team perspective ロール）とは別物**: `src/lib/reviewer-orchestrator.mjs` の `frontend-reviewer` は review-team のマルチエージェントレビューで Claude/Codex が演じる perspective ロール（UI/component/styling ファイル検知時に自動追加）。本スキルは agent-skills ルーター群の一員で、キーワードから個別 registry skill へルーティングする別サーフェス。2つは独立して動作し、互いを呼び出さない。

## When to Use / いつ使うか

- UI コンポーネント・スタイリングの変更時
- アクセシビリティ（a11y）に関わる変更時
- デザインシステム・デザイントークンの準拠確認が必要なとき
- Tailwind クラスの衛生確認が必要なとき
- Next.js App Router / React Router のフレームワーク境界チェックが必要なとき
- 他の専門エージェント（architecture, security, performance, testing, code）に該当しない UI 固有の懸念があるとき

## Routing / ルーティング

| キーワード                                       | スキルID                        | 説明                                                                                          |
| ------------------------------------------------ | ------------------------------- | --------------------------------------------------------------------------------------------- |
| a11y, アクセシビリティ, alt属性, aria-label      | `a11y-accessible-name`          | アクセシビリティ基本                                                                          |
| キーボード操作, フォーカス管理, ARIA role        | `modern-web-a11y-interactive`   | インタラクティブ UI アクセシビリティ                                                          |
| セマンティック, div クリック, ネイティブ要素     | `modern-web-semantic`           | セマンティック HTML・プラットフォームネイティブ                                               |
| ブラウザ互換, Baseline, feature detection        | `modern-web-browser-compat`     | ブラウザ互換性・Baseline                                                                      |
| デザインシステム, コンポーネント再利用, Button   | `design-system-component-reuse` | デザインシステム コンポーネント再利用                                                         |
| デザイントークン, 色の直書き, 余白, 角丸         | `design-token-enforcement`      | デザイントークン                                                                              |
| DESIGN.md, デザイン定義準拠, スケール逸脱        | `design-source-conformance`     | デザイン Source-of-Truth 準拠                                                                 |
| Tailwind, 任意値, クラス衛生                     | `tailwind-class-hygiene`        | Tailwind クラス衛生                                                                           |
| ローディング, 空状態, スピナー, 状態欠落         | `loading-state`                 | ローディング状態遷移                                                                          |
| コンポーネントバリアント, hover, focus, disabled | `component-variants-states`     | コンポーネント状態の文書化                                                                    |
| Next.js, App Router, use client                  | `nextjs-app-router-boundary`    | Next.js App Router 境界                                                                       |
| React Router, loader, useEffect データ取得       | `react-router-loader-boundary`  | React Router loader 境界                                                                      |
| React Router, action, ErrorBoundary              | `react-router-action-contract`  | React Router action 契約                                                                      |
| Core Web Vitals, LCP, INP, CLS                   | `modern-web-performance`        | 参照のみ。実行は `river-review-performance`（[理由](#modern-web-performance-の帰属について)） |

### デフォルト動作

- キーワード指定なし → 以下のヒューリスティクスで判定:
  - React/Vue/Svelte コンポーネントファイル → `a11y-accessible-name` + `modern-web-a11y-interactive`
  - `app/` ディレクトリ（Next.js App Router）→ `nextjs-app-router-boundary`
  - `routes/` ディレクトリ（React Router）→ `react-router-loader-boundary` + `react-router-action-contract`
  - CSS/Tailwind ファイル → `design-token-enforcement` + `tailwind-class-hygiene`

### `modern-web-performance` の帰属について

14 候補スキルのうち `modern-web-performance`（Core Web Vitals / LCP / INP / CLS）は UI 起因の懸念だが、ドメイン一貫性を優先し実行は `river-review-performance` に据え置く（`river-review-performance/references/ROUTING.md` の「Core Web Vitals・Modern Web パフォーマンス」節）。本表には**到達性のための参照行**として掲載するのみで、frontend 側に重複するアクティブなキーワードルートは追加しない（同一キーワードが2ルーターで競合発火するリスクを避けるため）。

## Execution Flow / 実行フロー

```text
1. 変更内容の分類
   ├─ キーワード指定あり → 該当スキルを直接選択
   ├─ コンポーネントファイル → a11y-accessible-name + modern-web-a11y-interactive を優先
   ├─ app/ ディレクトリ → nextjs-app-router-boundary を追加
   ├─ routes/ ディレクトリ → react-router-loader-boundary + react-router-action-contract を追加
   └─ CSS/Tailwind ファイル → design-token-enforcement + tailwind-class-hygiene を追加

2. スキルの実行
   ├─ a11y-accessible-name: アクセシビリティ基本
   ├─ modern-web-a11y-interactive: インタラクティブ UI アクセシビリティ
   ├─ modern-web-semantic: セマンティック HTML・プラットフォームネイティブ
   ├─ modern-web-browser-compat: ブラウザ互換性・Baseline
   ├─ design-system-component-reuse: デザインシステム コンポーネント再利用
   ├─ design-token-enforcement: デザイントークン
   ├─ design-source-conformance: デザイン Source-of-Truth 準拠
   ├─ tailwind-class-hygiene: Tailwind クラス衛生
   ├─ loading-state: ローディング状態遷移
   ├─ component-variants-states: コンポーネント状態の文書化
   ├─ nextjs-app-router-boundary: Next.js App Router 境界
   ├─ react-router-loader-boundary: React Router loader 境界
   └─ react-router-action-contract: React Router action 契約

3. 統合
   ├─ 重複する指摘の除去
   └─ Checklistに基づく UI 品質チェックの補完
```

## Checklist / チェックリスト

フロントエンドレビューでは以下を確認する:

### アクセシビリティ

- alt / aria-label / label 関連付けが欠けていないか
- キーボード操作・フォーカス管理・ライブリージョンが機能するか
- セマンティックでない要素（div onClick 等）を native 要素に置き換えられないか

### デザインシステム / トークン

- 既存コンポーネント（Button / Input / Modal / Card 等）の再実装がないか
- 色・余白・フォントサイズ・角丸・シャドウがデザイントークン / DESIGN.md のスケールに準拠しているか
- Tailwind の任意値（arbitrary value）がテーマスケールを迂回していないか

### UI 状態設計

- loading / error / empty state の表示が欠けていないか
- コンポーネントの variants・インタラクティブ状態（hover / focus / disabled）が定義・文書化されているか

### フレームワーク境界

- Next.js App Router のサーバー/クライアントコンポーネント境界（`use client`）が適切か
- React Router の loader/action 契約（データ取得は loader、`useEffect` フェッチの誤用、action のエラー表現と ErrorBoundary）を満たすか

## Output Format / 出力形式

```text
<file>:<line>: <message>
```

- **Finding**: 何が問題か（1文）
- **Impact**: 何が困るか（短く）
- **Fix**: 次の一手（最小の修正案）

## 他スキルとの関係

| スキル                      | 関係 | 棲み分け                                                                                                     |
| --------------------------- | ---- | ------------------------------------------------------------------------------------------------------------ |
| `river-review-code`         | 補完 | frontend は「UI 固有の懸念」、code は「一般コード品質」。UI 系ルートは frontend に一元化済み（二重発火なし） |
| `river-review-performance`  | 補完 | frontend は「UI 表現」、performance は「実行効率」。`modern-web-performance` は performance に据置           |
| `river-review-architecture` | 補完 | frontend は「コンポーネント単位」、architecture は「マクロ設計」                                             |

## References

- [ROUTING.md](./references/ROUTING.md): 詳細なルーティングルール
- [UX-SAFEGUARD.md](../river-review-code/references/UX-SAFEGUARD.md): 破壊的操作の確認・取り消し / エラー回復支援の report-only 参照観点（`river-review-code` に据置、#1460）。`loading-state` / `component-variants-states` / `react-router-action-contract` の委譲表を含む
