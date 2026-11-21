---
name: update-memory
description: 'Use when an existing memory entry must be superseded, retired, merged or confirmed, or when a run produced a failure, decision, open question, scope boundary, glossary term, pointer or workflow. Keeps history: nothing is deleted.'
---

# Update memory

## Goal

Memory stays consistent with the owner's latest words, so a request never applies two entries that disagree. Every change leaves a trail: the old entry, the new entry and the link between them, because the owner may ask why a rule changed, and because a superseded entry is the evidence that the old behavior was once wanted. Nothing is deleted, renumbered or reordered, since ids are cited in tests, dispositions and reports, and a deleted id breaks every citation. Operations are small and named, supersede, retire, confirm, narrow or leave, so a reader can see what happened from the metadata line alone. A confirmation is recorded too, because an entry confirmed by a correction twice is an entry that is not taking effect, and that signal is what triggers a new check. The non-fact memory types, failures, decisions, open questions, scope, glossary, pointers and workflows, are appended here in their own formats so that the next request can load them by type. The measure of this skill is that memory never holds two active answers to the same question.

## Objective

Find every existing entry the new information touches, by searching the fact files and the memory files for the subject, the artifact kind and the ids the feedback names. Decide one operation per entry from the five below, with leave as the default when nothing changes. Apply the operation by editing only the metadata line of the old entry and, when a replacement is needed, appending a new entry at the end of the file. Append any failure, decision, open question, scope line, glossary term, pointer or workflow the new information implies, in its type's format from the memory map. Inside feedback handling, apply operations only within the feedback-update subagent's own files and report the rest for the orchestrator. Report every id touched with its operation and reason, so the request report and the disposition can cite them.

## Tasks

1. Find the entries the new information touches. Grep `facts/` and `memory/` for the subject, its synonyms, the artifact kind and every id the feedback names, and list each candidate with its file and current status. Skip entries that are already superseded or retired; they are history.
2. Pick one operation per candidate: supersede, retire, confirm, narrow or leave, by the definitions below. Write the reason in a few words while deciding; the reason goes on the metadata line or in the report.
3. Apply it by editing only the metadata line of the old entry, adding or changing the keys the operation calls for, and by appending a new entry when the operation needs one. The body of the old entry is never touched; the keys are added at the end of its metadata line.
4. For a failure, decision, open question, scope line, glossary term, pointer or workflow the information implies, append one entry to the matching file in its format from `memory/MAP.md`, with the next id for its prefix and a complete metadata line. If the file still holds a `(no entries yet)` line, replace that line.
5. Report every id touched and its operation, and the ids of every new entry, so the orchestrator or the request report can cite them. Include the candidates left alone. The report is what the disposition and the request report are built from.

## Instructions

- **Supersede** when the new information contradicts the entry. Set `status: superseded` and `superseded-by: <new id>` on the old entry, and `supersedes: <old id>` on the new one, so each points at the other. The old text stays as it was, because it records what the owner wanted before. An entry is never superseded by nothing: if there is no replacement, the operation is retire.
- **Retire** when the entry no longer applies to anything: the subject is gone, the tool was replaced, the owner withdrew the rule. Set `status: retired` and `reason: <why>`. The text stays, the id stays taken, and tests that cite the entry are retired the same way through the test skill.
- **Confirm** when the feedback restates an entry that is already active. Set `confirmed: YYYY-MM-DD` with today's date, replacing an older confirmation. If the same entry is confirmed by a correction twice, the rule exists but is not taking effect, so report it as `not-taking-effect` and the orchestrator adds a check through `skills/create-test/SKILL.md`. A confirmation from praise is recorded the same way but is not a not-taking-effect signal.
- **Narrow** when the feedback shows the entry over-applies: the owner corrected the agent for following a rule where it should not have. Supersede the entry with a narrower one and set `scope` on the new entry to say where it applies. Inside feedback handling the fact subagent writes the narrower fact or rule; this skill writes the narrower entry only for the non-fact types.
- **Leave** when nothing in the feedback touches the entry. Say so in the report for every candidate you examined, so the next reader knows the entry was considered and not missed. Leave is the default, and most candidates end here; the grep is wide on purpose and the operations are narrow.
- **A workflow is written only from a run the owner accepted.** It has a `trigger:` line and at least two numbered steps with `{placeholders}` for the values that vary between runs. A workflow from a run the owner rejected would teach the mistake; a workflow with concrete values would apply to one run only.
- **A failure entry needs `do instead`.** `tried:`, `failed because:` and `do instead:` on three lines; without the third line the entry says what not to do and leaves the agent to guess, so write an open question instead and let the owner supply the alternative. When the correction itself is the alternative, the failure entry carries it in the owner's words.
- **An open question closes by supersession.** When a fact or decision answers it, set `status: superseded` and `superseded-by: <the answering id>` on the question. A question is never deleted, because the answer's history starts with it.
- **Never delete, renumber or reorder.** Ids are cited in tests, dispositions, reports and other entries, and every one of those citations is checked by the integrity test. A file is appended to and its metadata lines are edited in place; nothing else about it changes.

## Checklist

- [ ] **Every touched entry has exactly one operation and valid metadata keys.** The keys are from the allowed list in `memory/MAP.md`, values contain no ` | `, and dates are absolute. An entry is never both superseded and retired.
- [ ] **Superseded entries point at an existing successor, and the successor points back.** `superseded-by` names an active entry that exists, and that entry carries `supersedes` with the old id. Inside feedback handling, where the successor's id is not known yet, the report says which id the orchestrator must fill in.
- [ ] **New entries follow their type's body format.** A failure has its three lines, a decision its three lines, a workflow its trigger and placeholders, a question its settling sentence, and each has a complete metadata line with the next free id. The formats are in `memory/MAP.md`, and the integrity test parses every entry, so a malformed body is caught before the request ends.
- [ ] **The integrity test passes.** Run `python -m pytest -q tests/test_memory_integrity.py` outside feedback handling, or the mid-feedback suite from `tests/README.md` inside it, and fix every failure in the entries you touched. A failure in an entry you did not touch is reported, not fixed, because it belongs to another writer.

## Output

A list of `id: operation (reason)` lines, one per candidate including `leave`, the ids of any new entries with their files, and any `not-taking-effect` ids.

## Runtime behavior

- Edits only metadata lines of existing entries; appends new entries at the end of the file. Never rewrites a file whole.
- Writes only to `memory/` files other than `rules.md`, `hints.md`, `guarantees.md`, `progress.md`, `run-log.md` and `footprint.md`, plus metadata lines in `facts/`, `memory/rules.md` and `memory/hints.md` when superseding, retiring or confirming.
- Inside feedback handling, the feedback-update subagent reports those metadata edits under `for-orchestrator` instead of making them, because the fact and test subagents write the same files at the same time, and the orchestrator applies them in the stitching step.
- Runs inside the feedback-update subagent during feedback handling, in the orchestrator's stitching step, or directly when a run produced a failure, decision, question or pointer outside feedback.
