---
name: visual-html-renderer
description: |
  HTMLを最終成果物として生成・検証・プレビューしたい時に使う共通レンダラー。Use this shared renderer when the user wants content turned into a final, validated, previewable HTML artifact. 現行rendererの表現能力を前提にagentが文書モデルを直接設計し、表・リスト・コード・注記・図・生成画像を選んだHTML bundleとセッション限定のプレビューURLを提示する。Triggers: html出力して, HTMLにして, HTMLで出して, この内容をHTMLで出して, HTMLでプレビューして, HTMLレンダラー, HTML出力を共通化, 図示つきHTML, visual HTML renderer, render this as HTML, turn this into HTML, create an HTML preview, generate a visual HTML report, make this a reviewable HTML document, diagrammed HTML report。使用しない場面: Plan Mode 中の計画確認プレビュー、設計内容そのものの作成、Notion投稿だけ、既存HTMLの軽微な見た目修正だけ。Do not use for: Plan Mode proposal previews, creating the design content itself, Notion-only publishing, or minor visual tweaks to existing HTML.
argument-hint: "[document-model.json] [--output output/<date>_<slug>] [--preview auto|tailscale|local|off]"
strict_procedure: true
---

# visual-html-renderer

## 役割

HTML出力系skillの共通レンダラーとして、個別HTML生成ロジックを置き換える。

重い処理は `scripts/html_review_workbench/` のPython実装に委譲し、このskillは入力確認、呼び出し順、ガード、検証を担当する。

## Role

Use this skill as the shared renderer for HTML-output workflows. It replaces one-off HTML generation logic with a fixed flow: understand the requested content, design the document model, run the shared CLI, validate the bundle, and return a preview URL. Heavy implementation stays in `scripts/html_review_workbench/`; this skill owns input handling, workflow order, gates, and verification.

Plan Mode 中の計画確認プレビューには、このskillを使わない。その場合は `plan-preview` を使い、一時HTML previewとして扱う。`visual-html-renderer` は通常の最終HTML成果物、レポート、レビュー可能な文書のbundle生成だけを担当する。

Do not use this skill for Plan Mode proposal previews. Route those requests to `plan-preview`; this skill is only for final HTML artifacts, reports, and reviewable document bundles.

## Strict procedure profile

- Strictness: strict-procedure。HTML表現設計、文書モデルread-back、render、validate、preview URL提示までがこのskillの成果。
- Hard gates: 外部サービス送信、画像生成、外部アップロード、shared state変更は該当する承認ゲートに従う。
- Forcing function: rendererブロック対応表、render前自己レビュー、`check-model` CLI、Completion receipt。
- Completion receipt: HTML表現設計、生成物、検証、preview、未実施層を最終応答に必ず含める。

## 言語方針 / Language behavior

Follow the language of the latest user request for progress updates, final responses, preview handoff text, and user-facing summaries. 日本語の依頼には日本語で、英語の依頼には英語で返す。入力本文や引用内容は、ユーザーが翻訳を求めない限り勝手に翻訳しない。HTML内の見出しや本文は、元資料の言語、ユーザーの指定、レビュー対象読者に合わせる。

## 基本手順

0. Plan Mode 中の計画確認プレビュー、`<proposed_plan>` の視覚確認、計画URLの追加が目的なら、このskillではなく `plan-preview` を使う。
1. 文書モデルとレンダリングオプションを確認する。
2. 文書モデルが未指定の場合は、直前の成果物またはユーザー指定内容を読み、HTML表現設計フェーズで構成を決める。
3. 現行rendererのブロック型に合わせて、agentが `document-model.json` を直接作る。
4. 一時的な入力退避が必要な場合だけ `build-model` で source-capture draft を作ってよい。ただし draft は最終モデルではないため、そのまま `render` へ渡さない。
5. render前に `document-model.json` を読み返し、未再構成テキストの流し込みやrenderer非対応型の使用がないことを確認する。
6. `image.generation_status=requested` のブロックがある場合は、`imagegen` skillで画像を生成し、`attach-image` CLIで文書モデルへ添付する。
7. `check-model` CLIで最終render前の文書モデル品質を検査する。
8. `render` CLIでHTML bundleを生成する。
9. `validate` CLIでHTML、asset、comment schema、図・画像の非空を検証する。
10. ユーザー向け最終HTMLでは既定で `preview` CLIを `--mode auto` で起動し、返却JSONの `url` と `stop_command` を最終応答に必ず書く。
11. preview 起動直後に、Monitor ツールで `watch-comments` を開始する。これによりブラウザからのコメントを自動検知できるようになる。Monitor 起動コマンド: `python3 -m scripts.html_review_workbench.cli watch-comments --root <output-dir>`。自前の polling スクリプトではなく、この CLI を使うこと。イベント受信後の処理は `reviewable-design-doc` skill の「コメント自動回答と解決待ちゲート」セクションに従う。

## Basic Workflow

0. If the request is a Plan Mode proposal preview, `<proposed_plan>` visual check, or plan preview URL request, use `plan-preview` instead of this skill.
1. Check the document model and rendering options.
2. If no `document-model.json` is provided, inspect the user's content or the latest artifact and design the HTML structure yourself.
3. Create the final `document-model.json` directly using the renderer-supported block types.
4. Use `build-model` only as a source-capture draft when temporary input storage is needed; never pass that draft straight to `render`.
5. Read back the model before rendering and confirm that raw or unsupported content was not dumped into the model.
6. If image blocks request generation, use the `imagegen` skill and attach images with `attach-image`.
7. Run `check-model`, then `render`, then `validate`, then `preview`.
8. For user-facing artifacts, use `preview --mode auto` by default and include the returned `url` and `stop_command` in the final response.
9. Start `watch-comments` immediately after preview startup so browser comments can be detected.

## HTML情報設計の規約

HTML出力はテキスト変換ではなく、最終HTML bundleの情報設計として扱う。

- 入力本文の記号や行構造をそのまま表示へ流し込まない。
- まず内容の意味、用途、読者、比較軸、時系列、依存関係、操作手順、注意点を読み取り、HTML上の表現を選ぶ。
- 比較は表、手順は番号付きリスト、並列項目はリスト、注意・決定・前提はcallout、処理や依存関係はdiagramブロック、画面イメージや説明画像が有効な箇所はimageブロック、コマンドやログはコードブロックにする。
- diagramブロックはMermaid sourceを構造保存用に残し、既定では生成画像を主表示にする。生成画像が未添付の場合だけMermaid fallbackを表示する。
- 現行rendererのブロック型で表現が足りない場合、未再構成テキストへ戻さず、必要なブロック型やレンダリング拡張を検討する。
- 一時入力ファイルが必要な場合も `.md` は使わない。`source.txt`, `input.txt`, `source-content.txt` のようなプレーンテキスト名を使う。
- ユーザーへの進捗・最終報告では、`.md` やMarkdownという語をHTML出力の前提として扱わない。

## rendererブロック対応表

現行rendererで最終HTMLに使う表現は、実装上の描画挙動に合わせて選ぶ。

| block type | rendererの扱い | contentに書くもの |
|---|---|---|
| `html` | HTML片をそのまま挿入する | agentが設計した `<p>`, `<table>`, `<ul>`, `<ol>`, `<pre><code>` 等の構造化HTML |
| `callout` | HTML escapeしてcallout表示する | 決定、注意、前提などの短いプレーンテキスト。HTMLタグは書かない |
| `diagram` | Mermaid sourceを保存し、fallback previewまたは生成画像を表示する | `diagram_source` または `diagram.source` にMermaid source。sourceに無い関係を画像側で追加しない |
| `image` | 添付済み生成画像を表示する | `image.prompt`, `image.alt`, `image.caption`, `image.source_path` |
| `section` / `text` / `table` | 専用描画なし。通常段落へescapeされる | 最終HTMLモデルでは使わない。表は `html` block内の `<table>` で表現する |

`html` blockはraw insertされるため、外部入力をそのまま混ぜない。入力由来の文字列はagentが意味単位へ再構成し、必要な箇所だけescape済みHTMLとして入れる。

## 見出し階層

rendererは `<h1>` を文書タイトルに使う。本文ブロックの見出しは `heading_level` フィールドで制御する。

| heading_level | HTML タグ | 用途 |
|---|---|---|
| `2` | `<h2>` | 章見出し。文書を大きく区切る上位セクション。読者が目次で選ぶ単位 |
| `3` | `<h3>` | 節見出し。章の中を細分化するサブセクション |

- `heading_level` は必須。`2`（章）または `3`（直前の章の配下の節）を指定する。
- content 内に `<h2>` や `<h3>` を直接書かない。小見出しが必要な場合は `<h4>` を使う（renderer が content 内の見出しを自動シフトする）。

## html block 内の HTML 品質

`html` block の content に書く HTML は、セマンティックな構造を意識する。

- 表は `<table>` に `<thead>` と `<tbody>` を含め、ヘッダセルは `<th scope="col">` または `<th scope="row">` にする。
- 手順は `<ol>`、並列項目は `<ul>`、用語と説明の対は `<dl>` にする。
- 長い本文は `<p>` で段落分けし、`<div>` に流し込まない。
- 強調は `<strong>`（重要）と `<em>`（ニュアンス）を使い分ける。

## HTML表現設計フェーズ

文書モデルを作る前に、agentは次を決める。

- 読者と用途。
- 章構成。文書全体を概要→各論→結論のような読み手を誘導する流れに分ける。どのブロックが章（`heading_level: 2`）でどのブロックが節（`heading_level: 3`）かを先に決める。1つの章に節が偏りすぎないようバランスを取る。
- 主要な情報単位。
- 比較軸、時系列、依存関係、操作手順、決定、前提、未決事項。
- 各blockの `type`, `title`, `heading_level`, `content`, `review_required`。
- 各 `heading_level: 2` ブロックの冒頭に、その章で扱う内容の文脈を示す導入段落を置く。
- `html` block内で使う表、番号付きリスト、箇条書き、コードブロック、通常本文の構成。
- 図示または画像が必要な箇所と、Mermaid sourceまたは生成画像prompt。

入力がMarkdownや箇条書きで整理されていても、記号構造をそのまま変換しない。最終HTMLで読みやすい単位へ組み替えてから文書モデルにする。

## HTML Information Design Rules

Treat HTML output as information design for the final bundle, not as text conversion. Identify the audience, purpose, comparison axes, chronology, dependencies, steps, decisions, assumptions, and unresolved issues before writing the model. Use tables for comparisons, ordered lists for procedures, lists for parallel items, callouts for decisions or cautions, diagrams for flows and dependencies, images for useful visual explanations, and code blocks for commands or logs. Even when the input is Markdown or a list, restructure it into readable HTML blocks instead of mechanically converting the symbols.

## 入力モデル未指定時の規約

ユーザーが「html出力して」「HTMLにして」「HTMLで出して」「render this as HTML」「turn this into HTML」「create an HTML preview」「generate a visual HTML report」「make this a reviewable HTML document」「diagrammed HTML report」のように自然文で依頼し、`document-model.json` を指定していない場合も、このskillを発火させる。

その場合は、次の順で入力を決める。

1. ユーザーが明示した対象ファイル、本文、直前の成果物をHTML化対象にする。
2. 対象が曖昧で、直前の成果物も特定できない場合だけ、短く確認する。
3. 対象を特定できる場合は、確認で止めずにHTML表現設計フェーズへ進み、`output/tmp/<purpose>/document-model.json` または `output/<YYYY-MM-DD>_<name>/document-model.json` を直接作る。
4. 作成する文書モデルは `schema_version`, `document_id`, `title`, `generated_at`, `blocks` を必ず持つ。
5. `image.generation_status=requested` のブロックがある場合は画像生成と `attach-image` を完了してから、`check-model` → `render` → `validate` → `preview` まで進める。

`build-model` は最終HTMLモデルを作るplannerではない。入力を安全に保持する source-capture draft を作るだけで、Markdown表・リスト・コード等の機械変換や、内容に応じた表現選択は行わない。最終HTML出力では、agentがHTML表現設計フェーズで文書モデルを直接設計する。画像生成が外部サービス送信・機密情報・ユーザー承認を要する条件に当たる場合は、該当する承認ゲートに従う。設計判断、要求整理、レビュー観点の作成が主目的の場合は `reviewable-design-doc` を使う。

## When No Input Model Is Provided

Natural requests such as `render this as HTML`, `turn this into HTML`, `create an HTML preview`, `generate a visual HTML report`, `make this a reviewable HTML document`, and `diagrammed HTML report` should still trigger this skill. Use the explicitly named file, pasted content, or latest artifact as the HTML source. Ask only when the target cannot be identified. If the target is clear, proceed into HTML information design and create `output/tmp/<purpose>/document-model.json` or `output/<YYYY-MM-DD>_<name>/document-model.json` directly.

## render前自己レビュー

`render` CLIを呼ぶ前に、文書モデルを読み返して次を確認する。

- `heading_level: 2` のブロックが少なくとも1つある。`heading_level: 3` のブロックが最初の `heading_level: 2` ブロックより前に出現していない。
- 各 `heading_level: 2` ブロックの content が導入段落で始まっている。
- `html` block の `<table>` に `<thead>` と `<th>` がある。content 内に `<h2>` や `<h3>` を直接書いていない。
- `html` blockが未再構成テキストを `<p>` または `<pre>` だけで抱えていない。
- 比較対象がある場合は、`html` block内の `<table>` 等で比較軸を明示している。
- 手順がある場合は、`html` block内の `<ol>` 等で順序を明示している。
- 決定、前提、注意は `callout` または専用の `html` blockとして本文に埋もれないようにしている。
- `callout` blockの `content` にHTMLタグを書いていない。
- `section`, `text`, `table` block typeを最終モデルで使っていない。
- `diagram` blockは有効なMermaid sourceを持ち、画像生成promptはsourceに無い事実を追加していない。
- `image` blockは `source_path` が添付済みになるまで `render` しない。

## Pre-render Self Review

Before calling `render`, read the model back and confirm the heading hierarchy, introductory paragraphs, supported block types, table semantics, ordered steps, callouts, diagram sources, attached images, and absence of raw unstructured dumps. Do not render until requested images have been attached and unsupported block types have been removed.

## 生成画像promptの規約

- diagramブロックの生成画像は、Mermaid sourceのノード、ラベル、矢印方向、関係を保持する。sourceに無い事実、指標、関係、ブランド要素、装飾を追加しない。
- diagramブロックではMermaid sourceを `assets/diagrams/*.mmd` に保存し、HTML上は生成画像を主表示にする。生成画像が未添付の場合だけMermaid fallbackを表示する。
- imageブロックの生成画像は、白背景、十分な余白、資料向けの落ち着いた見た目、必要最小限の文字量を基本にする。
- 画面イメージは実在スクリーンショットではなくmockupとして生成する。公式ロゴ、ブランド名、UIラベル、数値、根拠を入力に無い形で作らない。
- 概念画像は直感理解の補助に限定する。事実関係、依存関係、数値、判断順を説明する場合はdiagramブロックを優先する。

## CodexでのCLI呼び出し

このskillは、低レベル実装へ直接importせず、共通CLIだけを呼ぶ。

CLI実行前に、この `SKILL.md` の配置から renderer repo root を決める。
`skills/visual-html-renderer/SKILL.md` の2階層上が renderer repo root であり、
そこに `scripts/html_review_workbench/cli.py` が存在することを確認する。
すべての `python3 -m scripts.html_review_workbench.cli ...` は renderer repo root を
作業ディレクトリにして実行する。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
cwdに `scripts/html_review_workbench/cli.py` が無い場合は、代替HTMLを作らず、
renderer repo rootへ移動してCLIを実行する。

```bash
python3 -m scripts.html_review_workbench.cli build-model \
  --text "<content>" \
  --output <document-model.json>

python3 -m scripts.html_review_workbench.cli attach-image \
  --model <document-model.json> \
  --block-id <generated-image-block-id> \
  --image <generated-image-path>

python3 -m scripts.html_review_workbench.cli check-model \
  --model <document-model.json>

python3 -m scripts.html_review_workbench.cli render \
  --model <document-model.json> \
  --output <output-dir>

python3 -m scripts.html_review_workbench.cli validate \
  --root <output-dir>

python3 -m scripts.html_review_workbench.cli preview \
  --root <output-dir> \
  --mode auto
```

Codex / Claude では preview コマンドを一回限りの shell から起動することがあるため、標準手順では `--owner-pid` を渡さない。preview server は 24時間アクセスが無い場合に idle timeout で自動停止する。

Codex sandbox内で `tailscale ip -4` が設定ファイル読み取りに失敗する場合は、preview本体をsandbox内で起動したまま、IPだけを小さいresolverで先に取得して渡す。

```bash
python3 -m scripts.html_review_workbench.preview_host_resolve

HTML_REVIEW_WORKBENCH_TAILSCALE_IP=<tailscale-ip> \
  python3 -m scripts.html_review_workbench.cli preview \
    --root <output-dir> \
    --mode auto
```

長寿命の所有プロセスが明確に分かる場合だけ `--owner-pid <pid>` を使ってよい。一回限りの shell の `$$` や `$PPID` は短命プロセスを指すため使わない。

ユーザーが明示的にプレビュー不要と言った場合、または自動テスト・fixture検証で副作用を抑える場合だけ `--mode off` を使う。ユーザー向け成果物では `--mode off` を既定にしない。
成果物はユーザーが直接読む最終HTMLなら `output/<YYYY-MM-DD>_<name>/`、再利用しない検証なら `output/tmp/<purpose>/` に置く。

## CLI Usage in Codex

Call only the shared CLI. Resolve the renderer repo root from this `SKILL.md`: two levels above `skills/visual-html-renderer/SKILL.md`. Run every `python3 -m scripts.html_review_workbench.cli ...` command from that repo root. If the current workspace does not contain `scripts/html_review_workbench/cli.py`, move to the renderer repo root instead of creating fallback HTML. Use `--mode off` only for explicit no-preview requests or tests; user-facing artifacts should default to `--mode auto`.

## Preview URL提示とライフサイクル

- `preview` が `status: running` を返した場合、最終応答に `url` を必ず含める。ファイルパスだけで完了しない。
- `preview` が `status: off` または `status: failed` の場合、URLが無い理由を明示し、可能なら `--mode auto` で再実行してURL提示まで進める。
- 標準では `--owner-pid` を渡さず、24時間アクセスが無い場合に idle timeout で自動停止させる。長寿命の所有プロセスが明確な場合だけ `--owner-pid <pid>` を使う。
- 手動停止が必要な時だけ、返却JSONの `stop_command` を使う。PIDなしで全previewを停止しない。

## Preview URL and Lifecycle

When `preview` returns `status: running`, include the `url` in the final response; a file path alone is not completion. If preview is off or failed, state the reason and try `--mode auto` when appropriate. Do not pass `--owner-pid` by default; the preview server stops after 24 hours without access. Use the returned `stop_command` only when manual cleanup is needed.

## 完了時の確認

- `index.html` と `renderer-manifest.json` が生成されている。
- `validate` が `status: ok` を返している。
- preview 有効時は提示URL、bind先、PID、停止方法をユーザーへ伝える。
- preview は `0.0.0.0` にbindしていない。

## 実シナリオ検証

自動テスト pass と CLI の JSON 出力確認は、実シナリオ検証ではない。「動作確認」を求められた場合、以下を実行する。

1. 実際の内容について `document-model.json` を作り、`render` → `validate` → `preview` を実行する。
2. preview URL をユーザーに提示し、ブラウザで表示を確認してもらう。
3. 表示に問題がある場合は、文書モデルを修正して再 render する。

検証の完了条件: ユーザーがブラウザ上で最終 HTML の表示を確認した時点。`validate` が `status: ok` を返したことではない。

## Real Scenario Verification

Passing unit tests and receiving valid CLI JSON are prerequisites, not real scenario verification. When the user asks for an operational check, create a real `document-model.json`, run `render` -> `validate` -> `preview`, provide the preview URL, and have the user confirm the rendered HTML in the browser. Verification is complete only after the browser-visible result is accepted.

## Completion receipt

最終応答には次を含める。

- HTML表現設計: 使用した主要block型と、その表現にした理由。
- 生成物: `index.html` と `renderer-manifest.json` の場所。
- 検証: `validate` の結果。
- preview: URL、bind先、PID、`stop_command`。
- 未実施: 画像生成、manual-acceptance-testing 等の未実施層があれば理由。

Final responses must include: HTML design choices, generated `index.html` and `renderer-manifest.json` paths, validation result, preview URL/bind/PID/`stop_command`, and any unperformed verification layers with reasons.

## ガード

- レンダラーは内容判断を作らない。
- 図示は入力された構造を補助する目的に限定する。
- ブラウザを自動で開かない。URL提示までを責務とする。
- Preview Runtime は `0.0.0.0` にbindしない。
- 外部サービスへ投稿・アップロードする場合は別途承認ゲートを通す。

## Guards

The renderer does not invent content decisions. Diagrams only support the provided structure. Do not open the browser automatically; return the URL. Never bind Preview Runtime to `0.0.0.0`. Any external posting, upload, or service transmission requires the appropriate approval gate.
