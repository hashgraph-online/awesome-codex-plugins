---
name: ru-score
description: >
  Score Russian text 0.0–10.0 across five dimensions: typography, clean language, grammar,
  structure, precision for the reader. Triggers: оцени текст, ru-score, оценка качества
  текста, насколько хорош текст, балл за текст. Use when the user wants a number rather than
  a list of findings. Never edits a file.
allowed-tools: Read, Grep, Glob
disallowed-tools: Write, Edit, NotebookEdit, Bash, PowerShell, Monitor
context: fork
user-invocable: true
---

# Russian Text Quality Score

Score the text provided in $ARGUMENTS (or the most recent Russian text output if no arguments) using the ru-text scoring rubric.

## Procedure

## Where the reference files live

This skill reads the corpus that ships with the **ru-text** skill, which is installed
alongside it. Locate that folder once, then read the named files from it:

- Look for a directory named `references` whose parent directory is named `ru-text`, and
  which contains `info-style.md`. Every file named below sits in that folder.
- **Search with file tools, never with a shell.** `Glob` on a pattern like
  `**/ru-text/references/info-style.md`, or whatever file search the host offers, then
  `Read`. This command has no use for a command line: `Bash` is on its `disallowed-tools`
  list, and hosts that do not implement that field still refuse it — measured in Claude
  Cowork on 12.08.2026, where an opening `ls` returned «Permission to use Bash has been
  denied» in red before the search found the corpus anyway. The call bought nothing and
  cost the reader a scare.
- In Claude Code the plugin root is also available directly, which saves the search.
- **Do not guess a path.** If the folder cannot be found, say so and stop — a check run
  against remembered rules instead of the corpus is not this command, and reporting one
  as the other is the failure this whole product exists to prevent.

1. **Load rubric** — read `scoring.md` for the full rubric with anchors.

2. **Determine domain** — identify whether the text is UI/interface, business email, article, or general:
   - UI text → also load `ux-writing.md` for the Reader Precision dimension
   - Business email → also load `business-writing.md` for the Reader Precision dimension
   - General → use `info-style.md` only

3. **Evaluate each dimension separately** — score in this order:
   - **T — Типографика** (weight 0.15): quotes, dashes, spaces, special characters per `typography.md`
   - **Ч — Чистота языка** (weight 0.25): stop-words, bureaucratic language, clichés, passive voice per `info-style.md` + `anti-patterns.md`
   - **Г — Грамотность** (weight 0.20): punctuation, agreement, tautology per `editorial-grammar.md` + `editorial-punctuation.md`
   - **С — Структура** (weight 0.20): logical flow, paragraphs, transitions, heading use per `info-style.md` structure section + `addenda.md`
   - **Ц — Точность для читателя** (weight 0.20): facts, evidence, reader benefit, actionability per domain rules

4. **For each dimension** — assign a score (0.0–10.0) using the rubric anchors in scoring.md. List 1–3 specific issues, quoting the problematic text fragment.

5. **Apply non-compensatory rules:**
   - Any dimension < 3.0 → cap total at 5.0
   - Typography < 4.0 → cap total at 7.0
   - Grammar < 4.0 → cap total at 7.0
   - Use the most restrictive cap when multiple conditions trigger

6. **Compute composite score:**
   ```
   S = round₁(T × 0.15 + Ч × 0.25 + Г × 0.20 + С × 0.20 + Ц × 0.20)
   ```

7. **Short text warning** — if text is under 50 words, prepend a reliability caveat.

## Score labels

| Score | Label |
|---|---|
| 9.0–10.0 | Эталонный |
| 7.0–8.9 | Хороший |
| 5.0–6.9 | Средний |
| 3.0–4.9 | Слабый |
| 0.0–2.9 | Критический |

## Output format

**Read-only — do NOT modify the source files.** `ru-score` reports a score and issues; it must not write to, edit, or overwrite the analysed file(s).

In Claude Code this is hardened by `disallowed-tools`, which removes the listed tools while the command is active — verified on 2.1.220. The list removes the direct file-writers `Write`, `Edit` and `NotebookEdit`, plus the command-executing tools we identified and tested: `Bash`, `PowerShell` and `Monitor`. It names the paths we closed, not every path that exists. `allowed-tools` pre-approves tools; it does not restrict them.

Four limits, stated plainly. A connected MCP server can expose write tools that a per-tool denial list cannot know about. A named subagent whose own definition grants it `tools: Write` is governed by that definition, not by this list. A later Claude Code release can add a tool this file does not name. And on hosts without `disallowed-tools` support the rule is an instruction rather than a platform guarantee.

The contract itself is behavioural and does not depend on the list: this command returns a score and never writes.

The report shape is not written twice. Read section «Output format» of `scoring.md` —
the mandated heading, the five Russian dimension labels, the per-cell limit of one to
three issues with quoted fragments, the weighted formula, the cap note, and the closing
«Что оценка не измеряет» section — and follow it exactly.

That file is the single source of it. A copy lived here until v2.0 and sat outside the
no-loss gate, so the two could drift and only a reader comparing them would notice.

If a dimension has no issues, write «Замечаний нет» in the remarks column.
