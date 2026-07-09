# Reviewable HTML Workbench

[![Test](https://github.com/u-ichi/reviewable-html-workbench/actions/workflows/test.yml/badge.svg)](https://github.com/u-ichi/reviewable-html-workbench/actions/workflows/test.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A Claude Code / Codex CLI plugin that lets you review agent-generated HTML documents with inline comments — and have the agent read those comments, reply, and improve the document in the next iteration.

![Overview](docs/images/overview.png)

## Overview

Agent workflows produce reports, design documents, and comparison tables — but turning those outputs into something you actually trust requires back-and-forth review. Chat-based feedback loses context: "fix the table in section 3" works once, but doesn't scale when you have dozens of comments across a long document.

Reviewable HTML Workbench solves this by putting the review conversation **inside the document itself**:

1. **Generate** — The agent produces an HTML bundle with structured sections, diagrams, and images.
2. **Review** — You open the preview, select any text or image, and leave a comment right where the issue is.
3. **Ingest** — The agent reads your comments, classifies each one, and writes replies explaining what it will change.
4. **Improve** — The agent updates the document, re-renders, and you see the changes in context.
5. **Repeat** — Keep commenting and refining until the document is ready.

Comments are attached to exact document ranges and persisted as structured JSON, so nothing is lost between iterations. When you're satisfied, export the final document as a single self-contained HTML file.

The plugin includes three skills. `visual-html-renderer` creates reviewable visual HTML documents. `reviewable-design-doc` builds review-ready design documents and feeds browser comments back into the agent workflow. `plan-preview` gives Plan Mode proposals a temporary HTML preview URL before implementation starts.

## Features

- **Inline Review Comments**: select any text or image in the preview to leave a comment. Comments are highlighted in the document with margin cards showing status, replies, and threading.
- **Automatic Agent Replies**: when you add a comment in the browser, the agent can read the selected text and surrounding document context, then write its reply back into the same thread.
- **Resolution-Gated Updates**: clarification threads stay in the document until you resolve them. Once the thread is resolved, the agent can apply the agreed document changes and notify the browser.
- **Plan Preview URLs**: when a plan needs visual review, the agent can include a temporary Reviewable HTML Workbench preview URL directly in the plan text.
- **Review Ingestion**: comments are classified as actionable, clarification, already addressed, and related states so the review conversation stays structured across iterations.
- **Publish & Download**: switch to a clean reading view with no review UI, then download a single self-contained HTML file with all CSS and images embedded. The exported file auto-detects OS light/dark theme.
- **Document Model**: schema-driven document input for predictable HTML generation.
- **HTML Rendering**: produces `index.html`, copied assets, and `renderer-manifest.json`.
- **Preview Server with Tailscale**: starts a session-scoped preview server, preferring Tailscale IPv4 and falling back to `127.0.0.1`; `0.0.0.0` bind is rejected.
- **Dark/Light Theme**: UI support for theme switching in rendered review documents.
- **Diagram + Image Support**: stores Mermaid sources, renders fallback diagrams, and attaches generated image assets to document model blocks.

## Installation

### Claude Code

Add the GitHub repository as a plugin marketplace and install:

```bash
claude plugin marketplace add u-ichi/reviewable-html-workbench
claude plugin install reviewable-html-workbench
```

Alternatively, clone the repository and install locally:

```bash
git clone https://github.com/u-ichi/reviewable-html-workbench.git
cd reviewable-html-workbench
claude plugins install .
```

For local development, run Claude Code with this plugin directory:

```bash
claude --plugin-dir /path/to/reviewable-html-workbench
```

### Codex CLI

Add the GitHub repository as a plugin marketplace, then add the plugin. This
repository's marketplace name is `reviewable-html-workbench-local`:

```bash
codex plugin marketplace add u-ichi/reviewable-html-workbench
codex plugin add reviewable-html-workbench@reviewable-html-workbench-local
```

To verify the configured marketplace name, check the left column:

```bash
codex plugin marketplace list
```

Or clone and register locally:

```bash
git clone https://github.com/u-ichi/reviewable-html-workbench.git
codex plugin marketplace add ./reviewable-html-workbench
codex plugin add reviewable-html-workbench@reviewable-html-workbench-local
```

Codex installs plugins as a whole plugin. It does not currently install only one language variant of this plugin. This plugin keeps one shared runtime and includes both English and Japanese skill instructions.

## Quick Start

You use Reviewable HTML Workbench by asking Claude Code or Codex CLI for a reviewable artifact. You do not normally run the Python commands yourself; the agent uses them behind the scenes and gives you a browser URL.

### 1. Ask for a reviewable HTML document

Use a natural request in your agent session:

```text
Create a reviewable design doc in HTML
```

or:

```text
Render this as a visual HTML report
```

The agent creates the document, validates it, starts a session-scoped preview, and returns a URL.

### 2. Review in the browser

Open the preview URL. Select text or images, add comments where the issue appears, and keep the review context inside the document instead of scattering it across chat messages.

### 3. Let the agent answer comments

When comments are added, the agent can read them, classify what needs action or clarification, and then write substantive replies into the same browser threads with `add-reply`. You can read the agent reply beside the original selected text.

### 4. Resolve threads to trigger updates

If the agent needs clarification, answer in the thread. When the thread is resolved, the agent can apply the agreed document changes, re-render the HTML, and show a browser notification so you can reload when ready.

### 5. Preview plans before implementation

For implementation plans, ask for a visual plan preview:

```text
Preview this plan as HTML
```

The plan text can include a temporary `Plan preview:` URL. The preview preserves the full proposed plan text and adds supplemental sections for phases, dependencies, review context, and test coverage that are hard to inspect in CLI text.

### Language behavior

The skills are bilingual. If you ask in English, the agent should use English for progress updates, preview handoff text, review replies, and final responses. If you ask in Japanese, it should use Japanese. Source material and quoted text are not translated unless you explicitly ask for translation.

## Skills

| Skill | Purpose | Trigger examples |
|---|---|---|
| `visual-html-renderer` | Turn content into a polished, reviewable HTML preview with diagrams, images, comments, and publish/download controls. | `visual HTML renderer`, `render this as HTML`, `turn this into HTML`, `create an HTML preview`, `generate a visual HTML report`, `make this a reviewable HTML document`, `diagrammed HTML report` |
| `reviewable-design-doc` | Create a review-ready design document, watch browser comments, reply in-thread, and apply resolved feedback. | `design doc`, `reviewable design doc`, `create a reviewable design doc`, `make a design doc in HTML`, `build a review-ready design document`, `ingest review comments`, `process review comments`, `reply to review comments`, `apply resolved comments` |
| `plan-preview` | Add a temporary Reviewable HTML Workbench preview URL that preserves the full proposed plan and adds supplemental visual context before implementation starts. | `graphical plan review`, `graphical plan preview`, `preview this plan as HTML`, `show this plan visually`, `add a plan preview URL`, `preview the proposed plan`, `この計画をHTMLでプレビューして`, `計画をHTMLで確認したい` |

## Agent / Developer CLI Reference

These commands are the internal interface used by the skills and by plugin developers. End users normally interact through Claude Code or Codex prompts and browser review.

All commands are exposed through:

```bash
python3 -m scripts.html_review_workbench.cli <command>
```

| Command | Description |
|---|---|
| `build-model` | Build a document model from natural content. |
| `render` | Generate an HTML bundle from a document model. |
| `check-model` | Check whether a document model is ready for final HTML rendering. |
| `attach-image` | Attach a generated image asset to an image-capable block in a document model. |
| `preview` | Start or describe a session-scoped preview runtime. |
| `plan-preview` | Create an ephemeral HTML preview for a proposed plan. |
| `plan-preview-stop` | Stop and clean up an ephemeral plan preview. |
| `ingest-review` | Read review comments, classify them, and save review-cycle state. |
| `validate` | Validate a generated HTML bundle. |
| `add-reply` | Add an agent reply to a comment thread in `comments.json`. |
| `check-gates` | Check whether unresolved clarification threads block document updates. |
| `watch-comments` | Stream browser comment change events from a running preview. |
| `notify-update` | Notify the browser that the document has been updated. |

## Schemas

The workbench is schema-driven:

- `schemas/document-model.schema.json`
- `schemas/comments.schema.json`
- `schemas/preview-session.schema.json`

These schemas define the rendered document model, persisted review comments, and preview session metadata.

## Development

Requirements:

- Python 3.11+
- No Python package dependencies for the core runtime
- Standard library tests with `unittest`

Run tests:

```bash
PYTHONPYCACHEPREFIX="$PWD/tmp/python-pycache" python3 -m unittest discover -s tests
```

Validate plugin manifests:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Validate the Claude Code plugin manifest:

```bash
claude plugins validate .
```

Check the CLI entrypoint:

```bash
python3 -m scripts.html_review_workbench.cli --help
```

## License

MIT

<details>
<summary>日本語</summary>

Reviewable HTML Workbench は、Claude Code / Codex CLI 向けの HTML レビュー用プラグインです。agent が生成した設計資料・調査レポート・比較表を HTML で出力し、本文の任意の箇所にレビューコメントを書き込めます。agent はそのコメントを読み取り、返信し、内容を改善して再出力します。コメントと改善を繰り返して、ドキュメントを一緒に磨き上げるワークフローを実現します。

完成したら、レビュー要素を除いた読者向けの HTML を 1 ファイルでダウンロードできます（CSS・画像埋め込み済み、OS テーマ自動検知対応）。

英語と日本語の両方の依頼に対応します。英語で依頼した場合は進捗、preview案内、レビューコメントへの返信、最終応答も英語に追従します。日本語で依頼した場合は日本語で返します。元資料や引用は、明示的に翻訳を依頼しない限り翻訳しません。

3つの skill を含みます。

- `visual-html-renderer`: HTML生成、図示、Preview Runtime、bundle検証。
- `reviewable-design-doc`: レビュー可能な設計資料作成、コメント自動検知、agent返信、解決後の設計反映。
- `plan-preview`: Plan Mode の計画本文に一時HTMLプレビューURLを追加。

## 日本語での使い方

通常は Python コマンドを直接実行せず、Claude Code や Codex CLI のチャットで自然に依頼します。agent が HTML bundle を生成し、検証し、ブラウザで開ける preview URL を返します。

### 1. レビュー可能な HTML を作る

設計資料をレビュー用 HTML として作りたい場合:

```text
設計資料をレビュー可能なHTMLで作って
```

```text
レビュー可能な設計資料
```

```text
設計資料をHTMLで
```

調査結果や比較表を図示つき HTML にしたい場合:

```text
この調査結果を図示つきHTMLでプレビューして
```

```text
html出力して
```

```text
HTMLにして
```

```text
HTMLで出して
```

```text
HTMLでプレビューして
```

```text
図示つきHTML
```

### 2. ブラウザでレビューする

agent が返した preview URL をブラウザで開きます。本文や画像を選択して、修正してほしい箇所にコメントします。チャットではなく HTML 上にコメントを残すことで、指摘箇所と文脈が失われません。

### 3. コメントを agent に確認・返信させる

コメントを入れ終わったら、次のように依頼します。

```text
レビュー終わったので確認して
```

```text
コメントを反映して
```

agent はコメント本文と選択範囲を読み、回答・受領・確認依頼が必要なコメントには `add-reply` で同じ HTML コメントスレッドへ返信します。チャットだけで回答して終わるのではなく、ブラウザ上のコメントと回答が対応する形で残ります。解決済みになった指摘は、document model に反映して再 render します。

### 4. 実装前に計画を HTML で確認する

計画の段階、依存関係、検証範囲を視覚的に確認したい場合:

```text
この計画をHTMLでプレビューして
```

```text
計画をHTMLで確認したい
```

```text
planをグラフィカルに見たい
```

```text
planを図で確認したい
```

```text
proposed_planをプレビューして
```

```text
計画URLを入れて
```

計画本文には一時的な `Plan preview:` URL が入り、元の計画本文を全文表示したうえで、CLI本文だけでは読み取りにくいフェーズ、依存関係、判断材料、検証観点を補助表示できます。

### 5. 日本語依頼時の言語方針

日本語で依頼した場合、進捗、preview 案内、レビューコメントへの返信、最終応答は日本語になります。元資料や引用は、明示的に翻訳を依頼しない限り翻訳しません。

### 6. インストール

```bash
# Claude Code（GitHub から直接）
claude plugin marketplace add u-ichi/reviewable-html-workbench
claude plugin install reviewable-html-workbench

# Codex CLI（GitHub から直接）
codex plugin marketplace add u-ichi/reviewable-html-workbench
codex plugin add reviewable-html-workbench@reviewable-html-workbench-local
```

Codex CLI で marketplace 名を確認したい場合は `codex plugin marketplace list` の左列を見ます。

Codex CLI は plugin 全体を導入する形で、現行の公開操作では言語だけを選んでインストールする方式ではありません。この plugin は同じ runtime に英語・日本語の skill 文書を同梱します。

テストは次のコマンドで実行します。

```bash
PYTHONPYCACHEPREFIX="$PWD/tmp/python-pycache" python3 -m unittest discover -s tests
```

</details>
