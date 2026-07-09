---
name: plan-preview
description: |
  Plan Mode の `<proposed_plan>` を出す直前に、計画の段階・依存関係・検証観点を一時HTMLで視覚確認したい時に使う agent-internal skill。Use this agent-internal skill to create a temporary HTML preview for a plan just before presenting `<proposed_plan>`. plugin配布だけで発火し、ユーザーにCLI実行を求めず、agentが `plan-preview` CLIでセッション限定URLを作り、本文に自然に差し込む。Triggers: planをグラフィカルに見たい, planを図で確認したい, この計画をHTMLでプレビューして, 計画をHTMLで確認したい, graphical plan review, proposed_planをプレビューして, 計画URLを入れて, preview this plan as HTML, show this plan visually, graphical plan preview, add a plan preview URL, preview the proposed plan。使用しない場面: 通常の最終HTML生成、レビュー可能な設計資料作成、コメント取り込み、恒久成果物の公開、外部アップロードが必要な図式化。Do not use for: final HTML artifacts, reviewable design docs, comment ingestion, permanent publication, or external-upload diagrams.
argument-hint: "[plan-preview-payload.json]"
strict_procedure: true
---

# plan-preview

## 役割

Plan Mode で正式な `<proposed_plan>` を提示する直前に、同じ計画内容を一時HTML previewとして出す。

このskillは利用者が手でコマンドを打つためのものではない。agentが計画本文を組み立てた段階で `plan-preview` CLIを呼び、返却JSONの `url` を `<proposed_plan>` 内へ自然に入れる。

Plan Mode 中の計画確認プレビューは、このskillが優先入口になる。通常の最終HTML成果物を作る `visual-html-renderer` の `document-model.json` → `render` → `validate` → `preview` フローへ流さない。

## Role

Create a temporary visual preview for a Plan Mode proposal. The user should not run the CLI manually. The agent calls `plan-preview`, receives a session-scoped URL, and places that URL naturally inside the `<proposed_plan>` text. During Plan Mode, plan preview requests should route here instead of the final-artifact `visual-html-renderer` document-model flow.

## Strict procedure profile

- Strictness: strict-procedure。Plan Mode の正式な実装基準は `<proposed_plan>` 本文であり、previewは判断補助として扱う。
- Hard gates: 外部サービス送信、shared state変更、永続ファイル出力、skill実行時にhookを動的に追加しない（plugin同梱の静的hook定義は対象外）。
- Forcing function: `plan-preview` CLI、TTL付き一時ディレクトリ、`Plan preview: <url>` 行、失敗時の明示。
- Completion receipt: `<proposed_plan>` 内に preview URL または `Plan preview: unavailable (<reason>)` を含める。

## 言語方針 / Language behavior

Follow the language of the latest user request for progress updates, preview labels, and the surrounding plan text. 日本語の計画依頼には日本語で、英語の計画依頼には英語で返す。`Plan preview: <url>` の固定ラベルは互換性のため英語のまま使ってよい。

## 発火条件

次のいずれかに当たる場合、このskillを使う。

- ユーザーが plan のグラフィカル表示、図示、preview URL、graphical plan review を求めている。
- ユーザーが Plan Mode 中に「この計画をHTMLでプレビューして」「計画をHTMLで確認したい」のように求めている。
- ユーザーが `preview this plan as HTML`, `show this plan visually`, `graphical plan preview`, `add a plan preview URL`, `preview the proposed plan` のように求めている。
- 計画に phase、依存関係、並列worker、検証層、リスク・前提の分岐があり、文字だけでは確認しづらい。
- plugin利用者の体験として、Plan Mode の本文に自然にURLが入っていることが求められている。

## Trigger Conditions

Use this skill when the user asks for a graphical plan view, diagrammed plan, preview URL, `preview this plan as HTML`, `show this plan visually`, `graphical plan preview`, `add a plan preview URL`, or `preview the proposed plan`. During Plan Mode, use this skill for plan preview requests instead of `visual-html-renderer`. Also use it when the plan has phases, dependencies, parallel workers, verification layers, or risk branches that are hard to inspect as plain text.

## 使用しない場面

- 最終成果物としてHTMLを生成する場合。これは `visual-html-renderer` を使う。
- レビュー可能な設計資料を作り、HTML上のコメントを取り込む場合。これは `reviewable-design-doc` を使う。
- planとは無関係な説明資料、恒久公開資料、Notion投稿、外部アップロードが必要な図式化。

## Do Not Use For

Do not use this skill for final HTML artifacts, reviewable design documents, comment ingestion, unrelated explainers, permanent publications, Notion posts, or diagrams that require external uploads.

## 入力payload

agentは `<proposed_plan>` に入れる直前の計画全文を `source_text` にそのまま入れる。
`summary` / `phases` / `key_changes` / `flow` / `test_plan` / `assumptions` / `sections` / `visual_notes`
は、全文の代替ではなくHTML上の補助ビューとして使う。preview用に情報を削らない。
CLI本文では読み取りにくい依存関係、判断材料、検証観点、未決事項は `sections` や `visual_notes`
で追加表示してよい。

```json
{
  "title": "Plan Preview",
  "summary": "この計画で何を達成するか",
  "source_text": "<proposed_plan> に出す計画本文全文",
  "phases": [
    {"title": "Phase 1", "detail": "調査と境界確認"}
  ],
  "key_changes": [
    "CLIを追加する",
    "skill metadataを追加する"
  ],
  "flow": [
    {"from": "計画作成", "to": "preview生成", "label": "agent内部"}
  ],
  "sections": [
    {
      "title": "判断材料",
      "content": "CLI本文では長くなりやすい背景・比較・依存関係を補足する",
      "items": ["元本文にない実装範囲は追加しない"]
    }
  ],
  "test_plan": [
    "unit test",
    "CLI疎通確認"
  ],
  "assumptions": [
    "hookは初期版では追加しない"
  ],
  "visual_notes": [
    "図とリストで依存関係を補助表示する"
  ]
}
```

外部画像URL、外部asset、機密情報、未確定のsecret値はpayloadに入れない。

## Input Payload

Put the full plan text that will appear in `<proposed_plan>` into `source_text`. Use summary, phases, key changes, flow, test plan, assumptions, sections, and visual notes only as supplemental HTML views, not as replacements for the original text. Do not drop information for preview generation; add dependencies, review context, verification details, and unresolved points that are hard to inspect in CLI text. Do not include external image URLs, external assets, secrets, or unconfirmed secret values.

## CLI手順

1. renderer repo root を作業ディレクトリにする。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
2. payloadを標準入力で渡して、次を実行する。preview は `auto` mode を既定にし、Tailscale IPv4 を検出できる場合は Tailscale URL を優先する。

```bash
python3 -m scripts.html_review_workbench.cli plan-preview --payload - --ttl 1800 --mode auto
```

3. 成功したら返却JSONの `url` を `<proposed_plan>` 本文に入れる。推奨表記:

```text
Plan preview: http://<tailscale-ip-or-127.0.0.1>:<port>/index.html
```

Codex sandbox内で Tailscale 検出に失敗する場合は、IPだけを先に取得して `HTML_REVIEW_WORKBENCH_TAILSCALE_IP=<tailscale-ip>` を渡してから `plan-preview --mode auto` を起動する。

4. 失敗しても計画提示を止めない。代わりに短い理由を入れる。

```text
Plan preview: unavailable (<short reason>)
```

5. `stop_command` はagent用の後片付け手段であり、通常はユーザーに実行させない。TTLで自動終了する。

## CLI Workflow

Run the CLI from the renderer repo root. Pass the plan payload through standard input with `python3 -m scripts.html_review_workbench.cli plan-preview --payload - --ttl 1800 --mode auto`. On success, insert `Plan preview: <url>` into `<proposed_plan>`. On failure, do not block the plan; insert `Plan preview: unavailable (<short reason>)`. The returned `stop_command` is for agent cleanup and normally should not be handed to the user.

## 計画本文との関係

- 正式な実装基準は `<proposed_plan>` のテキスト。previewだけに存在する項目を作らない。
- preview URLは本文の冒頭または末尾ではなく、計画の確認に自然な位置へ置く。
- preview作成のために計画を短縮しない。HTML上では元の計画本文を全文表示し、構造化ビューは補助表示として追加する。
- CLI本文では表現しにくい図示、依存関係、比較、検証の広がりはHTML側で情報量を増やす。ただし実装範囲や約束をpreviewだけに追加しない。
- previewの生成に失敗した場合でも、`<proposed_plan>` 自体は成立させる。

## Relationship to the Plan Text

The authoritative implementation plan is the `<proposed_plan>` text, not the preview alone. Do not add implementation scope that exists only in the preview. Place the URL where it helps review the plan. Do not shorten the plan to make preview generation easier. The HTML preview must show the original plan text in full, then add structured supplemental views for relationships, comparisons, verification context, and unresolved points that are hard to inspect in CLI text. If preview generation fails, still produce the plan with the unavailable reason.

## 禁止事項

- ユーザーに CLI を実行させない。
- Plan Mode の前にhookを自動追加しない。
- `output/` やplugin cacheにpreview成果物を残さない。
- 外部アップロードを使わない。
- Preview Runtime は `auto` mode で Tailscale IPv4 を優先し、検出できない場合だけ `127.0.0.1` にfallbackする。
- preview URLを正式な実装基準として扱わない。

## Guards

Do not ask the user to run the CLI. Do not auto-add hooks before Plan Mode. Do not leave preview artifacts in `output/` or plugin cache. Do not use external uploads. Prefer Tailscale IPv4 in `auto` mode and fall back to `127.0.0.1` only when needed. Do not treat the preview URL as the authoritative implementation plan.
