# Hyper-Extract design steals (authoring rules)

Three reusable authoring contracts mined from Hyper-Extract's template-design
skills (`graph-designer`, `yaml-validator`, `template-optimizer`). They apply to
any AgentOps surface that pairs a machine-readable **schema** with human-written
**guidance** — SKILL.md frontmatter + body, extraction templates, record/graph
designers, and the corpus schemas under `schemas/`.

## 1. The WHAT-vs-HOW authoring contract

**Rule:** the **schema defines WHAT** (the fields, their types, their identity);
the **guideline defines HOW to do it well** (extraction strategy, quality bars,
creation conditions, common mistakes). A guideline that restates field
definitions is drift — the schema already owns that. Keep them disjoint.

This is the single most load-bearing separation when a schema and a guideline
travel together: every duplicated field description in the guideline is a place
the two can silently diverge. Author the guideline as if the reader has already
read the schema.

| Guideline SHOULD carry | Guideline should NOT carry (schema owns it) |
|------------------------|---------------------------------------------|
| Extraction strategy ("extract the valuable entities") | Field definitions ("`name` should be…") |
| Quality requirements ("keep naming consistent") | Type descriptions ("the `type` field is a str") |
| Creation conditions ("only when the text states it") | Reference requirements ("must point at `name`") |
| Common mistakes to avoid | Restated schema field descriptions |

**Enforcement smell (steal from `template-optimizer` rule 4):** flag any
guideline/rules prose that repeats a field definition or a type description —
that is a schema-vs-guideline boundary violation, not guidance. Fix by deleting
the restated field text from the guideline; the schema is the single source of
WHAT.

Applied to skill authoring: the SKILL.md frontmatter (`name`, `description`,
`hexagonal_role`, `consumes`/`produces`) is the schema = WHAT the skill is; the
SKILL.md body is the guideline = HOW to run it well. Do not restate frontmatter
fields prose-side; spend the body on strategy, quality bars, and footguns.

## 2. Identifier dedup-key patterns (canonical dedup-key form)

**Rule:** a dedup key (identity key) for a relationship/edge is a **template of
field references**, not a free-text string. The canonical form is:

```
'{from}|{rel}|{to}'
```

i.e. pipe-joined `{field}` placeholders that resolve against the record's own
fields. This replaces hand-written string `dedup_keys` (which drift from the
schema and can't be validated). Hyper-Extract's live forms:

```yaml
identifiers:
  entity_id: name
  relation_id: '{source}|{relation_type}|{target}'              # graph edge
  relation_id: '{source}|{relation_type}|{target}|{event_date}' # temporal edge
  relation_id: '{source}|{relation_type}|{target}|{location}'   # spatial edge
  relation_members:
    source: ...
    target: ...
```

Why a template, not a string:

- **Validatable** — every `{placeholder}` must resolve to a declared field, so a
  dedup key referencing a non-existent field is a catchable error (see the
  `yaml-validator` identifier checklist).
- **Schema-anchored** — the dedup key is derived from WHAT (the fields), so it
  cannot silently diverge from the schema the way a free string can.
- **Composable** — add a dimension (time, location) by appending another
  `{field}`; the dedup key extends with the schema instead of being rewritten.

**Adopt as canonical:** when a corpus/extraction surface needs an identity or
dedup key, express it as a `{field}|{field}|…` template over declared fields —
never an opaque string `dedup_key`.

## 3. Folded patterns from the three Hyper-Extract design skills

Useful, runtime-agnostic patterns lifted into our authoring doctrine:

- **`graph-designer` → type-driven design + display labels.** Confirm the shape
  first (record vs graph vs hypergraph vs temporal/spatial), then design fields
  to the shape. Carry a human-readable display label derived from fields
  (`'{name} ({category})'`) so output is legible without re-deriving identity.
  Mirror for skills: pick the skill *mode* first, then author to that mode.
- **`yaml-validator` → tiered, ordered validation.** Validate in a fixed order
  (syntax → structure → identifiers → field-quality) and grade findings by
  level: **ERROR** (won't work — must fix), **WARNING** (quality risk — should
  fix), **INFO** (recommended). This is the same tiering our heal-skill deep audit uses;
  prefer ordered + level-graded checks over a flat pass/fail.
- **`template-optimizer` → information-density discipline.** Flag > 5 fields per
  entity/relation for review; prioritize **Essential → Important → Optional** and
  cut to the essential set. Standardize names to the concise canonical token
  (`relation_type` → `type`, `event_date` → `time`). Apply the same three
  optimization tiers to authoring fixes: **Auto-fix** (always-safe), **Suggest**
  (needs review), **Review** (a design decision, leave to the author). This is
  the field-count complement to our context-density rule.

## Provenance

Steals captured from the `Hyper-Extract` reference clone
(`hyperextract-skills/{graph-designer,yaml-validator,template-optimizer}`) under
bead age-bp1. Folded as additive authoring rules; no runtime behavior depends on
the Hyper-Extract code.
