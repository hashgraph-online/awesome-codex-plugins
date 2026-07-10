---
id: review-team
name: review-team
description: |
  6つの専門レビュアーロールを並列実行し、consensusLevel（複数ロールの合意度）と
  Tech Lead レポート（top3指摘・blindSpots・consensusSummary）で結果を統合する
  マルチエージェントレビュー entry skill。
  Parallel multi-role review with consensus scoring (consensusLevel) and Tech
  Lead report. Use when a major release needs exhaustive multi-angle review,
  or when a single-perspective review is not enough and you want confidence
  that no reviewer angle was missed（重要リリース前の網羅レビュー・多視点の確証が
  欲しいとき）。
phase: [upstream, midstream, downstream]
severity: major
applyTo: ['**/*']
tags: [entry, routing, multi-agent, parallel, consensus, team, orchestration]
version: '0.1.0'
license: MIT
---

# Review Team（レビュー・チーム）

複数の専門レビュアーロールを**並列実行**し、複数ロールが同一箇所を指摘した「コンセンサス指摘」を自動的に浮かび上がらせるレビュー手法。

## When to Use / いつ使うか

- 重要リリース前の網羅的なレビューが必要なとき
- セキュリティ・バグ・テスト・依存関係を一度に確認したいとき
- 「どこから見ても問題ない」という確証が欲しいとき
- 単一視点のレビューでは不十分と感じるとき

## Reviewer Roles / レビュアーロール

| ロール                | 担当領域                                                                      | 自動選択条件（auto モード）                        |
| --------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------- |
| `bug-hunter`          | ロジックエラー・境界値・null/undefined 参照・並行アクセス競合・エラー握り潰し | 常時                                               |
| `security-scanner`    | インジェクション・認証・機密漏洩                                              | リスクファイルまたはインフラ変更                   |
| `test-gap`            | テストカバレッジ・エッジケース                                                | テストファイルまたはアプリファイル3件以上          |
| `dependency-reviewer` | サプライチェーン・バージョンジャンプ                                          | package.json / lockfile 変更                       |
| `frontend-reviewer`   | アクセシビリティ・レンダリング・レスポンシブ・loading/error 状態の欠落        | .tsx/.jsx/.css/.scss/.sass/.less/.vue/.svelte 変更 |
| `ci-cd-reviewer`      | ワークフロー・アクションのピン・権限                                          | `.github/workflows/` 変更                          |

## Execution Flow / 実行フロー

```text
Step 1: ロール決定
  ├─ 明示指定あり → 指定ロールを使用
  └─ 指定なし → auto（差分内容から最適ロールを自動選択）

Step 2: 並列実行
  [bug-hunter] [security-scanner] [test-gap] ...（同時起動）
       ↓
  Union-Find クラスタリングで重複 finding を統合

Step 3: consensusLevel の付与（finding ごと）
  agreement.length ≥ 3 → "consensus" ★★★
  agreement.length = 2  → "multi"     ★★
  agreement.length ≤ 1  → "single"    ★

Step 4: Tech Lead レポートの生成（追加 LLM コストなし）
  top3Findings    : consensusLevel → severity 順の上位3件
  blindSpots      : 今回実行されなかったロール一覧
  consensusSummary: consensus / multi / single の件数集計
```

## Output Fields / 出力フィールド

### finding ごと

```json
{
  "title": "SQLインジェクションの可能性",
  "severity": "critical",
  "consensusLevel": "consensus",
  "agreement": ["bug-hunter", "security-scanner", "test-gap"],
  "reviewerRole": "bug-hunter"
}
```

### teamLeadReport（run 全体）

```json
{
  "teamLeadReport": {
    "top3Findings": [...],
    "blindSpots": [{ "role": "frontend-reviewer", "label": "Frontend Reviewer" }],
    "consensusSummary": { "consensus": 1, "multi": 3, "single": 8, "total": 12 }
  }
}
```

## How to Run / 実行方法

River Review は npm パッケージを公開しない（プロジェクト方針）。したがって `npx river-review` は使えない。実行環境ごとに次の手段を使う。

### プラグイン / エージェント環境（第一手段・CLI 不要）

Claude Code / Codex のプラグイン経由では、**エージェントがこのスキルの手順を直接実行する**。CLI は不要で、上記の Execution Flow（ロール決定 → 並列実行 → consensusLevel 付与 → Tech Lead レポート）をエージェント自身が再現する。

- スラッシュコマンド: `/review-team` または `/review-team bug-hunter,security-scanner`
- CLI が無くても設計どおり動作する。CLI 実行を試みて失敗しても、スキル駆動のレビューで継続すること。

### コントリビューター（リポジトリ内）

リポジトリ内では `river` CLI をアクセラレータとして使える（任意）。

```bash
# 差分から自動選択（推奨）
npm run river -- run . --reviewers auto

# ロールを明示指定
npm run river -- run . --reviewers bug-hunter,security-scanner,test-gap

# JSON 出力（teamLeadReport を含む）
npm run river -- run . --reviewers auto --output json

# コスト事前確認
npm run river -- run . --reviewers auto --dry-run
```

CLI は必須でない。存在しない、または失敗した場合はスキル駆動のレビューで継続する。

### GitHub Actions

Actions では CLI が実行エンジンとして起動される。ワークフロー設定は Actions 用ドキュメントを参照する。

## Output Interpretation / 結果の読み方

1. **`consensus` 指摘を最優先で確認する** — 複数の独立したロールが同箇所を指摘したため信頼度が最も高い
2. **`multi` 指摘を次に確認する** — 2ロールが合意した指摘
3. **blindSpots を見て追加実行を検討する** — 未実行ロールが多い場合はそのロールを追加して再実行
4. **`single` 指摘はノイズ混入の可能性がある** — ロール固有の観点からの指摘なので文脈に応じて判断

## Cost / コスト

- 実行ロール数 × 通常レビューコストが目安
- `auto` モードは差分に関係するロールのみを起動するため無駄がない
- Tech Lead レポートは追加 LLM コストなし（deterministic 計算）

## 他スキルとの関係

| スキル               | 関係                                                                               |
| -------------------- | ---------------------------------------------------------------------------------- |
| `adversarial-review` | 補完: adversarial は「どう壊れるか」に特化。review-team は「網羅的な多視点」に特化 |
| `river-review`       | 上位: river-review entry skill がロールを決定し review-team を起動する経路もある   |
