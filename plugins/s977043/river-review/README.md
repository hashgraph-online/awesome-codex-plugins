# River Review

**Review Judgment as Code for AI-assisted development.**
**AI支援開発のための Review Judgment as Code。レビュー判断を repo-owned skill としてコード化します。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-available-blue)](https://river-review.the3396.com/explanation/intro/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13339/badge)](https://www.bestpractices.dev/projects/13339)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/s977043/river-review/badge)](https://securityscorecards.dev/viewer/?uri=github.com/s977043/river-review)
[![Listed on awesome-codex-plugins](https://img.shields.io/badge/awesome--codex--plugins-listed-brightgreen)](https://github.com/hashgraph-online/awesome-codex-plugins/tree/main/plugins/s977043/river-review)

![River Review logo](assets/logo/river-review-logo.svg)

日本語版READMEです。[English README is available here.](./README.en.md)

River Review は、レビュー基準を **versioned / repo-owned な skill** として扱う OSS フレームワークです。plan / diff / tests / JUnit / 既存レビュー結果といった SDLC のアーティファクトをまたいで実行できます。

AI 支援開発（Claude Code / Codex / Cursor 等）でコードは速く書けるようになりました。一方で、**レビュー判断は依然としてチームのもの**として、明示的・再現可能・所有可能に保つ必要があります。

River Review は、こうした問いに答えるためのフレームワークです。

- この差分は承認された実装プランと一致しているか？
- テストは plan で約束された境界条件を満たしているか？
- この PR はチームの migration / security / a11y / dependency ポリシーに違反していないか？
- 実装エージェントは、過去レビューのフィードバックを無視していないか？

> River Review は人間のレビューを AI で置き換えるのではなく、チームの判断基準を versioned skill として実行することで、人間が本当に見るべき高リスクな判断に集中できる状態を作ります（[Human Judgment Focus](https://river-review.the3396.com/explanation/human-judgment-focus/)）。

⭐ AI 支援開発のレビュー運用に役立ちそうなら、[Star](https://github.com/s977043/river-review) で応援してください。更新を追えるほか、同じ課題を持つチームに River Review が届きやすくなります。

## なぜ River Review か

| 軸               | 既存の AI レビューツール | River Review                                                 |
| ---------------- | ------------------------ | ------------------------------------------------------------ |
| 入力             | 主に diff のみ           | plan / diff / tests / JUnit / 既存レビュー                   |
| 判断             | ベンダー black box       | リポジトリ内の versioned skill                               |
| 知識の所有       | provider-owned           | repo-owned / レビュー可能                                    |
| 実行ゲート       | 通常は PR 時点のみ       | 設計 / 実装の 2 ゲート（検証ゲートは計画中）                 |
| 指摘の再現性     | 毎回ブレる               | suppression memory / fixture 回帰テスト / 決定論スコアリング |
| エージェント連携 | スタンドアロンレビュアー | **AI 支援実装の監査レイヤー**                                |

River Review は「PR diff にプロンプトを巻いただけのツール」ではなく、**チームのレビュー判断を実行可能にするフレームワーク**です。実装エージェントが書いたコードを、チーム所有のルールで検査するレイヤーとして機能します。

## コアモデル

![River Review のコアモデル: plan / diff / tests / JUnit / 過去レビューを入力に、repo-owned skill がレビュー判断を実行し、チーム基準に対する指摘を出力する team-owned audit layer](assets/social/diagram.svg)

**Skills define judgment.**
skill は「どんなレビュー判断を行うか」を記述します。security / a11y / migration safety / dependency policy / plan conformance など、チーム固有の基準を載せます。

**Gates execute judgment.**
plan / exec ゲートが、適切なタイミングで skill を実行します。PR 完成後だけでなく、設計段階・実装段階のいずれでも動かせます（verify ゲートは [#802](https://github.com/s977043/river-review/issues/802) で計画中）。

**Riverbed remembers judgment.**
レビュー結果や決定、再利用可能なコンテキストは operating memory として残り、suppression や過去判断の再利用を通じて将来のレビューを一貫させます（[`pages/guides/use-riverbed-memory.md`](pages/guides/use-riverbed-memory.md)）。

AI 支援ワークフローにおいて、River Review は **チーム所有の監査レイヤー** として機能します。実装エージェントはコードを書けますが、それがチームのルールに従っているかを River Review が検査します。

## 3 つの主軸

River Review が提供する価値は、次の 3 軸で整理できます。いずれも「チームのレビュー判断を versioned / repo-owned な資産にする」という基盤の考えから派生しています。

### 1. AI エージェントのレビュー能力を強化する capability pack

River Review のスキル／エージェント定義は、Claude Code / Cursor / Codex などの AI エージェントに「チームのレビュー判断」を持ち込む **capability pack** です。通常はエージェント自身のモデルがスキルを適用するため、**River Review 用の LLM キーは不要**です。LLM キーが要るのは GitHub Action / standalone `river run` のヘッドレス実行だけで、機械的に判定できる観点はキー無しでも動きます（詳細は [FAQ](#faq) 節を参照）。

### 2. レビュースキルの用意（Skill Registry）

基盤となるのは Skill Registry です。security / a11y / migration safety / dependency policy / plan conformance などチーム固有の暗黙知を versioned / repo-owned なレビュー資産として明示化します。fixture と golden output による継続的な改善も可能です。詳細は [コアモデル](#コアモデル) 節を参照してください。

### 3. レビュー用エージェント + 観点別レビュアーの review team

River Review には、レビューに特化した 3 つの実行形態があります。

- **レビュー用エージェント定義**: プラグイン／サブエージェントとして配布される `agents/river-review.md`。スキルルーティング型のオーケストレーターとして動き、`/river-review:<skill>` で各専門スキルを呼び出せる。
- **観点別レビュアーを並列実行する review team**: 観点別ロールを 1 つの orchestrator（`src/lib/reviewer-orchestrator.mjs`）内で並列に走らせ findings を connected-components でマージする。ロールは bug-hunter / security-scanner / test-gap / dependency-reviewer / frontend-reviewer / ci-cd-reviewer であり、`--reviewers auto` 指定で差分タイプから自動選択される。
- **verdict 付きの critic（Agent 層）**: generate → review → revise のループにおいて findings と verdict（判定素材）を出す。Reference Loop は `examples/loop-reference-agent/`、収束契約は [`pages/reference/loop-convergence-contract.md`](pages/reference/loop-convergence-contract.md) にある（Agent 層 Epic [#1150](https://github.com/s977043/river-review/issues/1150)）。

> **役割分担と HITL 境界**: review team は findings + verdict を出力しますが、GO / NO-GO の判断・反復・停止は呼び出し側／人間の責務です。自動承認・自動マージは行いません。ここでの review team は「1 つの orchestrator 内で観点別レビュアーロールを並列実行し findings をマージするもの」であり、完全自律な独立エージェント群ではありません。「River Review = レビューする / PlanGate = 止める・通す」という役割分担を維持しています。

## はじめる

インストール不要の最短手順は同梱プラグインです。マーケットプレイスを追加し、`river-review` エージェントに現在の差分のレビューを依頼してください（[river-review プラグインの導入](#river-review-プラグインの導入)）。CI では GitHub Actions を使います（[クイックスタート](#クイックスタートgithub-actions)）。

> **配布は 2 チャネル: 同梱プラグイン（Claude Code / Codex）と GitHub Actions**。River Review は npm パッケージを公開しません（プロジェクト方針）。コントリビューターはリポジトリ内で `npm run river -- ...` として CLI を実行できます（ローカルで試すなら `npm run river -- run . --dry-run`）。CLI は GitHub Action の実行エンジンでもあるため維持されます。

| やりたいこと                               | 行き先                                                                                            |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| 5分で試す                                  | [クイックスタート（GitHub Actions）](#クイックスタートgithub-actions)                             |
| Claude Code / Codex プラグインとして入れる | [プラグインの導入](#river-review-プラグインの導入)                                                |
| 既存リポジトリに導入する                   | [セットアップガイド](https://river-review.the3396.com/guides/github-actions/)                     |
| 梱包済み Skill Pack で始める               | [Skill Pack を使う](pages/guides/use-skill-packs.md)                                              |
| スキルを1個作る                            | [スキル作成チュートリアル](https://river-review.the3396.com/tutorials/creating-your-first-skill/) |
| コストを見積もる                           | [コスト見積もりガイド](pages/guides/cost-estimation.md)                                           |
| W チェック（二重レビュー）を使う           | [W チェックガイド](pages/guides/w-check.md)                                                       |
| AI エージェントから使う                    | [エージェント連携ガイド](pages/guides/agent-workflow.md)                                          |
| リポジトリ全体を踏まえたレビュー           | [リポジトリ全体レビューガイド](pages/guides/repo-wide-review.md)                                  |
| 設計思想を理解する                         | [アーキテクチャ解説](https://river-review.the3396.com/explanation/river-architecture/)            |

開発手順は [docs/runbook/dev.md](docs/runbook/dev.md) を参照してください。ライセンスは [本ファイル末尾](#ライセンス) に記載しています。

## FAQ

### ESLint や型チェック、SonarQube ではダメか？

それらは引き続き使ってください。River Review は静的解析の置き換えではありません。

linter や静的解析は、コード内で完結する決定論的なチェック（構文、型、危険な API、スタイル、複雑度、重複、既知のセキュリティパターン）が得意です。

River Review が扱うのは、**アーティファクトを跨ぐレビュー判断**です。

- 実装 diff が承認されたプランと意図を維持しているか？
- テストは plan で約束された境界条件を満たすか？
- この migration はチームのロールアウトポリシーに従っているか？
- この依存追加はリポジトリのポリシー上許容されるか？
- PR は別のレビュアーが既に指摘した観点に対応しているか？

これらは plan / diff / tests / 既存コメント / チーム基準といった構造化された文脈を必要とします。ルールベース linter では書けない判断を、**LLM + 構造化されたアーティファクト + テスト可能な skill** で扱います。

> **LLM キーは通常不要**: River Review のスキルは AI エージェント（Claude Code / Cursor / Codex 等）の**レビュー能力を強化する capability pack** です。通常はエージェント自身のモデルがスキルを適用するため **River Review 用の LLM キーは不要**。LLM キーが要るのは **GitHub Action / standalone `river run` のヘッドレス実行**だけです（機械的に判定できる一部の観点はキー無しでも動きます）。詳細は [River Review とは § 実行モデル](pages/explanation/what-is-river-review.md)。

### コードやレビューデータはどこに送られるか？

River Review は **repo-owned な設定** と **provider-agnostic な実行** を前提に設計されています。

skill はあなたのリポジトリに置きます。レビュールールはコードと一緒にバージョン管理され、ベンダーのアカウント内に隠れることはありません。実行時の振る舞いは、設定したプロバイダ（OpenAI / Anthropic / Google）と runner（GitHub Actions / CLI / Node API）に依存するため、チームは自分のセキュリティ要件に合わせてデータ境界を選べます。

センシティブなリポジトリでは、入力を絞り、アーティファクト契約を明示し、CI 制御下で実行する運用から始めることを推奨します。

### PlanGate に依存しているか？

いいえ。PlanGate は有用なワークフロー形態の一つですが、River Review が単一のプランニング手法に依存することはありません。

コア契約は **artifact-based** です。plan / diff / tests / JUnit / 既存レビューコメントなど、構造化された入力を評価できます。チームはまず PR 時点のチェックだけ採用し、後から plan / verify ゲートを追加することができます。

### コストはどう制御するか？

skill を CI job のように扱ってください。

安価で決定論的なチェックを先に走らせる、変更に関係するアーティファクトと skill にだけ River Review を当てる、まずは小さな公式 skill pack から始めて、人間のレビューコストや回帰リスクが高い箇所にだけリポジトリ固有 skill を追加する、という運用が現実的です。

良い skill には fixture と golden output を必ず付け、レビュー信号が実行コストに見合うかを測定できる状態にします。Anthropic provider 利用時は prompt caching が自動適用され、`RIVER_USAGE_TELEMETRY=1` で使用量を JSONL に永続化できます。

<a id="philosophy"></a>

## 📖 The Philosophy (なぜ作ったのか)

> **We stopped believing "polish the prompt and you win."**
> **「プロンプトを磨けば勝てる」をやめました。**

AIレビューの実用化における最大の壁は、プロンプトの精度ではなく「レビュー指摘の再現性」と「運用コスト」でした。
River Review は、単にコードをAIに読ませるツールではありません。

チーム固有の「判断基準」や「手順」といった暗黙知を、**再利用可能な「Agent Skills（マニュアル付きの道具箱）」** として定義し、組織の資産として育てるための実験的フレームワークです。

さらに、レビューの「自由度」をリスクで設計し、**HITL（Human-in-the-Loop）** を前提にした Plan / Validate / Verify の運用で、実務に耐える再現性を確保します。

要点は次の3つです。

- **Agent Skills**: 暗黙知をレビュー資産として明示化し、継続的に改善できる状態にする。
- **自由度の設計**: 崖・丘・原っぱのリスク設計で、AIの裁量と検証コストを制御する。
- **HITLワークフロー**: 実行前に計画を人が検証し、レビュー結果は検証可能にする。

🔗 **Read the full story (Japanese):**
[「プロンプトを磨けば勝てる」をやめた：AIレビューを運用に乗せる“Agent Skills”設計](https://note.com/mine_unilabo/n/nd21c3f1df22e)

## フローのストーリー

- **上流（設計）**: ADR を踏まえたチェックでコードのドリフトを防ぎ、アーキテクチャ判断との整合を保ちます。
- **中流（実装）**: スタイルと保守性のガードレールで日々のコーディングを支援します。
- **下流（テスト/QA）**: テスト指向のスキルがカバレッジ不足や失敗パスを浮かび上がらせます。
- **フェーズ指向ルーティング**: `phase` とファイルメタデータを見て、開発段階に合ったスキルを選択します。

## ポジション: artifact-driven review agent

River Review は **artifact-driven review agent** です。外部から渡されるアーティファクト（`plan` / `diff` / `test-cases` / `junit` ほか）を入力として読み取り、`findings` を含むレビュー結果を出力します。入力の契約は [Artifact Input Contract](pages/reference/artifact-input-contract.md) で、出力スキーマは [Review Artifact](pages/reference/review-artifact.md) で定義されています。

現在の主な統合例は **PlanGate v6** との連携です。PlanGate が生成した `plan` / `pbi-input` アーティファクトを受け取り、設計整合性・実装適合性を専用スキルで検査します。

### 4 つのユースケース

- **設計レビュー**: `pbi-input` / `plan` を入力に、計画の整合性・網羅性を上流 skill で検査します（例: `skills/upstream/plangate-plan-integrity/`）。
- **実装レビュー**: `plan` と `diff` を入力に、実装差分が計画と一致しているかを検査します（例: `skills/upstream/plangate-exec-conformance/`）。
- **QA レビュー**: `test-cases` / `junit` / `coverage` を入力に、テストカバレッジや失敗パスの抜けを下流 skill で浮かび上がらせます。
- **W チェック（二重レビュー）**: 既存の AI / 人間レビュー結果を `review-self` / `review-external` として渡し、レビューそのものを再点検します。

### CLI 利用例

詳細な仕様は [`river review plan` CLI 仕様](pages/reference/cli-review-plan-spec.md) / [`river review exec` CLI 仕様](pages/reference/cli-review-exec-spec.md) を参照してください。

```bash
# 設計レビュー: plan 単体を検査
river review plan --artifact plan=./artifacts/plan.md

# 実装レビュー: plan と diff の整合性を検査
river review exec \
  --artifact plan=./artifacts/plan.md \
  --artifact diff=./artifacts/diff.patch

# QA レビュー: テスト観点のアーティファクトを追加
river review exec \
  --artifact diff=./artifacts/diff.patch \
  --artifact test-cases=./artifacts/test-cases.md \
  --artifact junit=./artifacts/junit.xml
```

## クイックスタート（GitHub Actions）

`v1` タグを使った最小構成のワークフロー例です。`phase` は将来拡張を見据えた任意入力で、SDLC のフェーズごとにスキルを振り分けます。Permissions/fetch-depth などを明示して安定動作させます。

```yaml
name: River Review
on:
  pull_request:
    branches: [main]
jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0 # merge-base を安定取得
      - name: Run River Review (midstream)
        uses: s977043/river-review/runners/github-action@v1.14.0
        with:
          phase: midstream # upstream|midstream|downstream|all (future-ready)
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

タグは `@v1.14.0` などのリリースタグにピン留めしてください。あるいは、常に最新の 1.x を指す浮動メジャーバージョンエイリアス `@v1` を使うこともできます。

<!-- x-release-please-start-version -->

最新リリース: [v1.40.0](https://github.com/s977043/river-review/releases/latest)

<!-- x-release-please-end -->

> **ℹ️ v0.1.x からのアップグレード:** v0.2.0以降では、GitHub Actionのパスが `.github/actions/river-review` から `runners/github-action` に変更されています。詳細は[移行ガイド](docs/migration/runners-architecture-guide.md)と[DEPRECATED.md](docs/deprecated.md)をご確認ください。

### 高度な設定例

- フェーズ別レビューを並列実行（上流・中流・下流を個別ジョブに分割）

```yaml
jobs:
  review-upstream:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: s977043/river-review/runners/github-action@v1.14.0
        with: { phase: upstream }
        env: { OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} }

  review-midstream:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: s977043/river-review/runners/github-action@v1.14.0
        with: { phase: midstream }
        env: { OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} }

  review-downstream:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: s977043/river-review/runners/github-action@v1.14.0
        with: { phase: downstream }
        env: { OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} }
```

- コスト見積もりと上限の例

```yaml
review:
  runs-on: ubuntu-latest
  if: "!contains(github.event.pull_request.title, '[skip-review]')" # タイトルでスキップ
  steps:
    - uses: actions/checkout@v6
      with: { fetch-depth: 0 }
    - uses: s977043/river-review/runners/github-action@v1.14.0
      with:
        phase: midstream
        estimate: true # コスト見積もりのみ
        max_cost: 1.5 # USD 上限、超過で終了
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

- Draft/Ready でレビュー強度を変える例

```yaml
  review-light:
    if: github.event.pull_request.draft == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: s977043/river-review/runners/github-action@v1.14.0
        with:
          phase: midstream
          dry_run: true            # Draft はドライランでプロンプト確認のみ
          debug: true
        env: { OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} }

  review-full:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: s977043/river-review/runners/github-action@v1.14.0
        with:
          phase: midstream
          dry_run: false           # Ready ではフルレビュー
        env: { OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }} }
```

### 設定ファイルでのカスタマイズ

リポジトリ直下に `.river-review.json` / `.river-review.yaml` / `.river-review.yml` を置くと、モデル設定・レビュー言語・厳格度・除外パターンをプロジェクト単位で上書きできます。見つからない場合は下記のデフォルト値で動作します。

```yaml
# デフォルト値の例
model:
  provider: openai
  modelName: gpt-4o-mini
  temperature: 0
  maxTokens: 600
review:
  language: ja
  severity: normal
  additionalInstructions: []
exclude:
  files: []
  prLabelsToIgnore: []
```

設定は `ConfigLoader` が Zod で検証したうえでデフォルトとマージされます。値を部分的に指定するだけで残りは自動補完されるため、JSON/YAML どちらでも最小限の記述でカスタムできます。
トップレベルはオブジェクトのみ受け付けるため、配列やスカラー値のみのファイルはエラーとなります。

#### Anthropic (Claude) プロバイダーを使う

`@anthropic-ai/sdk` ベースの Claude モデル (`claude-sonnet-4-6` / `claude-opus-4-7` / `claude-haiku-4-5`) を指定できます。`ANTHROPIC_API_KEY`（または `RIVER_ANTHROPIC_API_KEY`）を環境変数で渡してください。

```json
{
  "model": {
    "provider": "anthropic",
    "modelName": "claude-sonnet-4-6",
    "temperature": 0
  },
  "review": {
    "language": "ja"
  }
}
```

GitHub Actions では:

```yaml
- uses: s977043/river-review/runners/github-action@v1.14.0
  with:
    phase: midstream
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Prompt caching（自動）**: skill の systemPrompt は Anthropic の 5 分 ephemeral cache を自動利用します。同じ skill で複数ファイルをレビューする際、2 回目以降の system トークンが大幅に割引（cache_read 単価は通常の 1/10）されます。グローバル無効化は `RIVER_ANTHROPIC_PROMPT_CACHE=0`、skill 単位無効化は `skill.disableCache: true` を使用します。

**コスト計測（usage telemetry）**: `AIClientFactory.create(...)` が返す Anthropic / OpenAI クライアントは、`generateReview()` 完了後に `client.lastUsage` を `{ provider, model, inputTokens, outputTokens, cacheCreationInputTokens, cacheReadInputTokens }` 形式で公開します。`SkillDispatcher` の結果配列にも `usage` フィールドとして含まれるため、独自スクリプトでコスト集計や cache 効率の計測に利用できます。`RIVER_AI_RETRY_DEBUG=1` を設定すると 1 呼び出しごとに usage が標準出力にも記録されます。

**Disk への永続化（opt-in）**: `RIVER_USAGE_TELEMETRY=1` を設定すると、`SkillDispatcher` 実行完了時に `artifacts/usage/<YYYY-MM-DD>-<runId>.jsonl` へ 1 (file, skill) ペアにつき 1 行の JSONL を書き出します。各行は `{ timestamp, runId, commit, file, skill, provider, model, inputTokens, outputTokens, cacheCreationInputTokens, cacheReadInputTokens }` の安定スキーマで、外部のコスト分析ツールに直接食わせられます。永続化失敗はレビュー本体を止めません（警告のみ）。

### セキュリティ考慮事項

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` は必ず Repository Secrets に設定し、`env:` で参照する
- Private リポジトリでは必要な permissions（contents, pull-requests）を明示する
- `fetch-depth: 0` でマージベースを正しく取得し、誤差分を避ける

## クイックスタート（ローカル）

1. 環境: Node 22+ 推奨（CI は主に Node 22 系で運用、Unit tests は 20.x も検証）
2. 依存導入: `npm install`
3. スキル検証: `npm run skills:validate`
4. Agent Skills 検証（任意）: `npm run agent-skills:validate`
5. テスト: `npm test`
6. Planner 評価（任意）: `npm run planner:eval`
7. Review fixtures 評価（任意）: `npm run eval:fixtures`（must_include 方式）
8. リポ全体評価（任意）: `npm run eval:repo-context`（[#688](https://github.com/s977043/river-review/issues/688) の repo-wide fixtures に対し detection / context lift / false positive を測定する）
9. ドキュメント開発（任意）: `npm run dev`（Docusaurus）

### v0.21〜v0.28 で追加された主な機能

- **Riverbed Memory による suppression**（[#687](https://github.com/s977043/river-review/issues/687)）: `river suppression add --fingerprint <fp> --feedback accepted_risk` で確定済み指摘の再表示を抑止する。`memory.suppressionEnabled: false` で gate を一時バイパス可能。
- **Secret redaction**（[#692](https://github.com/s977043/river-review/issues/692)）: repo-wide context と LLM プロンプトに対する多段階 redaction。`security.redact.*` でカテゴリ／allowlist／denyFiles を制御する。
- **Context budget / ranking / reviewMode**（[#689](https://github.com/s977043/river-review/issues/689)）: `context.budget` で token／char 上限を制御。`context.ranking.enabled` で近接度ベースの並び替えを有効化。`context.reviewMode: tiny | medium | large` でプリセット budget を切替。
- **Repo-wide eval suite**（[#688](https://github.com/s977043/river-review/issues/688)）: `npm run eval:repo-context` が detection / context lift / false positive の 3 指標を出力する。

詳細は [`pages/guides/repo-wide-review.md`](pages/guides/repo-wide-review.md) および [`pages/reference/config-schema.md`](pages/reference/config-schema.md) を参照。

## river-review プラグインの導入

### Claude Code

river-review は同一リポジトリ内のマーケットプレイスから Claude Code プラグインとして配布されます。

1. マーケットプレイスを追加（GitHub ショートハンド）:

   ```text
   /plugin marketplace add s977043/river-review
   ```

   再現可能なインストールが必要ならタグを固定: `/plugin marketplace add s977043/river-review@v1.14.0`。

2. プラグインをインストール:

   ```text
   /plugin install river-review@river-review-marketplace
   ```

3. 再起動せずに有効化:

   ```text
   /reload-plugins
   ```

得られるもの（プラグイン名で名前空間化されます）:

- コマンド: `/river-review:review-local`, `/river-review:challenge`, `/river-review:skill`, `/river-review:check`, `/river-review:pr`
- エージェント: `river-review`（スキルルーティング型のコードレビュー・オーケストレーター）
- スキル: オーケストレーターに加えて `river-review-code`, `river-review-security`, `river-review-performance`, `river-review-architecture`, `river-review-testing`, `adversarial-review`, `river-review-docs`—`/river-review:<skill-name>` で呼び出せます

管理: `/plugin enable|disable|uninstall river-review@river-review-marketplace`。

インストールせずにローカルで開発・テストする場合:

```text
claude --plugin-dir .
```

### Codex

Codex も Claude Code と同じプラグインマーケットプレイスに対応しています。両者は同一の `.claude-plugin/marketplace.json` を共有するため、Claude Code と同じ手順で導入できます。

```text
codex plugin marketplace add s977043/river-review
```

再現可能なインストールが必要ならタグを固定します: `codex plugin marketplace add s977043/river-review@v1.14.0`。

Codex は skills と interface メタデータをリポジトリ同梱の `.codex-plugin/plugin.json`（Codex ネイティブ manifest）から読み込みます。マーケットプレイス追加時に、専門レビュー skill（`river-review-code` / `-security` / `-performance` / `-architecture` / `-testing` / `adversarial-review` / `-docs`）がネイティブに登録されます。

#### 代替手段: 手動コピーイン（フォールバック）

マーケットプレイスが使えない環境では、テンプレートとスキルを手動でコピーインできます。

1. Codex 連携テンプレートをプロジェクトにコピーします:

   ```text
   cp templates/agent-workflow/codex/AGENTS.md ./AGENTS.md
   ```

2. レビュースキルを Codex から利用できるよう、スキルディレクトリをプロジェクトにコピーします（または本リポジトリのチェックアウトを Codex に参照させます）:

   ```text
   cp -R skills/agent-skills ./skills
   ```

3. `AGENTS.md` からスキルを参照し、自分用の `.codex/config.toml`（`approval_policy`, `sandbox`）を追加します—本リポジトリの `.codex/` 設定は環境依存のためテンプレートとしては配布されません。

Codex（および Cursor）の完全なセットアップは `templates/agent-workflow/README.md` を参照してください。手動コピーインを使う場合、Codex 側は git のみでバージョン管理されるため、アップグレード時は再コピーが必要です。

## AI エージェント運用

- ルートの `AGENTS.md` が AI コーディングエージェント向けの SSOT です。
- `AGENT_LEARNINGS.md` には、再利用できる確定済みの学びだけを追加します。
- 秘密情報、個人情報、一時的なメモはどちらにも書きません。

### Codex を project-local config で使う

Codex 用の project-local config は [`.codex/config.toml`](./.codex/config.toml) にあり、**opt-in** です。通常の Codex 利用には影響しません。このリポジトリ設定を使うときだけ、以下のいずれかで起動します。

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
CODEX_HOME="$REPO_ROOT/.codex" codex -C "$REPO_ROOT"
npm run codex:local -- "AGENTS.md を読んで、このブランチの作業計画を出して"
```

非対話で実行したい場合:

```bash
npm run codex:exec -- "review this branch"
```

運用上の前提:

- project-local config は安全寄りの既定値だけを持ち、モデル選択や web search は CLI 引数で都度上書きします。
- レビューや PR 準備の前には、少なくとも `npm run lint` と `npm test` を実行してください。
- `src/` と `docs/` は要確認パスです。変更が必要な場合は、先に明示的な許可を取ってください。

### ローカルレビュー実行（river run .）

> **注**: River Review は npm を公開しないため、`river` CLI はリポジトリ内で `npm run river -- ...` として実行します（[はじめる](#はじめる)）。プラグインのレビューは CLI 非依存です（[プラグインの導入](#river-review-プラグインの導入)）。

1. リポジトリ内では `npm run river -- run . --dry-run` で現在の差分を対象にローカルレビューを実行（GitHub への投稿なし）
2. `--debug` を付けるとマージベース、対象ファイル一覧、プロンプトのプレビュー、トークン見積もり、diff 抜粋を標準出力へ表示
3. OpenAI の LLM を使う場合は `OPENAI_API_KEY`（または `RIVER_OPENAI_API_KEY`）を設定して `river run .` を実行。未設定時はスキルベースのヒューリスティックコメントでフォールバック
4. `--dry-run` は外部 API を呼ばず標準出力のみ。`--phase upstream|midstream|downstream` でフェーズ指定も可能（デフォルトは `RIVER_PHASE` 環境変数または `midstream`）
5. コンテキスト/依存の制御: `RIVER_AVAILABLE_CONTEXTS=diff,tests` や `RIVER_AVAILABLE_DEPENDENCIES=code_search,test_runner` を設定すると、スキル選択時に要求を満たさないものを理由付きでスキップできます（未設定の場合は依存チェックをスキップ）。
6. CLI で直接指定する場合: `--context diff,fullFile` や `--dependency code_search,test_runner` フラグで環境変数を上書きできます（逗号区切り）。
7. 依存のスタブ有効化: `RIVER_DEPENDENCY_STUBS=1` を指定すると、既知の依存（`code_search`, `test_runner`, `coverage_report`, `adr_lookup`, `repo_metadata`, `tracing`）を「利用可能」とみなしてスキップを防ぎます。実装準備中の環境でプランだけ確認したいときに使用してください。

### CLI Runnerインターフェイス（runners/cli）

新しいCLIインターフェイスにより、コアランナー機能に直接アクセスできます:

- `river review [files...]` - ファイルをレビュー（実行プラン生成とスキル選択）
- `river eval <skill>` - スキル定義の検証と評価
- `river eval --all` - すべてのスキルを評価
- `river create skill` - 新しいスキルをテンプレートから作成

詳細は [runners/cli/README.md](./runners/cli/README.md) を参照してください。

## Project-specific review rules

- リポジトリルートに `.river/rules.md` を置くと、プロジェクト固有のレビューポリシーが LLM プロンプトへ自動注入されます（`river run .` と GitHub Actions の双方で有効）
- ファイルが無い/空の場合は従来通り。読み込みエラー時のみ失敗します
- 例（.river/rules.md）:
  - Next.js App Router を前提とし、`pages/` ディレクトリは使用しない
  - React サーバーコンポーネントを優先し、クライアントコンポーネントは必要な場合のみ使う
  - ビジネスロジックは hooks ではなく service モジュールに寄せる

## Diff Optimization（差分最適化）

- River Review は lockfile や Markdown、コメント・フォーマットのみの変更を自動で除外し、LLM に渡すトークン量を削減します
- 大きな差分はハンク単位で圧縮し、必要な変更周辺のみを送信してコストとノイズを低減します
- `river run . --debug` で最適化前後のトークン見積もりと削減率を確認できます

## スキルと拡張性

River Review は「設定」ではなく「スキル」を追加することで成長します。`skills/` ディレクトリに新しいスキル定義ファイル（Markdown または YAML）を置くだけで、エージェントは自動的にそれを学習し、適切なフェーズで適用します。

### スキルの定義（Manifest-driven）

スキルは以下の柔軟なフォーマットで定義できます。

**1. Markdown 形式（推奨）**:
フロントマターでメタデータを、本文で具体的な指示を記述します。

```markdown
---
id: my-custom-check
name: Custom Check
phase: midstream
files: ['src/**/*.ts']
---

ここにレビューの指示を書きます。
```

`phase` は単一値/配列どちらも許容される点に注意してください。
`phase` / `files` は `trigger` コンテナ内にまとめても構いません（`trigger.phase`, `trigger.files`）。

**2. YAML 形式**:
構造化されたメタデータと指示を単一の YAML ファイルで記述します。

```yaml
metadata:
  id: security-check
  name: Security Review
  phase: [midstream, downstream] # 複数フェーズに対応
  files: ['**/*.ts', 'Dockerfile']
instruction: |
  セキュリティチェックの具体的な指示...
```

`trigger` を使う例:

```yaml
metadata:
  id: security-check
  name: Security Review
  trigger:
    phase: [midstream, downstream]
    files: ['**/*.ts', 'Dockerfile']
instruction: |
  セキュリティチェックの具体的な指示...
```

### ディレクトリ構成のベストプラクティス

`skills/` 配下は自由に構成できますが、以下の構成を推奨します。

- `skills/core/`: 標準搭載スキル
- `skills/<stream>/community/`: コミュニティ提供や特定ライブラリ向けスキル（例: `skills/midstream/community/`）
- `skills/private/`: プロジェクト固有の非公開スキル

Agent Skills 仕様のパッケージは `skills/agent-skills/` に配置し、`SKILL.md` + `references/` を基本構成とします（River Review のスキーマ検証対象外）。

### LLM ベースのスキル選択（Skill Planner）

LLM を使ったスキル選択はプランナー関数を差し込むだけで利用できます。具体例は `pages/guides/skill-planner.md` のミニマム実装例を参照してください。LLM 未指定の場合は従来通り決定論的に並び替えて実行します。

Planner 統合後の全体アーキテクチャ（metadata → loader → planner → runner）は `pages/explanation/river-architecture.md` にまとめています。

Planner の出力品質を簡易評価する手順とメトリクスは `pages/guides/planner-evaluation.md` を参照してください（`npm run planner:eval` で実行）。

```markdown
---
id: code-quality-sample
name: Sample Code Quality Pass
description: Checks common code quality and maintainability risks.
phase: midstream
applyTo:
  - 'src/**/*.ts'
tags: [style, maintainability, midstream]
severity: minor
---

- Instruction text for the reviewer goes here.
```

- サンプル: `skills/upstream/architecture-sample/SKILL.md`, `skills/midstream/code-quality-sample/SKILL.md`, `skills/downstream/test-review-sample/SKILL.md`
- examples: `examples/README.md`
- スキーマ: スキルメタデータは `schemas/skill.schema.json`, レビュー出力は `schemas/output.schema.json`
- 参考: スキルスキーマの詳細は `pages/reference/skill-schema-reference.md`、Riverbed Memory の設計ドラフトは `pages/explanation/riverbed-memory.md`
- 既知の制限: `pages/reference/known-limitations.md`

## AI レビュー標準ポリシー

River Review は、品質と再現性を保つための標準レビューポリシーに従って動作します。このポリシーは、評価方針・出力形式・禁止事項を定義し、建設的で具体的なフィードバックを提供します。

- **評価方針**: 差分からの意図理解、危険性の特定、影響範囲の評価
- **出力形式**: Summary（要約）、Comments（具体的指摘）、Suggestions（改善提案）
- **禁止事項**: 過度な推測、抽象的なレビュー、不適切なトーン、範囲外の指摘

詳細は [AI レビュー標準ポリシー](pages/reference/review-policy.md) を参照してください。

## ドキュメント設計

River Review の技術ドキュメントは、[Diátaxis ドキュメントフレームワーク](https://diataxis.fr/) に基づいて構成しています。日本語がデフォルト言語で、英語版は `.en.md` 拡張子の別ファイルとして管理します（差分がある場合は日本語版を優先）。
公開ドキュメントの正（Single Source of Truth）は `pages/` で、`docs/` は内部資料のみに限定します。詳細は `docs/policy/DOCUMENTATION.md` を参照してください。

ドキュメントは次の 4 種類に分類されます。

- Tutorials（チュートリアル）: 学習志向。最初の成功体験のためのレッスン。
- Guides（ハウツーガイド）: タスク志向。特定のゴールを達成するための手順。
- Reference（リファレンス）: 仕様・API・スキーマなどの事実の一覧。
- Explanation（解説）: 背景・設計思想・なぜそうなっているかの説明。

`/docs` 配信（ソースは `pages/`）で上記 4 種をマッピングし、ファイル名で言語を表します。

- `pages/tutorials/*.md`（日本語）と `pages/tutorials/*.en.md`（英語）
- `pages/guides/*.md` と `pages/guides/*.en.md`
- `pages/reference/*.md` と `pages/reference/*.en.md`
- `pages/explanation/*.md` と `pages/explanation/*.en.md`

## ロードマップ

コンセプト刷新（2026-05）に伴い、Roadmap は以下の 7 Epic で構成しています。状態列は最新の安定版リリース時点の実装到達点を示します。

| Epic                                       | 内容                                                                                                         | 状態                                                                                                                                                                                                                                               |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Epic 0**: Official Skill Pack            | 公式 Skill Pack と最小 Registry（security / a11y / migration-safety / dependency-policy / plan-conformance） | Partial — community tier で modern-web-semantic / modern-web-performance が landed ([#873](https://github.com/s977043/river-review/pull/873) / [#875](https://github.com/s977043/river-review/pull/875))。公式 Skill Pack の registry 整備は未着手 |
| **Epic 1**: First-Run Adoption             | プラグイン / GitHub Actions / `npm run river` での 10 分 Quick Start                                         | Partial — プラグイン・GitHub Actions・リポジトリ内 CLI の 3 経路を提供。**npm 配布は方針として行わない**（npm publish ワークフローは削除済み、[#800](https://github.com/s977043/river-review/issues/800) は not planned でクローズ）               |
| **Epic 2**: SDLC Gates                     | `plan` / `exec` / `verify` CLI 安定化、artifact-input-contract v1                                            | Partial — `plan` / `exec` は v0.53.0 で安定（silent-skip 5/6 解消済み）。`exec --plan` replay execution は v0.68.0 でリリース済み（[#935](https://github.com/s977043/river-review/pull/935)）。`verify` 実行は未実装                               |
| **Epic 3**: Concept Refresh                | README / vision / intro 刷新                                                                                 | Implemented — v0.51.0 でランディング ([#860](https://github.com/s977043/river-review/pull/860))                                                                                                                                                    |
| **Epic 4**: Skill Authoring and Governance | `npm run river create skill`、catalog、contribution policy                                                   | Planned — registry.yaml 拡張と contribution policy が未着手                                                                                                                                                                                        |
| **Epic 5**: Evaluation Observability       | CI 回帰、skill バッジ、dashboard                                                                             | Planned — promptfoo eval は per-skill 基盤あり、全体 dashboard 化は未着手                                                                                                                                                                          |
| **Epic 6**: Docs IA and Onboarding         | first-run / skill authoring / CI operation の動線再設計                                                      | Partial — `docs/review/troubleshooting.md` 整備済み ([#866](https://github.com/s977043/river-review/pull/866), [#872](https://github.com/s977043/river-review/pull/872))。Quick Start / Skill authoring の動線は Epic 1 と並行                     |

凡例: **Implemented** = 主要受け入れ条件を達成 / **Partial** = 一部到達、残スコープあり / **Planned** = 着手予定。

従来の柱（フェーズ別レビュー拡張、Riverbed Memory、Evals/CI 連携）は引き続き有効で、上記 Epic に吸収されます。

進捗のソース・オブ・トゥルースは Milestones と Projects です（README の箇条書きは概観のみ）。

- Milestones: [river-review/milestones](https://github.com/s977043/river-review/milestones)
- Projects: [リポジトリの Projects ページ](https://github.com/s977043/river-review/projects)

（任意）Issue に `m1-public` / `m2-dx` / `m3-smart` / `m4-community` のいずれかを付与すると、Milestone を自動で設定します（`.github/workflows/auto-milestone.yml`）。

## トラブルシューティング

詳細は `pages/guides/troubleshooting.md` を参照してください。

## OSS としての信頼性とセキュリティ姿勢

River Review は [OpenSSF Best Practices](https://www.bestpractices.dev/projects/13339) の Passing バッジを取得しています。これは、OSS プロジェクトとしてのドキュメント、ライセンス、貢献フロー、品質管理、脆弱性報告手順などの基本的なベストプラクティスを満たしていることを示すものであり、OpenSSF による安全性の保証や「脆弱性がないことの証明」ではありません。

River Review は、AI 支援開発におけるチーム所有の監査レイヤーとして設計されています。そのため、OpenSSF Best Practices への準拠に加えて、非公開の脆弱性報告経路（`SECURITY.md`）、CodeQL 解析、CI 検証、貢献ルール（`CONTRIBUTING.md`）を整備し、OSS としての基本的な品質・保守性・セキュリティ運用を明示しています。

## コントリビューション

ガイドラインは `CONTRIBUTING.md` を参照してください。Issue や PR を歓迎します。

- レビューチェックリスト: `pages/contributing/review-checklist.md`

## ライセンス

本リポジトリは複数ライセンス（ファイル種別ごと）を採用しています。

- `LICENSE-CODE`（MIT）: コードとスクリプト
  - 例: `src/**`, `scripts/**`, `tests/**`
- `LICENSE-CONTENT`（CC BY 4.0）: ドキュメント、テキスト、メディア
  - 例: `pages/**`, `skills/**`, `assets/**`,（ルート直下の）`*.md`
- `LICENSE`（Apache-2.0）: リポジトリ構成（scaffolding）と設定（configuration）
  - 例: `.github/**`, `docusaurus.config.js`, `sidebars.js`, `package*.json`, `*.config.*`, `.*rc*`

追加するファイルのライセンス方針に迷う場合は、PR で明示して相談してください。
