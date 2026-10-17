# SIMPLIFY 観点 — 品質クリーンアップレビュー

Claude Code の `/simplify` に由来する4観点。correctness bug ではなく**品質クリーンアップ**（重複・無駄・複雑さ・実装深度）を検出する。bug 探索は bug 系観点の責務であり、本観点では行わない。

River Review の契約に従い **report-only** である。fix は「次の最小一手」の提案テキストとして出力し、適用はしない。

## Pre-execution Gate

**最初に判定する**。満たさない場合は以降のチェック（Grep 含む）を行わず `NO_REVIEW` を返す。

- 差分に**リポジトリ内で実行されるコード**（`src/` / `scripts/` / `runners/` 等の `.ts` / `.tsx` / `.js` / `.jsx` / `.mjs`）が含まれる。docs・設定ファイルのみの差分は対象外
- ビルド成果物・生成物（`dist/**`・`*.map`・lockfile・自動生成 manifest）は Gate 判定からもレビュー対象からも除外する

## 観点 / Perspectives

| 観点               | 対象とする無駄                                  | 核心の問い                                      |
| ------------------ | ----------------------------------------------- | ----------------------------------------------- |
| **Reuse**          | 既存ヘルパ・ユーティリティの再実装              | 「このコード、もう**存在して**いない？」        |
| **Simplification** | 冗長 state・copy-paste・dead code               | 「同じ仕事を**より単純な形**で書けない？」      |
| **Efficiency**     | 冗長計算・繰返し I/O・逐次実行・closure 保持    | 「この仕事、**しなくてよく/まとめられ**ない？」 |
| **Altitude**       | 共有基盤への special-case な継ぎ接ぎ（bandaid） | 「この修正、**正しい深さ**で実装されている？」  |

## 委譲 / Delegation（既存スキル優先）

重複指摘を避けるため、以下の領域は既存 registry skill に委譲する。本観点は**委譲先が扱わない残余のみ**を検出する。

| 対象領域                                                            | 委譲先                                           | 本観点が扱う残余                                                                                       |
| ------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| 先行実装と同型の共通ロジック再実装                                  | `existing-pattern-conformance`                   | 「呼び出して置換可能」と確定した先行パターンへの準拠のみ委譲（分界は「1. Reuse」参照）                 |
| UI プリミティブ（Button 等）の再実装                                | `design-system-component-reuse`                  | UI 以外の再実装                                                                                        |
| 冗長・無効 state の型による排除                                     | `type-driven-design`                             | 型で表現しない導出 state（既存 state から計算可能な保持）                                              |
| N+1・逐次 DB I/O（Laravel）                                         | `laravel-eloquent-nplus1`                        | Laravel 以外の繰返し I/O・並列化可能な独立 await                                                       |
| i18n 未使用キー                                                     | `i18n-unused-key`                                | i18n 以外の dead code（未使用 export・到達不能分岐）                                                   |
| 深いネストの平坦化                                                  | [SKILL.md](../SKILL.md) チェックリスト（可読性） | —                                                                                                      |
| 共有基盤への caller special-case（Altitude の詳細検出・一般化提案） | `altitude-generalization`                        | 既存の一般機構で表現できる変更を機構迂回の重複実装で足すケース（分岐・フラグ証拠なし）のみ本観点が扱う |
| 長寿命オブジェクトの closure / 環境キャプチャによるスコープ保持     | `closure-scope-retention`                        | closure 保持以外の Efficiency（ループ内不変計算・逐次 `await`・起動パスへのブロッキング追加）          |

## 各観点のチェック / Checks

### 1. Reuse（既存資産の再利用）

- 差分で新規追加された関数・定数・変換ロジックが、次のいずれかを再実装していないか:
  - リポジトリ内の shared/utility モジュールや変更ファイルに隣接する既存ヘルパ（Grep はソースツリー全域、少なくとも `src/` 相当を対象にする）
  - Node.js 標準 API・宣言済み依存パッケージの API（例: `node:module` の `isBuiltin()`）
- 検出時は**呼ぶべき既存ヘルパ / API を名指し**する（repo 内なら `file:line`、標準・依存 API ならモジュール名）
- 証拠要件: 既存実装の実在を、repo 内は Grep/Glob、標準・依存 API は実行確認または公式ドキュメントで確認できた場合のみ finding 化する（「ありそう」という推測は禁止）
- 分界: **差分外の既存実装**との重複は本観点（Reuse）が、**差分内の新規ブロック同士**の重複は Simplification が扱う。helper として抽出されていない inline の先行実装との重複も Reuse が扱う（委譲先 `existing-pattern-conformance` は「呼び出し可能な先行パターンへの準拠」を見る）

### 2. Simplification（簡素化）

- 導出可能な state の保持: 既存 state から計算できる値を別変数・別フィールドとして保存していないか
- slight variation の copy-paste: **差分内に**同型ブロックが2回以上現れ、差分が引数化できる程度でないか（差分内1回のみで、差分外の既存同型ブロック群に合わせた追加は「ファイル内既存規約への準拠」であり指摘しない）
- リファクタ後の dead code: 呼ばれなくなった関数・使われない export・到達不能になった分岐が残っていないか
- 検出時は**同じ仕事をするより単純な形**を具体的に提示する

### 3. Efficiency（無駄な仕事）

- 適用条件: 「ループ・ホットパス・長寿命プロセスの起動パス」の文脈証拠が差分から読み取れる場合のみ指摘する。one-shot CLI スクリプトの単発の逐次 I/O は対象外とし、ループ内の繰返しは対象とする
- ループ内の不変計算・同一引数での繰返し I/O（メモ化・ループ外への巻き上げで解消できるもの）
- 独立した非同期処理の逐次 `await`（`Promise.all` 等で並列化できるもの）
- 起動パス・ホットパスへのブロッキング処理の追加
- closure / 環境キャプチャによるスコープ保持は registry skill `closure-scope-retention` に**委譲済み**（委譲表参照）。本観点では重複指摘しない

### 4. Altitude（実装の深さ）

- caller special-case の検出（呼び出し元判定の分岐・専用フラグ・型チェックによるバイパス）と、同種2つ以上での**下層機構の一般化提案**は registry skill `altitude-generalization` に**委譲済み**（委譲表参照）。本観点では重複指摘しない
- 本観点が扱う残余: 既存の一般機構で表現できる変更を、機構を迂回する**重複実装**で足していないか（special-case 分岐の形をとらないケース）
- 証拠要件: 迂回判定は差分内に既存機構の存在と迂回実装の証拠がある場合のみ。証拠のない設計思想への一般論は禁止

## False-positive guards

- 指摘行（finding の `file:line`）が差分内にあること（VERIFICATION の evidence 規則）。根拠の一部が差分外の周辺コンテキスト（同一 hunk 内の既存行など）にあることは許容する
- correctness bug・セキュリティ欠陥は対象外（bug 系・security 系観点の責務。本観点で重複指摘しない）
- 意図的な非 DRY（過度な抽象化の回避、テストコードの明示的な重複）は指摘しない
- 委譲表に該当する指摘は出さない（委譲先 skill の実行に委ねる）
- 観点ごとに最大5件。超過分は severity 降順で切り捨てる

## Output

[SKILL.md](../SKILL.md) の Output Format に従い（Finding / Impact / Fix）、各 finding に Severity と Confidence（`high` / `medium` / `low`）を併記する。severity は**出力スキーマ語彙**（`info` / `minor` / `major`）で書く。`minor` を起点とし、無駄の規模が大きく確証が強い場合のみ `major`。確信が持てない場合は `info` に落とす（VERIFICATION の calibration 規則）。

参考: 内部語彙（blocker/warning/nit）との対応が必要な場合のみ `.claude/rules/review-core.md` を参照する（本観点の実行には不要）。
