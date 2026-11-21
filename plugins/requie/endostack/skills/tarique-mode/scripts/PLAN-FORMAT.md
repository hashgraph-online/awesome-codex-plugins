# Program plan format

The multi-phase-plan playbook writes a program plan, and `check-plan.mjs` lints it. This file is the only place the format is defined. The playbook points here rather than copying the rules, and `test/check-plan.test.mjs` pulls the example plan out of this file and fails when the checker rejects it. Any rule change touches three things in one commit: this file, the constants near the top of `check-plan.mjs`, and the example.

Invoke the checker on a plan file:

```
node skills/tarique-mode/scripts/check-plan.mjs path/to/plan.md
```

For each PR section it prints the section title, its total box count, and a per-block count in the form `needs=N touches=N changes=N result=N unit=N live=N perf=N review=N land=N`. The last stdout line reads `checked <N> PR sections; found <M> problems`. Problems go to stderr, one per line, as `FILE:LINE: message`. The exit code is 0 for a clean plan, 1 when there is at least one problem, and 2 when the arguments are wrong or the file cannot be read.

## The proof rule sentence

Each plan carries one fixed sentence, copied exactly. The checker compares it character by character:

```
Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked.
```

The sentence sits once in the reading section. Each of the three proof blocks also opens with it, on the same line as its bold label.

## Lines the checker skips

- Front matter. When line 1 is `---`, every line through the next `---` is skipped.
- Fenced code. An opening fence has at most 3 spaces of indent followed by at least three backticks or tildes; a backtick opener whose info string contains a backtick does not count. A fence ends at a line with at most 3 spaces of indent, the opening character repeated at least as many times as the opener, and only spaces or tabs after it. Every other line, including a would-be closer carrying an info string, stays inside the fence. Nothing inside a fence counts toward headings, boxes, or prose.
- Prose rules only: inline code spans, image syntax, link targets, and autolinks. A code span is a run of N backticks ended by the next run of exactly N. A run with no partner is plain text, and checking continues after it.

## Prose rules

The checker scans each non-code line for three problems and reports each with its line number:

| Problem | Trigger | Fix |
|---|---|---|
| long dash | an en dash or an em dash | rewrite with a comma, a period, or parentheses |
| curly quote | a curly single or double quote | switch to straight quotes |
| mid-sentence colon | a colon followed by a space and then a non-space character | split the sentence, or move what follows the colon onto its own line or into a list |

A colon that ends its line passes, so a line such as "Run these commands:" can introduce a list.

## Section order

An H2 is a non-code line that starts with `## `. Each section extends to the next H2. Titles match on prefix, so `## Reading this plan before you start` satisfies `Reading this plan`.

1. An H1 title. Fewer than ten non-blank lines may sit between the H1 and the reading section. Use them to say what the program changes, who it serves, which rule the run holds every PR to, and the PR ids in sequence.
2. `## Reading this plan` (prefix). Case does not matter for its three required phrases: `each box is a single task`, `each box cites its proof`, and `tick a box only once its proof exists`. It must also hold a backticked path ending in `playbooks/<name>.md` that names the execution playbook, and the proof rule sentence. State who merges and which PR ids halt at merge-ready for the operator as well; the checker does not test those.
3. `## Run checklist`, immediately after the reading section. It has exactly five H3s, matched by prefix and in this order: `Start the run`, `Assign owners`, `Branch and PR rules`, `Verification and landing`, `Lane setup`. Somewhere in its body it needs a code span beginning with `git show origin/main:` (playbooks and skills are read from trunk), the words `hourly audit loop`, and the words `status message`. The hourly audit loop is the host agent's own recurring-run feature; write the actual command into the plan.
4. At least one PR section. Every H2 that falls between the run checklist and the finish section counts as a PR section. Title each with a verb phrase and the PR id, for example `## Add the export button (PR-2)`.
5. `## Finish the run` (prefix).
6. Appendices. Every H2 after the finish section starts with `Appendix`, and one of them contains `Experiment results`. Order them as `Appendix A. Experiment results`, `Appendix B. Options considered and dropped`, `Appendix C. Risk register`, `Appendix D. Sources and pre-reading`.

Any other H2 ahead of the run checklist is reported as unexpected.

## PR sections

A checkbox is a line of the form `- [ ] text` or `- [x] text`, at any indent, with `*` accepted in place of `-`. Indented lines below a box extend that box's text. A box that appears before the first block label is an error.

Every PR section holds these nine bold labels, in this order, each at the start of its own line:

| Label | Requirement |
|---|---|
| `**Needs.**` | Same-line text after the label naming one PR id, several ids, or `none`. |
| `**Touches.**` | One or more boxes, one per file the PR edits, creates, or deletes. |
| `**Changes.**` | One or more boxes. Each box holds a single change and names both the symbol and its file. |
| `**Observable result.**` | One or more boxes. Each box gives one result a person can observe and quotes the precise log line or screen state. |
| `**Unit proof.**` | The rule sentence on the label line, then one or more boxes, each naming the test file, the test case, and the command that runs it. |
| `**Live proof.**` | The rule sentence on the label line, followed on that line by ``Ten lanes run on `<model>` against the PR head.`` with a real model or model tier inside the backticks (`<model>` and similar placeholders fail). Then exactly ten boxes, `Lane 1.` through `Lane 10.` in sequence. Every lane names its screenshot with ``Save `name.png` `` and gives its pass condition with `Pass when`. Lane 1 is the trunk regression lane. Any other box in this block is an error. |
| `**Perf proof.**` | The rule sentence on the label line, then exactly four boxes that begin with `Metric.`, `Probe.`, `Baseline.`, and `Budget.`, in that order. |
| `**Operator review.**` | Either `None.` directly after the label and no boxes (the PR leaves every interaction unchanged), or one or more boxes, with the words screenshot, video, and operator appearing somewhere in the block. |
| `**Landing.**` | One or more boxes. |

## Example plan

The tests extract the block below and expect the checker to report zero problems on it. Start new plans from a copy of it.

~~~~markdown
---
status: draft
---

# Ship CSV export for the reports page

Analysts can download the report table as CSV. Each PR in this run has to show working behavior at its own head before it merges.
The PR sequence is PR-1 (export endpoint), then PR-2 (export button).

## Reading this plan

Each box is a single task. Each box cites its proof, and boxes nested under it are sub-steps. Tick a box only once its proof exists, in the form of a commit SHA, a test run, a saved file, a screenshot, or a quoted log line. Instructions live in the plan body, while background material and records go in the appendices.

The execution playbook is `playbooks/autopilot-stack.md`. Each owner squash-merges their own PR. PR-2 belongs to the operator and halts at merge-ready.

Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked.

## Run checklist

### Start the run

- [ ] Walk the operator through the protocol and this plan, and wait for an explicit go before doing anything else.
- [ ] On every tick, load the execution playbook from trunk with `git show origin/main:skills/tarique-mode/playbooks/autopilot-stack.md`.
- [ ] Once the go arrives, start the hourly audit loop through the agent's recurring-run command, using the fixed tick prompt below.
- [ ] Send a status message only when a tick turns up a tracked change that no earlier message covered.

### Assign owners

- [ ] Give PR-1 an owner whose branch starts from main.
- [ ] Give PR-2 an owner once PR-1 has merged.

### Branch and PR rules

- [ ] Each PR opens ready for review, following `playbooks/opening-a-pr.md`.

### Verification and landing

- [ ] Each PR gets one full swarm at its code-ready head.

### Lane setup

- [ ] On the lane machine, check out the head SHA, bring up the backend and the surface, and wait until both report ready.

## Add the export endpoint (PR-1)

**Needs.** none

**Touches.**
- [ ] Edit `server/reports.ts`.

**Changes.**
- [ ] Add `exportCsv` in `server/reports.ts`.

**Observable result.**
- [ ] The log prints `export rows=42`.

**Unit proof.** Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked.
- [ ] Case `exports header row` in `server/reports.test.ts`, run with `npm test -- reports`.

**Live proof.** Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked. Ten lanes run on `fast` against the PR head.
- [ ] Lane 1. Trunk regression, the report table loads on trunk and head. Save `lane1.png`. Pass when both show the same row count.
- [ ] Lane 2. Export an empty report. Save `lane2.png`. Pass when the file holds only the header.
- [ ] Lane 3. Export 10k rows. Save `lane3.png`. Pass when the file has 10001 lines.
- [ ] Lane 4. Export with commas in cells. Save `lane4.png`. Pass when cells are quoted.
- [ ] Lane 5. Export with a cell starting with an equals sign. Save `lane5.png`. Pass when the cell is prefixed with a single quote.
- [ ] Lane 6. Export as a user without report access. Save `lane6.png`. Pass when the server returns 403.
- [ ] Lane 7. Export twice in a row. Save `lane7.png`. Pass when both files match.
- [ ] Lane 8. Export with a unicode report name. Save `lane8.png`. Pass when the filename is preserved.
- [ ] Lane 9. Cancel an export midway. Save `lane9.png`. Pass when no partial file remains.
- [ ] Lane 10. Export after a filter change. Save `lane10.png`. Pass when only filtered rows appear.

**Perf proof.** Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked.
- [ ] Metric. Milliseconds to first byte of the export response.
- [ ] Probe. Ten interleaved trunk and head requests against the same report.
- [ ] Baseline. Trunk report load time, measured first.
- [ ] Budget. Fail if head export of 10k rows exceeds 800 ms.

**Operator review.** None. No interaction changes in this PR.

**Landing.**
- [ ] Clean root verdict at the exact head SHA, bot triage done, rebased onto trunk with patch identity unchanged, then squash-merge.

## Finish the run

- [ ] Confirm each box above is ticked and its proof is on record.
- [ ] Send the operator the closing report that the execution playbook specifies.

## Appendix A. Experiment results

- Question one was answered by branch `proto/csv` at SHA `abc1234`.

## Appendix B. Options considered and dropped

- Server-side XLSX was dropped because it adds a dependency.

## Appendix C. Risk register

- Large exports may time out (PR-1).

## Appendix D. Sources and pre-reading

- Read `server/reports.ts` before editing.
~~~~

To stay short, the example has a single PR section. A real plan gives each PR its own section. When a PR changes an interaction, its review block looks like this:

```markdown
**Operator review.** The export button changes in this PR, so the operator signs off before it merges.
- [ ] Copy the lane screenshots into the PR's media path.
- [ ] Capture a video of 30 to 60 seconds on one lane machine.
- [ ] Share both the screenshots and the video with the operator in the chat, stop at merge-ready, and wait for a reply.
```
