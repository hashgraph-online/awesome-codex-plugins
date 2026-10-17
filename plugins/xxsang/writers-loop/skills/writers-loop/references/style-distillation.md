# Style Learning And Style Distillation

Use this reference when the user asks to learn writing style from files,
chapters, pasted text, reports, docs, or codebase text.

## Goal

Create reusable style guidance that lets future drafts write in the user's own
style or a permitted reference style without copying private content, source
passages, plot facts, names, business facts, or domain-specific claims into a
style rule.

## Flow

1. Identify source type, target artifact type, audience, permission or ownership, and intended reuse.
2. Select representative samples instead of reading every token when the corpus is large.
3. Separate style from content facts.
4. Extract observable traits.
5. Produce a reusable style pack.
6. Validate the style pack against samples.
7. Ask whether to use it for the current task, save it, or keep it session-only.

## Style Pack Lifecycle

Use this lifecycle for reusable style work:

```text
learn style -> review style pack -> apply style -> critique style match -> revise -> save or keep session-only
```

`Style Pack` and `Learned Preferences` are different artifacts:

- `Style Pack`: reusable voice, rhythm, structure, diction, imagery, register, and formatting guidance derived from samples.
- `Learned Preferences`: decision-backed writing rules learned from user accept, reject, adjust, undo, or manual rewrite events.

Do not treat a newly generated style pack as a permanent preference. A style
pack is a drafting constraint until the user reviews it, applies it, or saves it.

Always include an explicit `Style Versus Content` section before the style pack.
This section must name what will be extracted as style and what will not be
copied into reusable rules.

Always start the response with a `Frame` section and end with a `Storage
Decision` section. The storage decision must ask whether to apply the style pack
now, keep it session-only, or save it durably.

## Source Handling

Use selected files, pasted text, chapters, reports, docs, or codebase prose.
If the user wants to clone or adapt another person's style, confirm the samples
are permitted for the requested use or keep the style pack session-only and
avoid durable storage until permission is clear.

When the source is a codebase, search for writing-heavy files first:

```text
README.md
docs/
*.md
*.mdx
prompts
templates
examples
fixtures
```

Avoid treating implementation code as prose style unless the user asks for code
comment or API documentation style.

For long corpora, sample from the beginning, middle, and end. Prefer multiple
representative documents over one oversized document.

## Style Versus Content

Extract:

```text
voice
tone
sentence rhythm
paragraph shape
level of abstraction
image density
argument structure
transition style
dialogue style
terminology conventions
formatting conventions
reader relationship
```

Do not extract:

```text
plot events
private facts
customer names
confidential claims
domain truths
source passages
temporary project constraints
one-off factual wording
```

## Style Pack Format

```text
Frame
- Source type:
- Target artifact type:
- Audience:
- Permission or ownership:
- Intended reuse:
- Constraints:

Style Versus Content
- Extract as style: [voice, rhythm, structure, terminology pattern, formatting pattern]
- Do not copy as reusable rules: [plot facts, private facts, names, source passages, project-specific claims]

Style Pack
Name:
Source:
Intended reuse:
Confidence:

Summary:
[2-4 sentence summary]

Observable Traits:
- [trait]

Do:
- [reusable instruction]

Avoid:
- [reusable anti-pattern]

Structure Rules:
- [section, scene, paragraph, or argument pattern]

Language Rules:
- [diction, syntax, terminology, rhythm]

Reusable Prompts:
- Drafting: [prompt]
- Critique: [prompt]
- Revision: [prompt]

Evidence Notes:
- [source evidence summary without long quotes]

Storage Decision:
Reply "apply now", "keep session-only", or "save durably".
```

## Confidence

Use `high` only when a trait appears in at least 3 instances across 2 or more
documents. "Appears" means the same pattern, not the same wording — paraphrase
and structural repetition count.
Use `medium` when a trait appears in at least 2 instances but from a single
document, or when 3+ instances exist but variety is limited.
Use `low` when the corpus is small (fewer than 2 clear instances), inconsistent,
or heavily edited by unknown authors.

Ask before applying low-confidence style rules.

## Applying A Style Pack

When using a style pack inside the main loop:

1. Add it to `Frame` as a style constraint.
2. Mention which style rules materially affect the `Plan`.
3. Draft with the style pack.
4. Critique for style match and content quality separately.
5. Treat user acceptance or rejection of style-matching edits as preference evidence.

## Using A Learned Style

Use this path when the user says to write in a saved, learned, or named style:

1. Load the style pack from the conversation or from `.writers-loop/styles/` only when local storage was explicitly enabled.
2. Summarize the style constraints that will affect the new artifact.
3. Frame the new writing task with the style pack as a constraint.
4. Plan for content and style separately.
5. Draft in the learned style using only current-task facts.
6. Run a `Style Match Review` that checks voice, rhythm, sentence texture, paragraph shape, diction, imagery, register, and structure.
7. Revise style mismatches without copying source passages or source facts.
   Before finalizing, run the `Source-Passage Check` (see section below).
8. Ask whether any accepted style edits should become decision-backed preferences.

Use this output shape:

```text
Frame
- Artifact type:
- Audience:
- Goal:
- Style pack:
- Constraints:

Plan
- Content structure:
- Style application notes:

Draft
[new text using current-task facts]

Critique
- Content quality:
- Style match:

Style Match Review
- Matches:
- Misses:
- Risks:

Proposed Changes
- [targeted content or style changes]
```

Style-pack availability is checked before artifact questions. If the requested
style pack is missing, unavailable, or the user says not to load it first, do
not draft, do not output `QUESTION GATE`, and do not ask general artifact
questions yet. Use the section headers below exactly:

```text
Frame
- Artifact type:
- Audience:
- Goal:
- Style pack: [name] (not loaded)
- Constraints:

Style Pack Status
- Requested pack:
- Lookup result:
- Needed next: paste the style pack or provide the project directory containing `.writers-loop/styles/[name].md`

Content Plan
- [structure for the requested artifact, using only current-task facts]

Style Application Plan
- Waiting for style rules before drafting
- Will review content quality and style match separately after the pack is loaded

Next Action
- Paste the style pack or confirm the local path to load it from.
```

## Local Style Pack Storage

When the user opts into durable local style storage, use:

```text
.writers-loop/
|-- journal.jsonl
|-- prefs.md
`-- styles/
    |-- my-style.md
    `-- reference-style.md
```

Use `scripts/style-pack.mjs` from the skill directory:

```bash
node scripts/style-pack.mjs init /path/to/project
node scripts/style-pack.mjs save /path/to/project my-style /tmp/reviewed-style-pack.md
node scripts/style-pack.mjs list /path/to/project
node scripts/style-pack.mjs show /path/to/project my-style
```

Relative style-pack file paths are resolved from `/path/to/project` first, then
from the current working directory. `save` rejects files that look like raw
source samples; use `--force` only after explicit review and approval.

Only save reviewed style packs, not raw source samples. Do not save another
person's style durably when permission or intended reuse is unclear.

## Source-Passage Check

Before finalizing any style-informed revision, confirm:

```text
SOURCE-PASSAGE CHECK
The following changes use only current-task facts and original drafting.
No source passages, private names, or content facts from the style pack evidence
have been copied into this revision.
```

If a proposed change contains quoted or closely paraphrased material from the
style pack's evidence notes, rewrite it using only current-task content.

## Common Mistakes

- Copying content facts into style rules.
- Copying source passages into reusable prompts or examples.
- Overfitting from one short sample.
- Treating genre conventions as the user's personal style.
- Treating another person's style samples as permitted when permission or intended reuse is unclear.
- Applying a saved style pack without loading or summarizing it first.
- Revising content while skipping the style-match review.
- Mixing style preferences across unrelated artifact types.
- Claiming a permanent preference when the user only asked to match a source once.
