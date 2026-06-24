---
name: reviewable-design-doc
description: |
  要求・設計・アーキテクチャ・未決事項を整理し、レビュー可能な設計資料HTMLを作りたい時に使う。Use this skill to structure requirements, design, architecture, alternatives, decisions, and unresolved issues into a review-ready HTML design document. レビュー完了後はHTMLコメントを読み込み、設計へ反映し、確認が必要な場合はHTMLコメントスレッドへagent返信を書き戻す。Triggers: レビュー可能な設計資料, 設計資料をHTMLで, design doc, reviewable design doc, レビュー終わったので確認して, コメントを反映して, create a reviewable design doc, make a design doc in HTML, build a review-ready design document, ingest review comments, process review comments, reply to review comments, apply resolved comments。使用しない場面: 汎用HTMLレンダリングだけ、Notion投稿だけ、既存HTMLの見た目修正だけ。Do not use for: generic HTML rendering, Notion-only publishing, or small visual tweaks to existing HTML.
argument-hint: "[設計対象またはdocument-model.json] [--review-mode standalone|review-server] [--preview auto|tailscale|local|off]"
---

# reviewable-design-doc

## 役割

設計資料としてレビューできる構造を作り、最終HTML生成は `visual-html-renderer` に渡す。

レビュー完了後は `annotations/comments.json` を読み、明確な指摘は設計へ反映し、確認・回答が必要な指摘は `add-reply` CLI でHTMLの同じコメントスレッドへ書き戻す（チャットへの回答ではなくHTML上の返信として）。

## Role

Create a design document that can be reviewed in the browser. This skill owns design structure, review intent, comment ingestion, and comment-thread replies. Final HTML rendering is delegated to `visual-html-renderer`. After review, read `annotations/comments.json`, apply clear resolved feedback, and write clarification replies back into the same HTML comment thread with `add-reply`.

## 言語方針 / Language behavior

Follow the language of the latest user request for progress updates, final responses, and review handoff text. レビューコメントへの返信は、原則としてそのコメント本文の言語に合わせる。日本語コメントには日本語で、英語コメントには英語で返信する。設計本文や引用内容は、ユーザーが翻訳を求めない限り勝手に翻訳しない。

## 基本手順

1. 設計対象、読者、レビュー目的、完了条件を整理する。
2. 要求、制約、アーキテクチャ、代替案、意思決定、未決事項へ分解する。
3. レビュー観点とコメントしてほしい範囲を明示する。
4. 最初から `document-model.json` を作る。設計本文の下書きや中間成果物として `.md` を作らない。
5. 文書モデルには、要求、制約、アーキテクチャ、代替案、意思決定、未決事項、レビュー観点を、それぞれ現行rendererで有効なHTML表現を選んだblockとして入れる。
6. `image.generation_status=requested` のブロックがある場合は、`imagegen` skillで画像を生成し、`attach-image` CLIで文書モデルへ添付する。
7. `check-model` CLIで最終render前の文書モデル品質を検査する。
8. `render` CLIでHTML bundleを生成する。
9. `validate` CLIでHTML bundleを検証する。
10. ユーザー向け最終HTMLでは既定で `preview` CLIを `--mode auto` で起動し、返却JSONの `url` と `stop_command` を最終応答に必ず書く。
11. preview 起動直後に、Monitor ツールで `watch-comments` を開始する。これによりブラウザからのコメントを自動検知できるようになる。Monitor 起動コマンド: `python3 -m scripts.html_review_workbench.cli watch-comments --root <output-dir>`。イベント受信後の処理は「コメント自動回答と解決待ちゲート」セクションに従う。
12. ユーザーがコメントを入れたら「レビューコメントへの対応」セクションに従う。

## Basic Workflow

1. Clarify the design target, audience, review purpose, and completion criteria.
2. Split the material into requirements, constraints, architecture, alternatives, decisions, unresolved issues, and review points.
3. Create `document-model.json` from the start; do not create a `.md` draft as the design body.
4. Choose renderer-supported HTML blocks for each design unit.
5. Generate requested images with `imagegen` and attach them before rendering.
6. Run `check-model`, `render`, `validate`, and `preview`.
7. Start `watch-comments` after preview startup.
8. When the user adds comments, ingest them, classify them, reply in the HTML thread, and apply resolved feedback only after gates allow it.

## 設計資料モデル作成の規約

設計資料作成は、`.md` 原稿をHTMLへ変換する作業ではない。`reviewable-design-doc` は、設計内容を最初からレビュー可能なHTML bundleの情報設計として作る。

- 新規に設計資料を作る場合、最初の保存対象は `output/tmp/<purpose>/document-model.json` または `output/<YYYY-MM-DD>_<name>/document-model.json` にする。
- `.md` ファイルを設計本文の下書き、中間成果物、HTML化対象として作らない。
- 一時的に自然文入力を保存する必要がある場合だけ、`source.txt`, `input.txt`, `source-content.txt` のようなプレーンテキスト名を使う。
- 設計資料の本文は、見出し記号を含む原稿ではなく、`blocks[].title`, `blocks[].type`, `blocks[].heading_level`, `blocks[].content`, `review_required` を持つ文書モデルとして表現する。
- 大区分のブロック（背景・要求、アーキテクチャ、代替案比較、意思決定、未決事項など）には `heading_level: 2` を設定し、その配下の詳細ブロックには `heading_level: 3` を使う。各章の冒頭にはその章で扱う内容を示す導入段落を置く。
- 比較・代替案・評価軸は `html` block内の `<table>`、手順は `<ol>`、並列項目は `<ul>`、操作例・ログ・コマンドは `<pre><code>`、処理・依存・構成はdiagramブロック、決定・前提・注意はplain textのcallout、レビューしてほしい論点は専用のレビュー観点blockにする。
- `section`, `text`, `table` block typeは現行rendererに専用描画がないため、最終モデルでは使わない。
- diagramブロックはMermaid sourceを構造保存用に残し、生成画像を主表示にする。sourceに無い関係や判断を画像側で追加しない。
- 既存資料を取り込む場合も、既存ファイルをそのまま表示へ流し込まず、`visual-html-renderer` のHTML情報設計規約に従って文書モデルへ再構成する。
- `build-model` は最終HTMLモデルを作るplannerではなく、入力退避用のsource-capture draftに限る。既存本文やユーザー指定内容を取り込む場合も、そのdraftをそのままrenderせず、agentが設計構造を判断して文書モデルを直接作る。

## Design Document Model Rules

This skill does not convert a `.md` draft into HTML. It designs a reviewable HTML bundle from the beginning. Store new models under `output/tmp/<purpose>/document-model.json` or `output/<YYYY-MM-DD>_<name>/document-model.json`. If temporary natural-language input must be saved, use plain text filenames such as `source.txt`, `input.txt`, or `source-content.txt`. Use `heading_level: 2` for major sections and `heading_level: 3` for detailed subsections. Represent comparisons with tables, steps with ordered lists, parallel items with lists, commands and logs with code blocks, flows and dependencies with diagrams, and decisions or cautions with callouts.

## レビューコメントへの対応

ユーザーが「コメント入れた」「レビューした」「ingest review comments」「process review comments」「reply to review comments」「apply resolved comments」等でコメントの存在を知らせた時に開始する。文書作成（手順 1-10）とは独立したインタラクションであり、以下を毎回実行する。

IMPORTANT: レビューコメントへの回答は、必ず `add-reply` CLI で HTML コメントスレッドに書き戻す。チャットだけで回答を返して終わりにしてはならない。チャットでは補足や次のアクション提案のみ行い、コメントへの実質的な回答は HTML 側に書く。

### 手順

1. `ingest-review` CLI でコメントを分類し、`annotations/review-cycle-state.json` に状態を保存する。`ingest-review` はコメントスレッドへ返信を書かない。
2. 分類結果に関係なく、各コメントの `comment` と `selected_text` を読み、設計資料の該当箇所の文脈を踏まえてコメントの意図を理解する。
3. 回答・受領・確認依頼が必要なコメントには、実質的な回答を `add-reply` CLI で HTML コメントスレッドに書き戻す。
4. `actionable` なコメントは、解決待ちゲートが開いてから設計へ反映し、必要に応じて再 render する。
5. ユーザーにブラウザでの確認を依頼する。

### なぜチャット回答ではなく add-reply か

- ユーザーはブラウザ上でコメントと回答をセットで読む。チャットに書いた回答は、コメントの文脈から切り離される。
- 複数コメントがある場合、チャットでは各コメントへの回答の対応関係が崩れる。
- HTML 上の回答はコメントスレッドに紐づいて永続化される。チャットの回答はセッション終了で消える。

## Handling Review Comments

Start this workflow when the user says comments were added or asks to `ingest review comments`, `process review comments`, `reply to review comments`, or `apply resolved comments`. Always run `ingest-review` to classify comments and write review-cycle state only, inspect each comment's `comment` and `selected_text`, write substantive answers with `add-reply` when a thread needs a response, and apply actionable feedback only when the review gates allow it. Do not answer only in chat; the durable answer belongs in the HTML comment thread.

## コメント自動回答と解決待ちゲート

preview server 起動後に必ず実行する。手順 11 で Monitor ツールによる `watch-comments` を起動し、以下のフローでコメントの自動検知・回答・解決待ちを行う。

### watch-comments の起動

preview server 起動後、以下で SSE イベント監視を開始する。

```bash
python3 -m scripts.html_review_workbench.cli watch-comments \
  --root <output-dir>
```

agent は Monitor ツールでこのプロセスの stdout を監視する。各行は 1 行 JSON のイベント。

### 自動回答フロー

`watch-comments` から `comment_updated` イベントを受信したら:

1. `ingest-review --root <dir>` でコメントを分類し、状態だけを保存する。`ingest-review` の実行だけで返信が追加されることはない。
2. `comment` と `selected_text` を読み、設計資料の文脈を踏まえて実質的な回答を作成する。
3. 回答・受領・確認依頼が必要なコメントにだけ `add-reply --root <dir> --thread-id <id> --body "<reply>"` で HTML コメントスレッドに書き戻す。
4. 回答本文をコンソール（会話）にも出力する。ユーザーはブラウザとコンソールの両方で回答を確認できる。
5. `actionable` コメントにはまだ設計変更を適用しない。回答で受領を伝え、スレッド解決後に反映する旨を書く。
6. 自動回答が完了したら、設計変更には進まず停止する。`ingest-review` と `watch-comments` の出力に含まれる `gate` フィールドが `blocked` の場合、`document-model.json` を含むいかなる設計ファイルも変更してはならない。ゲートが `open` になるまで待機する。

### 解決待ちゲート

IMPORTANT: 未解決の `needs_clarification` スレッドがある間は、設計反映（ドキュメント修正）に進まない。

修正判断の前に以下でゲートを確認する:

```bash
python3 -m scripts.html_review_workbench.cli check-gates \
  --root <output-dir>
```

- `{"gate": "blocked", ...}` → 設計修正を行わない。コメントへの回答に専念する。
- `{"gate": "open", "resolved_actionable": [...]}` → 解決済みの actionable スレッド内容を document model に反映してよい。

### スレッド解決時の反映フロー

ユーザーがスレッドを「解決」した `comment_updated` イベントを受信したら:

1. `check-gates` でゲートが `open` であることを確認する。
2. `resolved_actionable` の各スレッドについて、スレッド全体の議論を読み、修正が必要か判断する。
3. 必要な修正を document model に適用する。
4. `render` CLI で再生成する。
5. `notify-update --root <dir> --message "コメント反映済み"` でブラウザに更新通知を送る。

### 修正完了のブラウザ通知

`notify-update` を実行すると、preview server 経由でブラウザに SSE イベントが送られ、画面上部にバナーが表示される。ユーザーは自分のタイミングでリロードして確認できる。自動リロードはしない。

```bash
python3 -m scripts.html_review_workbench.cli notify-update \
  --root <output-dir> \
  --message "コメント反映済み。リロードして確認してください"
```

## Automatic Comment Reply and Resolution Gate

After preview startup, monitor browser comment events with `watch-comments`. On each `comment_updated` event, run `ingest-review`, identify clarification threads, write same-thread replies with `add-reply`, and avoid design edits while unresolved clarification threads remain. Before applying any document changes, run `check-gates`. Apply resolved actionable feedback to the document model, re-render, and use `notify-update` so the browser shows an update notice without forcing an automatic reload.

## CodexでのCLI呼び出し

HTML生成時は、`visual-html-renderer` と同じ共通CLI入口を使う。
CLI実行前に、この `SKILL.md` の配置から renderer repo root を決める。
`skills/reviewable-design-doc/SKILL.md` の2階層上が renderer repo root であり、
そこに `scripts/html_review_workbench/cli.py` が存在することを確認する。
すべての `python3 -m scripts.html_review_workbench.cli ...` は renderer repo root を
作業ディレクトリにして実行する。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
cwdに `scripts/html_review_workbench/cli.py` が無い場合は、代替HTMLを作らず、
renderer repo rootへ移動してCLIを実行する。

```bash
python3 -m scripts.html_review_workbench.cli build-model \
  --text "<existing content when converting an existing source>" \
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

Codex / Claude では preview コマンドを一回限りの shell から起動することがあるため、標準手順では `--owner-pid` を渡さない。preview server は 24時間アクセスが無い場合に idle timeout で自動停止する。長寿命の所有プロセスが明確に分かる場合だけ `--owner-pid <pid>` を使ってよい。一回限りの shell の `$$` や `$PPID` は短命プロセスを指すため使わない。

Codex sandbox内で `tailscale ip -4` が設定ファイル読み取りに失敗する場合は、`visual-html-renderer` と同じく `python3 -m scripts.html_review_workbench.preview_host_resolve` で取得したIPv4を `HTML_REVIEW_WORKBENCH_TAILSCALE_IP` に渡してから `preview --mode auto` を起動する。

`preview` が `status: running` を返した場合、レビュー依頼の最終応答に `url` を必ず含める。ファイルパスだけで完了しない。標準では `--owner-pid` を渡さず、24時間アクセスが無い場合に idle timeout で自動停止させる。長寿命の所有プロセスが明確な場合だけ `--owner-pid <pid>` を使う。

レビュー取り込み時は、最新のpreview sessionまたはユーザー指定の成果物rootから `annotations/comments.json` を読み込む。

```bash
python3 -m scripts.html_review_workbench.cli ingest-review \
  --root <output-dir>
```

回答・受領・確認依頼が必要なコメントへagent replyを書き戻す場合は、`ingest-review` の分類結果から対象thread idを確認し、同じ成果物rootへ `add-reply` を実行する。

```bash
python3 -m scripts.html_review_workbench.cli add-reply \
  --root <output-dir> \
  --thread-id <thread-id> \
  --body "<agent reply body>"
```

document modelへ反映する場合は、完全一致置換に限定して明示的に実行する。

```bash
python3 -m scripts.html_review_workbench.cli ingest-review \
  --root <output-dir> \
  --model <document-model.json> \
  --apply-model
```

解決待ちゲートの確認:

```bash
python3 -m scripts.html_review_workbench.cli check-gates \
  --root <output-dir>
```

コメント変更の SSE 監視（Monitor ツールで stdout を監視する）:

```bash
python3 -m scripts.html_review_workbench.cli watch-comments \
  --root <output-dir>
```

ドキュメント更新通知をブラウザへ送信:

```bash
python3 -m scripts.html_review_workbench.cli notify-update \
  --root <output-dir> \
  --message "コメント反映済み"
```

## CLI Usage in Codex

Use the same shared CLI as `visual-html-renderer`. Resolve the renderer repo root from this `SKILL.md`: two levels above `skills/reviewable-design-doc/SKILL.md`. Run every `python3 -m scripts.html_review_workbench.cli ...` command from that repo root. If the current workspace does not contain `scripts/html_review_workbench/cli.py`, move to the renderer repo root instead of creating fallback HTML. Use `ingest-review`, `add-reply`, `check-gates`, `watch-comments`, and `notify-update` for review cycles.

## 完了時の確認

- `index.html` と `renderer-manifest.json` が生成され、`validate` が `status: ok` を返している。
- `check-model` が `status: ok` 相当の成功終了を返している。
- preview有効時は、レビュー用URLをユーザーへ提示している。
- レビュー取り込み後、`annotations/review-cycle-state.json` が生成されている。
- 回答・受領・確認依頼が必要なコメントには、`add-reply` によりHTMLコメントスレッド上のagent replyが追加されている。
- コメント反映でユーザー確認が必要な場合は、チャットだけでなくHTMLコメントへ返信済みであることを確認している。

## 実シナリオ検証

自動テスト pass と CLI の JSON 出力確認は、実シナリオ検証ではない。「動作確認」を求められた場合、以下のエンドツーエンドフローを実行する。

### レビュー取り込み・返信の検証

1. ユーザーが HTML 上にコメントを入れたことを確認する（ユーザーからの報告を待つ）。
2. `ingest-review` で `comments.json` を取り込み、分類結果を読む。
3. 各コメントの `comment` と `selected_text` を読み、設計資料の該当箇所の文脈を踏まえて、コメントの意図を理解する。
4. 回答・受領・確認依頼が必要なコメントに対して、コメント内容に対する実質的な返答を考え、`add-reply` で HTML コメントスレッドに書き戻す。
5. ユーザーに返信した旨を伝え、ブラウザで表示と内容の両方を確認してもらう。

検証の完了条件: ユーザーがブラウザ上で agent の返信を読み、内容と表示の両方が意図通りであることを確認した時点。CLI が正しい JSON を返したことではない。

## Real Scenario Verification

Passing unit tests and receiving valid CLI JSON are prerequisites, not real scenario verification. For an operational check, the user must add a browser comment, the agent must ingest it, read `comment` and `selected_text`, write the actual answer with `add-reply`, and the user must confirm in the browser that both the reply text and display are correct.

## ガード

- 設計として未確定の内容は確定事項と分けて書く。
- レビューコメント機能は必須で有効化する。
- IMPORTANT: レビューコメントに回答する時は `add-reply` で HTML コメントスレッドに書き戻す。チャットで回答内容を述べただけでは回答完了にならない。
- HTML低レベル実装をこのskillに重複実装しない。
- IMPORTANT: `comments.json` を Edit ツールや直接のファイル編集で変更してはならない。コメントの追加・返信は必ず `add-reply` CLI 経由で行う。CLI はスキーマ検証を通すため、不正なデータがファイルに書き込まれることを防ぐ。

## Guards

Separate unresolved design ideas from confirmed decisions. Keep review comments enabled. When answering comments, use `add-reply` to write back into the HTML thread; a chat-only answer is not completion. Do not duplicate low-level HTML implementation inside this skill.

IMPORTANT: Never edit `comments.json` directly with the Edit tool or any file-writing tool. All comment mutations must go through the `add-reply` CLI, which enforces schema validation and prevents malformed data from being written.

### 禁止事項 / Prohibited Actions

以下の操作は明示的に禁止する。違反するとデータ破損やレビュープロセスの破綻を引き起こす。

1. `comments.json` を Edit/Write ツールで直接変更すること。reply の追加は `add-reply` CLI のみ。
2. `check-gates` が `blocked` を返している状態で `document-model.json` を変更すること。
3. `ingest-review` の出力に `"gate": {"gate": "blocked", ...}` が含まれている状態で設計変更に着手すること。
4. `render` の stderr 警告を無視して次のステップに進むこと。

The following actions are explicitly prohibited. Violations cause data corruption or review process breakdown.

1. Editing `comments.json` directly with Edit/Write tools. Use `add-reply` CLI only.
2. Modifying `document-model.json` while `check-gates` returns `blocked`.
3. Starting design changes when `ingest-review` output contains `"gate": {"gate": "blocked", ...}`.
4. Ignoring `render` stderr warnings and proceeding to the next step.
