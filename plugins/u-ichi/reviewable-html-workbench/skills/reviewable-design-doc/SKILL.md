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

<!-- BEGIN SHARED: md-file-prohibition -->
設計資料作成は、`.md` 原稿をHTMLへ変換する作業ではない。`reviewable-design-doc` は、設計内容を最初からレビュー可能なHTML bundleの情報設計として作る。

- 新規に設計資料を作る場合、最初の保存対象は `output/tmp/<purpose>/document-model.json` または `output/<YYYY-MM-DD>_<name>/document-model.json` にする。
- `.md` ファイルを設計本文の下書き、中間成果物、HTML化対象として作らない。
- 一時的に自然文入力を保存する必要がある場合だけ、`source.txt`, `input.txt`, `source-content.txt` のようなプレーンテキスト名を使う。
<!-- END SHARED: md-file-prohibition -->
- 設計資料の本文は、見出し記号を含む原稿ではなく、`blocks[].title`, `blocks[].type`, `blocks[].heading_level`, `blocks[].content`, `review_required` を持つ文書モデルとして表現する。
- 大区分のブロック（背景・要求、アーキテクチャ、代替案比較、意思決定、未決事項など）には `heading_level: 2` を設定し、その配下の詳細ブロックには `heading_level: 3` を使う。各章の冒頭にはその章で扱う内容を示す導入段落を置く。
- 比較・代替案・評価軸は `html` block内の `<table>`、手順は `<ol>`、並列項目は `<ul>`、操作例・ログ・コマンドは `<pre><code>`、処理・依存・構成はdiagramブロック、決定・前提・注意はplain textのcallout、レビューしてほしい論点は専用のレビュー観点blockにする。
- `section`, `text`, `table` block typeは現行rendererに専用描画がないため、最終モデルでは使わない。
- diagramブロックはMermaid sourceを構造保存用に残し、生成画像を主表示にする。生成画像が未添付の場合、全diagram kindを同梱 mermaid.js でブラウザ描画し、standalone publishでは mermaid.js と図の拡大用scriptをHTMLへinline化する。Mermaid v11系の記法に準拠してsourceを書く。sourceに無い関係や判断を画像側で追加しない。
- Mermaidで描画される図は、図右上の拡大ボタンから全画面表示に切り替え、pan / zoom で詳細を確認できる。
- 既存資料を取り込む場合も、既存ファイルをそのまま表示へ流し込まず、`visual-html-renderer` のHTML情報設計規約に従って文書モデルへ再構成する。
- `build-model` は最終HTMLモデルを作るplannerではなく、入力退避用のsource-capture draftに限る。既存本文やユーザー指定内容を取り込む場合も、そのdraftをそのままrenderせず、agentが設計構造を判断して文書モデルを直接作る。

<!-- BEGIN SHARED: html-style-classes -->
## html block で使える表現部品

同梱の `style.css` には、`html` block 内でそのまま使える表現 class が実装済みである。比較・評価・推奨・決定がある内容では、素の `<table>` / `<p>` で終えず、該当する部品を選ぶ。

| 用途 | class | 書き方 |
|---|---|---|
| 表番号 + 表題 | `table-wrap` / `table-cap` / `t-no` / `t-title` / `table-scroll` | `<figure class="table-wrap"><figcaption class="table-cap"><span class="t-no">表 1</span><span class="t-title">3 案の比較</span></figcaption><div class="table-scroll"><table>…</table></div></figure>` |
| 表ヘッダの補助説明 | `axis-sub` | `<th scope="col">実装量<span class="axis-sub">行数の目安</span></th>` |
| 5 段階評価 | `rate` + `good`/`mid`/`low` + `r1`〜`r5` + `pips` / `pip` | `<span class="rate good r4"><span class="pips"><i class="pip"></i><i class="pip"></i><i class="pip"></i><i class="pip"></i><i class="pip"></i></span>容易</span>` (pip は常に 5 個。`rN` が塗る数、`good`/`mid`/`low` が色) |
| 可否・対応状況 | `tag-yes` / `tag-no` / `tag-cell-note` | `<td><span class="tag-yes">対応</span><span class="tag-cell-note">v2.0 以降</span></td>` |
| 桁揃え数値 | `num` | `<td><span class="num">1,024</span></td>` (表中の数値列に使う) |
| 推奨パネル | `reco` / `reco-tag` | `<div class="reco"><span class="reco-tag">推奨</span><p>案 B を採る。理由は…</p></div>` |
| 決定の枠囲み | `decision-panel` | `<div class="decision-panel"><p>…</p></div>` |
| コード内の着色 | `tok-k` (keyword) / `tok-f` (function) / `tok-s` (string) / `tok-c` (comment) / `tok-n` (number) | `<pre><code><span class="tok-k">def</span> <span class="tok-f">main</span>():</code></pre>` |

### 多軸の比較表 (`table.cmp`)

軸が 3 つ以上ある比較、または行数が多くて横スクロールが要る比較には `<table class="cmp">` を使う。通常の `<table>` と違い、ヘッダ行と最初の列 (比較軸) がスクロール中も固定され、推奨案の列を緑で浮かせられる。

| class | 効果 |
|---|---|
| `cmp` (table に付ける) | 比較表本体。`thead th` が sticky ヘッダになる。最小幅 720px のため `table-scroll` の中に入れる |
| `axis` (最初の列の `th` / `td` に付ける) | 比較軸の列が横スクロール中も左端に残る |
| `pick` (`<col>` / `th` / `td` に付ける) | 推奨する案の列を緑系で強調する。`<colgroup><col><col class="pick"></colgroup>` で列単位、または個別セルに付ける |

```html
<figure class="table-wrap">
  <figcaption class="table-cap"><span class="t-no">表 1</span><span class="t-title">3 案の比較</span></figcaption>
  <div class="table-scroll">
    <table class="cmp">
      <colgroup><col><col><col class="pick"><col></colgroup>
      <thead><tr>
        <th scope="col" class="axis">評価軸</th>
        <th scope="col">案 A</th><th scope="col" class="pick">案 B</th><th scope="col">案 C</th>
      </tr></thead>
      <tbody>
        <tr><th scope="row" class="axis">実装量<span class="axis-sub">行数の目安</span></th>
            <td><span class="num">40</span></td><td class="pick"><span class="num">180</span></td><td><span class="num">920</span></td></tr>
      </tbody>
    </table>
  </div>
</figure>
```

軸が 2 つだけ、または行が少なく横スクロールが不要な表では、`cmp` を使わず素の `<table>` にする。sticky と最小幅は狭い表では邪魔になる。

使い分けの基準:

- 比較表には `table-wrap` + `table-cap` で番号と表題を付ける。本文からの参照は「表 1」で行う。
- 軸が 3 つ以上あるなら `table.cmp` + `axis` を使い、推奨案の列に `pick` を付ける。
- 評価軸 (容易さ・成熟度・リスク等) は文字だけでなく `rate` の点表示でも符号化する。
- 推奨・決定は本文の段落に埋めず、`reco` または `decision-panel` で独立させる。
- 段落を文字の大きさで強調しない。強調したい段落があるなら、それは推奨・決定・注意のいずれかなので、`reco` / `decision-panel` / `callout` block のうち内容に合うものを使う。文書全体の導入は `metadata.deck` が担うので、節ごとに導入段落を作らない。
- これらは class 指定だけで効く。`style` 属性の直書きで同等の見た目を再実装しない。
- 色は `metadata.palette` の `brand` / `brand_soft` だけ主題に合わせて上書きできる。コントラスト比は `check-model` / `render` / `validate` が WCAG 4.5:1 で検査し、不足すると error で止まる (brand は最も薄い地色との比、brand_soft は本文色との比、両方指定時は 2 色の相互比も見る)。

## Style Classes Available in html Blocks

The bundled `style.css` ships ready-to-use presentation classes for `html` blocks. When the content contains comparisons, ratings, recommendations, or decisions, do not stop at bare `<table>` / `<p>`: use `table-wrap` + `table-cap` (numbered table captions), `axis-sub` (header sub-labels), `rate good|mid|low r1..r5` with five `pip` elements (dot ratings), `tag-yes` / `tag-no` / `tag-cell-note` (availability cells), `num` (tabular figures), `reco` + `reco-tag` (recommendation panel), `decision-panel` (decision box), and `tok-k` / `tok-f` / `tok-s` / `tok-c` / `tok-n` (code token coloring). Reference numbered tables from body text as "表 1" / "Table 1". These work by class alone; do not re-implement the same look with inline `style` attributes. Do not emphasize a paragraph by making its type larger — if a paragraph deserves emphasis it is a recommendation, a decision, or a warning, so use `reco`, `decision-panel`, or a `callout` block instead. The document-level intro is `metadata.deck`; do not add a per-section intro paragraph.

For comparisons with three or more axes, use `<table class="cmp">` inside `table-scroll`: the header row stays sticky while scrolling, `axis` on the first column keeps the comparison axis pinned during horizontal scroll, and `pick` on a `<col>`, `th`, or `td` tints the recommended option's column green. Keep plain `<table>` for narrow two-column comparisons — the sticky behavior and 720px minimum width get in the way there.
<!-- END SHARED: html-style-classes -->

<!-- BEGIN SHARED: html-design-guidance -->
## 表現の質の指針

見た目の判断に迷った時は、次の 4 つに従う。ユーザーが見た目の方向を明示した場合は、その指定が常に優先する。

1. **AI が作りがちな見た目を避ける。** 次の定番の組み合わせは、指定が無い限り選ばない: cream 地 (#F4F1EA) + serif 見出し + terracotta accent / near-black 地 + acid-green や vermilion の一点差し / 絵文字を節の目印にする / 全要素センタリング / 一様な大きい角丸 / 角丸カードの左端 accent バー。
2. **構造装飾は内容の事実を符号化する。** 01 / 02 / 03 のような番号は、内容が本当に順序を持つ時 (手順・時系列) だけ使う。区切り線・eyebrow・ラベルも、内容の区分を実際に表す時だけ入れ、装飾目的では入れない。
3. **読む文書と操作する画面で作法を変える。** 一覧・ダッシュボード的な内容は上から順に読まれず走査される。要約を詳細より先に置き、状態は数値だけでなく形 (rate の点、tag-yes の色、callout の左帯) でも符号化して、注意が要る箇所が一目で分かるようにする。
4. **余白は layout で作る。** 兄弟要素の間隔は `gap` を持つ flex / grid で作り、要素ごとの margin を積まない。幅の広い表・コード・図は自前の `overflow-x: auto` コンテナ (表は `table-scroll`) に入れ、ページ全体を横スクロールさせない。

## Design Quality Guidance

When unsure about visual choices, follow four rules; explicit user direction always wins. (1) Avoid stereotypical AI-generated looks — cream (#F4F1EA) with serif display and terracotta accent, near-black with a lone acid-green pop, emoji as section markers, centering everything, uniformly large border radii, accent bars on rounded cards. (2) Structural devices must encode facts: numbered markers (01/02/03) only when the content truly is a sequence; rules, eyebrows, and labels only when they mark real divisions. (3) Documents are read, dashboards are scanned: put summaries before detail and encode state in form (rating dots, tag colors, callout stripes), not numbers alone. (4) Create spacing with `gap` in flex/grid rather than stacked per-element margins, and give wide tables/code/diagrams their own `overflow-x: auto` container (`table-scroll` for tables) so the page body never scrolls sideways.
<!-- END SHARED: html-design-guidance -->

<!-- BEGIN SHARED: html-interactive-controls -->
## 操作部品 (触って試す / 触った結果を作業へ戻す)

読むだけでなく触って決める資料では、`html` block に操作部品を直接書ける。値を試すスライダー、切り替えのトグル、並べ替えできるカードなどが対象。

### 書ける範囲

- `html` block の中に `<script>` を inline で書ける。`onclick=` 等の inline event handler も使える。
- 外部 host からの読み込みは `check-model` が error にする (`<script src="…">` と `<link rel="stylesheet" href="https://…">` の両方)。bundle が手元で完結する性質を保つため。図表の描画ライブラリが要る場合は Mermaid の `diagram` block を使う。
- 部品の見た目は既存の class (`rate` / `tag-yes` / `num` 等) と揃える。inline `style` の直書きは最小限にする。

### 触った結果を保存する

同梱の `RHWState` を使う。preview server があれば `PUT /annotations/state/<name>.json` で保存し、端末をまたいで同じ状態を見せる。server が無い場合 (publish した standalone、`file://` で開いた場合) は localStorage に落ち、どちらも使えない環境ではメモリ上だけで動く。操作そのものは止まらない。

```html
<label>duration <input type="range" id="dur" min="0" max="2000" value="300"></label>
<output id="durOut">300</output>ms
<script>
  (async function () {
    var dur = document.getElementById("dur");
    var out = document.getElementById("durOut");
    // 保存済みの値があれば復元する
    var saved = await window.RHWState.load("tuning");
    if (saved && saved.duration) { dur.value = saved.duration; out.textContent = saved.duration; }
    dur.addEventListener("input", function () {
      out.textContent = dur.value;
      // 動かしている間の表示更新と一緒に呼んでよい。debounce が server への PUT をまとめる
      window.RHWState.save("tuning", { duration: dur.value }, { debounce: 300 });
    });
  })();
</script>
```

`<name>` は英数字とハイフン・アンダースコアだけ (最大 64 文字)。保存した内容は agent が `annotations/state/<name>.json` として読める。触って決めた結果を作業へ戻す経路がこれになる。文書の中で用途ごとに名前を分ける (`tuning` / `priority-order` など)。

連続して動く部品 (スライダー、テキスト入力) では `{ debounce: 300 }` を渡す。手元の保存 (localStorage) は毎回すぐ行い、server への書き込みだけを入力が止まってから 1 回にまとめる。これを渡さずに `input` で呼ぶと、つまみを端から端まで動かすだけで PUT が 100 回以上飛ぶ。

逆に `debounce` を渡さないのは、操作が 1 回で完結する部品 (ボタン、`dragend`、チェックボックス) のとき。その場で保存され、戻り値の `saved` が `remote` / `local` / `memory` のどれかになる。

`debounce` 付きで待っている間の戻り値は `superseded` になる (新しい値で予約が取り直された、という意味)。最後の呼び出しだけが実際の保存結果を返す。画面に保存状態を出す場合は `superseded` を「保存中」として扱う。

### 使う判断

- 値の範囲を試したい、順序を決めたい、選択肢を絞りたい場面で使う。読んで終わる資料には入れない。
- 操作した結果を agent が受け取る必要があるなら `RHWState.save()` を必ず呼ぶ。呼ばないと結果は画面上だけで消える。
- 操作部品を入れた資料は、`preview` で server 越しに開いて動作を確認する。`file://` で開くと状態が端末間で共有されない状態の確認になる。

## Interactive Controls (Try Values, Return the Result to the Session)

For documents where the reader decides by manipulating rather than only reading, write controls directly into an `html` block: sliders for trying values, toggles, reorderable cards.

Inline `<script>` and inline event handlers are allowed inside `html` blocks. Loading from an external host is rejected by `check-model` — both `<script src="…">` and `<link rel="stylesheet" href="https://…">` — so the bundle stays self-contained. Use the `diagram` block when you need diagram rendering.

To persist what the reader manipulated, use the bundled `RHWState`. With a preview server it saves through `PUT /annotations/state/<name>.json` so state is shared across devices; without one (published standalone, opened via `file://`) it falls back to localStorage, and to memory when neither is available. The interaction never breaks.

```html
<label>duration <input type="range" id="dur" min="0" max="2000" value="300"></label>
<output id="durOut">300</output>ms
<script>
  (async function () {
    var dur = document.getElementById("dur");
    var out = document.getElementById("durOut");
    var saved = await window.RHWState.load("tuning");
    if (saved && saved.duration) { dur.value = saved.duration; out.textContent = saved.duration; }
    dur.addEventListener("input", function () {
      out.textContent = dur.value;
      window.RHWState.save("tuning", { duration: dur.value }, { debounce: 300 });
    });
  })();
</script>
```

`<name>` accepts alphanumerics, hyphens, and underscores (64 chars max). Saved state is readable by the agent at `annotations/state/<name>.json` — that is the path by which a decision made in the browser returns to the session. Use distinct names per purpose (`tuning`, `priority-order`). For continuously moving controls (sliders, text inputs) pass `{ debounce: 300 }`: local storage is written on every call, while the server write is coalesced into one after input stops. Omit `debounce` for one-shot interactions (buttons, `dragend`, checkboxes). While a debounced write is waiting, `save()` resolves with `saved: "superseded"` — treat that as "saving" in any status display; only the final call reports the real result.

Add controls only when the reader needs to try values, decide an order, or narrow options; leave them out of read-only documents. If the agent must receive the outcome, `RHWState.save()` is required — otherwise the result stays on screen and disappears. Verify interactive documents through `preview` over the server, since opening via `file://` exercises the fallback path instead.
<!-- END SHARED: html-interactive-controls -->

<!-- BEGIN SHARED: mermaid-kinds -->
## Mermaid 対応 kind と最小サンプル

diagramブロックのMermaid sourceは、mermaid.js v11系が対応する記法から選ぶ。同梱済み `mermaid.min.js` がHTML上でSVGに置換する。

主要 kind:

| kind | 用途 |
|---|---|
| `flowchart` / `graph` | 処理・依存関係のフロー |
| `sequenceDiagram` | 相互作用・時系列メッセージ |
| `stateDiagram-v2` | 状態遷移 |
| `classDiagram` | クラス構造・継承・関連 |
| `erDiagram` | エンティティ関係 |
| `gantt` | 期間・スケジュール |
| `journey` | ユーザー体験の順序 |
| `timeline` | 時系列イベント |
| `mindmap` | 概念マップ・分類 |
| `pie` | 割合 |
| `gitGraph` | ブランチ・マージ |
| `requirementDiagram` | 要件・トレーサビリティ |
| `quadrantChart` | 2軸マトリクス |
| `sankey` | フロー量 |
| `xychart-beta` | 2次元数値プロット |
| `architecture-beta` | システム構成 |
| `block-beta` | ブロック配置 |
| `packet-beta` | パケット構造 |
| `kanban` | カンバンボード |
| `radar` | レーダーチャート |
| `treemap` | 階層構造の面積表現 |
| `zenuml` | ZenUML記法 |

最小サンプル:

`erDiagram`

    erDiagram
        CUSTOMER ||--o{ ORDER : places
        CUSTOMER {
            string id PK
            string name
        }
        ORDER {
            string id PK
            string customer_id FK
        }

`sequenceDiagram`

    sequenceDiagram
        participant User
        participant API
        User->>API: request
        API-->>User: response

`stateDiagram-v2`

    stateDiagram-v2
        [*] --> Idle
        Idle --> Running: start
        Running --> Idle: stop

`flowchart LR`

    flowchart LR
        A[Input] --> B{Decide}
        B -->|yes| C[Do it]
        B -->|no| D[Skip]

sourceの記法が不確かな場合は mermaid.js 公式docs (https://mermaid.js.org/) を参照する。schemaの `diagram_kind` は表示ラベル用のグループ名で、Mermaidの内部kind名と一致させる必要はない。

## Mermaid Kinds and Minimal Samples

Use Mermaid source supported by mermaid.js v11. The bundled `mermaid.min.js` renders diagram blocks into SVG in the browser, and rendered Mermaid diagrams can be opened from the zoom button for full-screen pan / zoom inspection. Common kinds include `flowchart` / `graph`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`, `gantt`, `journey`, `timeline`, `mindmap`, `pie`, `gitGraph`, `requirementDiagram`, `quadrantChart`, `sankey`, `xychart-beta`, `architecture-beta`, `block-beta`, `packet-beta`, `kanban`, `radar`, `treemap`, and `zenuml`. If syntax is uncertain, check the Mermaid docs. The schema `diagram_kind` is a display grouping label and does not need to match Mermaid's internal kind name.
<!-- END SHARED: mermaid-kinds -->

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
<!-- BEGIN SHARED: repo-root-resolution -->
CLI実行前に、この `SKILL.md` の配置から renderer repo root を決める。
`skills/reviewable-design-doc/SKILL.md` の2階層上が renderer repo root であり、
そこに `scripts/html_review_workbench/cli.py` が存在することを確認する。
すべての `python3 -m scripts.html_review_workbench.cli ...` は renderer repo root を
作業ディレクトリにして実行する。現在のチャットやworkspaceのcwdをrepo rootとして扱わない。
cwdに `scripts/html_review_workbench/cli.py` が無い場合は、代替HTMLを作らず、
renderer repo rootへ移動してCLIを実行する。
<!-- END SHARED: repo-root-resolution -->

<!-- BEGIN SHARED: cli-commands-core -->
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
<!-- END SHARED: cli-commands-core -->

<!-- BEGIN SHARED: preview-owner-pid-note -->
Codex / Claude では preview コマンドを一回限りの shell から起動することがあるため、標準手順では `--owner-pid` を渡さない。preview server は 24時間アクセスが無い場合に idle timeout で自動停止する。長寿命の所有プロセスが明確に分かる場合だけ `--owner-pid <pid>` を使ってよい。一回限りの shell の `$$` や `$PPID` は短命プロセスを指すため使わない。
<!-- END SHARED: preview-owner-pid-note -->

<!-- BEGIN SHARED: tailscale-sandbox-fallback -->
Codex sandbox内で `tailscale ip -4` が設定ファイル読み取りに失敗する場合は、`visual-html-renderer` と同じく `python3 -m scripts.html_review_workbench.preview_host_resolve` で取得したIPv4を `HTML_REVIEW_WORKBENCH_TAILSCALE_IP` に渡してから `preview --mode auto` を起動する。
<!-- END SHARED: tailscale-sandbox-fallback -->

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
