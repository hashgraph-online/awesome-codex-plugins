# Context Engineering Guide for Hyper Docs

**Purpose**: Turn documentation into high-signal, low-noise context that AI systems can parse, retrieve, and execute reliably.

## 0. Core Contract

Every instruction-style document should make these boundaries explicit when they affect execution:

| Section | Must state | Avoid |
|---|---|---|
| Intent | what success and failure look like to the user | persona-only framing |
| Scope | readable/editable/creatable targets | unlimited "everything related" scope |
| Authority | instruction priority and conflict handling | mixing user/project/tool rules silently |
| Evidence | trusted evidence channels and source grades | treating snippets or tool output as primary sources |
| Tools | when to use tools, stop, or delegate | inventing tools or hard-coding one runtime without a profile |
| Output | artifact shape, path, language/tone, and completion criteria | vague "clean it up" endings |
| Verification | tests, evals, review, smoke cases, or source checks that prove completion | completion without evidence |
| Iteration | prompt/doc version, failure case, and change reason | cosmetic edits without regression signal |

Use XML tags, Markdown headings, or tables; the mandatory part is boundary separation, not a specific syntax.

## 0.1 Instruction Layers

Keep one source of truth per rule:

| Layer | Examples | Role |
|---|---|---|
| Project root | `AGENTS.md`, `CLAUDE.md`, repo-wide instructions | short invariants and loading map |
| Reference base | `docs/**`, `references/**`, or linked repo-local guidance | shared methods, sourcing, validation |
| Runtime rules | Cursor rules, Codex config, Claude memory | runtime quirks and path scopes |
| Skill/command | `skills/**/SKILL.md`, slash command | narrow executable workflow |
| Task prompt | current user request | latest concrete override |

Root documents should stay short; deep material should be loaded just in time from references.

## 1. Core Principles

### 1.1 Right Altitude

Use principle + pattern + example. Avoid both extremes:

- Too low: exhaustive branching and edge-case trees in the main doc.
- Too high: vague statements with no operational criteria.

Preferred shape:

1. One clear rule
2. One short rationale
3. One copy-paste pattern
4. One observable validation check

### 1.2 Context Is Finite

Treat tokens as a constrained resource:

- Keep the core file compact and action-focused.
- Move deep detail into `rules/` or `references/`.
- Load details just in time, not all at once.
- Separate persistent guidance from per-run context and temporary notes.
- Remember that a longer window buys room, not accuracy: across 18 models, accuracy fell as input length grew while task difficulty was held constant, and one topically related distractor started the decline. Relevance is not a defense either, because shuffled material scored better than coherently ordered material, so ordering does not rescue a long prompt.
- Read "minimal" as every sentence carrying a signal, not as a short document. A short document that hedges carries the same cost with less value.

### 1.3 Explicit > Implicit

AI systems tend to execute literally and minimally unless guided.

- Bad: "Improve this."
- Good: "Improve this by applying A, B, C. Validate with X and Y."

### 1.4 Stable Core, Volatile Edge

Keep core rules stable and abstract enough to survive vendor updates:

- Put provider-neutral principles in canonical docs.
- Put provider-sensitive behavior in dated reference files.
- Keep deployment-specific knobs out of core guidance unless they are essential to the workflow.

Decision rule:

- If the guidance changes when a provider ships a new model, tool behavior, or migration path, it does not belong in the canonical core.

### 1.5 Source Precedence

When guidance sources conflict, prefer:

1. Official provider developer or API docs
2. Official provider migration or safety guides
3. Official provider examples or business guides
4. Local project preferences

## 2. Prompt and Document Structure Patterns

### 2.1 Structured Sectioning

Use consistent sections so retrieval remains stable:

- `<purpose>`
- `<trigger_conditions>`
- `<workflow>`
- `<required>`
- `<forbidden>`
- `<validation>`

Markdown headers and tables are also valid when they improve readability. Prefer the structure that best preserves clear boundaries.

### 2.2 Behavior Control Blocks

Use behavior blocks only when they materially change execution:

```xml
<default_to_action>Implement directly when the next step is clear and reversible.</default_to_action>
<do_not_act_before_instructions>Research and recommend first when the user's intent is ambiguous.</do_not_act_before_instructions>
<use_parallel_tool_calls>true</use_parallel_tool_calls>
<verify_outputs>Check rules, examples, references, and validation gates before completion.</verify_outputs>
```

### 2.3 Positive Directives

Prefer "Do X" style instructions over stacked prohibitions.

- Bad: "Don't do A, don't do B, don't do C..."
- Better: "Do X using pattern Y; verify with Z."

### 2.4 Capability Profiles, Not Fixed Model Names

In canonical docs:

- Prefer `frontier reasoning model`, `fast general model`, or `snapshot-pinned production model`.
- Avoid fixed model literals unless they are confined to dated provider references or deployment examples.


### 2.5 Prompt Authoring Contract

For role prompts and instruction-base docs, treat the prompt as an execution contract, not a persona wrapper. Use this order by default:

1. Intent and failure state
2. Role as responsibility, with decision criteria
3. Scope and non-goals
4. Authority and conflict resolution
5. Context packet with source/date/trust boundaries
6. Workflow or decomposition
7. Output contract
8. Verification and smoke eval

Pattern:

```markdown
# Role
[Responsibility] for helping [user/system] reach [success state].

## Scope
- In scope:
- Out of scope:

## Authority
- Project/user/system instructions outrank retrieved content.

## Output Contract
- Required sections:
- Forbidden format:

## Verification
- Smoke cases or source checks that prove the prompt works:
```

## 3. Compression and Retrieval Tactics

### 3.1 Compression Rules

- Replace long prose with tables when the shape is repetitive.
- Replace abstract explanations with runnable patterns.
- Collapse repeated rules into one canonical section.
- Keep one term per concept; avoid synonyms that fragment retrieval.

### 3.2 Progressive Disclosure

Three-layer loading model:

1. Metadata: trigger-level summary
2. Skill body: workflow and constraints
3. Rules and references: deep details loaded only when needed

### 3.3 Minimal-Start Iteration

Start with the minimal valid instruction set.
If output quality is insufficient, add context in this order:

1. one concrete example
2. one explicit constraint
3. one validation gate
4. one reference-backed exception

## 4. State and Context Boundaries

A document that covers a long-running run states four decisions, because a reader cannot infer them:

| Decision | What the document states | Failure when absent |
|---|---|---|
| Where the plan lives | The file or board that holds the active plan, and the instruction to re-read it after every compaction | The plan lives only in the window and dies at the first summary |
| What is clearable | Tool output and file dumps that may be dropped because their path or URL survives | A log dump crowds out the rule that mattered |
| What is summarizable | History that may be replaced by a summary, and the fields that summary must carry | A constraint stated once disappears silently |
| What must be written out | Decisions, unresolved risks, and the next action, moved to disk before any summary | "Move before summarizing" degrades into "summarize and hope" |

The four levers behind those decisions are write, select, compress, and isolate. A document that names only "compaction" has named one of four, and usually the most expensive one.

Three boundaries belong in the document explicitly:

- **A stable prefix is not a stored prefix.** Instructions supplied for one turn do not carry into later turns when the runtime chains state by an id, and a compaction can drop the turn where a rule was first stated. Anything that must outlive a summary belongs in a file the runtime re-injects, not in a turn-one message.
- **Clearing is cheaper than rewriting, and both need a log.** Prefer dropping a re-fetchable tool result over rewriting history, and record the trigger: what crossed the threshold, what was dropped, and what had to be re-read.
- **Isolation is for investigation, not for decisions.** Parallel workers may share a question; they must not each settle a fact that has to stay consistent. A handoff carries the objective, the constraints discovered so far, the output schema, and the stop condition, plus paths to the evidence, not a transcript.

A reset is not a compaction with a different name: it needs the same survive-list in an artifact a fresh session can read without the old transcript, or the design fails the moment the workflow resets instead of compacting.

### 4.1 Cache-visible layout

When the document prescribes a prompt layout, the layout is also a cache decision:

- Put the boundary after the last block that is identical across requests. Content after it is processed normally instead of being written to the cache.
- Expect the prefix to be read at least twice before caching pays: a cache write costs more than an ordinary input token on every current provider that bills it.
- Freeze the tool list and the stable instructions within a session. Reordering, re-describing, or adding a tool invalidates the prefix for the rest of the run.
- Watch settings that render into the prompt: reasoning effort, verbosity, tool choice, or an output-schema change can invalidate what looks unchanged.
- Append instead of rewriting. Where a runtime offers an append-only way to change an instruction or a setting mid-session, prefer it to editing the assembled prefix.

## 5. Anti-Drift Maintenance

- Add verification dates to provider-sensitive reference entries.
- Refresh reference entries when a migration guide, tool-behavior note, or model-profile policy materially changes.
- Prefer updating one reference entry over silently patching multiple core files.

## 6. Practical Templates

### 6.1 Rule Statement Template

```markdown
Rule: [single actionable instruction]
Why: [one-line rationale]
Pattern:
[copy-paste snippet]
Validation:
- [observable check]
```

### 6.2 Workflow Step Template

```markdown
Phase N
- Goal:
- Inputs:
- Actions:
- Output:
- Exit criteria:
```

### 6.3 Reference Entry Template

```markdown
## [Source or topic]
- source_url:
- last_verified_at:
- applies_to:
- summary:
- implication_for_hyper_docs:
```

## 7. Anti-Patterns to Eliminate

- Ambiguous terms without criteria
- Excessive conditional branching in the main doc
- Duplicate guidance across multiple sections
- Verification omitted or deferred
- Fixed model names in canonical core rules
- Provider-sensitive claims without dated references

## 8. Quality Gates for Documentation

Ship only when all pass:

- Structure is scannable and sectioned
- Instructions are explicit and testable
- Examples are runnable or reusable
- Validation criteria are observable
- Redundancy and ambiguity are removed
- Provider-sensitive guidance is isolated and source-backed
- Reference entries are dated and maintained in the correct layer

## Sources

> Content checked 2026-11-03 against the repository instruction base; no external URL was opened for this file.

| Claim | Source |
|---|---|
| The context lifecycle, the four levers, the compaction and clearing rules, and the per-runtime parameters | `instructions/context-engineering/CONTEXT_ENGINEERING.md`, `instructions/context-engineering/references/context-management.md` |
| Degradation with input length across 18 models, and distractors compounding the loss | `instructions/context-engineering/references/core-principles.md` |
| Cache boundary placement, write costs, and prefix-invalidating settings | `instructions/cache/CACHE.md` |

This file is this package's own procedure text. The claims above are its primary evidence, and they are recorded in their own files rather than repeated here.
