---
id: river-review-docs
name: river-review-docs
description: |
  ドキュメント観点のレビューエージェント。
  README / docs / AGENTS.md と実装の整合性、API ドキュメントとコードの対応、
  usage や例の正確性、i18n（JA/EN）整合性、用語統一を検証する。
category: midstream
phase: [midstream]
severity: minor
applyTo:
  - '**/*.md'
  - '**/*.mdx'
  - 'README*'
  - 'AGENTS.md'
  - 'docs/**/*'
  - 'pages/**/*'
inputContext: [diff, fullFile]
outputKind: [findings, actions]
tags: [docs, documentation, i18n]
version: 0.1.0
license: MIT
---

# Documentation Review（ドキュメントレビュー）

ドキュメントと実装の整合性、翻訳パリティ、用語統一を検証する。

## When to Use / いつ使うか

- README / docs / AGENTS.md / ガイドの変更時
- コードの公開インターフェース（CLI フラグ、API、設定キー）が変わったが、対応するドキュメントが更新されていない可能性があるとき
- 多言語（JA/EN）ドキュメントの一方のみが更新されたとき
- 用語・命名（プロダクト名、コマンド名など）の揺れが疑われるとき

## Review Viewpoints / レビュー観点

1. **実装との整合性**: ドキュメントが記述するコマンド・フラグ・設定キー・パス・バージョンが、実際のコード（CLI ヘルプ、設定スキーマ、ソース）と一致しているか。古い・誤った記述を検出する。
2. **API ドキュメントとコードの対応**: 公開関数・スキーマ・出力フォーマットの説明が実装と一致しているか。欠落した項目（未文書化のフラグ・コマンド・設定）を検出する。
3. **usage / 例の正確性**: コード例・コマンド例がそのまま実行可能か。存在しないファイル・廃止された手順を参照していないか。
4. **i18n 整合性**: JA/EN のペアで、一方にあるセクション・表・注記が他方に欠落していないか。バージョンピンや手順の食い違いがないか。
5. **用語統一**: プロダクト名・コマンド名・固有名詞の表記が統一されているか（例: 旧称の残存）。

## Output / 出力

他の専門スキルと同じ finding 契約に従って出力する。各 finding には以下を含める。

- `severity`（`critical` / `major` / `minor` / `info`）/ `file` / `line` / `message`（Finding 本文）
- `impact`: そのドキュメント不整合が読者・利用者に与える影響
- `fix`: 推奨する修正（どのドキュメントをどう直すか）
- `evidence`: ドキュメントと実装の不一致では、対応する実装側の根拠（ファイル・行・該当記述）
- `confidence`: 確信度（推測が含まれる場合は明示する）

差分に存在しない箇所への推測に基づく指摘は行わない。

## Notes / 注意

- 文章スタイル（textlint / markdownlint）の機械的チェックは既存の lint が担うため、本スキルは**内容の整合性**に集中する。
- 多言語パリティの指摘では、SSoT（通常は JA）を基準に欠落を示す。
