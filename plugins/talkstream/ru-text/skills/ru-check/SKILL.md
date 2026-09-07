---
name: ru-check
description: >
  Full Russian text quality check against the whole corpus. Triggers: вычитай, вычитай через
  ru-text, прогони ru-text, проверь текст по ru-text, ru-check, полная вычитка. Use when the
  user asks to proofread Russian text, or when a project gate names ru-text. Returns findings
  with the rule behind each and a proposed replacement; never edits a file. Self-initiated
  runs start with a fast triage and escalate on evidence; an explicit request always runs the
  full corpus.
allowed-tools: Read, Grep, Glob
disallowed-tools: Write, Edit, NotebookEdit, Bash, PowerShell, Monitor
context: fork
user-invocable: true
---

# Russian Text Quality Check

Review the text provided in $ARGUMENTS (or the most recent Russian text output if no arguments) using the ru-text skill.

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

## Two depths, one command

This check runs at one of two depths. Nobody chooses a depth; these rules do.

**Full** — the «Check order» below, whole. Run it whenever a person asked for this check
(«вычитай», «прогони ru-text», a gate that names ru-text, a golden-set run) or triage
escalated. An explicit request is never answered with triage.

**Triage** — for self-initiated runs only: you produced or encountered Russian text and are
checking it out of discipline, with no instruction naming ru-text. Load three things and
nothing else:

1. The ru-text `SKILL.md` — its inline typography table and top stop-words. Skip if it is
   already in context, which on an always-on host it usually is.
2. The «Neuroslop index» section of `addenda.md`: from the `## Neuroslop index` heading to
   the next `##`. Not the rest of the file — the rest is ten times the size.
3. Section «B. Каталог стоп-слов» of `info-style.md`: from its `## B.` heading to the next
   `##`. Not the rest of the file.

Then check the text: typography mechanically (straight quotes, a hyphen doing a dash's work,
`...` for an ellipsis, an ordinary space after в, к, с, о, у, и, а, я — verify by codepoint, not
by eye); catalog stop-words including inflected forms, judging every candidate line yourself
(«данные» the noun is not «данный» the stop-word); index tells by eye.

Triage may **report** only what a single line decides: typography and confirmed catalog hits.
**A neuroslop tell is never a triage finding.** Every AD rule carries carve-outs that live
only in the full file, and «не X, а Y» with a real antecedent is ordinary prose — flagging it
from an index alone is the false positive this command would lose the most trust for. A tell
seen in triage is an escalation trigger and nothing else.

**Escalate to full** when any one of these holds: a neuroslop candidate appeared · five
findings are confirmed · the text is bound for a reader (a deliverable, a publication, a
client). Escalating is silent — continue into the full procedure as though it had been asked
for.

A triage report names itself: «Быстрая проверка: типографика и стоп-слова. Полная вычитка по
корпусу не выполнялась.» Reporting triage as the full check is the failure this product
exists to prevent. No search tool on this host → no triage: run the full check.

## Check order

1. **Typography** — read `typography.md`, then apply:
   - Quotes: «» primary, „“ nested
   - Dashes: — (em) in text, – (en) in ranges, - (hyphen) in compounds only
   - Spaces: NBSP after single-letter words, in digit groups, before units
   - Ellipsis, abbreviations, special characters

2. **Anti-patterns** — read `anti-patterns.md`, then scan for:
   - Bureaucratic language and nominalization
   - Passive voice overuse
   - Sentence bloat
   - Tautology and pleonasm

3. **Writing quality** — read `info-style.md`, then apply:
   - Stop-words and filler
   - Specificity and facts
   - Structure and clarity

4. **Domain-specific** — load if text type is identifiable:
   - UI/interface text → `ux-writing.md`
   - Email/business → `business-writing.md`
   - Needs grammar review → `editorial-punctuation.md` + `editorial-grammar.md`

5. **Experience-based / neuroslop** — read `addenda.md`, then scan for the AI-generated-prose tells:
   - Manufactured antithesis (AD-6) — «не X, а Y» / «не просто X, а Y» with no antecedent
   - Preemptive virtue qualifier (AD-7) — «без воды», «чётко, по делу»
   - Assistant-register meta-commentary (AD-8) — «Отличный вопрос!», «Надеюсь, это помогло»
   - Hollow openers (AD-9) — «давайте разберёмся», «погрузимся», «важно понимать, что»
   - Declared sincerity (AD-10) — «честный разбор», «давайте будем честны»: honesty predicated of the piece.
     The same reflex on a single statement — «скажу честно: дедлайн сорван» — is AD-7
   - Mandatory tricolon (AD-11) — «инновационный, трансформирующий, прорывной»
   - Hollowed mechanism (AD-12) — «зависит от различных факторов», «свои особенности»
   - Phantom attribution (AD-13) — «исследования показывают», «эксперты отмечают»
   - Chat transcript as the artifact (AD-14) — the document's skeleton is a dialogue
   - Search-engine addressee (AD-15) — the query phrase repeated where a pronoun would serve
   - Additive pseudo-pair (AD-16) — «не только X, но и Y» where Y adds nothing
   - Comma welded to a dash (AD-17) — a comma and an em dash side by side inside one sentence,
     both demanded by the same construction: «Отчёт, собранный за ночь, — на столе». Search by
     codepoint: the gap between the marks is normally the NBSP R16/R44 require before a dash, so
     a search written with an ordinary space finds nothing in correctly typeset text. Direct
     speech («Сроки поедут», — предупредила Петрова) is two constructions meeting, and a comma
     closing homogeneous subordinate clauses before the main clause forms a single mark with the
     dash — different grounds, same outcome: never this rule
   - Uppercase band (AD-18) — three or more consecutive uppercase Cyrillic words of two letters
     or more, unbroken by a lowercase word or by a line break. Not a neuroslop tell, and it is
     absent from the index above on purpose: a person shouts on a keyboard with no italic key,
     a model does not. It belongs to this full pass and to nothing faster. One or two uppercase
     words are deliberate emphasis and are never flagged; abbreviations, machine text, status
     cells and headings do not count toward the run

   The list above is a prompt for the eye, not the rule set. Two of these — AD-14 and AD-15
   — are charged to the **document**, so ask them of the piece as a whole and not of any
   one sentence. Every rule has carve-outs that decide as many cases as the triggers do;
   they are in `addenda.md`, and a finding raised without checking them is the false
   positive this command costs the most trust for.

## Output format

**Read-only — do NOT modify the source files.** `ru-check` is a *check*: it reports issues and returns the corrected text for the user to apply. It must not write to, edit, or overwrite the analysed file(s).

How this is enforced depends on the host, and it is worth being exact about it.

In Claude Code, `disallowed-tools` removes the listed tools from the pool while the command is active — verified on 2.1.220 by attempting a write through `Write`, through `Bash` redirection, through `Monitor`, and through a delegated subagent: every path was denied and no file was created. `allowed-tools` alone would not achieve this; that field pre-approves tools, it does not restrict them.

The list removes the direct file-writers — `Write`, `Edit`, `NotebookEdit` — and the command-executing tools we identified and tested on 2.1.220: `Bash`, `PowerShell` and `Monitor`. `Monitor` is easy to miss: it runs commands too, and it follows `Bash` permission rules, so a broad `Bash` allow-rule silently pre-approves it while a `disallowed-tools: Bash` entry does not remove it. **The list names the paths we closed, not every path that exists.**

Four limits, stated plainly. A connected MCP server can expose its own write tools, which a per-tool denial list cannot know about. A named subagent whose own definition grants it `tools: Write` is governed by that definition, not by a parent command's denial list. A later Claude Code release can add a tool this file does not name, and a hand-written list does not update itself. And on hosts that do not implement `disallowed-tools`, everything above is an instruction the agent is asked to follow, not a guarantee the platform enforces.

Where the mechanism ends, the contract does not: the rule is that this command returns text and never writes, on every host, whatever the tool roster happens to contain.

Returning the corrected text in the output rather than writing it keeps the command deterministic and free of side effects. Silently inserting NBSP into a source file is doubly harmful: a target that strips NBSP on import (e.g. Notion) shows the reader no change, and the same insertion breaks later exact-string tooling (grep/replace) on that file.

Return:
1. Corrected text
2. List of changes grouped by category (typography / style / grammar / domain)
3. Severity per change: critical / high / medium / low
