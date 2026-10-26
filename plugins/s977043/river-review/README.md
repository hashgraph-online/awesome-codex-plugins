# River Review

**レビューを、組織の判断資産へ。**  
Review Judgment as Code for AI-assisted development.

[![Documentation](https://img.shields.io/badge/docs-available-blue)](https://river-review.the3396.com/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13339/badge)](https://www.bestpractices.dev/projects/13339)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/s977043/river-review/badge)](https://securityscorecards.dev/viewer/?uri=github.com/s977043/river-review)

![River Review logo](assets/logo/river-review-logo.svg)

日本語が正本です。[English README](./README.en.md)

River Review は、レビュー基準を **versioned / repo-owned な Skill** として管理し、計画・差分・テスト・既存レビューの根拠を横断して実行する OSS です。Claude Code / Codex のローカルレビューと GitHub Actions に、同じチームの判断基準を持ち込めます。人間の承認や自動マージの代行はしません。

- **Skills define judgment**—チームがレビュー観点を所有し、fixture / golden output で評価する。
- **Gates execute judgment**—計画・差分・検証証跡を対象に、現在利用可能なレビューゲートで判断基準を適用する。
- **Riverbed remembers judgment**—決定とフィードバックを記録し、不要な指摘の再発を抑える。

[設計思想](https://river-review.the3396.com/explanation/concept/) / [機能と実行モデル](https://river-review.the3396.com/explanation/what-is-river-review/) / [既知の制限](https://river-review.the3396.com/reference/known-limitations/)

## はじめる

### Claude Code（最短）

```text
/plugin marketplace add s977043/river-review
/plugin install river-review@river-review-marketplace
/reload-plugins
/river-review:review-local
```

### Codex

```text
codex plugin marketplace add s977043/river-review
```

通常のプラグイン利用では、**River Review 専用の LLM API キーは不要**です。GitHub Actions や standalone `river run` のヘッドレス実行では、設定した LLM プロバイダーの API キーが必要です。

導入手順の詳細は [プラグインを導入する](https://river-review.the3396.com/guides/plugin/install/)、GitHub Actions 設定は [5分クイックスタート](https://river-review.the3396.com/guides/quickstart/) を参照してください。npm パッケージの公開は配布方針に含まれず、リポジトリ内の開発用 CLI は `npm run river -- ...` で実行します。

<!-- x-release-please-start-version -->

最新リリース: [v1.136.0](https://github.com/s977043/river-review/releases/latest)

<!-- x-release-please-end -->

## 得られるもの

得られるもの（プラグイン名で名前空間化されます）:

- コマンド: `/river-review:setup-team` / `/river-review:review-local` / `/river-review:review-team` / `/river-review:challenge` が含まれる。加えて `/river-review:skill` / `/river-review:check` / `/river-review:pr` も使える。

- スキル: オーケストレーターの `river-review` に加えて `river-review-code` / `river-review-security` / `river-review-security-audit` / `river-review-performance` の各スキルが含まれる。さらに `river-review-architecture` / `river-review-testing` / `river-review-frontend` も含まれる。加えて `river-review-docs` / `adversarial-review` / `review-team` / `unknown-coverage-review` も含まれる。いずれも `/river-review:<skill-name>` で呼び出せる

スキルを追加する前に、[Starter Cookbook](https://river-review.the3396.com/guides/starter-cookbook/) で既存の観点を試してください。プロジェクト固有の基準は [Skill作成チュートリアル](https://river-review.the3396.com/tutorials/creating-your-first-skill/) に沿って作成できます。

## ドキュメント

- **初回導入**：[Quickstart](https://river-review.the3396.com/guides/quickstart/)
- **レビュー運用**：[2段構えレビューゲート](https://river-review.the3396.com/guides/two-stage-review-gate/)
- **GitHub Actions**：[GitHub Actionsガイド](https://river-review.the3396.com/guides/github-actions/)
- **Skill一覧とスキーマ**：[Skill Catalog](https://river-review.the3396.com/reference/skills-catalog/) / [Schema](https://river-review.the3396.com/reference/skill-schema/)
- **CLIの仕様**：[CLIリファレンス](https://river-review.the3396.com/reference/runner-cli-reference/)
- **トラブルシューティング**：[Troubleshooting](https://river-review.the3396.com/guides/troubleshooting/)
- **ロードマップ**：[ROADMAP.md](./ROADMAP.md) / [Issues](https://github.com/s977043/river-review/issues)

公式ドキュメントの正本は `pages/` です。`docs/` は開発・保守資料であり、公式サイトには掲載しません。ただし両ディレクトリとも公開GitHubリポジトリ上で閲覧可能です。[ドキュメント管理方針](docs/policy/DOCUMENTATION.md)

## FAQ

**ESLint・型チェック・静的解析の代わりですか？** いいえ。River Review は計画と実装、テストと期待値など、複数アーティファクトを跨ぐレビュー判断を補完します。

**レビュー結果が自動承認になりますか？** いいえ。findings と verdict は判断材料であり、最終承認・GO / NO-GO は人間・呼び出し側の責務です。

その他は [FAQ](https://river-review.the3396.com/guides/faq/) と [セキュリティモデル](https://river-review.the3396.com/explanation/security-model/) を参照してください。

## コントリビューションとセキュリティ

バグ報告、改善提案、ドキュメントの貢献を歓迎します。

- [貢献ガイド](.github/CONTRIBUTING.md) / [行動規範](.github/CODE_OF_CONDUCT.md)
- [脆弱性の非公開報告](.github/SECURITY.md)（公開Issueへ脆弱性情報を投稿しない）
- [公開の実践進化方針](https://river-review.the3396.com/guides/governance/practice-evolution/)

## ライセンス

コードは [LICENSE-CODE](LICENSE-CODE)（MIT）、ドキュメントやメディアは [LICENSE-CONTENT](LICENSE-CONTENT)（CC BY 4.0）を参照してください。ルートの [LICENSE](LICENSE) 本文は MIT です。ただし設定ファイル等への適用範囲については、LICENSE-CODE / LICENSE-CONTENT の説明に Apache-2.0 への不一致があり、[Issue #2721](https://github.com/s977043/river-review/issues/2721) で確認中です。
