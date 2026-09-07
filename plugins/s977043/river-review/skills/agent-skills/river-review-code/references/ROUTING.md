# ルーティングルール — Code Quality Review

> UI/コンポーネント系のキーワード（a11y, デザインシステム, デザイントークン, ブラウザ互換, セマンティック HTML, Next.js App Router 境界）は `river-review-frontend` の [ROUTING.md](../../river-review-frontend/references/ROUTING.md) へ移設済み（#1462）。本ファイルには残さず、二重発火を避ける。

## キーワードマッチング

### TypeScript strict

- 日本語: 型, TypeScript, strict, 型安全
- 英語: type, TypeScript, strict, type safety
- → `typescript-strict`

### null チェック

- 日本語: null, undefined, optional, 未定義
- 英語: null, undefined, optional, nullable
- → `typescript-nullcheck`

### 非同期処理の正しさ

- 日本語: 非同期, await 漏れ, Promise, 競合, レースコンディション
- 英語: async, await, floating promise, race condition, unhandled rejection
- → `async-correctness`
- 注意: 逐次 await の**並列化提案**は SIMPLIFY 観点 Efficiency、**配線断点**（発火しっぱなしで経路が途切れる）は `e2e-wiring` が担う。本スキルは「await を忘れて結果・順序・エラー伝播が壊れる」correctness のみ

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

### レビュー統合（マルチエージェント）

- 日本語: レビュー統合, 複数レビュー, マージ推奨, ハルシネーション検証
- 英語: review synthesis, multi-agent, merge recommendation, hallucination guard
- → `independent-review-synthesis`

### 品質クリーンアップ（SIMPLIFY 観点）

- 日本語: 簡素化, 重複コード, デッドコード, 整理, 無駄, 車輪の再発明
- 英語: simplify, duplication, dead code, cleanup, reinvent
- → SIMPLIFY 観点を本 skill 内で実行（[SIMPLIFY.md](./SIMPLIFY.md) の品質クリーンアップ4観点）
- 注意: 「リファクタ」単独は adversarial-review の `refactor-claim-audit`（完了主張の反証）に割り当て済みのため、本観点のキーワードにしない。リファクタの**完了主張の検証**は adversarial-review、**差分の簡素化余地の検出**は本観点が担う
- 注意: Altitude の caller special-case 検出と Efficiency の closure 保持検出は registry skill へ委譲済み（下記2セクション）。SIMPLIFY 観点は残余のみを扱う（[SIMPLIFY.md](./SIMPLIFY.md) の委譲表参照）

### 実装の深さ・一般化（Altitude）

- 日本語: 実装の深さ, 一般化, 特例分岐, 継ぎ接ぎ, 呼び出し元分岐
- 英語: altitude, generalization, special-case, bandaid, caller-specific branch
- → `altitude-generalization`

### 新知識のコード反映・設計知識の保全（Knowledge-to-Code）

- 日本語: 知識反映, リファクタリング, 命名の更新, 責務, 境界, 過去の設計判断, 制約の消失
- 英語: knowledge delta, knowledge-to-code, refactoring intent, naming update, responsibility, design history, constraint preservation
- → `knowledge-to-code-alignment`
- 注意: ドメイン用語の一貫性は `ubiquitous-language-naming`、境界設計の妥当性は `bounded-context-language`、振る舞い/構造の分離は `behavior-structure-separation` に割り当て済み。本スキルは新知識の命名・責務・境界への反映と過去の設計知識の保全のみを扱う

### 振る舞い変更と構造変更の分離・外部挙動維持（Behavior-Structure）

- 日本語: 振る舞い変更, 構造変更, 混在, 外部挙動維持, characterization test, safety net, 挙動不変
- 英語: behavior change, structural change, separation, behavior preservation, characterization test, safety net
- → `behavior-structure-separation`
- 注意: 公開 API/DTO の破壊的変更は `api-compatibility`、完了主張の反証・抽出リファクタの性能退行は `refactor-claim-audit` に割り当て済み。本スキルは振る舞い/構造変更の混在と外部挙動維持の証拠のみを扱う

### closure スコープ保持（メモリ）

- 日本語: クロージャ, スコープ保持, メモリ保持, シングルトンのキャッシュ肥大
- 英語: closure, scope retention, memory retention, environment capture
- → `closure-scope-retention`

### 幻覚的参照の実在確認

- 日本語: 幻覚的参照, 存在しない参照, 実在確認, 未定義の関数, 存在しない API
- 英語: hallucinated reference, nonexistent reference, reference existence, undefined function
- → `hallucinated-reference`
- 注意: 「ハルシネーション検証 / hallucination guard」は `independent-review-synthesis`（レビュー指摘の evidence 実在確認）に割り当て済みのため、本スキルのキーワードにしない。**レビュー指摘の幻覚**は independent-review-synthesis、**コード内参照の幻覚**は hallucinated-reference が担う

### 操作の安全装置（UX-SAFEGUARD 観点）

- 日本語: 破壊的操作, 確認ダイアログ, 取り消し, undo, 回復支援
- 英語: destructive action, confirmation, undo, error message, recovery
- → UX-SAFEGUARD 観点を本 skill 内で実行（[UX-SAFEGUARD.md](./UX-SAFEGUARD.md) の操作の安全装置2観点）
- 注意: loading/error/empty state の**表示欠落**は `loading-state`、mutation の**認可**は security 系、DB の破壊的変更は `migration-safety` に割り当て済み（委譲表は UX-SAFEGUARD.md を参照）。本観点は「確認・取り消し手段の欠如」と「回復方法を示さない文言」のみを扱う

## 自動判定ルール

1. `.ts`/`.tsx` ファイル → `typescript-strict` + `typescript-nullcheck`
2. React コンポーネント → `river-review-frontend`（`a11y-accessible-name` 等）も参照
3. `app/` ディレクトリ（Next.js）→ `river-review-frontend`（`nextjs-app-router-boundary`）も参照
4. 設定・型定義ファイル → `type-driven-design`

## フォールバックルール

1. キーワード指定なし → 変更ファイルの拡張子とパスで自動判定
2. 複数該当 → 関連する全スキル実行
3. 判定不能 → 一般的なコード品質チェックリスト（SKILL.md のチェックリスト）を適用
