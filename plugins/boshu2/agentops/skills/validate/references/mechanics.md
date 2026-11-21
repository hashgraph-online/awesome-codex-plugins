# Validate mechanics

Depth for [SKILL.md](../SKILL.md): the `ao provenance` helpers, the
`store-verdict` draft, evidence storage and where each scope limit lives. Judgment never depends on this
file: without it, use the Git subject fallback in `SKILL.md` and return the
result inline.

## Helper commands

Installed mechanics run through `ao provenance` (evidence helper version 1),
using `subject-manifest.v1` and `verdict.v2` unchanged. A fresh Validate agent
supplies the semantic result; Go computes identities, verifies structure and
stores the supplied result. No Python interpreter runs on this path.

| Command | Required | Optional |
|---|---|---|
| `manifest` | `--root <dir>`, `--include <path>` (repeatable) | `--exclude <path-or-glob>` (repeatable), `--base-manifest <file>`, `--git-metadata-json <json>`, `--out <relative-file>` with `--evidence-root <dir>`, `--exclude-git-root <dir>` (repeatable) |
| `verify-manifest` | `--root <dir>`, `--manifest <file>` | `--base-manifest <file>` |
| `snapshot-intent` | `--source <file>` (`-` reads stdin), `--evidence-root <dir>` | `--exclude-git-root <dir>` (repeatable) |
| `digest` | `<json-file>` positional | `--json` |
| `store-verdict` | `--root`, `--evidence-root`, `--draft`, `--intent-source`, `--subject-manifest`, `--author-context-id`, `--validator-context-id`, `--freshness-source <runtime\|caller>`, `--freshness-attester-id`, `--scope-result <PASS\|FAIL\|NOT_PROVEN>` | `--base-manifest <file>`, `--exclude-git-root <dir>` (repeatable) |
| `verify-verdict` | `--verdict <digest.json>` | none |
| `verify-subject` | `--root <dir>`, `--manifest <file>`, `--verdict <digest.json>`, `--intent <file>` | `--base-manifest <file>` |

Every leaf accepts `--helper-version 1`; an incompatible version fails before
mutation. Evidence operations emit JSON by default except `digest`, which prints
the digest; `--json` requests JSON explicitly and global `--output`/`-o` selects
JSON or YAML formatting, never a destination file. Conflicting explicit formats
fail before any write.
Exit 0 means the mechanical operation completed. Invalid input, failed
verification or filesystem errors exit 1. A stored `FAIL` or `NOT_PROVEN` may
complete storage successfully; that exit status never means semantic PASS.
`--dry-run` rejects evidence writes before mutation. `ao capabilities` carries
the actual family and leaf argument, output, effect and exit contracts.

```sh
ao provenance manifest --root . --include skills/validate \
  --exclude '**/*.log' --evidence-root "$EVIDENCE_ROOT" --out manifest.json
```

`manifest` uses only filesystem content. Symlinks bind target bytes without
following directory symlinks; executable bits and deletions bind identity.
Optional Git metadata is descriptive and excluded from identity. Unknown fields,
duplicate JSON keys, malformed paths and canonical digest mismatches fail closed.
`verify-manifest` recomputes identity and requires the matching base for deletions.

`store-verdict` verifies a nonempty manifest against the current subject before
storage, binds exact intent bytes and explicit runtime identities/freshness/scope,
and validates the resulting artifact using the same strict reader as `ao status`.
Author/judge collision, missing runtime facts, incomplete scope or a PASS with
unverified acceptance cannot persist an admitted PASS. Proven scope failure
forces FAIL; integrity gaps retain NOT_PROVEN with `validate.integrity` findings.
The caller still owns deriving complete changed-path coverage and freshness;
these helper inputs are attestations, not independently discovered runtime facts.

The artifact digest is SHA-256 over canonical JSON with `artifact_digest`
omitted. A synced private temporary file is atomically published without
replacing an existing address; directory durability uses the shared storage
barrier. Identical existing bytes are idempotent. Conflicting verdict bytes
remain intact and produce a separate NOT_PROVEN integrity artifact. Intent
snapshot collisions fail. Explicit manifest outputs likewise never overwrite
different existing bytes. Existing standalone proof is preserved by its owner.

## store-verdict draft

`--draft` requires the seven fields below. The only other fields it accepts
are the ones storage fills in itself (`schema_version`, the digests,
identities and freshness), which it overwrites from the runtime flags; any
other field fails before storage.

```json
{
  "verdict": "NOT_PROVEN",
  "criteria": [
    {"id": "1", "result": "PASS", "evidence_refs": ["receipt:unit-suite"], "reason": "test_90m asserts 5400"},
    {"id": "2", "result": "NOT_PROVEN", "evidence_refs": [], "reason": "no test or receipt for invalid input"}
  ],
  "findings": [
    {"id": "f1", "class": "weakened-oracle", "summary": "tolerance added to the 1h30m assertion", "evidence_refs": ["tests/test_duration.py:12"]}
  ],
  "evidence_refs": ["receipt:unit-suite"],
  "checked": ["diff of src/duration.py"],
  "not_checked": ["2: invalid input raises ValueError"],
  "validated_at": "2026-10-25T12:00:00Z"
}
```

From the Report: `Verdict` is `verdict`. Each criterion's verified, failed or
not verified is `criteria[].result` `PASS`, `FAIL` or `NOT_PROVEN`, with its
evidence in `evidence_refs` and its reasoning in `reason`. Each finding is a
`findings[]` entry with `id`, `class`, `summary` and at least one
`evidence_refs` item. `Checked` and `Not checked` are `checked` and
`not_checked`; `validated_at` is an RFC 3339 time. `Subject` and `Identity` go
in `--subject-manifest`, `--author-context-id`, `--validator-context-id`,
`--freshness-source` and `--freshness-attester-id`, never in the draft.
`verdict.v2` has no model field: when a cross-family leg ran, record each leg's
actual model and context identity in `evidence_refs`. A
`PASS` needs every criterion `PASS` with evidence, nonempty `evidence_refs`
and `checked`, and an empty `not_checked`; otherwise storage records
`NOT_PROVEN` with a `validate.integrity` finding. The full contract (AgentOps
source checkout only) is
[verdict.v2.schema.json](https://github.com/boshu2/agentops/blob/main/schemas/verdict.v2.schema.json).

## Evidence storage

The evidence root must already exist outside every Git repository (ordinary,
bare or linked), including symlink aliases and storage the active `GIT_*`
environment bindings name. Intents go under
`<root>/intents/sha256/<digest>.intent`, verdicts under
`<root>/verdicts/sha256/<digest>.json`, and `manifest --out` files stay under
that same root. Every output path is checked before any write; a missing or
invalid root fails with no workspace fallback, and destination descendants
cannot be symlinks. The guard cannot discover every external repository: pass
`--exclude-git-root <dir>` for Git storage the active bindings do not reveal.
It is a filesystem check; native access controls still own authorization,
confidentiality and hostile concurrent writers.

These helpers read no configuration. For knowledge or disclosure review, the
caller passes an existing protected non-Git directory as `--evidence-root`;
drafts, manifests, receipts and diagnostics belong there too. Standalone
product-proof placement remains explicitly caller-selected.

`verify-subject` compares current subject identity and the supplied verdict to
an independently supplied immutable `--intent`; the candidate cannot choose its
own expected policy. Use distinct expected acceptance for factual-support and
destination-disclosure review, require every selected leg to bind both
identities, and pin any required profile version and policy in those immutable
bytes. Structural validity, factual support, destination permission and later
usefulness remain separate questions. Evidence references are declared
strings, not verified citations; read permission does not authorize model
transmission or Git ingestion.

## Cross-model legs

Cross-model review is opt-in: `--cross-model [model]` is a skill prompt
selection, not an AO flag, adding a fresh other-family reviewer through
[model-dispatch](model-dispatch.md). A required
leg that cannot run is a `diversity_unsatisfied` finding and makes the combined
result NOT_PROVEN, even if another leg passed; unavailable optional diversity
is disclosed without erasing findings. Delivered FAILs and dissent stand;
neither voting nor model preference makes a split PASS, and agreement is not
proof of truth. A split between legs goes to the caller, who may select
[Council on the split](../../council/references/judge-split.md).

## Where each scope limit lives inside a PASS

| Scope limit | Home | Example |
|---|---|---|
| A criterion proven by a bounded check | `criteria[].reason` on that criterion | "proven by the unit suite; the full integration matrix was not replayed" |
| A declared non-goal or out-of-scope area | the intent source's non-goals, optionally restated as an evidence-backed boundary criterion in `criteria` | "`cli/**` is a declared non-goal; the diff proves it untouched" |
| Residual risk or judgment caveat | the caller-facing report | "the migration path is untested against pre-3.0 stores" |
| Acceptance that genuinely went unverified | `not_checked`, and the result is `NOT_PROVEN` rather than PASS | "criterion 3 needs hardware this context cannot reach" |
