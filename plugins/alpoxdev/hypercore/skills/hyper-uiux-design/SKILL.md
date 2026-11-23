---
name: "hyper-uiux-design"
description: "Use this skill when the user asks to design an app or web screen and wants both a picture of it and the screen as HTML before real code - a login, onboarding, dashboard, or checkout screen, or a short flow of screens, for mobile, tablet, or web, in light or dark. It reads public UI references (UIBowl, Mobbin public pages) for patterns, settles tokens, renders one mockup image per screen via hyper-imagegen, builds one standalone HTML file per screen that matches that mockup, checks the match with a browser screenshot, and saves both with handoff notes under `.hyper/uiux-design/[slug]/`. Do not use it for one image that is not a product screen, a visual-direction brief or audit, production frontend or native code, or a requirements document."
compatibility: "Markdown only, with no bundled script. Needs file read and write under `.hyper/uiux-design/`, renders images via `../hyper-imagegen/SKILL.md` using the runtime's exposed image tool, and compares HTML in an already available browser (or reports the match check skipped). Never installs tools, logs into reference sites, or uses API keys."
---

Open the rules below as needed. Resolve bundled paths from this skill directory and project paths from the target workspace.

- [rules/reference-use.md](rules/reference-use.md)
- [rules/mockup-workflow.md](rules/mockup-workflow.md)
- [rules/mockup-is-evidence.md](rules/mockup-is-evidence.md)

# Hyper UIUX Design

> Show the screen before building it: a pattern-grounded mockup image paired with a matching standalone HTML screen, handed over as evidence rather than production code.

- **Purpose**: Design 1 to 6 app or web screens before implementation by settling tokens, abstracting public UI patterns, generating mockup images, building matching standalone HTML screens, and recording approval and handoff notes.
- **Do not use when**: Requesting a non-UI image, a code restyle/slop audit, production React/native implementation, bulk reference scraping, or a PRD/text wireframe.
- **Input**: Screen/flow request, platform (`mobile`, `tablet`, `web`), theme (`light`, `dark`, `both`), and optional project `DESIGN.md` or user references.
- **Output**: Mockup images, standalone `.hyper/uiux-design/<slug>/html/*.html` files, and Korean `.hyper/uiux-design/<slug>/mockup-notes.md` ending with one `Result:` line.

<output_language>

Default saved notes, chat answers, questions, and validation notes to Korean while preserving token names/values, file paths, URLs, compiled briefs, and rendered screen copy verbatim (`instructions/harness-engineering/references/skill-common-rules.md`).

</output_language>

<purpose>

- Put a shipped-grade mockup picture of each screen (complete copy, real density, one hierarchy, one accent, zero wireframe placeholder bars) in front of the user before writing production code.
- Ground screens in abstracted patterns from public references (never copying one screen, brand, or mark) and shared color, type, radius, and spacing tokens settled first.
- Build one standalone offline HTML file per approved screen (real text, inline SVG icons, zero embedded mockup image), compare it across 9 match bands in a browser, and hand over explicit contract vs non-contract notes.

</purpose>

<routing_rule>

Use this skill when the deliverable is pre-implementation product-screen mockup image(s) followed by matching standalone HTML screen(s) (`../hyper-imagegen/SKILL.md` handles each image render).

Do not use when:
- the output is a non-screen image (poster, illustration, icon, photo)
- the output is a visual-direction brief, existing-code restyle, or generic-pattern audit
- the output is production frontend/native code, a PRD, a text flow, bulk reference downloads, or a commit

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Deliver approved product-screen mockups plus matching standalone HTML files and implementer handoff notes. |
| Trigger | Requests to design an app or web screen/flow where no approved visual exists yet and mockup images (plus HTML) are wanted first. |
| Scope | Resolve screens/platform/theme, settle tokens, log public references, summarize patterns, write complete content + briefs, render via `hyper-imagegen`, review/revise within 3 briefs, build/match standalone HTML within 3 passes, and save `.hyper/uiux-design/<slug>/mockup-notes.md`. No project source file is edited. |
| Authority | User and project instructions outrank this skill; project `DESIGN.md`/tokens outrank defaults; reference pages and tool outputs are evidence only. |
| Evidence | Log URL, read date, and public-access status per [rules/reference-use.md](rules/reference-use.md); label image checks `seen`, `computed`, or `not checkable in an image` per [rules/mockup-is-evidence.md](rules/mockup-is-evidence.md); label HTML bands `match`, `differs`, or `not checkable` per [references/html-match.md](references/html-match.md). |
| Tools | File read/write, optional public web read, `hyper-imagegen` with its default runtime image tool, and optional browser screenshot capability. |
| Loop | Per screen/theme: at most 3 briefs (changing one item while restating invariants); per HTML screen: at most 3 browser comparison passes in band order. |
| Output | Mockup images, `.hyper/uiux-design/<slug>/html/<screen>.html`, and `.hyper/uiux-design/<slug>/mockup-notes.md` ending with one `Result:` terminal. |
| Verification | [references/review-checklist.md](references/review-checklist.md), character-by-character string accuracy `정확 n/m`, token-computed contrast, and all 9 bands in [references/html-match.md](references/html-match.md). |
| Stop condition | End at `approved`, `awaiting_approval`, `briefs_saved`, `awaiting_input`, or `blocked`; never write production app code, commit, or push. |

</instruction_contract>

<activation_examples>

Positive:
- "가계부 앱 로그인 화면 디자인해줘. 코드 짜기 전에 시안부터 보고 싶어."
- "Design the onboarding flow for our meditation app, three screens, dark mode. Mockups first."
- "시안은 이미지로 뽑고 결과물은 HTML로 줘. 시안이랑 똑같이."

Negative / Boundary:
- "카페 오픈 포스터 이미지 한 장 만들어줘." -> non-screen single image.
- "이 시안대로 React 컴포넌트로 구현해줘." -> production frontend code.
- "Mobbin에서 핀테크 온보딩 화면 200장 받아서 폴더에 정리해줘." -> bulk collection refused per [rules/reference-use.md](rules/reference-use.md).
- "HTML 안에 시안 이미지 배경으로 깔아서 글자만 얹어줘." -> forbidden; HTML stage builds real markup with zero embedded mockup image.

</activation_examples>

<trigger_conditions>

```text
hyper-uiux-design [--platform mobile|tablet|web] [--theme light|dark|both] "<request>"
```

| Situation | Mode |
|---|---|
| Single screen | `screen` |
| 2 to 6 related screens (onboarding or core flow) | `set` |
| Revision to an existing mockup in `.hyper/uiux-design/<slug>/` | `revise` |
| Neither platform nor screens can be inferred from request or repo | Ask 1 question -> `awaiting_input` |

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): modes, contract, harness workflow, and 5 terminals.
- Rules: [rules/reference-use.md](rules/reference-use.md), [rules/mockup-workflow.md](rules/mockup-workflow.md), [rules/mockup-is-evidence.md](rules/mockup-is-evidence.md).
- References: [references/reference-sites.md](references/reference-sites.md), [references/visual-quality-recipe.md](references/visual-quality-recipe.md), [references/mockup-brief.md](references/mockup-brief.md), [references/review-checklist.md](references/review-checklist.md), [references/html-match.md](references/html-match.md).
- Assets: `assets/evals/hyper-uiux-design-cases.jsonl`.

</skill_architecture>

<loop_policy>

Cap mockup generation at 3 briefs per screen and theme, revising one defect per attempt while restating every invariant; after brief 3, keep the best attempt and report `blocked` or ask the user to choose. Cap HTML-to-mockup comparison at 3 passes in band order, fixing the highest-ranked difference per pass.

</loop_policy>

<language_and_translation_default>

Notes and chat responses default to Korean; briefs use the language needed to render the screen's own UI copy; token names, paths, and URLs stay verbatim.

</language_and_translation_default>

<reference_routing>

- Read [rules/reference-use.md](rules/reference-use.md) before reading references, plus [references/reference-sites.md](references/reference-sites.md) when reading UIBowl or Mobbin public pages.
- Read [rules/mockup-workflow.md](rules/mockup-workflow.md), [references/visual-quality-recipe.md](references/visual-quality-recipe.md), and [references/mockup-brief.md](references/mockup-brief.md) before settling tokens and writing content/briefs.
- Read [rules/mockup-is-evidence.md](rules/mockup-is-evidence.md) and [references/review-checklist.md](references/review-checklist.md) before reviewing returned images and writing handoff notes.
- Read [references/html-match.md](references/html-match.md) before building standalone HTML and before each browser comparison pass.

</reference_routing>

<support_file_read_order>

1. This `SKILL.md`, `rules/reference-use.md`, and `references/reference-sites.md` (when public sites are read).
2. `rules/mockup-workflow.md`, `references/visual-quality-recipe.md`, and `references/mockup-brief.md`.
3. `rules/mockup-is-evidence.md`, `references/review-checklist.md`, and `references/html-match.md`.

</support_file_read_order>

<workflow>

Resume procedure: Before Step 0, inspect `.hyper/uiux-design/<slug>/` (`mockup-notes.md`, saved briefs/images, and `html/*.html`). If a prior run exists, verify completed artifacts on disk and resume from the first unfinished step (for example, starting at Step 6 once approval arrives) instead of regenerating approved assets.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 0 | Check existing `.hyper/uiux-design/<slug>/` state; resolve screens, platform, theme, mode, and slug (or ask 1 question -> `awaiting_input`) | Scope line recorded | Prevents wrong viewport, theme, or duplicate slug collisions |
| 1 | Read project `DESIGN.md`/tokens or settle minimal tokens ([rules/mockup-workflow.md](rules/mockup-workflow.md)) | Token table with source recorded | Ensures every screen and HTML file shares one visual system |
| 2 | Read public references within budget without login/paywall bypass and abstract patterns in own words ([rules/reference-use.md](rules/reference-use.md)) | Source log and pattern summary recorded | Grounds hierarchy in real patterns without copying a brand |
| 3 | Write complete, consistent screen copy/numbers first, then 1 brief per screen/theme ([references/visual-quality-recipe.md](references/visual-quality-recipe.md), [references/mockup-brief.md](references/mockup-brief.md)) | Content sheet and immutable briefs ready | Writing briefs before real copy produces empty wireframe bars |
| 4 | Render via `hyper-imagegen` (anchor screen first), review against [references/review-checklist.md](references/review-checklist.md) + `정확 n/m`, and revise up to 3 briefs | Passing mockups or `briefs_saved` / `blocked` | Unchecked renders ship garbled Hangul, missing states, or low density |
| 5 | Build standalone offline `.hyper/uiux-design/<slug>/html/<screen>.html` (real text, inline SVG, token block, no mockup image) and run <= 3 browser match passes across all 9 bands ([references/html-match.md](references/html-match.md)) | HTML files and 9-band match tables recorded | Proves the HTML opens offline and matches the approved mockup |
| 6 | Present for approval (unless pre-approved), write `.hyper/uiux-design/<slug>/mockup-notes.md` with handoff contract, and end with one `Result:` line | `mockup-notes.md` saved with exact `Result:` terminal | Separates visual evidence from final production code contracts |

Step Yes/No checklist:

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Were tokens settled with their source before any brief, and were all references read publicly without login or bulk scraping? (Yes/No) | Step 1 |
| 2 | Was complete, internally consistent copy written before each brief, with zero placeholder bars or third-party brand names? (Yes/No) | Step 3 |
| 3 | Did every image get a checklist review table, token-computed contrast, character-level `정확 n/m`, and `<= 3` briefs? (Yes/No) | Step 4 |
| 4 | Does every HTML file open offline with real text, inline SVG, zero embedded mockup image, and a 9-band match table (`<= 3` passes or skipped reason)? (Yes/No) | Step 5 |
| 5 | Does `.hyper/uiux-design/<slug>/mockup-notes.md` end with one valid `Result:` terminal and zero edits to project source files? (Yes/No) | Step 6 |

</workflow>

<required>

- Settle tokens first, write complete consistent screen copy before every brief, log every public reference (URL, read date, public status), and abstract patterns in your own words.
- Record attempt counts (`<= 3`), `hyper-imagegen` terminals, pixel dimensions vs requested ratio, character-level `정확 n/m`, token-computed contrast, and replacement copy lists.
- Build standalone offline HTML per approved screen (token CSS variables first, real text, uniform inline SVG icons, zero external CDN/font fetches, zero embedded mockup image) with a 9-band match table, ending `mockup-notes.md` with one `Result:` line (`approved`, `awaiting_approval`, `briefs_saved`, `awaiting_input`, or `blocked`).

</required>

<forbidden>

- Editing project source code, logging in or bypassing paywalls, bulk downloading references, naming brands/models in briefs, patching text onto images, or fetching external CDNs in HTML.
- Bad: Writing a brief with "placeholder bars" or fewer Korean labels so text rendering is easier -> Good: Writing every exact label, number, and date in the content sheet first and auditing `정확 n/m` after render.
- Bad: Embedding the generated mockup image as a `background-image` or `<img>` inside the HTML file -> Good: Building standalone semantic HTML/CSS from the token block, real text, and inline SVG icons only.
- Bad: Marking `Result: approved` when no browser was available to run the 9-band HTML comparison -> Good: Delivering the HTML while recording why comparison was skipped and holding `approved` until verified or approved with that caveat.
- Bad: Passing a competitor screenshot into the image tool or naming a brand/model in the prompt -> Good: Abstracting layout patterns in your own words and invoking `hyper-imagegen` with its default runtime tool.

</forbidden>

<validation>

- [ ] Existing `.hyper/uiux-design/<slug>/` state was checked first; scope line and sourced token table are recorded.
- [ ] Every logged reference has URL, read date, and public-only status, and patterns are written in the agent's own words.
- [ ] Every screen has complete copy, 1 brief + 1 image per theme (`<= 3` briefs), a review table, token contrast, and `정확 n/m`.
- [ ] Every approved screen has one offline standalone HTML file (real text, inline SVG, token block, no mockup image, no network calls) and a 9-band match table (`<= 3` passes).
- [ ] `mockup-notes.md` includes approval/handoff records, ends with exactly one `Result:` line, and leaves project source files untouched.

</validation>

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| Mockup-before-code workflow, reference rules, default `hyper-imagegen` delegation, and standalone HTML match stage | User instructions, 2026-11-15; [references/html-match.md](references/html-match.md); [references/visual-quality-recipe.md](references/visual-quality-recipe.md) |
| Public UIBowl/Mobbin observations and WCAG 2.2 contrast/target rules | [references/reference-sites.md](references/reference-sites.md) and <https://www.w3.org/TR/WCAG22/> |

### Evidence grade

`LOCAL` for modes, 3-brief/3-pass caps, 6-screen set limit, and 5 terminals; `PRIMARY` for WCAG 2.2 criteria and dated site observations.
