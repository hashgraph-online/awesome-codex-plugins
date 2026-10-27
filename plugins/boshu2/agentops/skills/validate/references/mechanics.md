# Validate mechanics

Depth for [SKILL.md](../SKILL.md): the `ao provenance` helpers, the
`store-verdict` draft, evidence storage, cross-family adapters, report
proportion and where each scope limit lives. Judgment never depends on this
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
Version 1 retains the reference's asymmetric root rule: live files and symlinks
use literal include roots, while deletion selection and structural membership
use the historical filename-pattern match against the base. Verification still
requires that exact base and recomputes the complete manifest.

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
`--freshness-source` and `--freshness-attester-id`, never in the draft. A
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
caller resolves the protected external evidence root, for example with
`ao config context --field evidence_root`, and passes it as `--evidence-root`;
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

## Proportionate fresh checks

Apply the owning skill's fresh same-family default. Risk sizes evidence depth;
only caller selection requires a different model family. Preserve an explicitly
requested leg until the caller changes it. Every mode retains exact subject,
full acceptance, evidence for every criterion, and the empty-`not_checked` bar.

Reuse existing digest-bound check receipts when their subject, inputs, tool
identity, and claimed criterion still match. Rerun the fast discriminating
check for a changed or uncertain criterion; rerun broader checks when the change
invalidates their receipts or acceptance explicitly requires them. A new receipt
label, changed digest, reduced finding count, or repeated review is not useful
progress without evidence that a named acceptance gap closed. Reuse the current
findings/evidence fields for causal comparisons; create no progress ledger.

## Cross-family adapters

Use the single [agent-native model-dispatch recipe](../../agent-native/references/model-dispatch.md)
for caller selection, host authorization and bounded invocation. The fresh
same-family leg and any explicitly selected cross-family leg receive independent
initial inputs. Time bounds come from the caller or native deadline. A judge
reads and judges; it never mutates the subject. Record
actual author/judge model and context identities in protected evidence refs
and freshness attestation notes; the `verdict.v2` schema is unchanged.
Transport, output, exit and process completion are facts, not semantic PASS.

## Report proportion

Keep the report proportional: cite the exact subject, complete bound manifest
and existing receipts instead of copying path or digest inventories. Group
generated companions by source owner and verified equivalence; still verify
every changed path and cited binding. Include excerpts only to assess a finding.
Retain every criterion, necessary finding, identity, freshness fact and
unchecked surface. Complete coverage does not require a second copy of the
evidence.

When delivery is outside the accepted review scope, the caller checks its
native facts without another semantic review of unchanged content. Use the
existing result for any pending delivery update, without repeating the
investigation or creating another report.

## Where each scope limit lives inside a PASS

| Scope limit | Home | Example |
|---|---|---|
| A criterion proven by a bounded check | `criteria[].reason` on that criterion | "proven by the unit suite; the full integration matrix was not replayed" |
| A declared non-goal or out-of-scope area | the intent source's non-goals, optionally restated as an evidence-backed boundary criterion in `criteria` | "`cli/**` is a declared non-goal; the diff proves it untouched" |
| Residual risk or judgment caveat | the caller-facing report | "the migration path is untested against pre-3.0 stores" |
| Acceptance that genuinely went unverified | `not_checked`, and the result is `NOT_PROVEN` rather than PASS | "criterion 3 needs hardware this context cannot reach" |
