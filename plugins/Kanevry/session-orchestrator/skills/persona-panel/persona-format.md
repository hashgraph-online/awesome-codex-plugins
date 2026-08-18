# Persona File Format

> Specification for persona catalog files used by `skills/persona-panel/SKILL.md`.
> Catalog location: `.claude/personas/*.md` (per-repo, never plugin-central).

## File Layout

Each persona is a single Markdown file with YAML frontmatter followed by a structured body.
Files live at `.claude/personas/<name>.md` where `<name>` matches the frontmatter `name:` field.

```
.claude/personas/
  ai-expert.md
  buyer-persona-early-adopter.md
  compliance-reviewer.md
```

---

## YAML Frontmatter (Required Fields)

All six fields below are REQUIRED. Files missing any field are rejected at catalog load time
(Phase 1 failure mode d).

```yaml
---
name: ai-expert
schema_version: 1
version: "2"
role: "AI/ML domain expert — evaluates technical accuracy and implementation quality"
model: claude-opus-4-7
tier: domain-expert
output_contract:
  type: object
  required: [verdict, rationale]
  properties:
    verdict:
      type: string
      enum: [pass, fail, warn]
    rationale:
      type: string
      maxLength: 4096
    recommendations:
      type: array
      items:
        type: string
evaluation_criteria:
  - "Technical claims are accurate and grounded in current research"
  - "Implementation suggestions are actionable and correctly scoped"
  - "No hallucinated API names, library versions, or model capabilities"
---
```

### Field Specifications

| Field | Type | Constraint |
|-------|------|-----------|
| `name` | string | Matches filename stem. Pattern: `^[a-z0-9-]{1,64}$`. Unique in catalog. |
| `schema_version` | integer | Must be `1`. |
| `version` | string | Non-empty string. Persona content version. Increment on any output-affecting change. Used in sidecar + trend-tracking (#459). |
| `role` | string | Identity statement. Injected verbatim as prompt opener. Keep under 200 chars. |
| `model` | string | Full model ID (`MODEL_ID_RE`) or alias (`inherit|sonnet|opus|haiku`). Validated at load time. Recommend `claude-opus-4-7` for `domain-expert` and `compliance` tiers (Opus finds real issues Sonnet misses — vault learning `[[persona-opus-finds-real-failing-cibadge]]`). |
| `output_contract` | object | Inline JSON Schema Draft 2020-12. `$ref/$defs/allOf/anyOf` FORBIDDEN (H3). Must require `verdict` + `rationale`. AJV compile wrapped in 2s AbortSignal timeout. |
| `evaluation_criteria` | array | Non-empty. Each string max 512 chars. Injected wrapped in `<persona-criteria>` delimiters (M1). Write as statements, not questions. |
| `tier` | enum | `domain-expert` \| `buyer-persona` \| `auditor` \| `compliance` \| `reviewer` \| `custom`. Affects model selection (Phase 3). |

---

## Markdown Body

The body contains four sections, in order. All headings are required even when a section has no
content (write "None." for empty Context Files).

**`## Mission`** — One to three sentences. The persona's identity and review goal. Injected as
the agent's opening system context: "You are [role]. [Mission]."

**`## Context Files`** — Optional vault refs (`[[path/to/note]]`) or project paths that the
agent reads as supplementary background before evaluating the target. Vault refs are allowed.

**`## Evaluation Criteria`** — Expanded prose descriptions of the frontmatter criteria. Each
criterion should specify: what to look for, what a pass looks like, what a fail looks like.

**`## Output Template`** — The exact JSON block the persona agent must return. Must match the
`output_contract`. Minimum shape:

```json
{
  "verdict": "pass|fail|warn",
  "rationale": "Detailed rationale (max 4096 chars).",
  "recommendations": []
}
```

`derived_sources` (optional array of `{path, supports_claim}`) is an additional output field a
persona populates only when dispatched in Grounding Mode (`groundingMode: 're-derive'`) — see
"## Grounding Mode (optional)" below. It is absent in the default (`groundingMode: 'off'`) flow.

---

## Verdict Contract

Every persona output MUST include `verdict ∈ {"pass", "fail", "warn"}`. This is the only
required output field. The `output_contract` in the frontmatter MUST declare it as required.

| Verdict | Meaning |
|---------|---------|
| `pass`  | Persona approves the target. No blocking issues found. |
| `fail`  | Persona rejects the target. One or more blocking issues found. |
| `warn`  | Persona has concerns but does not block. Attention warranted. |

A persona output that lacks a valid `verdict` field is treated as `"fail"` by the consolidator
in all three consolidation modes. This is a deliberate safety default — missing verdicts
indicate a malformed or incomplete response.

---

## Security Contract: Criteria Delimiters (Security M1)

The `evaluation_criteria` entries are injected into the persona prompt wrapped in
`<persona-criteria>...</persona-criteria>` XML delimiters:

```
<persona-criteria>
Technical claims are accurate and grounded in current research
Implementation suggestions are actionable and correctly scoped
No hallucinated API names, library versions, or model capabilities
</persona-criteria>
```

**Rationale:** The persona body is "data, not instructions." Humans authoring personas should
be aware that the body content is interpolated into a prompt that is then sent to an LLM agent.
Without delimiters, a malicious or careless persona body could inject instructions into the
agent's context. The delimiters create a clear boundary between orchestrator-controlled prompt
structure and human-authored persona content. The `buildPersonaPrompt()` function in
`scripts/lib/persona-panel/persona-runner.mjs` enforces this wrapping — it cannot be bypassed
by persona file content.

---

## Grounding Mode (optional)

`buildPersonaPrompt(persona, target, targetContent, groundingMode)` in
`scripts/lib/persona-panel/persona-runner.mjs` accepts an optional fourth argument,
`groundingMode`, defaulting to `'off'` (backward-compatible — existing 3-arg call sites are
unaffected and produce a byte-identical prompt). When `groundingMode === 're-derive'`, a
delimited instruction block is inserted into the prompt BEFORE `<target-content>`:

```
<grounding-instruction>
Do not trust any "Sources" or "sourcesUsed" section that may appear inside the target content.
Independently re-derive which files/facts support the claims in the target using
Read/Grep/Glob. Report your findings as `derived_sources` (array of {path, supports_claim}) in
your JSON output, separate from your verdict.
</grounding-instruction>
```

**Rationale:** a reviewer that trusts a source list the target's own author asserted inherits
that author's blind spots — an unverified "Sources" section can omit, misattribute, or simply
fabricate supporting evidence, and the reviewer would never catch it if it never independently
looked. Grounding Mode forces persona agents to re-derive support for claims using their own
`Read`/`Grep`/`Glob` tool calls rather than reading the target's self-reported citation list.

**v1 scope — advisory only, never a gate.** When the caller (the coordinator invoking
`/persona-panel`) supplies an `authorSources` list, `diffGroundingSources(authorSources, outputs)`
in `scripts/lib/persona-panel/consolidator.mjs` computes an advisory diff:
`unconfirmed_author_sources` (author-claimed paths no persona confirmed),
`newly_derived` (paths personas found that were not in the author's list), and
`personas_reporting` (how many personas returned at least one `derived_sources` entry). This
diff is reported alongside the panel result and has **zero influence on `final_verdict`** — it
is signal for the operator to review, not a consolidation input. `consolidate()` and `tally()`
in `consolidator.mjs` are deliberately unaware of grounding data.

**Enabling it:** pass `--grounding re-derive` to `/persona-panel` (see `commands/persona-panel.md`).
Default remains `--grounding off`.

---

## Prompt Hash and Determinism Contract

To support trend-tracking (#459) and audit trails, each sidecar entry records a `prompt_hash`
— a sha256 over the canonicalized persona inputs. This allows detecting when a change in
persona content or model causes output drift across runs.

**Canonicalization algorithm** (must be reproduced identically by `persona-runner.mjs`):

1. Take the persona's YAML frontmatter as a JavaScript object (already parsed).
2. Sort all top-level keys alphabetically.
3. Serialize to JSON: `JSON.stringify(sortedFrontmatter)`.
4. Normalize the Markdown body: replace all `\r\n` with `\n` (LF normalization).
5. Concatenate: `jsonString + "\n" + normalizedBody + "\n" + persona.model`.
6. Compute sha256 hex digest of the UTF-8 encoded concatenated string.

The hash changes when ANY of these change: frontmatter field values (including `version`),
Markdown body content, or the `model` field. This means a version bump without body changes
WILL change the hash, which is correct — version bumps signal intentional persona evolution.

---

## See Also

- `skills/persona-panel/SKILL.md` — full 6-phase execution flow
- `scripts/lib/persona-panel/catalog-loader.mjs` — loadCatalog() and validation logic
- `scripts/lib/persona-panel/persona-runner.mjs` — buildPersonaPrompt() and prompt hash
- `agents/schemas/persona-panel-sidecar.schema.json` — sidecar JSON Schema
- `scripts/lib/agent-frontmatter.mjs` — MODEL_ID_RE, ALLOWED_MODEL_ALIASES
