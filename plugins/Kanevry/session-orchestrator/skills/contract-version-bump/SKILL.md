---
name: contract-version-bump
user-invocable: true
tags: [contracts, versioning, schema, changelog, governance]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
args-schema:
  - flag: --contract <path>
    description: "Path to the contract file being bumped (JSON Schema, API spec, config schema). Inferred from conversation context if omitted."
description: >
  Use this skill when changing a machine-readable contract — a JSON Schema, an API spec, or a
  config schema — and bumping its version: tightening a constraint, adding/removing/renaming a
  field, introducing a breaking change, raising an API version, or writing the changelog entry
  for a schema change. Trigger on "change the schema", "tighten this constraint", "bump the
  schema version", "breaking change to the API", "new API version", "changelog entry for a
  schema change". Runs six phases — classify against the contract's OWN versioning rule (not
  generic semver instinct), find every version literal and vendored copy, check consumer
  compatibility for new keywords, apply consistently, write the changelog entry, and report
  downstream drift — codifying three non-obvious traps hit in a real case (GitLab issue #17,
  `aiat-enablement` repo, 2026-07-25).
---

# Contract Version Bump

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent
> aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md).
> Every reference to `CLAUDE.md` in this skill resolves via that precedence rule.

A version bump on a machine-readable contract (JSON Schema, OpenAPI/API spec, config schema) is
not just "increment the number." Three failure modes recur and are each individually
non-obvious enough that a careful agent still misses them without a checklist: the contract's
own versioning rule may not even cover the change you're making; version literals live in more
places than you remember; and a schema keyword that no consumer evaluates is worse than no
constraint at all, because it *looks* enforced. This skill runs six phases to close all three.

**Reference case:** `aiat-enablement` repo, GitLab issue #17 (2026-07-25). A JSON Schema contract
(`docs/spec/estate.schema.json`, draft/2020-12) had six fields tightened with new `pattern`
constraints; `schema_version` moved `0.1.0` → `0.1.1`. All three traps below happened in that
one change. Where cited, "the reference case" means this.

## Phase 1: Classify against the CONTRACT'S OWN versioning rule

Do not classify Patch/Minor/Major from generic semver instinct. Read the contract's own
versioning-rules section (in its prose spec, README, or a `## Versioning` block near the schema)
and ask explicitly: **does this rule even define the change class you're making?**

```bash
# Does the spec define rules for Patch changes at all? (substitute Minor/Major as needed)
grep -n "^#.*[Vv]ersion" docs/spec/<contract>.md
grep -c "Patch" docs/spec/<contract>.md
```

If the clause you need is missing, **authoring that clause is part of this change**, not a
side quest — write it with an explicit justification for why the new class exists and why your
change belongs in it, then proceed. If the clause exists but classifies your change as a stricter
tier than you assumed (e.g. a "just tightening a pattern" edit is actually forbidden under an
additive-only Minor rule), the rule wins — either recategorize the change or amend the rule
first, but never bump the number past what the contract's own rule permits.

Reference case: `docs/spec/estate-yaml-v0.md` defined only Minor (additive-only) and Major
(needs a migration step). `grep -c "Patch" docs/spec/estate-yaml-v0.md` returned `0`. A
constraint tightening is not additive, so under the existing rule alone it was forbidden. The
Patch clause had to be authored — with a written justification (no production consumers yet
validate against this vorproduktions-schema, so no migration burden exists) — before the bump
was legitimate.

## Phase 2: Find every version literal and copy — mechanically, not from memory

Never trust "I updated it everywhere I remember." Grep for the literal.

```bash
# 1. Every occurrence of the current version string in this repo
grep -rn "<current-version>" --include=*.json --include=*.md --include=*.yaml --include=*.yml .

# 2. The field/key that carries the version, wherever it's mentioned in prose
#    (field-catalog tables, example fixtures, README snippets)
grep -rln "schema_version\|apiVersion\|<version-field-name>" docs/ examples/ 2>/dev/null

# 3. Vendored copies in sibling repos — check every path under the instruction
#    file's `cross-repos:` list. Match by basename, not by path: a vendored copy
#    is rarely at an identical relative path.
#    CLAUDE.md and AGENTS.md are transparent aliases — resolve whichever exists.
INSTR=$([ -f CLAUDE.md ] && echo CLAUDE.md || echo AGENTS.md)
for repo in $(yq '.["cross-repos"][]' "$INSTR" 2>/dev/null || grep -A20 '^cross-repos:' "$INSTR" | grep '  - ' | sed 's/^ *- *//'); do
  find "$repo" -iname "$(basename <contract-file>)" 2>/dev/null
done
```

For every location found, decide explicitly: **does it get bumped, or is it exempt?** Exemptions
are legitimate (a dated SSOT snapshot like a PRD is allowed to stay frozen at the version it was
approved under) but the exemption must be written down next to the literal that was skipped, or
the next diff will read as silent divergence.

Reference case: `schema_version` lived in five places — the schema file itself
(`docs/spec/estate.schema.json`), the field-catalog table in the prose spec
(`docs/spec/estate-yaml-v0.md`), an example fixture (`docs/spec/examples/estate.example.yaml`), a
**vendored copy in a different repo** (`aiat-poc-infra/scripts/estate/estate.schema.json`), and
the PRD (`docs/prd/2026-07-25-aiat-enablement.md`, Anhang D.1). The PRD was deliberately *not*
bumped — but that decision was written into the spec's "Anmerkungen zu diesem Dokument" section
explicitly, precisely so it would never be mistaken for an oversight.

## Phase 3: Check consumer compatibility for every new/changed keyword

For each keyword you are adding or changing (`pattern`, `maxLength`, `enum`, `format`,
`additionalProperties`, a new required field, a new `apiVersion` value, …), find every known
consumer of the contract and ask: **does this consumer actually evaluate this keyword, or does
it silently ignore what it doesn't recognize?**

- A full-featured library (ajv, `jsonschema`, an OpenAPI-generated client) generally implements
  the standard vocabulary — trust it, but confirm the vocabulary/draft version matches (e.g. a
  draft-07 validator will not enforce 2020-12-only keywords).
- A hand-written parser/interpreter (a bash+heredoc validator, a custom regex-based checker, a
  bespoke deserializer) is the risk case. Grep its source for the keyword name:

```bash
grep -n "maxLength\|minLength\|pattern\|format\|enum" <consumer-script-or-module>
```

If the keyword is absent from the consumer's implementation, you have three options — pick one
and write it down, never leave it implicit:
1. **Extend the consumer** to support the keyword (preferred when the consumer is yours to change).
2. **Fold the constraint into a keyword the consumer already supports** (e.g. encode a length
   limit inside a `pattern` instead of a separate `maxLength`).
3. **Accept the gap and document it as a known limitation** in the spec, naming the consumer —
   only when neither of the above is feasible right now.

A constraint a consumer silently ignores is worse than no constraint: it looks enforced in the
schema, so nobody double-checks the actual runtime behavior, and invalid data passes through
undetected.

Reference case: `maxLength: 63` was the natural way to express S3 bucket-name limits. The
downstream validator (`aiat-poc-infra/scripts/estate/validate-estate-yaml.sh`) is a hand-written
JSON-Schema mini-interpreter that does not implement `maxLength` — it would have parsed the
schema, not recognized the keyword, and silently done nothing, so a 200-character bucket name
would still validate green. Decision: extend the consumer (option 1) rather than relying only on
the `pattern`'s implicit length ceiling — the `maxLength` branch was added to the interpreter in
the same session, on branch `feature/estate-yaml-format-tightening-17`, and proven by a mutation
test (disable the branch → the `[MAXLENGTH]` assertion goes red while `[PATTERN]` still fires).

That mutation test is itself the lesson: because the bucket `pattern`
(`^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$`) already bounds total length via its quantifier, an
over-length value trips BOTH rules. A fixture alone could not prove the new `maxLength` code was
load-bearing — only disabling that code and watching the specific assertion fail could. When a
new keyword overlaps an existing constraint, prove it in isolation or you have not proven it.

## Phase 4: Apply consistently

Bump the version literal and the constraint change together, everywhere Phase 2 found a
non-exempt occurrence. For each exemption identified in Phase 2, write the reason next to it
(a spec's "Anmerkungen"/decisions section, a code comment, a linked issue) — an exemption without
a written reason is indistinguishable from a bug the next time someone diffs the two documents.

## Phase 5: Write the changelog entry

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions already in use in
this repo's `CHANGELOG.md` — add the entry under the repo's convention for in-progress work
(commonly an `## [Unreleased]` section; check the top of the file for the existing pattern before
inventing a new one). What goes in the entry depends on the classification from Phase 1:

- **Patch (constraint tightening on an existing field):** name every field that changed, the old
  constraint and the new one. **State explicitly that this can reject previously-valid documents
  for consumers, even though the version number alone does not signal a breaking change** — the
  version-number tier and the actual blast radius for a consumer are two different axes; do not
  let the reader infer breaking-ness from the tier alone.
- **Minor (additive field(s)):** name the new field(s) and confirm the change is additive-only —
  no existing field's meaning, requiredness, or name changed.
- **Major (breaking structural change):** name the field(s)/structure that changed and link the
  migration step (e.g. `migrations/<contract>/`) a consumer must run.

## Phase 6: Report downstream drift

List every vendored copy or dependent repo found in Phase 2 that this change did **not** update.
For each: name the repo/path, why it wasn't updated now (e.g. "follow-up MR pending, tracked
separately"), and the tracking issue if one exists. Never let a known-stale copy pass silently —
surface it as explicit follow-up work, even if fixing it is out of scope for this change.

---

## Checklist

- [ ] Read the contract's own versioning-rule section. Does it define the change class you're
      making? If not, write the clause first (with justification), before touching the version.
- [ ] Classify Patch / Minor / Major against that rule — not generic semver instinct.
- [ ] `grep -rn` the current version literal across this repo (schema, prose spec, examples/fixtures).
- [ ] Search every repo in the instruction file's `cross-repos:` list (`CLAUDE.md`, or `AGENTS.md`
      on Codex CLI) for a vendored copy (basename match).
- [ ] For every new/changed keyword, grep each known consumer's source for that keyword name.
      Decide: extend / fold into a supported keyword / document the gap — pick one, write it down.
- [ ] Apply the bump + constraint change to every non-exempt literal found in Phase 2.
- [ ] Write the reason next to every exemption (a document deliberately NOT bumped).
- [ ] Write the changelog entry — name the fields, old vs. new constraint, and call out breaking
      risk for consumers explicitly, independent of the version tier.
- [ ] List every dependent repo/copy left un-synced, with a tracking issue.

## Anti-Patterns

1. **Silent contract violation.** Bumping a version for a change class the contract's own rule
   doesn't cover — or actively forbids — without amending the rule first. *Reference case:* the
   spec defined only Minor (additive) and Major (needs migration); a constraint tightening isn't
   additive, so it was forbidden under the existing rule until a Patch clause was authored with
   an explicit justification.
2. **Literal drift from memory.** Updating the version "everywhere I remember" instead of
   grepping mechanically. *Reference case:* the version literal lived in five places, including a
   vendored copy in a *different* repo (`aiat-poc-infra`) that a memory-based sweep would not
   have found; one location (the PRD) was correctly left un-bumped, but only because that
   exemption was written down explicitly instead of left silent.
3. **Ignored keyword, worse than no keyword.** Adding a schema keyword without checking whether
   every known consumer evaluates it. *Reference case:* `maxLength: 63` would have been silently
   skipped by a hand-written validator that doesn't implement it — the schema would have *looked*
   enforced while the runtime check let arbitrarily long values through.

## When this does not apply

Pure documentation-only edits to a contract (typo fixes, added examples, clarified descriptions)
that change no validated field, constraint, or version-relevant semantics do not need a version
bump or this skill — but if you're unsure whether a wording change is validation-relevant, treat
it as a change and run Phase 1.
