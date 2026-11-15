# Mockup Workflow

Read this rule before settling tokens or writing a brief. It decides the order of work from scope to approval, who renders the image, how many times a screen may be regenerated, and what the notes file holds.

## Contents

1. Scope and Modes
2. Tokens First
3. From Pattern to Brief
4. Generation
5. Review
6. Regeneration Cap
7. Screen Sets and Themes
8. Approval and Handoff
9. HTML Stage
10. Notes File

## 1. Scope and Modes

Resolve four things before anything else, from the request and the project:

| Item | Values | Default when unstated |
|---|---|---|
| Screens | The named screen or the steps of the flow | Ask, when the request names none |
| Platform | `mobile`, `tablet`, `web` | The project's platform; ask when the project does not show one |
| Theme | `light`, `dark`, `both` | The project's default theme, otherwise `light` |
| Mode | `screen`, `set`, `revise` | One screen is `screen`; two to six are `set` |

A set is at most six screens per run. A larger flow is split: the first run covers the six screens that carry the flow, and the notes list the rest as not yet drawn.

## 2. Tokens First

No brief is written before tokens exist.

1. Look for a design document and token source in the project: `DESIGN.md`, a theme file, CSS custom properties, a Tailwind or design-token config, or a native theme file. When found, copy the values that apply and record the file they came from.
2. When nothing is found, settle the minimal token set in [../references/mockup-brief.md](../references/mockup-brief.md) §4: color, type, radius, spacing. Mark it `provisional` in the notes, and say that it exists to keep the mockups consistent and is the user's to change.
3. Compute the contrast ratio of every text and background pair in the token set before use ([mockup-is-evidence.md](mockup-is-evidence.md) §4). A pair that fails is fixed in the tokens, not in the brief.
4. With `both` themes, settle both token columns now.

Minimal tokens are a floor for consistency. A brand identity, a mood, or a full visual direction is a larger decision and is not invented here; when the user wants one, say that it is a separate deliverable and continue with the provisional set only if the user agrees.

## 3. From Pattern to Brief

1. Write the pattern summary from the source log ([reference-use.md](reference-use.md) §5): structure, hierarchy, spacing, components, flow.
2. For each screen, decide the regions top to bottom, the one primary action, and the components, citing which pattern statement each choice follows.
3. Choose the screen's type from [../references/visual-quality-recipe.md](../references/visual-quality-recipe.md) §5 and start from that region order. Note the element count it expects (§7) so the brief cannot come back under-built.
4. Write the complete content before writing the brief: the headline number, every row's name, count, amount, and share, the dates, the names, the section counts. Make them add up. Budget one line per element and write them all.
5. Write the brief with the skeleton in [../references/mockup-brief.md](../references/mockup-brief.md) §3. The brief carries token values, the region list with its content inline, every string, and the canvas. It carries no product name, no reference URL, and no model name.
6. Run the content rule check before the call: open the brief and confirm that no position on the screen is left to a bar, a block, or an unlabelled shape. A bar that survives into the brief will survive into the image ([../references/visual-quality-recipe.md](../references/visual-quality-recipe.md) §2).
7. Write the checks the image must pass before the call is made, taken from [../references/review-checklist.md](../references/review-checklist.md).

## 4. Generation

Every image is made by hyper-imagegen, one brief to one image.

Find the image tool before deciding there is none, in this order, and record which step answered:

1. The tools the runtime already exposes to this session.
2. The MCP servers configured for this runtime, including a locally running image server; a server that is configured but not exposed to the session is still the tool to use if the runtime can reach it.
3. Only after both: the substitution path, and the notes say which substitution was used.

A session that concluded "no image tool" and rendered with code instead, while an image server was answering on the same machine, is the failure this order exists to prevent.

Two runtime facts decide what step 2 looks like, and both are checked rather than assumed:

- **A server enabled after the session started has no tool in this session's list.** The library and the session's tool list are different things: enabling a server for the runtime does not retroactively add its tools to a running session. Re-check the library (`magpie library mcp show <name>`) and the session's exposed tools before concluding anything.
- **The runtime's own MCP endpoint is reachable even then.** When the gateway process that fronts the runtime's MCP servers is the one that also routes to the session, a JSON-RPC call to that endpoint starts the same server and runs the same tool. That is not an API-key script: it is the same server, with the same credentials the runtime already holds, called one layer lower. Record which endpoint answered and what the call returned.

What is never acceptable is replacing the image step with a locally written rendering path. If the endpoint refuses, the terminal is the one the skill defines, and the notes say what refused and why.

- Hand over the brief as the request, with the canvas passed as the image skill's structured canvas value and not inside the prompt text.
- Do not name or choose a model. The image skill's default applies, and so do its own invocation cap and its terminals.
- Record what the image skill reported for each brief: the terminal, the invocation count, the saved path or returned-artifact record, and the digest when one exists.
- Record the returned pixel size and compare it with the requested ratio. When they differ, write one line in the notes: the ratio requested, the size returned, and that the frame is illustrative while the logical frame in the brief is the contract. Do not crop or resize the image to force the ratio.
- A `prompt_saved` or `blocked` terminal because no image tool exists is not a failure of this skill: keep the briefs in the notes and end `briefs_saved`. Do not switch to an API key, a paid endpoint, or a different tool on your own.
- No text is edited onto a returned image and no image is composited. A wrong image is answered with a revised brief.

## 5. Review

Each returned image is reviewed with [../references/review-checklist.md](../references/review-checklist.md) before the user sees it as a candidate. The review covers brief fidelity, readability, generated-image tells, accessibility, set consistency, and reference independence. Every item is recorded as `pass`, `fail`, or `not checkable in an image`, with the label from [mockup-is-evidence.md](mockup-is-evidence.md) §1.

An image is a candidate when no item is `fail`. Items that cannot be checked in an image become handoff requirements, not passes.

## 6. Regeneration Cap

- At most three briefs per screen and theme: the first and two revisions.
- A revision changes one thing, names it, and restates every invariant, because an unstated invariant drifts.
- A user-requested change after delivery starts a `revise` run with its own cap.
- A screen with two independent defects is still one change per brief. Rank the defects by the review order in [../references/review-checklist.md](../references/review-checklist.md) §9 and fix the highest one first; the second may not get a brief within the cap, and that is expected.
- After the third brief, keep the attempt with the fewest failing items, list every remaining `fail` with its id and note, and end `awaiting_approval` when the remaining failures are only a matter of the user's preference. Present the attempts and the failing-item list. End `blocked` only when a remaining failure is structural, such as a missing region or an unreadable hierarchy that the cap prevented fixing.
- The notes state plainly which checks the adopted attempt still fails. A screen that reached the cap with two wrong syllables is reported as two wrong syllables, not as a pass.
- Never loop to chase a perfect image. A mockup that shows the layout, the hierarchy, and the density has done its job.

## 7. Screen Sets and Themes

- Write an invariant block once and repeat it word for word in every brief of the set: token values, type treatment, component shapes, icon style, system bar treatment, and canvas.
- Generate the anchor screen first, the one that shows the most shared components. Review it, and show it to the user when the user is present. Generate the rest only after the anchor is a candidate.
- Change only what the screen needs: its regions, its strings, its primary action.
- A dark version is its own brief and image. It changes the token column and nothing else, and it is generated after the light anchor is a candidate.
- After the set is complete, run the consistency items of the checklist across all images together.

## 8. Approval and Handoff

- Present the candidates with their review tables and ask for approval or one change. Approval belongs to the user.
- When the user approved in advance, a candidate counts as approved; record that the approval was given in advance and quote the request.
- Without an answer, end `awaiting_approval`. Do not start implementation.
- On approval, write the handoff section ([mockup-is-evidence.md](mockup-is-evidence.md) §5) and end `approved`. Implementation is a separate job that receives the notes; this skill writes no interface code.

## 9. HTML Stage

The mockup is approved (or approved in advance), and the deliverable the user opens is HTML. [../references/html-match.md](../references/html-match.md) owns the rules, the match bands, and the fail signals; this section owns the order and the handoff.

1. **Read the match reference** before writing the first line of HTML.
2. **Build from the brief, not from the image.** The token table, the region list, and the copy list are already written and already agreed. The HTML copies those. A value measured off the picture is not a source, and copying one is how a screen drifts from its own contract.
3. **One file per screen**, at `.hyper/uiux-design/<slug>/html/<screen>.html`, opening from disk. The mockup stays beside it and is never embedded, never a background, never a hidden image.
4. **Real text, inline SVG icons, a token block first.** No font, icon, or image is fetched at render time.
5. **Compare in a browser** at the brief's logical viewport, capture a screenshot at the mockup's native scale, and work the bands in the reference's order. Write the diff list before changing anything, then fix the single highest item.
6. **Repeat at most three times.** Each pass records the pass number, the diff count before and after, and the one thing that changed.
7. **Stop** on an empty diff list or at the cap. Keep the attempt with the shortest diff list, list every remaining difference, and report a screen with a spacing difference as that difference rather than as a match.
8. **Hand off both artifacts** with the token block as the project theme contract, the icon inventory, and the remaining differences.

The HTML stage never becomes a production implementation. There is no data layer, no routing, no state beyond what the brief named, and no build integration. The implementer takes the tokens and the HTML as a reference and owns everything after that.

If the runtime has no browser for the screenshot, write the HTML, skip the comparison, record that the match check was skipped and why, and do not report the screen as matched.

## 10. Notes File

Write `.hyper/uiux-design/<slug>/mockup-notes.md` in Korean, in this order:

1. Result line summary and the terminal.
2. Scope: screens, platform, theme, mode.
3. Tokens and their source (`project` with the file, or `provisional`), with computed contrast.
4. Source log and the copyright notice. When a site's terms could not be read, write the standard line: `약관 본문 확인 실패(이유), 공개 목록 범위만 사용`.
5. Pattern summary, with the reference strength of each pattern.
6. Per screen and theme: the brief, the image path or returned-artifact record, the image skill's terminal and invocation count, the returned pixel size with the requested ratio beside it, the review table, the attempt count, and the string accuracy as `정확 n/m` over every string the screen shows.
7. Per screen: the HTML path, the match table over all nine bands, the diff list per pass, and the pass count.
8. Approval record.
9. Handoff, with the token block, the icon inventory, and the remaining differences.
10. Assumptions and what was not done.

The file ends with exactly one `Result:` line. Images stay where the image skill put them; the notes link to them and never copy third-party screens beside them.

A review table in the notes carries one row per checklist item, not a shortened summary of the sections. A table that collapses thirteen items into six rows is not a review and will hide a bar where content belongs.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| The order from reference research to handoff, mockup before code, tokens from `DESIGN.md` or a minimal set first, one screen and screen sets, three platforms, light and dark, a stated regeneration cap, and the image skill with its default model | user instruction, 2026-11-15 (new skill request) |
| One brief per image, the canvas passed as a structured value, shared invariants repeated in every brief of a series, a revision that changes one thing, no patching of rendered text, and no unprompted switch to an API-key path | this package's image-generation skill contract, restated for screens |
| The HTML stage order, one standalone file per screen, building from the brief rather than the image, the browser comparison, and the three-pass cap | user instruction, 2026-11-15; the rules and bands are in [../references/html-match.md](../references/html-match.md) |

### Evidence grade

`LOCAL`: the six-screen set size, the three-brief cap, the anchor-first order, the HTML comparison order, and the notes layout are this package's chosen procedure and carry no external measurement.
