# Validate mechanics

Loaded by `SKILL.md` at the manifest step (helper commands), at cross-family
dispatch (adapters), and at scope disclosure (the homes table). `$SKILL_DIR`
is the directory containing `SKILL.md`: `skills/validate/` in a repository
checkout, `.agents/skills/validate/` in an installed runtime.

## Helper commands

| Command | Required | Optional |
|---|---|---|
| `manifest` | `--root <dir>`, `--include <path>` (repeatable, at least one) | `--exclude <path-or-glob>` (repeatable), `--base-manifest <file>`, `--git-metadata-json <json>`, `--output <file>` |
| `verify-manifest` | `--root <dir>`, `--manifest <file>` | `--base-manifest <file>` |
| `snapshot-intent` | `--source <file>` (`-` reads stdin) | `--workspace <dir>`, `--intent-dir <dir>` |
| `digest` | `<json-file>` positional | none |
| `store-verdict` | `--draft`, `--intent-source`, `--subject-manifest`, `--author-context-id`, `--validator-context-id`, `--freshness-source <runtime\|caller>`, `--freshness-attester-id`, `--scope-result <PASS\|FAIL\|NOT_PROVEN>` | `--workspace <dir>`, `--verdict-dir <dir>` |

```sh
python3 "$SKILL_DIR/scripts/validate.py" manifest \
  --root . --include skills/validate --exclude '**/*.log' --output manifest.json
```

`manifest` uses only filesystem content; Git commit and tree IDs are optional
metadata. `store-verdict` snapshots the exact resolved intent under
`<workspace>/.agents/ao/intents/sha256/<digest>.intent`, then computes and
injects intent and subject digests plus author, validator, and freshness facts
from runtime-derived inputs and receipts, never model transcription. Storage
defaults to `<workspace>/.agents/ao/verdicts/sha256/<digest>.json`; callers
may provide `verdict_dir`. The digest is SHA-256 over canonical JSON with
`artifact_digest` omitted. Writes use a same-directory temporary file, flush,
fsync, and atomic rename. Identical existing content is idempotent success;
conflicting content is an integrity failure represented by `NOT_PROVEN`.
`store-verdict` refuses an empty manifest and refuses a PASS carrying
`not_checked` entries, recording a `validate.integrity` finding.

## Selected CDLC evidence routing (contract, later runtime work)

For knowledge/disclosure review, the caller must resolve an external protected
non-Git evidence root before any storage. Intents, drafts, manifests, verdicts,
receipts and diagnostics all belong there; missing or ambiguous owner/project
routing fails without consumer-workspace fallback. Exact factual support and
destination disclosure use distinct immutable caller-supplied acceptance and
exact payload/metadata identities. A fresh authorized reviewer may judge both;
neither substitutes for later usefulness. Read permission alone does not permit
model transmission or Git ingestion. ADR-0016 owns the full confidentiality order.

The current helper table above describes standalone behavior. In particular,
`store-verdict` still snapshots under `<workspace>/.agents/ao/intents/sha256`;
`--verdict-dir` alone does not relocate all evidence. This source adoption does
not implement the selected Go manifest/snapshot/verdict-storage path or certify
current helper defaults for restricted CDLC inputs. Keep such inputs out of an
incompatible entrypoint until its later owner provides the explicit external
routing and shared conformance. Existing requested standalone proof remains
caller-owned and is preserved.

## Proportionate fresh checks

Apply the owning skill's prospective effect-based risk rule. A low-risk wording
correction can use one fresh judge; acceptance or enforcement changes and
unknown risk require stronger review. The current change keeps every review
leg already required. This changes review cost, never the exact subject, full
acceptance, evidence for every criterion, or the empty-`not_checked` bar.

Reuse existing digest-bound check receipts when their subject, inputs, tool
identity, and claimed criterion still match. Rerun the fast discriminating
check for a changed or uncertain criterion; rerun broader checks when the change
invalidates their receipts or acceptance explicitly requires them. A new receipt
label, changed digest, reduced finding count, or repeated review is not useful
progress without evidence that a named acceptance gap closed. Reuse the current
findings/evidence fields for causal comparisons; create no progress ledger.

## Cross-family adapters

Use the single [agent-native model-dispatch recipe](../../agent-native/references/model-dispatch.md)
for caller selection, host authorization and bounded invocation. Both fresh
and required cross-family exact-subject legs remain; their initial inputs are
independent. A judge reads and judges; it never mutates the subject. Record
actual author/judge model and context identities in protected evidence refs
and freshness attestation notes; the `verdict.v2` schema is unchanged.
Transport, output, exit and process completion are facts, not semantic PASS.

## Where each scope limit lives inside a PASS

| Scope limit | Home | Example |
|---|---|---|
| A criterion proven by a bounded check | `criteria[].reason` on that criterion | "proven by the unit suite; the full integration matrix was not replayed" |
| A declared non-goal or out-of-scope area | the intent source's non-goals, optionally restated as an evidence-backed boundary criterion in `criteria` | "`cli/**` is a declared non-goal; the diff proves it untouched" |
| Residual risk or judgment caveat | the caller-facing report | "the migration path is untested against pre-3.0 stores" |
| Acceptance that genuinely went unverified | `not_checked`, and the result is `NOT_PROVEN` rather than PASS | "criterion 3 needs hardware this context cannot reach" |
