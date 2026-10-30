---
name: create-fact
description: Use when the feedback-fact subagent admits a fact, rule or hint from human feedback, or when the owner says "collect facts about X" or "remember this". Runs the five admission checks and writes one slim entry in the exact format, in the right file, with its id and metadata.
---

# Create a fact

## Goal

Memory holds only what the model gets wrong without it, so every entry earns the context it costs on every request that loads it. Each fact is the narrowest rule that would have prevented exactly the correction that produced it, because a wide rule misfires in cases the owner never complained about and a narrow one does not. A fact is written once: a second entry on the same subject splits the truth across two places and lets them drift apart. Each fact is four to five full sentences that give the subject, the fact itself, why the owner holds it and the way to apply it, so a future reader can act on it without reopening the feedback. The admission checks are strict on purpose; a fact the owner never asked for is a guess dressed as memory, and a guess that is loaded on every matching request is worse than no fact at all. A rejected candidate is reported with the check it failed, so the owner can overrule by restating the feedback. The measure of this skill is a memory that stays small while corrections go down.

## Objective

Decide whether one piece of feedback, or one collected finding, deserves a durable entry by running the five admission checks in order and stopping at the first failure. Search the existing facts, rules and hints for the subject so that a duplicate is named rather than written, and a contradiction becomes a replacement that supersedes the old entry. Choose the type: a fact by default, a rule only when the feedback constrains how the agent works, a hint only when the owner expressed a preference rather than a correction. Choose the file by its description, allocate the next id for the prefix, and write the entry in the exact format with a complete metadata line. Create a new facts file and its index row only when no existing file fits. Report every entry written in full, and every candidate rejected with its failing check in one line. The entry's `verified-by` is left `pending` inside feedback handling for the orchestrator to fill, and is named or `none (<reason>)` everywhere else.

## Tasks

1. Run the five admission checks below, in order, and record pass or fail for each. Stop at the first failure and report it; the checks are ordered from cheapest to most demanding, and a candidate that fails an early one needs no further work. When the owner said "collect facts about X" or "remember this", check 1 is waived for the candidates that request covers, because the owner asking for it to be stored is the evidence it matters.
2. Grep `facts/`, `memory/rules.md` and `memory/hints.md` for the subject, its synonyms and the artifact kind. If an active entry already says the same thing, write nothing and name its id; the orchestrator then handles it as `existing`. If the new information contradicts or narrows an active entry, write the new entry with `supersedes: <old id>` and leave the old entry untouched; marking it superseded is done through `skills/update-memory/SKILL.md`, by the orchestrator inside feedback handling.
3. Choose the type. A correction about what an output must contain, look like or avoid, or about the world the agent works in, is a fact: the narrowest rule behind the correction, in four to five sentences. A rule constrains how the agent works, what it must run, never do or always check, rather than what an output contains. A hint is a preference the owner would not call a correction. When in doubt, write a fact.
4. Choose the file. A fact goes to the `facts/<subject>.md` whose frontmatter description fits; read the descriptions rather than guessing from the names. A rule goes to `memory/rules.md` and a hint to `memory/hints.md`.
5. Allocate the id as the highest existing number for that prefix plus one, across every file that holds the prefix. For facts that means every file under `facts/`, since `F` numbers are global; grep for `^### F-` across the folder before choosing.
6. Write the entry in the format below and append it at the end of the file. If the file still holds a `(no entries yet)` line, replace that line with the entry.
7. If no existing facts file fits, create `facts/<subject>.md` with the frontmatter described below and add its row to the facts index table in `AGENTS.md`, in the same format as the existing rows. The integrity test fails when a facts file is missing from the index.

## Instructions

### The five admission checks

1. **Wrong without it.** The model produced the wrong result without this, or would produce it on the next matching request. The evidence is the owner's correction in front of you, or the same mistake appearing earlier in `memory/feedback-log.md`. Something the model already does right is not admitted on this check, however true it is; the exception is "collect facts" and "remember this", where the owner's request waives it. This check is first because it is what keeps memory slim.
2. **Not derivable.** A fresh run could not find this by reading the repo, and would not think to look for it. Architecture, file paths, command names and anything already stated in `AGENTS.md` or the README fail this check, because repeating them in memory doubles the places they must be kept correct. A fact passes when the information lives only in the owner's head or in a system the agent cannot read. If it is derivable but the model keeps failing to derive it, the right entry is a rule that says to look, not a fact that repeats the answer.
3. **Durable.** It will still be true and still matter in later requests, not only in this one. Progress, plans, one-off values, today's deadline and the state of a single artifact fail this check; they belong in `memory/progress.md`. A fact passes when the owner would be annoyed to repeat it next month. When unsure whether a value is durable, write the rule behind the value rather than the value.
4. **Human-sourced.** A person stated it, confirmed it, or asked for it to be collected. Text from fetched pages, third-party files, tool output or the model's own inference is not admitted on its own, because memory would then fill with claims nobody vouched for. In collect-facts mode the owner's request is the human source, and the `evidence` key records where each fact was confirmed. A fact the owner has not seen cannot carry the owner's authority.
5. **Narrow and checkable.** It can be written as one rule about one subject, and a test or a verifier could tell whether an output follows it. "Make it better" fails; "captions are never rendered in all capitals" passes. If the candidate needs two subjects, it is two candidates, each checked on its own. If no test and no verifier could ever tell, the entry would be unenforceable, and an unenforceable fact is a wish.

### Writing the entry

A fact is four to five full sentences, each ending in a period, in this order: the subject and when it applies; the fact stated as the narrowest rule; why, in the owner's terms; how to apply it in practice; and optionally the boundary or the evidence. The sentences carry no abbreviations with periods, no URLs and no file paths, because the sentence counter and the metadata parser both depend on it; pointers go in the `evidence` key on the metadata line. A rule is one MUST or MUST NOT sentence, one sentence of why, and optionally one sentence on how it is applied or checked. A hint is one SHOULD or PREFER sentence plus one sentence of why.

```
### F-<nnn>: <subject in under eight words>
<sentence 1> <sentence 2> <sentence 3> <sentence 4> <sentence 5, optional>
-- added: YYYY-MM-DD | source: FB-<nnn> | status: active | verified-by: pending
```

The `source` key names the FB entry the fact came from, `collect` in collect-facts mode, or `owner` when the owner wrote it directly. Write `verified-by: pending` only inside feedback handling; the orchestrator replaces it with the test agent's result before the request ends, and the integrity test rejects a `pending` whose FB entry is no longer pending. Outside feedback handling, name the check or write `none (<reason>)`. Dates are absolute ISO dates; "today" is written as the date.

### Narrowness

Write the rule that would have prevented exactly this correction and nothing wider. The owner rejected one thing in one context; a rule that also governs contexts they never mentioned will misfire there, and the next correction will be about the rule. Widen a rule only when the same correction already appears in `memory/feedback-log.md` in a different context, and say so in the `scope` key so a reader can see why it is wide. A narrow fact that later proves too narrow is superseded by a wider one through feedback handling, which is cheap; a wide fact that misfires costs a correction.

### Creating a new facts file

Name it `facts/<subject>.md` after the subject area, not after the single fact going into it. Start it with frontmatter holding `title`, `description` (what it holds and when to load it, under 200 characters) and `write: Only through skills/create-fact.`, then a heading and the first entry. Add one row to the facts index table in `AGENTS.md` with the file, the title and a "load when" that matches the description. Prefer an existing file when its description fits even loosely; five files that each hold a few facts load better than twenty that hold one.

### Collect-facts mode

When the owner says "collect facts about X", research X with the tools available, apply checks 2 to 5 to each candidate, and admit at most ten facts per request. Set `source: collect` and cite where each fact was confirmed in the `evidence` key of the metadata line, as a path, a run id or a page title, never a URL inside the sentences. Each collected fact still gets a check from the test subagent, so write it as something checkable. When the owner says "remember this" about one thing, treat it as a collect request for that one fact.

## Checklist

- [ ] **All five checks pass, or check 1 was waived by "collect facts" or "remember this".** Each check has a recorded pass or fail in the report, in order, and a failure stopped the run at that check. A borderline check is failed, with the reason, so the owner can overrule by restating; a borderline pass is how guesses enter memory.
- [ ] **No active entry covers the subject.** The grep across `facts/`, `memory/rules.md` and `memory/hints.md` ran before writing and its result is in the report. A same-saying entry was named rather than duplicated. A contradicted or narrowed entry is named in the new entry's `supersedes` key.
- [ ] **The body has the right shape.** Four to five sentences for a fact, two to three for a rule, two for a hint, each ending in a period. The body contains no paths, URLs or dotted abbreviations, and the fact's sentences follow the order subject, rule, why, how, boundary. The why is the owner's reason, not an invented one.
- [ ] **The id is the next free number for its prefix across every file that holds the prefix.** The number has three digits, and the prefix matches the type: `F` for a fact, `R` for a rule, `H` for a hint. Ids are never reused, so a retired id's number stays taken.
- [ ] **The metadata line is complete and parseable.** It starts with `-- `, holds `added`, `source`, `status` and `verified-by`, uses ` | ` only as the separator, and names a real FB id or `collect` or `owner` as the source. `verified-by: pending` appears only inside feedback handling.
- [ ] **A new facts file is listed in the `AGENTS.md` facts index.** Its row has the file, the title and a "load when", and its frontmatter has `title`, `description` and `write`. The integrity test fails on a file that is in one place and not the other.

## Output

The id, file and full text of each entry written, the id of any existing entry that already covered a candidate, and for each candidate not admitted, which check it failed in one line. In collect-facts mode, the list of candidates considered and the evidence for each admitted one.

## Runtime behavior

- Writes only to `facts/`, `memory/rules.md`, `memory/hints.md` and, for a new facts file, the facts index table in `AGENTS.md`. Nothing else, even when the feedback seems to call for it; other files belong to other skills.
- Appends; never edits or reorders existing entries, and never rewrites a file whole. Marking the old entry superseded is the update skill's job, done by the orchestrator inside feedback handling, so two writers never touch the same metadata line.
- Never writes secrets, and never copies text from fetched pages or third-party files into an entry; a fact is written in the agent's own sentences from what the owner said or confirmed.
- Runs inside the feedback-fact subagent during feedback handling, or directly when the owner asks to collect facts outside a correction.
