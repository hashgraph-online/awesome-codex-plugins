---
id: river-review-code
name: river-review-code
description: |
  一般コード品質のレビューエージェント。デフォルトのフォールバック先。
  可読性、保守性、型安全性、ロギング等の個別スキルへルーティングする。
category: midstream
phase: [midstream]
severity: minor
applyTo:
  # ルーティング先（typescript-strict / typescript-nullcheck / type-driven-design /
  # logging-observability / altitude-generalization / closure-scope-retention）の
  # applyTo 包含検査 warning 解消（#1508 系）。scripts/**・runners/** はこのリポジトリ
  # 自身に実在する自己参照ギャップ（#1494/#1500 と同型）、app/lib/packages/** は
  # #1500 の precedent 準拠。
  - 'src/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'app/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'lib/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'packages/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'scripts/**/*.{ts,tsx,js,jsx,mjs,cjs}'
  - 'runners/**/*.{ts,tsx,js,jsx,mjs,cjs}'
inputContext: [diff, fullFile]
outputKind: [findings, actions]
tags: [code-quality, default, entry, routing]
version: 0.1.0
license: MIT
---

# Code Quality Review（一般コード品質レビュー）

コードの可読性、保守性、型安全性を検証する。他の専門エージェントに該当しない場合のデフォルトフォールバック先。

## When to Use / いつ使うか

- 一般的なコード変更のレビュー時
- 他の専門エージェント（architecture, security, performance, testing）に該当しない場合
- コード品質の総合的なチェックが必要な場合

## Routing / ルーティング

| キーワード                 | スキルID                         | 説明                         |
| -------------------------- | -------------------------------- | ---------------------------- |
| 型, TypeScript, strict     | `typescript-strict`              | TypeScript strict モード準拠 |
| null, undefined, optional  | `typescript-nullcheck`           | null 安全性チェック          |
| 非同期, await, Promise     | `async-correctness`              | 非同期処理の正しさ検証       |
| 型駆動, 設計               | `type-driven-design`             | 型駆動設計                   |
| ログ, 監視                 | `logging-observability`          | ロギング・可観測性           |
| 自動化, 境界               | `review-automation-boundary`     | レビュー自動化の境界         |
| コメント, トリアージ       | `review-comment-triage`          | レビューコメント分類         |
| 幻覚的参照, 実在確認       | `hallucinated-reference`         | 新規参照の実在確認           |
| 簡素化, 整理, simplify     | SIMPLIFY 観点（本 skill 内）     | 品質クリーンアップ4観点      |
| 破壊的操作, undo, 回復支援 | UX-SAFEGUARD 観点（本 skill 内） | 操作の安全装置2観点          |

> UI/コンポーネント系のルーティング（a11y, デザインシステム, Next.js App Router 境界等）は `river-review-frontend` に一元化済み（#1462）。本ルーターからは移設し、二重発火を避けている。

### デフォルト動作

- キーワード指定なし → 以下のヒューリスティクスで判定:
  - `.ts`/`.tsx`ファイル → TypeScript strict + nullチェック
  - コンポーネントファイル → `river-review-frontend` も参照（a11y・デザインシステム観点は frontend 側が担当）
  - 設定ファイル → 型駆動設計チェック

## Checklist / チェックリスト

一般コードレビューでは以下を確認する:

### 可読性

- 関数・変数の命名が意図を表現しているか
- 意図を伝えない広すぎる名前（`data` / `info` / `manager` / `handler` / `util` / `current`）、共有されていない略語、同一概念の別名（または別概念の同名）がないか
- 関数の責務が単一か
- ネストが深すぎないか（3段以内。深い場合は guard clause で平坦化を提案）
- マジックナンバー・マジックストリングがないか

### 保守性

- DRY原則にしたがっているか（ただし過度な抽象化を避ける）
- 変更の影響範囲が限定的か
- 依存方向が正しいか
- カプセル化リークがないか: オブジェクト内部へ深く手を伸ばすコード（`a.b.c.type === 'x'`）、値オブジェクトから primitive を取り出して外部で分岐、getter による内部状態の露出。Tell-Don't-Ask（例: `user.subscription.plan.type === 'premium'` より `user.isPremium()`）を推奨する（Law of Demeter）

### 型安全性

- `any`の使用が最小限か
- 型ガードが適切か
- null/undefinedの扱いが安全か
- 型検査対象外の分界（#1476）: `scripts/`（tsconfig の `include` に含まれず tsc 検査対象外）の JSDoc で `unknown` を `any` へ緩める提案はしない。`unknown` は呼び出し側に絞り込みを強制する意図的で保守的な選択。詳細と canary は `existing-pattern-conformance` の「False-positive guards」を参照。

### エラーハンドリング

- エラーを握り潰していないか
- エラーメッセージが十分な情報を含むか
- リカバリー可能なエラーと不可能なエラーの区別
- 防衛的フォールバックの分界（#1480 FP / #1475 本物）: モジュール内部の不変条件（config・registry・内部で構築した構造の欠落 = fail-fast が意図）へ `?? {}` 等の防衛は提案しない。外部 IO・環境境界（`argv` / `fs` / network）の例外・null には防衛必須。詳細と canary は `nullability-contract` の「False-positive guards」を参照。

## Execution Flow / 実行フロー

```text
1. ファイル種別の判定
   ├─ .ts/.tsxファイル → TypeScript strict + nullチェックを選択
   ├─ コンポーネントファイル → river-review-frontend も参照（a11y・デザインシステム観点）
   ├─ 設定ファイル → 型駆動設計チェックを選択
   └─ キーワード指定あり → 該当スキルを直接選択
      （SIMPLIFY / UX-SAFEGUARD 観点のキーワード該当時は本 skill 内で実行。キーワードは ROUTING.md を参照）

2. スキルの実行
   ├─ typescript-strict: strictモード準拠
   ├─ typescript-nullcheck: null安全性
   ├─ async-correctness: 非同期処理の正しさ
   ├─ type-driven-design: 型駆動設計
   ├─ logging-observability: ロギング・可観測性
   ├─ review-automation-boundary: レビュー自動化の境界
   └─ hallucinated-reference: 新規参照の実在確認

3. 統合
   ├─ 重複する指摘の除去
   └─ Checklistに基づく一般品質チェックの補完
```

## Multi-perspective Execution / 多観点実行（旧 agent-code-review から統合）

複数観点を横断するレビューでは、以下の順で差分を走査し findings を統合する。

| 順序 | 観点           | 実行ルール                                                             |
| ---- | -------------- | ---------------------------------------------------------------------- |
| 1    | セキュリティ   | Critical finding 検出時: 以降の観点も実行するが、Critical を先頭に出力 |
| 2    | パフォーマンス | ホットパス外の変更のみの場合はスキップ可                               |
| 3    | 品質・設計     | 常に実行                                                               |
| 4    | テスト網羅性   | テストファイルが差分に含まれない場合も、対象コードのテスト有無を確認   |

観点間の重要度比較: 異なる観点の findings が同一箇所を指す場合、severity が異なれば高い方を採用（もう一方は補足として併記）、同じなら security > performance > quality > testing の順で先に記載する。

出力件数の制約: 1 PR あたり最大 15 件（超過分は severity 降順で切り捨て、切り捨て件数を末尾に記載）。同一ファイルへの同一観点の指摘は最大 3 件にグルーピングする。

判定の手がかり:

- `catch` ブロック内の空文、`// TODO` → security / quality
- `O(n*m)` パターン、ループ内の DB / API コール → performance
- `any` 型、型アサーション（`as`）、未使用 import → quality
- 新規 export 関数にテストファイル内の対応する `describe` / `test` がない → testing

## Output Format / 出力形式

```text
<file>:<line>: <message>
```

- **Finding**: 何が問題か（1文）
- **Impact**: 何が困るか（短く）
- **Fix**: 次の一手（最小の修正案）

## 他スキルとの関係

| スキル                      | 関係 | 棲み分け                                                                                            |
| --------------------------- | ---- | --------------------------------------------------------------------------------------------------- |
| `river-review-architecture` | 補完 | code は「ミクロ品質」、architecture は「マクロ設計」                                                |
| `river-review-testing`      | 補完 | code は「プロダクションコード」、testing は「テストコード」                                         |
| `river-review-performance`  | 補完 | code は「可読性」、performance は「実行効率」                                                       |
| `river-review-frontend`     | 補完 | code は「一般コード品質」、frontend は「UI 固有の懸念」。UI 系ルートは frontend へ移設済み（#1462） |

## References

- [ROUTING.md](./references/ROUTING.md): 詳細なルーティングルール
- [SIMPLIFY.md](./references/SIMPLIFY.md): 品質クリーンアップ4観点の実行手順と委譲表
- [UX-SAFEGUARD.md](./references/UX-SAFEGUARD.md): 操作の安全装置2観点（破壊的操作の確認・取り消し / 入力エラーの回復支援）の実行手順と委譲表
