# ルーティング参考: river-review-docs

`river-review-docs` は、ドキュメント整合性レビューを担う専門スキルです。

## いつこのスキルへルーティングするか

オーケストレーター（`river-review`）は、以下のいずれかに該当する場合に本スキルを選択します。

- 入力に「ドキュメント / ドキュメンテーション / README / 翻訳 / i18n / 用語 / 整合性 / 使い方」（または英語の docs / documentation / README / translation / i18n / terminology / consistency / usage）が含まれる。
- 差分が `**/*.md` / `**/*.mdx` / `README*` / `AGENTS.md` / `docs/**` / `pages/**` を主に変更している。
- コードの公開インターフェース（CLI フラグ・設定キー・出力フォーマット）が変わり、対応ドキュメントの追従が疑われる。

## 他スキルとの境界

- 文章スタイルの機械チェック（textlint / markdownlint）は lint が担うため、本スキルは扱わない。
- コードの正しさ自体は `river-review-code` ほかの専門スキルが担う。本スキルは「ドキュメントと実装の整合」に集中する。
- セキュリティ・パフォーマンス等の専門観点が主目的の場合は、それぞれの専門スキルを優先する。
